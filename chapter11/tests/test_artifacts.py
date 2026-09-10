from pathlib import Path
import importlib.util
import re
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]


class ArtifactTests(unittest.TestCase):
    def test_manuscript_local_links_and_footnotes_resolve(self):
        source = ROOT / "book/chapter11.md"
        text = source.read_text(encoding="utf-8")
        text = re.sub(r"(?ms)^~~~.*?^~~~\s*$", "", text)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            url = urlsplit(target)
            if not url.scheme and url.path:
                self.assertTrue((source.parent / unquote(url.path)).is_file(), target)
        references = set(re.findall(r"\[\^([^\]]+)\]", text))
        definitions = set(re.findall(r"(?m)^\[\^([^\]]+)\]:", text))
        self.assertEqual(references, definitions)

    @unittest.skipUnless(importlib.util.find_spec("markdown"), "optional preview dependency")
    def test_preview_renders_seven_images_and_valid_local_resources(self):
        from chapter11.preview import build_preview
        html = build_preview(ROOT).read_text(encoding="utf-8")
        self.assertEqual(7, html.count("<figure>"))
        self.assertIn("第 11 章", html)
        self.assertNotIn("第 10 章 ·", html)
        self.assertNotIn("<p>~~~", html, "fences must render as code, not prose")
        base = ROOT / "chapter11/preview-pages"
        for target in re.findall(r'(?:src|href)="([^"]+)"', html):
            url = urlsplit(target)
            if not url.scheme and url.path:
                self.assertTrue((base / unquote(url.path)).is_file(), target)
