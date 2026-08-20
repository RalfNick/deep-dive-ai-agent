from __future__ import annotations

import json
import unittest

from chapter1.generate_report import build_report


class ExperimentReportTest(unittest.TestCase):
    def test_default_report_uses_the_canonical_reproducible_timestamp(self) -> None:
        report = build_report()

        self.assertEqual(report["generated_at"], "2026-08-13T00:00:00+08:00")

    def test_report_contains_five_bounded_experiments_without_secrets(self) -> None:
        report = build_report(generated_at="2026-08-13T00:00:00+08:00")

        self.assertEqual(report["chapter_version"], "1.1")
        self.assertEqual(report["generated_at"], "2026-08-13T00:00:00+08:00")
        self.assertEqual(len(report["experiments"]), 5)
        self.assertEqual(
            {item["id"] for item in report["experiments"]},
            {"tokenizer", "attention", "bigram", "sampling", "coding_agent"},
        )
        for experiment in report["experiments"]:
            with self.subTest(experiment=experiment["id"]):
                self.assertIn("command", experiment)
                self.assertIn("controls", experiment)
                self.assertIn("observations", experiment)
                self.assertIn("supports", experiment)
                self.assertIn("does_not_prove", experiment)

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("API_KEY", serialized)
        self.assertNotIn("Temp\\chapter1", serialized)
        self.assertNotIn("sk-", serialized)


if __name__ == "__main__":
    unittest.main()
