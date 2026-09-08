"""Check the reader's actual module command, including its durable result."""
import json
from pathlib import Path
import subprocess
import sys
import unittest


class QuickstartTests(unittest.TestCase):
    def test_command_shows_submission_execution_and_committed_report(self):
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "chapter10.quickstart"],
            cwd=Path(__file__).resolve().parents[2], capture_output=True,
            text=True, encoding="utf-8", timeout=10,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(["queued", "running", "succeeded"], report["states"])
        self.assertEqual(["queued", "running", "progress", "progress", "progress", "succeeded"],
                         [event["kind"] for event in report["events"]])
        self.assertEqual({"month": "2026-08", "row_count": 3, "total_cents": 6000},
                         report["result"]["data"])
        self.assertEqual(1, report["receipt_count"])
