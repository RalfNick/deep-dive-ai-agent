from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs" / "author-sources"
IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?P<target>[^)]+)\)")


class AuthorSourceArchiveTests(unittest.TestCase):
    def test_chapter_six_author_sources_are_preserved_in_the_new_repository(self) -> None:
        expected = (
            ARCHIVE / "phase-4" / "03-agent-memory-system.md",
            ARCHIVE / "phase-4" / "05-agent-runtime-integration.md",
            ARCHIVE
            / "codex-tutorial"
            / "2026-08-12-from-ai-coding-to-digital-employee.md",
        )
        self.assertEqual([], [path.relative_to(ROOT).as_posix() for path in expected if not path.is_file()])

    def test_archived_author_source_images_resolve_locally(self) -> None:
        broken = []
        for article in ARCHIVE.rglob("*.md") if ARCHIVE.exists() else ():
            text = article.read_text(encoding="utf-8")
            for match in IMAGE_RE.finditer(text):
                target = match.group("target").split("#", 1)[0]
                if not target or "://" in target:
                    continue
                if not (article.parent / target).resolve().is_file():
                    broken.append(
                        f"{article.relative_to(ROOT).as_posix()} -> {target}"
                    )
        self.assertEqual([], broken)


if __name__ == "__main__":
    unittest.main()
