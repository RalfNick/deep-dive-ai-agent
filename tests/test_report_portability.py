from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TEXT_REPORTS = (
    "chapter1/reports/experiment-results.json",
    "chapter2/results/real_sft_summary.json",
    "chapter2/results/real_sft_curves.csv",
    "book/images/fig2-7-real-sft-curves.svg",
    "chapter3/reports/experiment-results.json",
    "chapter4/reports/harness-boundary-matrix.json",
    "chapter5/reports/context-experiments.json",
    "chapter6/reports/context-continuity.json",
    "chapter6/reports/context-continuity.md",
    "chapter6/reports/context-continuity-trace.jsonl",
    "chapter7/reports/memory-engineering.json",
    "chapter7/reports/memory-engineering.md",
    "chapter7/reports/memory-engineering-trace.jsonl",
    "chapter9/reports/tool-mcp-evidence.json",
    "chapter9/reports/tool-mcp-evidence.md",
    "chapter9/reports/tool-mcp-trace.jsonl",
)


class ReportPortabilityTests(unittest.TestCase):
    def test_canonical_text_reports_use_lf_bytes_on_every_platform(self) -> None:
        violations = []
        for relative in CANONICAL_TEXT_REPORTS:
            payload = (ROOT / relative).read_bytes()
            if b"\r\n" in payload:
                violations.append(relative)
        self.assertEqual([], violations)

    def test_canonical_json_reports_do_not_embed_host_identity(self) -> None:
        chapter1 = json.loads(
            (ROOT / "chapter1/reports/experiment-results.json").read_text(
                encoding="utf-8"
            )
        )
        chapter3 = json.loads(
            (ROOT / "chapter3/reports/experiment-results.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(">=3.11,<3.14", chapter1["environment"]["python_contract"])
        self.assertNotIn("python", chapter1["environment"])
        self.assertEqual(
            {"python_contract": ">=3.11,<3.14"},
            chapter3["runtime"],
        )


if __name__ == "__main__":
    unittest.main()
