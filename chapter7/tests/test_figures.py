import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = ROOT / "book" / "images"
FIGURES = tuple(
    IMAGE_DIR / name
    for name in (
        "fig7-1-state-boundary.svg",
        "fig7-2-from-history-to-memory.svg",
        "fig7-3-write-gate.svg",
        "fig7-4-record-lifecycle.svg",
        "fig7-5-recall-pipeline.svg",
        "fig7-6-experiment-matrix.svg",
        "fig7-7-product-responsibility-map.svg",
    )
)


class FigureContractTest(unittest.TestCase):
    def test_exact_seven_figures_are_safe_accessible_svg(self) -> None:
        self.assertEqual({path.name for path in IMAGE_DIR.glob("fig7-*.svg")}, {path.name for path in FIGURES})
        for path in FIGURES:
            root = ET.parse(path).getroot()
            self.assertEqual(root.attrib.get("viewBox"), "0 0 1200 675", path.name)
            self.assertEqual(root.attrib.get("role"), "img", path.name)
            text = path.read_text(encoding="utf-8")
            self.assertIn("<title", text, path.name)
            self.assertIn("<desc", text, path.name)
            safety_text = text.replace('xmlns="http://www.w3.org/2000/svg"', "")
            self.assertNotRegex(safety_text, r"<script|https?://|file:|[A-Za-z]:[\\/]", path.name)

    def test_visible_explicit_font_sizes_are_not_tiny(self) -> None:
        for path in FIGURES:
            sizes = [int(value) for value in re.findall(r'font-size="(\d+)"', path.read_text(encoding="utf-8"))]
            self.assertTrue(sizes, path.name)
            self.assertGreaterEqual(min(sizes), 15, path.name)

    def test_experiment_figure_uses_values_from_canonical_report(self) -> None:
        report = json.loads((ROOT / "chapter7" / "reports" / "memory-engineering.json").read_text(encoding="utf-8"))
        cases = {
            f'{group["group_id"]}/{case["variant_id"]}': case["metrics"]
            for group in report["groups"]
            for case in group["cases"]
        }
        figure = FIGURES[5].read_text(encoding="utf-8")
        self.assertIn(f'{cases["write/write-everything"]["write_precision"]:.2f} → {cases["write/policy-gated"]["write_precision"]:.2f}', figure)
        self.assertIn("0.40 / 0.50 / 1.00", figure)
        self.assertIn("陈旧索引泄漏：1", figure)
        self.assertNotIn("总分", figure.split("不压成一个总分", 1)[-1])

    def test_product_map_cites_all_public_responsibility_sources(self) -> None:
        figure = FIGURES[6].read_text(encoding="utf-8")
        for source_id in ("S07", "S08", "S09", "S10", "S11", "S12", "S15"):
            self.assertIn(source_id, figure)


if __name__ == "__main__":
    unittest.main()
