import json
import tempfile
import unittest
from pathlib import Path

from chapter10.experiments import run_all, write_reports


class EvidenceTests(unittest.TestCase):
    def test_five_groups_and_deterministic_evidence(self):
        first = run_all()
        self.assertEqual(first, run_all())
        self.assertEqual(5, len(first["groups"]))
        self.assertIsNone(first["model_quality"])
        self.assertIsNone(first["provider_tokens"])
        self.assertEqual(6000, first["groups"]["lifecycle"]["result"]["data"]["total_cents"])
        self.assertEqual("denied", first["groups"]["boundaries"]["revoked"])
        self.assertEqual("cancelled", first["groups"]["failures"]["cancel_before_commit"])
        self.assertEqual(1, first["groups"]["failures"]["recovered_receipts"])

    def test_report_bytes_reproduce(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_reports(root)
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            for content in before.values():
                self.assertNotIn(b"\r", content)
            write_reports(root)
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})
            self.assertIn("groups", json.loads(before["tool-jobs-evidence.json"]))


if __name__ == "__main__":
    unittest.main()
