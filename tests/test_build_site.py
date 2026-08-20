from hashlib import sha256
from pathlib import Path
import tempfile
import unittest


from scripts.build_site import build_site


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
        for number in range(1, 7):
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
            required.update(f"book/chapter{number}.md" for number in range(1, 7))
            required.update(f"chapter{number}/index.md" for number in range(1, 7))
            required.update(
                f"chapter{number}/reference-answers.md" for number in range(1, 7)
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


if __name__ == "__main__":
    unittest.main()
