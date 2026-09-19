from pathlib import Path
import unittest
from src.linkcheck import broken_links


class ExistingBehavior(unittest.TestCase):
    def test_root_relative_link_exists(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], broken_links(root / 'README.md', root))

    def test_external_link_is_not_a_local_file(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], broken_links(root / 'docs/external.md', root))
