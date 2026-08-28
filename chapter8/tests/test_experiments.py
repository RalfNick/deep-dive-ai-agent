import unittest

from chapter8.experiments.run_all import build_report


class ExperimentTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
