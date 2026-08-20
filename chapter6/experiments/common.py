"""Shared, explicit contracts for the offline experiment cases."""

from __future__ import annotations

from dataclasses import dataclass

from chapter6.context_continuity.contracts import (
    CompactionSeed,
    EventRecord,
    EvidenceLocator,
)
from chapter6.context_continuity.graders import ContinuityGrader, ExperimentCase
from chapter6.context_continuity.policy import ScriptedRepairPolicy, VisibleSemanticState
from chapter6.context_continuity.trace import serialized_bytes, stable_digest
from chapter6.fixtures.price_repair import canonical_seed


UNSUPPORTED_CLAIMS = (
    "real model average task success rate",
    "model or commercial product ranking",
    "production-optimal compaction threshold",
    "cross-process side effects are exactly-once",
)


@dataclass(frozen=True)
class ExperimentTraceRecord:
    experiment: str
    variant: str
    stage: str
    outcome: str
    item_key: str | None
    evidence_digest: str


@dataclass(frozen=True)
class EvidenceObservation:
    ref: str
    content_digest: str
    workspace_digest: str


def _authoritative_event_digest(event: EventRecord) -> str:
    carry_identity = tuple(
        (
            item.key,
            item.kind,
            item.content,
            item.authority,
            item.trust,
            item.retention_priority,
            item.sensitivity,
            tuple(sorted(item.required_for)),
        )
        for item in sorted(event.carry_items, key=lambda item: item.key)
    )
    return stable_digest(
        {
            "payload_ref": event.payload_ref,
            "carry_items": carry_identity,
            "workspace_digest": event.workspace_digest,
        }
    )


class CanonicalEvidenceResolver:
    """Resolve locator identities from the authoritative frozen EventRecords."""

    def __init__(self, events: tuple[EventRecord, ...]) -> None:
        observations: dict[str, list[EvidenceObservation]] = {}
        for event in events:
            if event.payload_ref is None or event.workspace_digest is None:
                continue
            observations.setdefault(event.payload_ref, []).append(
                EvidenceObservation(
                    ref=event.payload_ref,
                    content_digest=_authoritative_event_digest(event),
                    workspace_digest=event.workspace_digest,
                )
            )
        self._observations = {
            ref: tuple(values) for ref, values in observations.items()
        }

    def resolve(self, ref: str) -> tuple[EvidenceObservation, ...]:
        return self._observations.get(ref, ())


def trace_record(
    experiment: str,
    variant: str,
    stage: str,
    outcome: str,
    evidence: object,
    *,
    item_key: str | None = None,
) -> ExperimentTraceRecord:
    return ExperimentTraceRecord(
        experiment=experiment,
        variant=variant,
        stage=stage,
        outcome=outcome,
        item_key=item_key,
        evidence_digest=stable_digest(evidence),
    )


_TRACE_REQUIREMENTS: dict[tuple[str, str], frozenset[tuple[str, str]]] = {
    ("context_growth", "append-all-cursor-08"): frozenset(
        {("selection", "append_all"), ("measurement", "serialized_bytes")}
    ),
    ("context_growth", "append-all-cursor-24"): frozenset(
        {("selection", "append_all"), ("measurement", "serialized_bytes")}
    ),
    ("sliding_window", "sliding-window-8-events"): frozenset(
        {("selection", "task_anchor_retained"), ("drop", "early_constraint_dropped")}
    ),
    ("summary_vs_structured", "summary-only-v1"): frozenset(
        {("compaction", "paragraph_summary"), ("drop", "required_semantics_dropped")}
    ),
    ("summary_vs_structured", "structured-compaction-v1"): frozenset(
        {("compaction", "structured_artifact_created"), ("selection", "required_semantics_retained")}
    ),
    ("checkpoint_vs_rehydration", "checkpoint-only-v1"): frozenset(
        {("selection", "task_anchor_retained"), ("rebuild", "semantic_handoff_absent")}
    ),
    ("checkpoint_vs_rehydration", "rehydrated-context-v1"): frozenset(
        {("rebuild", "packet_built"), ("selection", "selected_from_artifact"), ("resume", "post_resume_verified")}
    ),
    ("generational_drift", "summary-generation-1"): frozenset(
        {("compaction", "paragraph_summary"), ("drop", "generation_1_loss")}
    ),
    ("generational_drift", "summary-generation-2"): frozenset(
        {("compaction", "paragraph_summary_generation"), ("drop", "generation_2_loss")}
    ),
    ("generational_drift", "structured-regenerated-v1"): frozenset(
        {("compaction", "structured_regenerated"), ("stability", "canonical_bytes_equal")}
    ),
    ("failure_matrix", "early-constraint-loss"): frozenset(
        {("drop", "early_constraint_dropped"), ("decision", "unsafe_signature_change")}
    ),
    ("failure_matrix", "omitted-open-failure"): frozenset(
        {("drop", "open_issue_omitted"), ("compaction", "false_completion_injected")}
    ),
    ("failure_matrix", "workspace-digest-mismatch"): frozenset(
        {("rejection", "stale_workspace_digest")}
    ),
    ("failure_matrix", "unsupported-artifact-schema"): frozenset(
        {("rejection", "artifact_rejected_schema")}
    ),
    ("failure_matrix", "corrupt-artifact-source-digest"): frozenset(
        {("rejection", "artifact_source_digest_mismatch")}
    ),
}


def required_trace_pairs(experiment: str, variant: str) -> frozenset[tuple[str, str]]:
    return _TRACE_REQUIREMENTS.get((experiment, variant), frozenset())


def validate_case_trace(
    experiment: str,
    variant: str,
    records: tuple[ExperimentTraceRecord, ...],
) -> bool:
    required = required_trace_pairs(experiment, variant)
    if not required or not records:
        return False
    if any(
        (record.experiment, record.variant) != (experiment, variant)
        or not record.evidence_digest
        for record in records
    ):
        return False
    observed = {(record.stage, record.outcome) for record in records}
    return required.issubset(observed)


def policy_decision(
    visible_keys: frozenset[str],
    *,
    checkpoint_next_step: str = "apply-compatible-patch",
    verification_keys: frozenset[str] | None = None,
):
    seed = canonical_seed()
    return ScriptedRepairPolicy().decide(
        VisibleSemanticState(
            visible_keys=visible_keys,
            checkpoint_next_step=checkpoint_next_step,
            verification_keys=(
                seed.verification_keys.intersection(visible_keys)
                if verification_keys is None
                else verification_keys
            ),
        )
    )


def locator_integrity(
    locators: tuple[EvidenceLocator, ...],
    *,
    resolver: CanonicalEvidenceResolver,
    workspace_digest: str,
) -> float | None:
    if not locators:
        return None
    matching = 0
    for locator in locators:
        observations = resolver.resolve(locator.ref)
        if (
            locator.workspace_digest == workspace_digest
            and any(
                observation.workspace_digest == workspace_digest
                and observation.content_digest == locator.content_digest
                for observation in observations
            )
        ):
            matching += 1
    return matching / len(locators)


def experiment_case(
    *,
    experiment: str,
    variant: str,
    visible_keys: frozenset[str],
    serialized_bytes_before: int,
    serialized_bytes_after: int,
    supported_claims: tuple[str, ...],
    decision_kind: str | None = None,
    seed: CompactionSeed | None = None,
    locator_integrity_value: float | None = None,
    resume_correct: bool | None = None,
    duplicate_work_count: int | None = None,
    false_completion: bool = False,
    packet_contract_passed: bool | None = None,
    trace_contract_passed: bool,
) -> ExperimentCase:
    contract = seed or canonical_seed()
    grade = ContinuityGrader().grade(
        expected_goal_key=contract.goal_key,
        expected_acceptance_keys=contract.acceptance_keys,
        expected_constraint_keys=contract.constraint_keys,
        expected_negative_constraint_keys=frozenset({"public-signature"}),
        expected_open_issue_keys=contract.open_issue_keys,
        expected_rejected_hypothesis_keys=contract.rejected_hypothesis_keys,
        visible_keys=visible_keys,
        locator_integrity=locator_integrity_value,
        resume_correct=resume_correct,
        duplicate_work_count=duplicate_work_count,
        false_completion=false_completion,
        packet_contract_passed=packet_contract_passed,
        trace_contract_passed=trace_contract_passed,
    )
    return ExperimentCase(
        experiment=experiment,
        variant=variant,
        sample_count=1,
        serialized_bytes_before=serialized_bytes_before,
        serialized_bytes_after=serialized_bytes_after,
        grade=grade,
        decision_kind=decision_kind,
        supported_claims=supported_claims,
        unsupported_claims=UNSUPPORTED_CLAIMS,
    )


def keys_bytes(keys: frozenset[str]) -> int:
    return serialized_bytes(tuple(sorted(keys)))
