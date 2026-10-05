from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest


from scripts.build_site import build_site
from scripts.validate_book_manifest import validate_manifest


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class BuildSiteTests(unittest.TestCase):
    def make_repository(self, root: Path) -> None:
        write(
            root / "README.md",
            "# Home\n[Book](book/README.md) [Lab](chapter1/README.md) "
            "[English](book-en/README.md)\n",
        )
        write(root / "CONTRIBUTING.md", "# Contributing\n")
        write(root / "LICENSE", "license\n")
        write(root / "docs" / "EXPERIMENT_STATUS.md", "# Status\n")
        write(root / "docs" / "TRANSLATION.md", "# Translation\n")
        write(root / "docs" / "RELEASES.md", "# Releases\n")
        write(root / "book-en" / "README.md", "status: planned\n")
        write(root / "book-en" / "chapter1.md", "must not publish\n")
        write(root / "book" / "README.md", "# Book\n")
        write(root / "book" / "introduction.md", "# Introduction\n")
        write(root / "book" / "OUTLINE.md", "# Outline\n")
        write(root / "book" / "WRITING_GUIDE.md", "# Guide\n")
        write(root / "book" / "sources" / "chapter1-sources.md", "private ledger\n")
        write(root / "book" / "reviews" / "chapter1-review.md", "private review\n")
        write(root / "book" / "images" / "figure.svg", "<svg/>\n")
        for number in range(1, 15):
            write(
                root / "book" / f"chapter{number}.md",
                f"# Chapter {number}\n![figure](./images/figure.svg)\n",
            )
            write(root / f"chapter{number}" / "README.md", f"# Lab {number}\n")
            write(
                root / f"chapter{number}" / "reference-answers.md",
                f"# Answers {number}\n",
            )
        write(root / "chapter1" / "reports" / "report.json", "{}\n")
        (root / "chapter1" / "ignored.pdf").write_bytes(b"pdf")
        chapters = []
        for number in range(1, 19):
            entry = {"order": number, "slug": f"chapter-{number}", "title": f"Chapter {number}",
                     "status": "published" if number <= 14 else "planned", "summary": "fixture"}
            if number <= 14:
                entry.update(source=f"chapter{number}.md", experiment=f"../chapter{number}/README.md",
                             answers=f"../chapter{number}/reference-answers.md", updated="2026-09-27")
            chapters.append(entry)
        write(root / "book/manifest.json", json.dumps({
            "slug": "fixture", "title": "Fixture", "subtitle": "Fixture", "description": "Fixture",
            "version": "0.14.0", "updated": "2026-09-27", "cover": "images/figure.svg",
            "repositoryUrl": "https://example.com/repo", "totalChapters": 18,
            "introduction": {"slug": "introduction", "title": "Introduction", "status": "published",
                             "summary": "fixture", "source": "introduction.md", "updated": "2026-09-27"},
            "sections": [{"order": 1, "chapters": chapters}],
        }))

    def test_builds_the_allowlisted_chinese_site_tree_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repository(root)
            output = root / "_web"

            build_site(root, output)
            first = snapshot(output)
            build_site(root, output)
            second = snapshot(output)

            required = {
                "index.md",
                "book/index.md",
                "book/introduction.md",
                "book/images/figure.svg",
                "book-en/index.md",
            }
            required.update(f"book/chapter{number}.md" for number in range(1, 15))
            required.update(f"chapter{number}/index.md" for number in range(1, 15))
            required.update(
                f"chapter{number}/reference-answers.md" for number in range(1, 15)
            )
            self.assertEqual(set(), required - set(first))
            self.assertEqual(first, second)
            self.assertNotIn("book/sources/chapter1-sources.md", first)
            self.assertNotIn("book/reviews/chapter1-review.md", first)
            self.assertNotIn("book-en/chapter1.md", first)
            self.assertFalse(any(path.endswith(".pdf") for path in first))
            index = (output / "index.md").read_text(encoding="utf-8")
            self.assertIn("(book/index.md)", index)
            self.assertIn("(chapter1/index.md)", index)
            self.assertIn("(book-en/index.md)", index)

    def test_refuses_to_delete_an_output_outside_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            self.make_repository(root)

            with self.assertRaisesRegex(ValueError, "output must stay inside repository"):
                build_site(root, root.parent / "outside")

    def test_unpublished_chapter_fifteen_stays_out_of_public_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repository(root)
            write(root / "book" / "chapter15.md", "# Local candidate\n")
            write(root / "book" / "images" / "chapter15" / "01-local.svg", "<svg/>\n")
            write(root / "chapter15" / "README.md", "# Local lab\n")
            write(root / "chapter15" / "reference-answers.md", "# Local answers\n")
            write(root / "chapter15" / "reports" / "candidate.json", "{}\n")

            output = root / "_web"
            build_site(root, output)
            published = snapshot(output)

            self.assertFalse(any("chapter15" in path for path in published))
            for number in range(1, 15):
                self.assertIn(f"book/chapter{number}.md", published)
                self.assertIn(f"chapter{number}/index.md", published)
            manifest = validate_manifest(root)
            self.assertEqual("0.14.0", manifest["version"])
            self.assertEqual("planned", manifest["sections"][0]["chapters"][14]["status"])

    def test_chapter16_stays_out_of_public_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repository(root)
            write(root / "book/chapter16.md", "# Local chapter 16\n")
            write(root / "book/images/chapter16/01-local.svg", "<svg/>\n")
            write(root / "chapter16/README.md", "# Local experiment\n")
            write(root / "chapter16/reference-answers.md", "# Local answers\n")
            write(root / "chapter16/reports/local.json", "{}\n")
            write(root / "book/reviews/chapter16-review.md", "# Local review\n")
            write(root / "book/versions/chapter16-v1.0-rc1.md", "# Local history\n")
            output = root / "_web"
            build_site(root, output)
            self.assertFalse(any("chapter16" in path for path in snapshot(output)))
            for number in range(1, 15):
                self.assertTrue((output / f"book/chapter{number}.md").is_file())

    def test_chapter_nine_supplement_remains_readable_after_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repository(root)
            write(root / "chapter9" / "faq.md", "# FAQ\n[Return](../book/chapter9.md)\n")
            write(root / "chapter8" / "production-guide.md", "# Production\n[Return](../book/chapter8.md)\n")
            output = root / "_web"
            build_site(root, output)
            self.assertTrue((output / "chapter9" / "faq.md").is_file())
            self.assertTrue((output / "chapter8" / "production-guide.md").is_file())
            self.assertIn("../book/chapter9.md", (output / "chapter9" / "faq.md").read_text())


if __name__ == "__main__":
    unittest.main()
