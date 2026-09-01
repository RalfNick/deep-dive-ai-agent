from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")


class ExperimentInventoryTests(unittest.TestCase):
    def test_each_chapter_has_reader_contract_files(self) -> None:
        missing = []
        for number in range(1, 10):
            chapter = ROOT / f"chapter{number}"
            for name in ("README.md", "requirements.txt", "reference-answers.md"):
                if not (chapter / name).is_file():
                    missing.append(f"chapter{number}/{name}")
        self.assertEqual([], missing)

    def test_experiment_tree_has_no_private_or_generated_artifacts(self) -> None:
        forbidden = []
        for number in range(1, 10):
            chapter = ROOT / f"chapter{number}"
            if not chapter.exists():
                continue
            for path in chapter.rglob("*"):
                relative = path.relative_to(ROOT).as_posix()
                if path.name in {"__pycache__", ".env", "live-reports"}:
                    forbidden.append(relative)
                if path.is_file() and path.suffix.lower() in {".pyc", ".pdf"}:
                    forbidden.append(relative)
        self.assertEqual([], forbidden)

    def test_chapter_readme_local_links_resolve(self) -> None:
        broken = []
        for number in range(1, 10):
            readme = ROOT / f"chapter{number}" / "README.md"
            if not readme.is_file():
                continue
            for match in LINK_RE.finditer(readme.read_text(encoding="utf-8")):
                target = match.group("target").split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (readme.parent / target).resolve()
                if not resolved.exists():
                    broken.append(f"chapter{number}/README.md -> {target}")
        self.assertEqual([], broken)

    def test_legacy_pdf_release_test_is_not_active(self) -> None:
        self.assertFalse((ROOT / "chapter6" / "tests" / "test_pdf_release.py").exists())


if __name__ == "__main__":
    unittest.main()
