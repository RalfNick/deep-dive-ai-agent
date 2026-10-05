from pathlib import Path
import unittest

from scripts.validate_book_manifest import validate_manifest


ROOT = Path(__file__).resolve().parents[1]


class BookManifestTest(unittest.TestCase):
    def test_manifest_exposes_eighteen_published_chapters_and_one_appendix(self):
        manifest = validate_manifest(ROOT)
        self.assertEqual("0.18.0", manifest["version"])
        chapters = [
            chapter
            for section in manifest["sections"]
            for chapter in section["chapters"]
        ]

        self.assertEqual(18, len(chapters))
        self.assertEqual(list(range(1, 19)), [chapter["order"] for chapter in chapters])
        self.assertEqual(18, sum(chapter["status"] == "published" for chapter in chapters))
        self.assertTrue(all(chapter["status"] == "published" for chapter in chapters))
        self.assertEqual(["appendix-a"], [entry["slug"] for entry in manifest["appendices"]])
        appendix = manifest["appendices"][0]
        self.assertEqual("published", appendix["status"])
        self.assertNotIn("order", appendix)

        chapter9 = chapters[8]
        # Later editorial updates may advance the date; never regress before
        # the verified three-contract revision or lag a chapter's update.
        self.assertGreaterEqual(chapter9["updated"], "2026-09-04")
        self.assertGreaterEqual(manifest["updated"], max(
            chapter["updated"] for chapter in chapters if chapter["status"] == "published"
        ))
        self.assertIn("三份调用合同", chapter9["summary"])
        self.assertNotIn("四份工具合同", chapter9["summary"])

        chapter10 = chapters[9]
        self.assertGreaterEqual(chapter10["updated"], "2026-09-09")
        self.assertIn("发现", chapter10["summary"])
        self.assertIn("异步", chapter10["summary"])
        self.assertIn("可恢复", chapter10["summary"])

        for chapter in chapters[10:]:
            self.assertGreaterEqual(chapter["updated"], "2026-09-27")
            self.assertEqual(f"chapter{chapter['order']}.md", chapter["source"])
            self.assertEqual(
                f"../chapter{chapter['order']}/README.md", chapter["experiment"]
            )
            self.assertEqual(
                f"../chapter{chapter['order']}/reference-answers.md", chapter["answers"]
            )

    def test_every_published_entry_has_reachable_publication_files(self):
        manifest = validate_manifest(ROOT)
        entries = [manifest["introduction"]] + manifest["appendices"] + [
            chapter
            for section in manifest["sections"]
            for chapter in section["chapters"]
            if chapter["status"] == "published"
        ]

        for entry in entries:
            self.assertTrue((ROOT / "book" / entry["source"]).is_file())

        self.assertTrue((ROOT / "book" / manifest["cover"]).is_file())

    def test_published_chapters_and_appendices_expose_their_publication_files(self):
        manifest = validate_manifest(ROOT)
        chapters = [
            chapter
            for section in manifest["sections"]
            for chapter in section["chapters"]
        ]

        for entry in chapters + manifest["appendices"]:
            self.assertTrue({"source", "experiment", "answers", "updated"}.issubset(entry), entry["slug"])
            for field in ("source", "experiment", "answers"):
                self.assertTrue((ROOT / "book" / entry[field]).is_file(), entry["slug"])


if __name__ == "__main__":
    unittest.main()
