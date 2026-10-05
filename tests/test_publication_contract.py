"""Behavior gates for manifest-selected chapters, appendices and stable reports."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_site import build_site
from scripts.validate_book_manifest import validate_manifest


ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def repository(root: Path, *, all_published: bool = True) -> dict:
    for relative in ("README.md", "CONTRIBUTING.md", "LICENSE", "book/README.md",
                     "book/OUTLINE.md", "book/WRITING_GUIDE.md", "book-en/README.md",
                     "docs/EXPERIMENT_STATUS.md", "docs/TRANSLATION.md", "docs/RELEASES.md"):
        write(root / relative, "# Public fixture\n")
    write(root / "book/introduction.md", "# Introduction\n")
    write(root / "book/images/cover.svg", "<svg/>\n")
    chapters = []
    for number in range(1, 19):
        published = all_published or number <= 14
        entry = {"order": number, "slug": f"chapter-{number}", "title": f"Chapter {number}",
                 "status": "published" if published else "planned", "summary": "fixture"}
        if published:
            entry.update(source=f"chapter{number}.md", experiment=f"../chapter{number}/README.md",
                         answers=f"../chapter{number}/reference-answers.md", updated="2026-10-05")
        chapters.append(entry)
        write(root / f"book/chapter{number}.md", f"# Chapter {number}\n![figure](images/chapter{number}/01.svg)\n")
        write(root / f"book/images/chapter{number}/01.svg", "<svg/>\n")
        write(root / f"chapter{number}/README.md", f"# Lab {number}\n")
        write(root / f"chapter{number}/reference-answers.md", "# Answers\n")
    appendix = {"slug": "appendix-a", "title": "Appendix A", "status": "published",
                "summary": "preparation", "source": "appendix-a.md",
                "experiment": "../appendix_a/README.md", "answers": "../appendix_a/EXERCISE_ANSWERS.md",
                "updated": "2026-10-05"}
    write(root / "book/appendix-a.md", "# Appendix A\n![figure](images/appendix-a/01.svg)\n")
    write(root / "book/images/appendix-a/01.svg", "<svg/>\n")
    write(root / "appendix_a/README.md", "# Preparation\n")
    write(root / "appendix_a/EXERCISE_ANSWERS.md", "# Answers\n")
    if not all_published:
        appendix = {key: value for key, value in appendix.items()
                    if key in {"slug", "title", "summary"}}
        appendix["status"] = "planned"
    manifest = {"slug": "fixture", "title": "Fixture", "subtitle": "Fixture", "description": "Fixture",
                "version": "0.18.0", "updated": "2026-10-05", "cover": "images/cover.svg",
                "repositoryUrl": "https://example.com/repo", "totalChapters": 18,
                "introduction": {"slug": "introduction", "title": "Introduction", "status": "published",
                                 "summary": "fixture", "source": "introduction.md", "updated": "2026-10-05"},
                "sections": [{"order": 1, "title": "Book", "chapters": chapters}],
                "appendices": [appendix]}
    save_manifest(root, manifest)
    return manifest


def save_manifest(root: Path, manifest: dict) -> None:
    write(root / "book/manifest.json", json.dumps(manifest, ensure_ascii=False))


class PublicationContractTests(unittest.TestCase):
    def test_published_appendix_is_valid_without_a_chapter_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            manifest = validate_manifest(root)
            self.assertEqual(18, manifest["totalChapters"])
            self.assertEqual("appendix-a.md", manifest["appendices"][0]["source"])
            self.assertNotIn("order", manifest["appendices"][0])

    def test_appendix_source_must_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = repository(root)
            manifest["appendices"][0]["source"] = "missing-appendix.md"
            save_manifest(root, manifest)
            with self.assertRaises(FileNotFoundError):
                validate_manifest(root)

    def test_appendix_paths_cannot_escape_the_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            manifest = repository(root)
            write(root.parent / "outside.md", "outside\n")
            manifest["appendices"][0]["answers"] = "../../outside.md"
            save_manifest(root, manifest)
            with self.assertRaisesRegex(ValueError, "escapes repository root"):
                validate_manifest(root)

    def test_unpublished_appendix_cannot_expose_publication_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = repository(root)
            manifest["appendices"][0]["status"] = "planned"
            save_manifest(root, manifest)
            with self.assertRaisesRegex(ValueError, "unpublished.*exposes files"):
                validate_manifest(root)

    def test_appendix_slug_cannot_duplicate_a_chapter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = repository(root)
            manifest["appendices"][0]["slug"] = "chapter-1"
            save_manifest(root, manifest)
            with self.assertRaisesRegex(ValueError, "slugs must be unique"):
                validate_manifest(root)

    def test_appendices_must_be_an_array(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = repository(root)
            manifest["appendices"] = {}
            save_manifest(root, manifest)
            with self.assertRaisesRegex(ValueError, "appendices must be an array"):
                validate_manifest(root)

    def test_site_includes_all_published_chapters_and_appendix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            build_site(root, root / "_web")
            public = {path.relative_to(root / "_web").as_posix()
                      for path in (root / "_web").rglob("*") if path.is_file()}
            self.assertIn("book/chapter18.md", public)
            self.assertIn("chapter18/index.md", public)
            self.assertIn("book/images/chapter18/01.svg", public)
            self.assertIn("book/appendix-a.md", public)
            self.assertIn("appendix_a/index.md", public)
            self.assertIn("appendix_a/EXERCISE_ANSWERS.md", public)
            self.assertIn("book/images/appendix-a/01.svg", public)

    def test_site_manifest_can_withhold_an_earlier_chapter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = repository(root)
            chapter = manifest["sections"][0]["chapters"][0]
            for field in ("source", "experiment", "answers", "updated"):
                chapter.pop(field)
            chapter["status"] = "planned"
            save_manifest(root, manifest)
            build_site(root, root / "_web")
            self.assertFalse((root / "_web/book/chapter1.md").exists())
            self.assertFalse((root / "_web/chapter1/index.md").exists())
            self.assertFalse((root / "_web/book/images/chapter1/01.svg").exists())

    def test_candidate_chapters_and_appendix_stay_private(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root, all_published=False)
            build_site(root, root / "_web")
            public = [path.relative_to(root / "_web").as_posix()
                      for path in (root / "_web").rglob("*") if path.is_file()]
            for stem in ("chapter15", "chapter16", "chapter17", "chapter18", "appendix-a", "appendix_a"):
                self.assertFalse(any(stem in path for path in public), stem)

    def test_site_exports_only_current_canonical_report_bundles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            current = ("chapter15/reports/post-training-report.json", "chapter16/reports/improvement-report.json",
                       "chapter17/reports/reference-rc3/report.json", "chapter18/reports/reference-rc2/team-report.json",
                       "appendix_a/reports/reference-rc1/api.json")
            historical = ("chapter15/report-history/v1.0-rc1/post-training-report.json",
                          "chapter16/reports/local-debug/private.json", "chapter17/reports/reference-rc2/report.json",
                          "chapter18/reports/reference-rc1/team-report.json", "appendix_a/reports/local-debug/private.json")
            for relative in current + historical:
                write(root / relative, "{}\n")
            build_site(root, root / "_web")
            for relative in current:
                self.assertTrue((root / "_web" / relative).is_file(), relative)
            for relative in historical:
                self.assertFalse((root / "_web" / relative).exists(), relative)


class PublicationMetadataHistoryTests(unittest.TestCase):
    def test_readme_publication_edits_retain_frozen_git_bytes_not_current_bytes(self):
        from book.tests.edition_contracts import assert_frozen_history, preserved_payload
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "chapter15/README.md"
            write(root / relative, "local candidate\n")
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            subprocess.run(["git", "add", relative], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                            "commit", "-qm", "Frozen candidate"], cwd=root, check=True, capture_output=True)
            baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                                      capture_output=True, text=True).stdout.strip()
            write(root / relative, "published edition\n")
            with patch("book.tests.edition_contracts.PUBLICATION_BASELINE", baseline, create=True):
                self.assertEqual(b"local candidate\n", preserved_payload(root, relative).replace(b"\r\n", b"\n"))
                assert_frozen_history(root, baseline, [relative])

    def test_readme_editorial_changes_use_the_actual_prepublication_git_bytes(self):
        from book.tests.edition_contracts import preserved_payload
        for relative in ["book/README.md"] + [f"chapter{number}/README.md" for number in range(15, 19)]:
            frozen = subprocess.run(["git", "show", f"363b05a:{relative}"], cwd=ROOT,
                                    check=True, capture_output=True).stdout
            self.assertEqual(frozen.replace(b"\r\n", b"\n"),
                             preserved_payload(ROOT, relative).replace(b"\r\n", b"\n"))


class PublicationWorkflowTests(unittest.TestCase):
    def test_final_chapter_hash_enforcement_only_uses_hashed_requirements(self):
        import yaml

        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
        expected_steps = {
            "Run Chapter 15 tests in its locked environment",
            "Run Chapter 16 tests in its locked environment",
            "Run Chapter 17, Chapter 18 and Appendix A tests in a locked environment",
        }
        steps = [step for job in workflow["jobs"].values() for step in job["steps"]
                 if step.get("name") in expected_steps]
        self.assertEqual(expected_steps, {step["name"] for step in steps})
        for step in steps:
            for command in step["run"].splitlines():
                if "pip install" not in command:
                    continue
                requirements = re.findall(r"(?:^|\s)-r\s+(\S+)", command)
                self.assertTrue(requirements, command)
                for relative in requirements:
                    with self.subTest(step=step["name"], requirements=relative):
                        text = (ROOT / relative).read_text(encoding="utf-8")
                        records = [line.strip() for line in re.sub(r"\\\s*\n", " ", text).splitlines()
                                   if line.strip() and not line.lstrip().startswith("#")]
                        self.assertTrue(records, relative)
                        hashed = all("--hash=sha256:" in line for line in records)
                        if "--require-hashes" in command:
                            self.assertTrue(hashed, f"Unhashed requirements forced into hash mode: {relative}")
                        if relative.endswith("requirements-dev.txt"):
                            self.assertTrue(hashed, relative)
                            self.assertIn("--require-hashes", command)
                        else:
                            self.assertTrue(relative.endswith("requirements-preview.txt"), relative)
                            self.assertFalse(hashed, relative)
                            self.assertNotIn("--require-hashes", command)


class MkDocsAnchorTests(unittest.TestCase):
    def render(self, text: str) -> str:
        import markdown
        from mkdocs.config import load_config
        config = load_config(str(ROOT / "mkdocs.yml"), docs_dir=str(ROOT / "book"))
        return markdown.Markdown(extensions=config["markdown_extensions"],
                                 extension_configs=config["mdx_configs"]).convert(text)

    def test_chapter17_answers_chinese_fragment_has_a_rendered_destination(self):
        html = self.render((ROOT / "book/chapter17.md").read_text(encoding="utf-8"))
        self.assertIn('id="十三道分层练习"', html)

    def test_render_uses_real_extensions_without_a_generated_web_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root / "mkdocs.yml", (ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
            text = "## 十三道分层练习\n\n## Quick Start\n"
            write(root / "book/chapter17.md", text)
            self.assertFalse((root / "_web").exists())
            with patch(f"{__name__}.ROOT", root):
                html = self.render(text)
            self.assertIn('id="十三道分层练习"', html)
            self.assertIn('id="quick-start"', html)
            self.assertFalse((root / "_web").exists())

    def test_existing_english_heading_slug_contract_is_preserved(self):
        html = self.render("## Quick Start\n\n## api_contract-v1\n\n## REST API: Error Handling\n")
        for slug in ("quick-start", "api_contract-v1", "rest-api-error-handling"):
            self.assertIn(f'id="{slug}"', html)


if __name__ == "__main__":
    unittest.main()
