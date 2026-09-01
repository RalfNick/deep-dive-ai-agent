from pathlib import Path
import unittest

from scripts.validate_book_manifest import validate_manifest


ROOT = Path(__file__).resolve().parents[1]


class BookManifestTest(unittest.TestCase):
    def test_manifest_exposes_nine_published_and_nine_unpublished_chapters(self):
        manifest = validate_manifest(ROOT)
        chapters = [
            chapter
            for section in manifest["sections"]
            for chapter in section["chapters"]
        ]

        self.assertEqual(18, len(chapters))
        self.assertEqual(list(range(1, 19)), [chapter["order"] for chapter in chapters])
        self.assertEqual(9, sum(chapter["status"] == "published" for chapter in chapters))
        self.assertEqual("published", chapters[8]["status"])
        self.assertTrue(all(chapter["status"] == "planned" for chapter in chapters[9:]))

    def test_every_published_entry_has_reachable_publication_files(self):
        manifest = validate_manifest(ROOT)
        entries = [manifest["introduction"]] + [
            chapter
            for section in manifest["sections"]
            for chapter in section["chapters"]
            if chapter["status"] == "published"
        ]

        for entry in entries:
            self.assertTrue((ROOT / "book" / entry["source"]).is_file())

        self.assertTrue((ROOT / "book" / manifest["cover"]).is_file())

    def test_unpublished_chapters_do_not_expose_publication_files(self):
        manifest = validate_manifest(ROOT)
        chapters = [
            chapter
            for section in manifest["sections"]
            for chapter in section["chapters"]
        ]

        for chapter in chapters:
            if chapter["status"] != "published":
                self.assertTrue(
                    {"source", "experiment", "answers"}.isdisjoint(chapter),
                    chapter["slug"],
                )


if __name__ == "__main__":
    unittest.main()
