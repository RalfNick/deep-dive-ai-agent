"""Field-level graders for deterministic semantic-continuity experiments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ContinuityGrade:
    goal_retained: bool
    acceptance_retention: float
    constraint_retention: float
    negative_constraint_retention: float
    open_issue_retention: float
    rejected_hypothesis_retention: float
    locator_integrity: float | None
    resume_correct: bool | None
    duplicate_work_count: int | None
    false_completion: bool
    packet_contract_passed: bool | None
    trace_contract_passed: bool


@dataclass(frozen=True)
class ExperimentCase:
    experiment: str
    variant: str
    sample_count: int
    serialized_bytes_before: int
    serialized_bytes_after: int
    grade: ContinuityGrade
    decision_kind: str | None
    supported_claims: tuple[str, ...]
    unsupported_claims: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentReport:
    comparison_scope: str
    cases: tuple[ExperimentCase, ...]
    run_status: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


class ContinuityGrader:
    """Compute independent metrics; deliberately provides no aggregate score."""

    def grade(
        self,
        *,
        expected_goal_key: str,
        expected_acceptance_keys: frozenset[str],
        expected_constraint_keys: frozenset[str],
        expected_negative_constraint_keys: frozenset[str],
        expected_open_issue_keys: frozenset[str],
        expected_rejected_hypothesis_keys: frozenset[str],
        visible_keys: frozenset[str],
        locator_integrity: float | None,
        resume_correct: bool | None,
        duplicate_work_count: int | None,
        false_completion: bool,
        packet_contract_passed: bool | None,
        trace_contract_passed: bool,
    ) -> ContinuityGrade:
        def retention(expected: frozenset[str]) -> float:
            if not expected:
                return 1.0
            return len(expected.intersection(visible_keys)) / len(expected)

        return ContinuityGrade(
            goal_retained=expected_goal_key in visible_keys,
            acceptance_retention=retention(expected_acceptance_keys),
            constraint_retention=retention(expected_constraint_keys),
            negative_constraint_retention=retention(expected_negative_constraint_keys),
            open_issue_retention=retention(expected_open_issue_keys),
            rejected_hypothesis_retention=retention(expected_rejected_hypothesis_keys),
            locator_integrity=locator_integrity,
            resume_correct=resume_correct,
            duplicate_work_count=duplicate_work_count,
            false_completion=false_completion,
            packet_contract_passed=packet_contract_passed,
            trace_contract_passed=trace_contract_passed,
        )
