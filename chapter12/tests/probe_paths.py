"""Standard-library platform probes, runnable in Linux without installing pytest."""
from pathlib import Path
import tempfile
import unittest

from chapter12.tools import read_file, safe_path


class PathBoundaryProbe(unittest.TestCase):
    def test_directory_symlink_cannot_expose_outside_file(self):
        with tempfile.TemporaryDirectory(prefix='chapter12-path-') as directory:
            base = Path(directory)
            root = base / 'repo'
            root.mkdir()
            other = base / 'outside'
            other.mkdir()
            (other / 'value.txt').write_text('keep')
            (root / 'jump').symlink_to(other, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'path_denied'):
                read_file(root, 'jump/value.txt')
            self.assertEqual('keep', (other / 'value.txt').read_text())

    def test_root_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='chapter12-path-') as directory:
            base = Path(directory)
            (base / 'real').mkdir()
            (base / 'linked').symlink_to(base / 'real', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'path_denied'):
                safe_path(base / 'linked', '.')

    def test_hard_link_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='chapter12-path-') as directory:
            base = Path(directory)
            (base / 'repo').mkdir()
            (base / 'value.txt').write_text('keep')
            (base / 'repo/hard.txt').hardlink_to(base / 'value.txt')
            with self.assertRaisesRegex(ValueError, 'path_denied'):
                read_file(base / 'repo', 'hard.txt')


if __name__ == '__main__':
    unittest.main()
