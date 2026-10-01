from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path.cwd() / "src"))
from linkcheck import resolve_link


class ExistingBehavior(unittest.TestCase):
    def test_external(self):
        self.assertIsNone(resolve_link("docs/a.md", "https://example.invalid/a"))

    def test_root_relative(self):
        self.assertEqual(resolve_link("docs/a.md", "/guide.md"), "guide.md")

    def test_empty(self):
        self.assertIsNone(resolve_link("docs/a.md", ""))

    def test_nested_relative(self):
        self.assertEqual(resolve_link("docs/nested/a.md", "../guide.md"), "docs/guide.md")
