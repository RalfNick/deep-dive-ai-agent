from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chapter11 import experiments
from chapter11.workbench import (BUG_LINE, FIX_LINE, REGRESSION, create_workspace,
                                fingerprint, patch_file, run_tests, verify)


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"

    def test_debug_stdout_and_stderr_do_not_change_test_or_acceptance_results(self):
        create_workspace(self.root)
        source = self.root / "linkcheck.py"
        patch_file(self.root, "linkcheck.py", fingerprint(source), BUG_LINE, FIX_LINE)
        patch_file(self.root, "linkcheck.py", fingerprint(source),
                   "    missing = []",
                   "    print('reading document')\n    import sys\n    print('diagnostic', file=sys.stderr)\n    missing = []")
        result = verify(self.root, fingerprint(self.root / "tests"))
        self.assertTrue(result["accepted"])
        self.assertEqual(3, result["tests"]["count"])
        self.assertIn("reading document", result["tests"]["stdout"])
        self.assertIn("diagnostic", result["tests"]["stderr"])
        self.assertIn("reading document", result["acceptance"]["stdout"])

    def test_regression_failure_preserves_test_name_and_expected_actual_difference(self):
        create_workspace(self.root)
        test = self.root / "tests/test_links.py"
        test.write_text(test.read_text(encoding="utf-8") + REGRESSION, encoding="utf-8")
        result = run_tests(self.root)
        details = result.get("details", [])
        self.assertEqual(1, len(details))
        self.assertTrue(details[0]["test"].endswith(".test_nested_document"))
        self.assertEqual("failure", details[0]["kind"])
        self.assertIn("[] != ['../faq.md']", details[0]["message"])
        self.assertNotIn(str(self.root), str(result))

    def test_no_report_is_not_reported_as_zero_discovered_tests(self):
        create_workspace(self.root)
        (self.root / "linkcheck.py").write_text("import os\nos._exit(7)\n", encoding="utf-8")
        result = run_tests(self.root)
        self.assertIsNone(result["count"])
        self.assertEqual(7, result["exit_code"])
        self.assertEqual("invalid_test_report", result["error"])

    def test_repair_refuses_green_error_and_unrelated_assertion_before_patch(self):
        cases = {
            "green": "\n    def test_nested_document(self):\n        self.assertTrue(True)\n",
            "error": "\n    def test_nested_document(self):\n        raise ImportError('fixture dependency missing')\n",
            "unrelated": "\n    def test_nested_document(self):\n        self.fail('unrelated assertion')\n",
        }
        for name, regression in cases.items():
            with self.subTest(name=name):
                root = Path(self.temp.name) / name
                # Change only teaching input; filesystem, tests and patching stay real.
                with patch.object(experiments, "REGRESSION", regression):
                    with self.assertRaisesRegex(ValueError, "unexpected_red"):
                        experiments.repair(root)
                self.assertIn(BUG_LINE, (root / "linkcheck.py").read_text(encoding="utf-8"))
