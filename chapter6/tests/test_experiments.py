import unittest
from dataclasses import replace

from chapter6.experiments.checkpoint_vs_rehydration import verify_post_resume
from chapter6.experiments.common import required_trace_pairs, validate_case_trace
from chapter6.experiments.run_all import (
    build_report,
    run_all,
    run_all_with_traces,
    validate_reference_cases,
)
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    canonical_trajectory,
)


class ContinuityExperimentsTest(unittest.TestCase):
    def test_run_all_has_five_groups_and_failure_matrix(self) -> None:
        report = run_all()

        self.assertEqual(
            {case.experiment for case in report.cases},
            {
                "context_growth",
                "sliding_window",
                "summary_vs_structured",
                "checkpoint_vs_rehydration",
                "generational_drift",
                "failure_matrix",
            },
        )
        failures = [case for case in report.cases if case.experiment == "failure_matrix"]
        self.assertGreaterEqual(len(failures), 4)

    def test_cases_freeze_sample_scope_and_use_null_for_unmeasured_metrics(self) -> None:
        report = run_all()

        self.assertEqual(
            report.comparison_scope,
            "deterministic semantic-continuity contract; not model or product ranking",
        )
        self.assertEqual(report.run_status, "passed")
        self.assertTrue(all(case.sample_count == 1 for case in report.cases))
        self.assertTrue(all(case.unsupported_claims for case in report.cases))
        checkpoint = next(
            case
            for case in report.cases
            if case.experiment == "checkpoint_vs_rehydration"
            and case.variant == "checkpoint-only-v1"
        )
        self.assertIsNone(checkpoint.grade.packet_contract_passed)
        self.assertIsNone(checkpoint.grade.locator_integrity)

    def test_rehydration_case_measures_real_chapter5_packet_and_trace_contract(self) -> None:
        report = run_all()
        rehydrated = next(
            case
            for case in report.cases
            if case.experiment == "checkpoint_vs_rehydration"
            and case.variant == "rehydrated-context-v1"
        )

        self.assertTrue(rehydrated.grade.packet_contract_passed)
        self.assertTrue(rehydrated.grade.trace_contract_passed)
        self.assertTrue(rehydrated.grade.resume_correct)
        self.assertEqual(rehydrated.decision_kind, "apply_legacy_compatible_patch")

    def test_checkpoint_control_retains_task_contract_but_not_handoff_semantics(self) -> None:
        checkpoint = next(
            case
            for case in run_all().cases
            if case.experiment == "checkpoint_vs_rehydration"
            and case.variant == "checkpoint-only-v1"
        )

        self.assertTrue(checkpoint.grade.goal_retained)
        self.assertEqual(checkpoint.grade.constraint_retention, 0.0)
        self.assertEqual(checkpoint.decision_kind, "unsafe_signature_change")
        self.assertIsNone(checkpoint.grade.resume_correct)
        self.assertIsNone(checkpoint.grade.duplicate_work_count)

    def test_resume_metrics_require_verified_post_resume_events(self) -> None:
        post_resume = canonical_trajectory()[CANONICAL_COMPACTION_CURSOR:]

        complete = verify_post_resume(
            post_resume,
            decision_kind="apply_legacy_compatible_patch",
        )
        incomplete = verify_post_resume(
            post_resume[:-1],
            decision_kind="apply_legacy_compatible_patch",
        )

        self.assertTrue(complete.resume_correct)
        self.assertEqual(complete.duplicate_work_count, 0)
        self.assertFalse(incomplete.resume_correct)
        self.assertIsNone(incomplete.duplicate_work_count)

        duplicate_item = canonical_trajectory()[8].carry_items[0]
        with_duplicate = list(post_resume)
        with_duplicate[2] = replace(
            with_duplicate[2],
            carry_items=(*with_duplicate[2].carry_items, duplicate_item),
        )
        duplicate = verify_post_resume(
            tuple(with_duplicate),
            decision_kind="apply_legacy_compatible_patch",
        )
        self.assertFalse(duplicate.resume_correct)
        self.assertEqual(duplicate.duplicate_work_count, 1)

    def test_early_growth_row_does_not_claim_a_policy_decision(self) -> None:
        early = next(
            case
            for case in run_all().cases
            if case.experiment == "context_growth"
            and case.variant == "append-all-cursor-08"
        )

        self.assertIsNone(early.decision_kind)

    def test_failure_matrix_names_required_injections_and_fails_closed(self) -> None:
        failures = {
            case.variant: case
            for case in run_all().cases
            if case.experiment == "failure_matrix"
        }

        self.assertTrue(
            {
                "early-constraint-loss",
                "omitted-open-failure",
                "workspace-digest-mismatch",
                "unsupported-artifact-schema",
                "corrupt-artifact-source-digest",
            }.issubset(failures)
        )
        self.assertEqual(
            failures["workspace-digest-mismatch"].decision_kind,
            "rejected_stale_workspace_digest",
        )
        self.assertEqual(
            failures["unsupported-artifact-schema"].decision_kind,
            "rejected_artifact_schema",
        )
        self.assertTrue(failures["omitted-open-failure"].grade.false_completion)

    def test_sliding_window_keeps_task_anchor_but_loses_early_constraint(self) -> None:
        case = next(
            case for case in run_all().cases if case.experiment == "sliding_window"
        )

        self.assertTrue(case.grade.goal_retained)
        self.assertEqual(case.grade.negative_constraint_retention, 0.0)
        self.assertEqual(case.decision_kind, "unsafe_signature_change")

    def test_every_case_has_valid_variant_specific_trace_evidence(self) -> None:
        report, traces = run_all_with_traces()
        for case in report.cases:
            with self.subTest(case=(case.experiment, case.variant)):
                case_records = tuple(
                    record
                    for record in traces
                    if (record.experiment, record.variant)
                    == (case.experiment, case.variant)
                )
                self.assertTrue(required_trace_pairs(case.experiment, case.variant))
                self.assertTrue(validate_case_trace(case.experiment, case.variant, case_records))
                self.assertTrue(case.grade.trace_contract_passed)
                if case.variant != "rehydrated-context-v1":
                    self.assertFalse(
                        any(record.stage.startswith("chapter5.") for record in case_records)
                    )

                required = required_trace_pairs(case.experiment, case.variant)
                removed_pair = next(iter(required))
                corrupted = tuple(
                    record
                    for record in case_records
                    if (record.stage, record.outcome) != removed_pair
                )
                self.assertFalse(
                    validate_case_trace(case.experiment, case.variant, corrupted)
                )

    def test_reference_expectations_cover_and_reject_corruption_of_every_case(self) -> None:
        report = run_all()
        self.assertTrue(validate_reference_cases(report.cases))

        for index, case in enumerate(report.cases):
            with self.subTest(case=(case.experiment, case.variant)):
                corrupted = list(report.cases)
                corrupted[index] = replace(
                    case, decision_kind="corrupted-reference-outcome"
                )
                self.assertFalse(validate_reference_cases(tuple(corrupted)))
                self.assertEqual(build_report(tuple(corrupted)).run_status, "failed")

                corrupted_bytes = list(report.cases)
                corrupted_bytes[index] = replace(
                    case,
                    serialized_bytes_after=case.serialized_bytes_after + 1,
                )
                self.assertEqual(
                    build_report(tuple(corrupted_bytes)).run_status,
                    "failed",
                )

                fabricated_claim = list(report.cases)
                fabricated_claim[index] = replace(
                    case,
                    supported_claims=(
                        *case.supported_claims,
                        "this proves one commercial provider ranks above another",
                    ),
                )
                self.assertEqual(
                    build_report(tuple(fabricated_claim)).run_status,
                    "failed",
                )

                weakened_non_claim = list(report.cases)
                weakened_non_claim[index] = replace(
                    case,
                    unsupported_claims=case.unsupported_claims[:-1],
                )
                self.assertEqual(
                    build_report(tuple(weakened_non_claim)).run_status,
                    "failed",
                )


if __name__ == "__main__":
    unittest.main()
