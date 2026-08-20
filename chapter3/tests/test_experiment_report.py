from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_all_experiments import run_all  # noqa: E402


class ExperimentReportTest(unittest.TestCase):
    def test_default_report_uses_the_canonical_reproducible_timestamp(self) -> None:
        report = run_all(write_report=False)

        self.assertEqual(report["generated_at"], "2026-08-14T00:00:00Z")

    def test_report_runs_all_six_local_experiments(self) -> None:
        report = run_all(generated_at="2026-08-14T00:00:00Z", write_report=False)

        expected = (
            "one_shot_vs_loop",
            "agent_loop",
            "loop_guards",
            "tool_errors",
            "verifier",
            "trace_replay",
        )
        self.assertEqual(tuple(report["experiments"]), expected)
        self.assertTrue(
            all(
                item["exit_code"] == 0
                for item in report["experiments"].values()
            )
        )
        self.assertEqual(report["generated_at"], "2026-08-14T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
