import unittest
from dataclasses import fields, replace

from chapter6.context_continuity.graders import (
    ContinuityGrade,
    ContinuityGrader,
    ExperimentCase,
    ExperimentReport,
)
from chapter6.context_continuity.compaction import StructuredCompactionStrategy
from chapter6.experiments.common import CanonicalEvidenceResolver, locator_integrity
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    CANONICAL_WORKSPACE_DIGEST,
    canonical_seed,
    canonical_trajectory,
)


class ContinuityGraderTest(unittest.TestCase):
    def test_locator_integrity_resolves_reference_and_recomputes_content_digest(self) -> None:
        events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
        artifact = StructuredCompactionStrategy().prepare(events, canonical_seed()).artifact
        assert artifact is not None
        resolver = CanonicalEvidenceResolver(events)

        self.assertEqual(
            locator_integrity(
                artifact.evidence_locators,
                resolver=resolver,
                workspace_digest=CANONICAL_WORKSPACE_DIGEST,
            ),
            1.0,
        )
        invalid_ref = replace(
            artifact.evidence_locators[0], ref="missing://evidence"
        )
        wrong_content = replace(
            artifact.evidence_locators[0], content_digest="0" * 64
        )
        self.assertEqual(
            locator_integrity(
                (invalid_ref,),
                resolver=resolver,
                workspace_digest=CANONICAL_WORKSPACE_DIGEST,
            ),
            0.0,
        )
        self.assertEqual(
            locator_integrity(
                (wrong_content,),
                resolver=resolver,
                workspace_digest=CANONICAL_WORKSPACE_DIGEST,
            ),
            0.0,
        )
    def test_report_contract_has_only_published_fields(self) -> None:
        self.assertEqual(
            tuple(field.name for field in fields(ContinuityGrade)),
            (
                "goal_retained",
                "acceptance_retention",
                "constraint_retention",
                "negative_constraint_retention",
                "open_issue_retention",
                "rejected_hypothesis_retention",
                "locator_integrity",
                "resume_correct",
                "duplicate_work_count",
                "false_completion",
                "packet_contract_passed",
                "trace_contract_passed",
            ),
        )
        self.assertEqual(
            tuple(field.name for field in fields(ExperimentCase)),
            (
                "experiment",
                "variant",
                "sample_count",
                "serialized_bytes_before",
                "serialized_bytes_after",
                "grade",
                "decision_kind",
                "supported_claims",
                "unsupported_claims",
            ),
        )

    def test_grader_keeps_independent_metrics_and_has_no_overall_score(self) -> None:
        grade = ContinuityGrader().grade(
            expected_goal_key="repair-price",
            expected_acceptance_keys=frozenset({"legacy-config"}),
            expected_constraint_keys=frozenset({"public-signature"}),
            expected_negative_constraint_keys=frozenset({"public-signature"}),
            expected_open_issue_keys=frozenset({"legacy-config-open"}),
            expected_rejected_hypothesis_keys=frozenset({"rounding-only-rejected"}),
            visible_keys=frozenset({"repair-price", "legacy-config", "public-signature"}),
            locator_integrity=None,
            resume_correct=False,
            duplicate_work_count=1,
            false_completion=True,
            packet_contract_passed=None,
            trace_contract_passed=True,
        )

        self.assertEqual(grade.acceptance_retention, 1.0)
        self.assertEqual(grade.constraint_retention, 1.0)
        self.assertEqual(grade.open_issue_retention, 0.0)
        self.assertTrue(grade.false_completion)
        self.assertNotIn("overall_score", {field.name for field in fields(grade)})

    def test_unmeasured_values_serialize_as_null(self) -> None:
        grade = ContinuityGrade(
            goal_retained=True,
            acceptance_retention=1.0,
            constraint_retention=1.0,
            negative_constraint_retention=1.0,
            open_issue_retention=0.0,
            rejected_hypothesis_retention=0.0,
            locator_integrity=None,
            resume_correct=False,
            duplicate_work_count=1,
            false_completion=True,
            packet_contract_passed=None,
            trace_contract_passed=True,
        )
        case = ExperimentCase(
            experiment="summary_vs_structured",
            variant="summary-only-v1",
            sample_count=1,
            serialized_bytes_before=4_000,
            serialized_bytes_after=600,
            grade=grade,
            decision_kind="unsafe_signature_change",
            supported_claims=("summary baseline omitted the open issue",),
            unsupported_claims=("real model failure rate",),
        )

        self.assertIsNone(case.to_dict()["grade"]["locator_integrity"])
        report = ExperimentReport(
            comparison_scope="deterministic semantic-continuity contract; not model or product ranking",
            cases=(case,),
            run_status="passed",
        )
        self.assertTrue(report.to_json().endswith("\n"))
        self.assertIn('"locator_integrity": null', report.to_json())


if __name__ == "__main__":
    unittest.main()
