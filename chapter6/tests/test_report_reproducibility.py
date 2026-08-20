import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from chapter6.experiments.run_all import REPORT_FILENAMES, write_reports
from chapter6.context_continuity.compaction import StructuredCompactionStrategy
from chapter6.experiments.generational_drift import artifacts_byte_equal
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    canonical_seed,
    canonical_trajectory,
)


class ReportReproducibilityTest(unittest.TestCase):
    def test_generational_stability_compares_canonical_content_not_length(self) -> None:
        events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
        artifact = StructuredCompactionStrategy().prepare(events, canonical_seed()).artifact
        assert artifact is not None
        same_length_different_content = replace(
            artifact,
            created_at="1970-01-01T00:00:01Z",
        )

        self.assertTrue(artifacts_byte_equal(artifact, artifact))
        self.assertFalse(artifacts_byte_equal(artifact, same_length_different_content))
    def test_all_offline_reports_are_byte_reproducible_and_portable(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = write_reports(Path(first_dir))
            second = write_reports(Path(second_dir))

            self.assertEqual(tuple(path.name for path in first), REPORT_FILENAMES)
            for left, right in zip(first, second, strict=True):
                left_bytes = left.read_bytes()
                right_bytes = right.read_bytes()
                self.assertEqual(hashlib.sha256(left_bytes).digest(), hashlib.sha256(right_bytes).digest())
                self.assertNotIn(b"2026-", left_bytes)
                self.assertNotIn(b"E:" + b"\\\\", left_bytes)
                self.assertNotIn(b"C:\\\\", left_bytes)

            payload = json.loads(first[0].read_text(encoding="utf-8"))
            self.assertNotIn("overall_score", first[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["run_status"], "passed")
            markdown = first[1].read_text(encoding="utf-8")
            for heading in (
                "Sample count",
                "Acceptance",
                "Negative constraint",
                "Rejected hypothesis",
                "Locator integrity",
                "Duplicate work",
            ):
                self.assertIn(heading, markdown)

    def test_trace_is_redacted_sorted_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, _, trace_path = write_reports(Path(directory))
            trace_text = trace_path.read_text(encoding="utf-8")
            lines = trace_text.splitlines()

        records = [json.loads(line) for line in lines]
        self.assertEqual(records, sorted(records, key=lambda item: (item["experiment"], item["variant"], item["stage"])))
        self.assertNotIn("Authorization", trace_text)
        self.assertTrue(all("content" not in record for record in records))
        self.assertIn(
            ("rebuild", "packet_built"),
            {(record["stage"], record["outcome"]) for record in records},
        )


if __name__ == "__main__":
    unittest.main()
