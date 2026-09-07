import tempfile
import unittest
import re
from importlib.util import find_spec
from pathlib import Path

from chapter10.preview import build_preview


@unittest.skipUnless(find_spec("markdown"), "optional preview dependency not installed")
class PreviewTests(unittest.TestCase):
    def test_relative_images_and_footnotes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book" / "images").mkdir(parents=True)
            (root / "book" / "images" / "x.png").write_bytes(b"image-fixture")
            (root / "book" / "chapter10.md").write_text(
                "# 标题\n\n![图](images/x.png)\n\n正文[^a]\n\n[^a]: 来源\n", encoding="utf-8")
            output = build_preview(root)
            html = output.read_text(encoding="utf-8")
            target = re.search(r'src="([^"]+)"', html).group(1)
            self.assertTrue((output.parent / target).is_file())
            self.assertIn('footnote', html)
            self.assertNotIn(str(root), html)
            self.assertIn('width=device-width', html)


if __name__ == "__main__":
    unittest.main()
