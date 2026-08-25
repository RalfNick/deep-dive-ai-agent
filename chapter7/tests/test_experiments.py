import unittest

from chapter7.experiments.run_all import build_report


EXPECTED_CASES = {
    "baseline/no-memory": {"task_accepted": False, "unsafe_temporary_rule_used": False},
    "baseline/full-transcript": {"task_accepted": False, "unsafe_temporary_rule_used": True},
    "baseline/structured-memory": {"task_accepted": True, "unsafe_temporary_rule_used": False},
    "write/write-everything": {"write_precision": 0.5, "sensitive_write_count": 1},
    "write/policy-gated": {"write_precision": 1.0, "sensitive_write_count": 0},
    "write/policy-plus-review": {"write_precision": 1.0, "write_recall": 1.0},
    "recall/global-scan": {"cross_scope_leak_count": 2, "recall_precision": 0.4},
    "recall/scoped-unranked": {"cross_scope_leak_count": 0, "recall_precision": 0.5},
    "recall/scoped-ranked": {"cross_scope_leak_count": 0, "recall_precision": 1.0},
    "correct/overwrite": {"audit_chain_complete": False, "correction_converged": True},
    "correct/versioned": {"audit_chain_complete": True, "correction_converged": True},
    "correct/stale-writer": {"stale_write_rejected": True, "duplicate_active_count": 0},
    "forget/stale-index": {"post_delete_leak_count": 1, "cross_scope_leak_count": 0},
    "forget/store-resolved": {"post_delete_leak_count": 0, "cross_scope_leak_count": 0},
    "forget/cross-tenant-probe": {"post_delete_leak_count": 0, "cross_scope_leak_count": 0},
}


class ExperimentTest(unittest.TestCase):
    def test_report_contains_five_groups_and_exact_fifteen_cases(self) -> None:
        report = build_report()
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["sample_count_per_case"], 1)
        self.assertEqual(tuple(group["group_id"] for group in report["groups"]), ("baseline", "write", "recall", "correct", "forget"))
        cases = {
            f'{group["group_id"]}/{case["variant_id"]}': case["metrics"]
            for group in report["groups"]
            for case in group["cases"]
        }
        self.assertEqual(set(cases), set(EXPECTED_CASES))
        for case_id, expected in EXPECTED_CASES.items():
            for key, value in expected.items():
                self.assertEqual(cases[case_id][key], value, f"{case_id}:{key}")

    def test_report_has_per_case_evidence_and_no_aggregate_score(self) -> None:
        report = build_report()
        self.assertNotIn("overall_score", report)
        for group in report["groups"]:
            for case in group["cases"]:
                self.assertTrue(case["evidence"])
                self.assertTrue(case["supported_claims"])
                self.assertTrue(case["unsupported_claims"])

    def test_unmeasured_model_and_token_metrics_are_null(self) -> None:
        report = build_report()
        self.assertIsNone(report["unmeasured"]["model_quality"])
        self.assertIsNone(report["unmeasured"]["token_savings"])


if __name__ == "__main__":
    unittest.main()
