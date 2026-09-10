import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ExerciseSolutionsTests(unittest.TestCase):
    def run_exercise(self, number):
        result = subprocess.run(
            [sys.executable, "-B", "-m", "chapter11.exercise_solutions", str(number)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_exercise6_records_red_green_and_patch(self):
        report = self.run_exercise(6)
        self.assertEqual(3, report["initial_tests"]["count"])
        self.assertEqual(1, report["red"]["failures"])
        self.assertTrue(report["final"]["accepted"])
        self.assertIn("+    base = document.parent", report["diff"])

    def test_exercise7_preserves_notes_and_rejects_outdated_source(self):
        report = self.run_exercise(7)
        self.assertTrue(report["notes_preserved"])
        self.assertEqual("stale_source", report["conflict_error"])
        self.assertTrue(report["collaborator_preserved"])

    def test_exercise8_distinguishes_zero_tests_from_acceptance(self):
        report = self.run_exercise(8)
        self.assertEqual(0, report["tests"]["exit_code"])
        self.assertEqual(0, report["tests"]["count"])
        self.assertFalse(report["accepted"])

    def test_exercise9_requires_missing_nested_link_and_rejects_always_empty(self):
        report = self.run_exercise(9)
        self.assertEqual(["../absent.md"], report["expected_nested_missing"])
        self.assertEqual(1, report["red"]["failures"])
        self.assertTrue(report["final"]["accepted"])
        self.assertFalse(report["always_empty"]["accepted"])
        self.assertFalse(report["always_empty"]["acceptance"]["checks"]["nested_missing_reported"])

    def test_exercise10_preserves_history_but_invalidates_current_evidence(self):
        report = self.run_exercise(10)
        self.assertTrue(report["historical_accepted"])
        self.assertFalse(report["current_after_document_edit"])
        self.assertTrue(report["revalidation"]["accepted"])
