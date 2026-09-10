from pathlib import Path
import tempfile
import unittest

from chapter11.workbench import (
    BUG_LINE, FIX_LINE, create_workspace, fingerprint, patch_file,
    run_tests, verify, evidence_is_current, instruction_inventory,
)


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        create_workspace(self.root)
        self.tests_digest = fingerprint(self.root / "tests")

    def fix(self):
        source = self.root / "linkcheck.py"
        patch_file(self.root, "linkcheck.py", fingerprint(source), BUG_LINE, FIX_LINE)

    def test_baseline_tests_pass_but_independent_acceptance_fails(self):
        result = verify(self.root, self.tests_digest)
        self.assertEqual(3, result["tests"]["count"])
        self.assertTrue(result["tests"]["ok"])
        self.assertFalse(result["acceptance"]["ok"])
        self.assertFalse(result["accepted"])

    def test_fix_passes_acceptance_and_keeps_user_notes(self):
        note = self.root / "notes.txt"
        note.write_text("my unfinished note", encoding="utf-8")
        self.fix()
        result = verify(self.root, self.tests_digest)
        self.assertTrue(result["accepted"])
        self.assertEqual("my unfinished note", note.read_text(encoding="utf-8"))
        self.assertTrue(evidence_is_current(self.root, result))

    def test_stale_patch_is_rejected_and_current_edit_survives(self):
        source = self.root / "linkcheck.py"
        before = fingerprint(source)
        source.write_text(source.read_text(encoding="utf-8") + "\n# collaborator\n", encoding="utf-8")
        current = source.read_bytes()
        with self.assertRaisesRegex(ValueError, "stale_source"):
            patch_file(self.root, "linkcheck.py", before, BUG_LINE, FIX_LINE)
        self.assertEqual(current, source.read_bytes())

    def test_wrong_scope_can_exit_zero_but_gate_rejects_zero_tests(self):
        empty = run_tests(self.root, "empty_tests")
        self.assertEqual(0, empty["exit_code"])
        self.assertEqual(0, empty["count"])
        self.assertFalse(verify(self.root, self.tests_digest, "empty_tests")["accepted"])

    def test_altered_tests_cannot_supply_acceptance(self):
        self.fix()
        (self.root / "tests/test_links.py").write_text("# removed assertions\n", encoding="utf-8")
        result = verify(self.root, self.tests_digest)
        self.assertFalse(result["tests_unchanged"])
        self.assertFalse(result["accepted"])

    def test_resume_requires_revalidation_after_source_change(self):
        self.fix()
        receipt = verify(self.root, self.tests_digest)
        self.assertTrue(evidence_is_current(self.root, receipt))
        source = self.root / "linkcheck.py"
        patch_file(self.root, "linkcheck.py", fingerprint(source), FIX_LINE, BUG_LINE)
        self.assertFalse(evidence_is_current(self.root, receipt))
        self.assertFalse(verify(self.root, self.tests_digest)["accepted"])

    def test_document_change_invalidates_old_evidence(self):
        self.fix()
        receipt = verify(self.root, self.tests_digest)
        doc = self.root / "docs/faq.md"
        doc.write_text(doc.read_text(encoding="utf-8") + "\nExtra note.\n", encoding="utf-8")
        self.assertTrue(receipt["accepted"])
        self.assertFalse(evidence_is_current(self.root, receipt))

    def test_always_empty_result_does_not_pass_independent_negative_sample(self):
        self.fix()
        source = self.root / "linkcheck.py"
        source.write_text(source.read_text(encoding="utf-8") + "\ndef broken_links(root, document):\n    return []\n", encoding="utf-8")
        result = verify(self.root, self.tests_digest)
        self.assertFalse(result["acceptance"]["checks"]["missing_still_fails"])
        self.assertFalse(result["accepted"])

    def test_patch_rejects_outside_scope(self):
        for relative in ("../outside.py", "notes.txt", "tests/test_links.py"):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                patch_file(self.root, relative, "irrelevant", BUG_LINE, FIX_LINE)

    def test_patch_requires_exactly_one_matching_hunk(self):
        source = self.root / "linkcheck.py"
        with self.assertRaisesRegex(ValueError, "hunk_mismatch"):
            patch_file(self.root, "linkcheck.py", fingerprint(source), "not present", FIX_LINE)

    def test_initialization_never_overwrites_existing_repository(self):
        before = fingerprint(self.root)
        with self.assertRaisesRegex(ValueError, "not_empty"):
            create_workspace(self.root)
        self.assertEqual(before, fingerprint(self.root))

    def test_instruction_inventory_is_an_inventory_not_product_loading(self):
        before = instruction_inventory(self.root)
        self.assertFalse(before["agents_exists"])
        create = self.root / "AGENTS.md"
        create.write_text("Run python -m unittest discover -s tests -v\n", encoding="utf-8")
        after = instruction_inventory(self.root)
        self.assertTrue(after["agents_exists"])
        self.assertEqual("not_measured", after["product_adherence"])


if __name__ == "__main__":
    unittest.main()
