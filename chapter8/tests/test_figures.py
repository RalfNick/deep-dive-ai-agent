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
        "fig8-1-state-boundary.svg",
        "fig8-2-offline-online-pipeline.svg",
        "fig8-3-rag-evolution.svg",
        "fig8-4-chunking-comparison.svg",
        "fig8-5-retrieval-funnel.svg",
        "fig8-6-evidence-citations.svg",
        "fig8-7-governed-index.svg",
        "fig8-8-evaluation-matrix.svg",
    )
)


def report_cases() -> dict[str, dict]:
    report = json.loads((ROOT / "chapter8" / "reports" / "rag-evidence.json").read_text(encoding="utf-8"))
    return {case["case_id"]: case["metrics"] for group in report["groups"].values() for case in group["cases"]}


class FigureContractTest(unittest.TestCase):
    def test_exact_eight_figures_are_safe_accessible_svg(self) -> None:
        self.assertEqual({path.name for path in IMAGE_DIR.glob("fig8-*.svg")}, {path.name for path in FIGURES})
        for path in FIGURES:
            root = ET.parse(path).getroot()
            self.assertEqual(root.attrib.get("viewBox"), "0 0 1200 675", path.name)
            self.assertEqual(root.attrib.get("role"), "img", path.name)
            text = path.read_text(encoding="utf-8")
            self.assertIn("<title", text, path.name)
            self.assertIn("<desc", text, path.name)
            safety_text = text.replace('xmlns="http://www.w3.org/2000/svg"', "")
            self.assertNotRegex(safety_text, r"<script|https?://|file:|[A-Za-z]:[\\/]", path.name)

    def test_visible_font_sizes_are_readable(self) -> None:
        for path in FIGURES:
            sizes = [int(value) for value in re.findall(r'font-size="(\d+)"', path.read_text(encoding="utf-8"))]
            self.assertTrue(sizes, path.name)
            self.assertGreaterEqual(min(sizes), 20, path.name)

    def test_offline_online_figure_keeps_upstream_and_evidence_boundaries(self) -> None:
        figure = FIGURES[1].read_text(encoding="utf-8")
        for label in (
            "Source Chunk",
            "检索前知识加工",
            "派生问答 / 事实卡（可选）",
            "评分前过滤",
            "Return Gate",
            "Evidence Packet",
        ):
            self.assertIn(label, figure)

    def test_retrieval_funnel_uses_canonical_report_values(self) -> None:
        metrics = report_cases()["governance-compound-upgrade"]
        figure = FIGURES[4].read_text(encoding="utf-8")
        self.assertIn(f'{metrics["filtered_before_score_count"]} \u7bc7\u5728\u8bc4\u5206\u524d\u88ab\u8fc7\u6ee4', figure)
        self.assertIn(f'{metrics["retrieved_chunk_count"]} \u4e2a\u6700\u7ec8 Chunk', figure)
        self.assertIn(f'MRR {metrics["mrr"]:.2f}', figure)
        self.assertIn(f'Recall@3 {metrics["recall_at_3"]:.2f}', figure)

    def test_evaluation_matrix_uses_values_and_preserves_null(self) -> None:
        cases = report_cases()
        good = cases["governance-public-internal"]
        no_answer = cases["evidence-correct-abstain"]
        figure = FIGURES[7].read_text(encoding="utf-8")
        self.assertIn(f'Precision@3 {good["precision_at_3"]:.2f}', figure)
        self.assertIn(f'NDCG@3 {good["ndcg_at_3"]:.2f}', figure)
        self.assertIsNone(no_answer["mrr"])
        self.assertIn("\u65e0\u76f8\u5173\u9879\uff1aMRR = null", figure)
        self.assertIn("\u4e0d\u538b\u6210\u4e00\u4e2a\u603b\u5206", figure)


if __name__ == "__main__":
    unittest.main()
