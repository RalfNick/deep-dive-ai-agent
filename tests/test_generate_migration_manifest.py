import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


from scripts.generate_migration_manifest import build_records, render_manifest


class GenerateMigrationManifestTests(unittest.TestCase):
    def test_text_payloads_are_hashed_with_canonical_lf_bytes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book").mkdir()
            (root / "book" / "chapter1.md").write_bytes(b"line-one\r\nline-two\r\n")

            records = build_records(root, "a" * 40, "b" * 40)

        canonical = b"line-one\nline-two\n"
        self.assertEqual(len(canonical), records[0].size)
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), records[0].sha256)

    def test_classifies_sources_and_hashes_target_bytes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book" / "images").mkdir(parents=True)
            (root / "book" / "chapter1.md").write_bytes(b"chapter-one")
            (root / "book" / "chapter5.md").write_bytes(b"chapter-five")
            (root / "book" / "images" / "fig5-1.svg").write_bytes(b"<svg/>")
            (root / "docs" / "author-sources").mkdir(parents=True)
            (root / "docs" / "author-sources" / "article.md").write_bytes(
                b"author-source"
            )

            records = build_records(root, "a" * 40, "b" * 40)

        self.assertEqual(
            [
                "book/chapter1.md",
                "book/chapter5.md",
                "book/images/fig5-1.svg",
                "docs/author-sources/article.md",
            ],
            [record.target for record in records],
        )
        self.assertEqual("current-workspace", records[0].source)
        self.assertEqual("a" * 40, records[0].commit)
        self.assertEqual("chapter6-worktree", records[1].source)
        self.assertEqual("b" * 40, records[1].commit)
        self.assertEqual(len(b"chapter-one"), records[0].size)
        self.assertEqual(hashlib.sha256(b"chapter-one").hexdigest(), records[0].sha256)

    def test_ignores_local_dependency_and_build_directories(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book" / "node_modules" / "package").mkdir(parents=True)
            (root / "book" / "node_modules" / "package" / "index.js").write_text(
                "generated dependency", encoding="utf-8"
            )
            (root / "book" / "__pycache__").mkdir()
            (root / "book" / "__pycache__" / "cache.pyc").write_bytes(b"cache")
            (root / "book" / "chapter1.md").write_text("chapter", encoding="utf-8")

            records = build_records(root, "a" * 40, "b" * 40)

        self.assertEqual(["book/chapter1.md"], [record.target for record in records])

    def test_rendered_rows_use_the_machine_readable_contract(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book").mkdir()
            (root / "book" / "introduction.md").write_text("intro", encoding="utf-8")
            records = build_records(root, "a" * 40, "b" * 40)

            rendered = render_manifest(records)

        expected = (
            "| `book/introduction.md` | `current-workspace` | "
            f"`{'a' * 40}` | 5 | `{hashlib.sha256(b'intro').hexdigest()}` |"
        )
        self.assertIn(expected, rendered)
        self.assertIn("不导入 PDF、HTML", rendered)
        self.assertIn("作者既有工程文章", rendered)
        self.assertIn("chapter6/tests/test_pdf_release.py", rendered)


if __name__ == "__main__":
    unittest.main()
