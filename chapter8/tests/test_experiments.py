import unittest

from chapter8.experiments.run_all import build_report


class ExperimentTests(unittest.TestCase):
    @staticmethod
    def _cases(report):
        return {
            case["case_id"]: case
            for group in report["groups"].values()
            for case in group["cases"]
        }

    def test_report_has_exactly_five_groups_and_twenty_single_sample_cases(self) -> None:
        report = build_report()
        self.assertEqual(
            ("baseline", "chunking", "retrieval", "governance", "evidence"),
            tuple(report["groups"]),
        )
        expected_counts = {"baseline": 3, "chunking": 3, "retrieval": 4, "governance": 5, "evidence": 5}
        case_ids = []
        for group_id, expected_count in expected_counts.items():
            cases = report["groups"][group_id]["cases"]
            self.assertEqual(expected_count, len(cases))
            self.assertEqual(expected_count, report["groups"][group_id]["case_count"])
            self.assertTrue(all(case["sample_count"] == 1 for case in cases))
            case_ids.extend(case["case_id"] for case in cases)
        self.assertEqual(20, len(case_ids))
        self.assertEqual(20, len(set(case_ids)))

    def test_every_case_has_evidence_scope_and_non_claim(self) -> None:
        report = build_report()
        for group in report["groups"].values():
            for case in group["cases"]:
                self.assertTrue(case["evidence_codes"], case["case_id"])
                self.assertTrue(case["supports"], case["case_id"])
                self.assertTrue(case["does_not_support"], case["case_id"])
                self.assertIn("metrics", case)
                self.assertNotIn("success_rate", case)

    def test_report_has_no_aggregate_score_and_unmeasured_values_are_null(self) -> None:
        report = build_report()
        self.assertNotIn("overall_score", report)
        self.assertNotIn("success_rate", report)
        self.assertEqual(
            {
                "real_model_quality": None,
                "provider_tokens": None,
                "provider_cost": None,
                "provider_latency_ms": None,
            },
            report["unmeasured"],
        )
        self.assertEqual("2026-08-27T16:00:00Z", report["generated_at"])

    def test_report_covers_v0_through_v7_without_vendor_ranking(self) -> None:
        report = build_report()
        variants = {
            variant
            for group in report["groups"].values()
            for case in group["cases"]
            for variant in case["variants"]
        }
        self.assertEqual({f"v{index}" for index in range(8)}, variants)
        serialized = str(report)
        self.assertNotIn("better_than", serialized)
        self.assertNotIn("vendor_ranking", serialized)

    def test_status_outcomes_distinguish_conformance_from_failure_probes(self) -> None:
        report = build_report()
        cases = self._cases(report)
        outcomes = {case_id: case["outcome"] for case_id, case in cases.items() if case.get("outcome")}

        probes = {
            "retrieval-synonym-login",
            "governance-future-preview",
            "evidence-conflicting-source",
        }
        self.assertEqual(probes, {case_id for case_id, outcome in outcomes.items() if outcome["expectation_mode"] == "failure_probe"})
        for case_id in probes:
            self.assertFalse(outcomes[case_id]["status_match"])
            self.assertEqual("false_abstain", outcomes[case_id]["classification"])
            self.assertEqual("failure_exposed", outcomes[case_id]["result"])
            self.assertTrue(any(word in cases[case_id]["supports"] for word in ("失败", "暴露")))

        conformance = [outcome for outcome in outcomes.values() if outcome["expectation_mode"] == "conformance"]
        self.assertTrue(conformance)
        self.assertTrue(all(outcome["status_match"] for outcome in conformance))
        self.assertTrue(all(outcome["result"] == "conforms" for outcome in conformance))
        self.assertEqual(
            {
                "status_compared_case_count": 13,
                "conformance_case_count": 10,
                "intentional_failure_probe_count": 3,
                "unexpected_status_mismatch_count": 0,
                "false_answer_count": 0,
                "false_abstain_count": 3,
            },
            report["outcome_summary"],
        )

    def test_no_answer_and_partial_cases_follow_their_fact_contracts(self) -> None:
        cases = self._cases(build_report())
        self.assertEqual("abstain", cases["retrieval-noise"]["metrics"]["answer_status"])
        self.assertEqual("abstain", cases["evidence-correct-abstain"]["metrics"]["answer_status"])
        self.assertEqual("partial", cases["evidence-missing-members"]["metrics"]["answer_status"])
        self.assertEqual(
            ["members-preserved-32"],
            list(cases["evidence-missing-members"]["metrics"]["missing_fact_ids"]),
        )

    def test_report_declares_document_level_fixed_k_metric_contract(self) -> None:
        report = build_report()
        self.assertEqual(
            {
                "retrieval_unit": "unique_document_id",
                "precision_at_k_denominator": "fixed_k",
                "unreturned_positions": "count_as_not_relevant",
            },
            report["metric_contract"],
        )


if __name__ == "__main__":
    unittest.main()
