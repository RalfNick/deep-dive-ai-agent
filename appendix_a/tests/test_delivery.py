from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from appendix_a.preview import build_preview
from infographic.appendix_a.generate_diagrams import generate


ROOT = Path(__file__).resolve().parents[2]


class DeliveryTests(unittest.TestCase):
    def test_preview_rewrites_assets_and_wraps_tables_without_rewriting_external_links(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "book").mkdir()
            (root / "book/appendix-a.md").write_text(
                "# 测试\n\n![图](images/appendix-a/x.svg)\n\n"
                "[来源](https://example.com)\n\n"
                "| A | B |\n| --- | --- |\n| x | y |\n", encoding="utf-8")
            result = build_preview(root).read_text(encoding="utf-8")
            self.assertIn('src="../../book/images/appendix-a/x.svg"', result)
            self.assertIn('href="https://example.com"', result)
            self.assertIn('class="table-wrap"', result)
            self.assertIn('<figcaption>', result)

    def test_preview_cannot_write_outside_its_owned_directory(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for output in (root / "book/chapter3.md", root / "outside.html",
                           root / "appendix_a/preview-pages/nested/index.html"):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    build_preview(root, output=output)

    def test_diagrams_are_parseable_and_every_arrow_binds_to_existing_shapes(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            paths = generate(root)
            self.assertEqual(len(paths), 8)
            for path in paths:
                if path.suffix == ".svg":
                    self.assertEqual(ET.parse(path).getroot().attrib["viewBox"], "0 0 1600 960")
                else:
                    records = json.loads(path.read_text(encoding="utf-8"))["records"]
                    ids = {record["id"] for record in records}
                    indexes = [record["index"] for record in records if record["typeName"] == "shape"]
                    self.assertEqual(len(indexes), len(set(indexes)))
                    for record in records:
                        if record.get("type") == "arrow":
                            self.assertIn(record["props"]["start"]["boundShapeId"], ids)
                            self.assertIn(record["props"]["end"]["boundShapeId"], ids)

    def test_cli_rejects_outside_output_and_never_creates_it(self):
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "not-owned"
            result = subprocess.run(
                [__import__("sys").executable, "-B", "-m", "appendix_a.preparation", "--output", str(target)],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(target.exists())

    def test_api_incoming_arrows_use_distinct_receiver_anchors(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            generate(root)
            records = json.loads((root / "infographic/appendix_a/03-api-contract.tldr")
                                 .read_text(encoding="utf-8"))["records"]
            incoming = [r for r in records if r.get("type") == "arrow"
                        and r["props"]["end"]["boundShapeId"] == "shape:build"
                        and r["props"]["start"]["boundShapeId"] != "shape:model"]
            anchors = [(r["props"]["end"]["normalizedAnchor"]["x"],
                        r["props"]["end"]["normalizedAnchor"]["y"]) for r in incoming]
            self.assertEqual(len(set(anchors)), 4)

    def test_public_build_does_not_collect_local_appendix_images(self):
        from scripts.build_site import _allowlisted_sources
        sources = _allowlisted_sources(ROOT)
        self.assertFalse(any(path.is_relative_to(ROOT / "book/images/appendix-a") for path in sources))

    def test_inspection_cannot_save_machine_observations_as_stable_reports(self):
        result = subprocess.run(
            [__import__("sys").executable, "-B", "-m", "appendix_a.preparation",
             "--inspect", "--output", "appendix_a/.runs/not-created"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((ROOT / "appendix_a/.runs/not-created").exists())

    @unittest.skipUnless(shutil.which("node"), "optional Node runtime is not installed")
    def test_typescript_fixtures_show_runtime_not_type_checking(self):
        for file, expected in (("task.ts", "检查链接，最多 3 步"), ("unchecked.ts", "31")):
            result = subprocess.run(["node", str(ROOT / "appendix_a/examples" / file)],
                                    capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
