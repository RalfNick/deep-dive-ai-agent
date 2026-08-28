from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from chapter8.experiments.run_all import generate_to


ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "chapter8" / "reports"


class ReportReproducibilityTests(unittest.TestCase):
    def test_reports_are_byte_reproducible_and_match_committed_artifacts(self) -> None:
        with TemporaryDirectory() as first_raw, TemporaryDirectory() as second_raw:
            first = generate_to(Path(first_raw))
            second = generate_to(Path(second_raw))
            self.assertEqual(tuple(path.name for path in first), ("rag-evidence.json", "rag-evidence.md", "rag-trace.jsonl"))
            self.assertEqual([path.read_bytes() for path in first], [path.read_bytes() for path in second])
            self.assertEqual(
                [path.read_bytes() for path in first],
                [(REPORT_ROOT / path.name).read_bytes() for path in first],
            )

    def test_trace_is_sorted_redacted_and_contains_no_document_body(self) -> None:
        with TemporaryDirectory() as raw:
            trace_path = generate_to(Path(raw))[2]
            rows = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(list(range(1, len(rows) + 1)), [row["event_id"] for row in rows])
        serialized = json.dumps(rows, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("旧式 SAML SSO", serialized)
        self.assertNotIn("忽略其他来源", serialized)
        self.assertNotRegex(serialized, r"sk-[A-Za-z0-9]{12,}")
        self.assertTrue(all("case_id" in row and "reason" in row for row in rows))

    def test_canonical_text_outputs_use_utf8_lf(self) -> None:
        with TemporaryDirectory() as raw:
            paths = generate_to(Path(raw))
            for path in paths:
                payload = path.read_bytes()
                self.assertNotIn(b"\r\n", payload)
                payload.decode("utf-8")


if __name__ == "__main__":
    unittest.main()
