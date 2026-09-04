import json
import unittest

from chapter9.experiments.run_all import build_report


class ExperimentTests(unittest.TestCase):
    def test_report_has_five_groups_twenty_one_cases_and_v0_through_v6(self):
        report = build_report()

        self.assertEqual(
            ["compatibility", "contract", "loop", "mcp_primitives", "safety"],
            sorted(report["groups"]),
        )
        cases = [
            case
            for group in report["groups"].values()
            for case in group["cases"]
        ]
        self.assertEqual(21, len(cases))
        self.assertEqual(
            set(range(7)),
            {version for case in cases for version in case["versions"]},
        )
        self.assertTrue(all(case["sample_count"] == 1 for case in cases))
        self.assertEqual(
            {"runtime_observation": 20, "specification_fixture": 1},
            {
                evidence_kind: sum(
                    case["evidence_kind"] == evidence_kind for case in cases
                )
                for evidence_kind in {case["evidence_kind"] for case in cases}
            },
        )

    def test_group_sizes_and_required_boundary_cases_are_explicit(self):
        report = build_report()
        self.assertEqual(
            {
                "contract": 5,
                "loop": 4,
                "safety": 5,
                "mcp_primitives": 4,
                "compatibility": 3,
            },
            {name: len(group["cases"]) for name, group in report["groups"].items()},
        )
        case_ids = {
            case["case_id"]
            for group in report["groups"].values()
            for case in group["cases"]
        }
        for required in (
            "contract-free-text",
            "contract-output-schema-violation",
            "loop-three-calls",
            "safety-forged-receipt",
            "mcp-resource",
            "compat-unsupported-version",
        ):
            self.assertIn(required, case_ids)

    def test_unmeasured_fields_are_null_and_no_vendor_ranking_exists(self):
        report = build_report()
        self.assertEqual(
            {
                "provider_cost": None,
                "provider_latency_ms": None,
                "provider_tokens": None,
                "real_model_quality": None,
            },
            report["unmeasured"],
        )
        self.assertNotIn("ranking", json.dumps(report, ensure_ascii=False).casefold())


if __name__ == "__main__":
    unittest.main()
