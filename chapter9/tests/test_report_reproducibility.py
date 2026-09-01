from pathlib import Path
import tempfile
import unittest

from chapter9.experiments.run_all import generate_to


ROOT = Path(__file__).resolve().parents[2]


class ReportReproducibilityTests(unittest.TestCase):
    def test_reports_are_byte_reproducible_and_match_committed_evidence(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = generate_to(Path(first_dir))
            second = generate_to(Path(second_dir))
            self.assertEqual([path.name for path in first], [path.name for path in second])

            for first_path, second_path in zip(first, second):
                first_bytes = first_path.read_bytes()
                self.assertEqual(first_bytes, second_path.read_bytes())
                self.assertNotIn(b"\r\n", first_bytes)
                committed = ROOT / "chapter9/reports" / first_path.name
                self.assertEqual(first_bytes, committed.read_bytes())

    def test_trace_omits_raw_payload_and_identity_fields(self):
        with tempfile.TemporaryDirectory() as output_dir:
            paths = generate_to(Path(output_dir))
            trace = next(path for path in paths if path.suffix == ".jsonl").read_text(
                encoding="utf-8"
            )

        for forbidden in (
            '"title"',
            '"runbook"',
            '"arguments"',
            '"caller"',
            '"grants"',
            '"exception"',
            '"content"',
        ):
            self.assertNotIn(forbidden, trace)


if __name__ == "__main__":
    unittest.main()
