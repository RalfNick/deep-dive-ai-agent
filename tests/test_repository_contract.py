from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_text_files_are_forced_to_lf_for_cross_platform_manifest_hashes(self) -> None:
        attributes = ROOT / ".gitattributes"
        self.assertTrue(attributes.is_file())
        self.assertIn("* text=auto eol=lf", attributes.read_text(encoding="utf-8"))

    def test_required_roots_exist(self) -> None:
        expected = ["book", "book-en", "docs", "scripts"]
        expected.extend(f"chapter{number}" for number in range(1, 10))
        self.assertEqual([], [name for name in expected if not (ROOT / name).is_dir()])

    def test_nine_chapters_have_prose_and_experiment_index(self) -> None:
        missing = []
        for number in range(1, 10):
            if not (ROOT / "book" / f"chapter{number}.md").is_file():
                missing.append(f"book/chapter{number}.md")
            if not (ROOT / f"chapter{number}" / "README.md").is_file():
                missing.append(f"chapter{number}/README.md")
        self.assertEqual([], missing)

    def test_public_repository_entry_files_exist(self) -> None:
        expected = ("README.md", "LICENSE", "CONTRIBUTING.md", "AGENTS.md")
        self.assertEqual([], [name for name in expected if not (ROOT / name).is_file()])

    def test_root_readme_links_every_published_chapter_and_experiment(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for number in range(1, 10):
            with self.subTest(chapter=number):
                self.assertIn(f"(book/chapter{number}.md)", readme)
                self.assertIn(f"(chapter{number}/README.md)", readme)
        self.assertIn("18 章", readme)
        self.assertIn("https://wlxralf.com/books/deep-dive-ai-agent", readme)

    def test_book_index_defines_the_published_reading_order(self) -> None:
        index = (ROOT / "book" / "README.md").read_text(encoding="utf-8")
        expected = ["(./introduction.md)"]
        expected.extend(f"(./chapter{number}.md)" for number in range(1, 10))
        positions = [index.find(target) for target in expected]
        self.assertTrue(all(position >= 0 for position in positions), positions)
        self.assertEqual(positions, sorted(positions))

    def test_chapter_navigation_connects_prose_experiments_and_next_reading(self) -> None:
        for number in range(1, 10):
            prose = (ROOT / "book" / f"chapter{number}.md").read_text(
                encoding="utf-8"
            )
            experiment = (ROOT / f"chapter{number}" / "README.md").read_text(
                encoding="utf-8"
            )
            with self.subTest(chapter=number):
                self.assertIn(f"../chapter{number}/README.md", prose)
                self.assertIn(f"../chapter{number}/reference-answers.md", prose)
                self.assertIn(f"../book/chapter{number}.md", experiment)
                if number < 9:
                    self.assertIn(f"./chapter{number + 1}.md", prose)
                else:
                    self.assertIn("./OUTLINE.md", prose)

    def test_unstarted_translations_are_truthfully_marked_planned(self) -> None:
        english_index = ROOT / "book-en" / "README.md"
        self.assertTrue(english_index.is_file())
        text = english_index.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?im)^status:\s*planned\s*$")
        self.assertFalse(tuple((ROOT / "book-en").glob("chapter*.md")))
        self.assertFalse((ROOT / "book-zhtw").exists())
        self.assertIsNone(re.search(r"English version (?:is )?complete", text, re.I))


if __name__ == "__main__":
    unittest.main()
