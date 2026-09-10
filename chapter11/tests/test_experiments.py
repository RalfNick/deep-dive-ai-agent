import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from chapter11.experiments import run_all, write_reports


class ExperimentTests(unittest.TestCase):
    def test_five_groups_and_observed_failures(self):
        report = run_all()
        groups = report["groups"]
        self.assertEqual(["repair", "instructions", "conflict", "verification", "resume"], list(groups))
        self.assertEqual(1, groups["repair"]["red"]["failures"])
        self.assertTrue(groups["repair"]["final"]["accepted"])
        self.assertEqual(4, groups["repair"]["final"]["tests"]["count"])
        self.assertFalse(groups["verification"]["zero_tests"]["accepted"])
        self.assertFalse(groups["verification"]["tampered_tests"]["accepted"])
        self.assertEqual("stale_source", groups["conflict"]["error"])
        self.assertFalse(groups["resume"]["old_evidence_current"])
        self.assertIsNone(report["model_quality"])

    def test_reports_reproduce_and_exclude_host_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_reports(root / "one")
            write_reports(root / "two")
            for name in ("repository-work.json", "repository-work.md"):
                a = (root / "one" / name).read_bytes()
                self.assertEqual(a, (root / "two" / name).read_bytes())
                canonical = Path(__file__).resolve().parents[1] / "reports" / name
                self.assertEqual(a, canonical.read_bytes(), "committed report must match execution")
                self.assertNotIn(b"\r\n", a)
                self.assertNotIn(str(root).encode(), a)

    def test_quickstart_module_emits_red_green_and_diff(self):
        result = subprocess.run([sys.executable, "-B", "-m", "chapter11.quickstart"],
                                capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(result.stdout)
        self.assertEqual(1, data["red"]["failures"])
        self.assertTrue(data["final"]["accepted"])
        self.assertIn("+    base = document.parent", data["diff"])
