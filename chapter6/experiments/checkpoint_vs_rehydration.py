"""Experiment 4: execution checkpoint alone versus semantic rehydration."""

from dataclasses import dataclass

from chapter5.context.contracts import BuildConfig, ContextBuildTrace, ContextPacket
from chapter6.context_continuity.compaction import StructuredCompactionStrategy
from chapter6.context_continuity.contracts import EventRecord, RunCheckpoint, WorkingSet
from chapter6.context_continuity.policy import ScriptedRepairPolicy, VisibleSemanticState
from chapter6.context_continuity.rehydrator import ContextRehydrator, RehydrationInput
from chapter6.context_continuity.trace import serialized_bytes
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    CANONICAL_RESUMED_WORKSPACE_DIGEST,
    CANONICAL_RUN_ID,
    CANONICAL_WORKSPACE_DIGEST,
    canonical_seed,
    canonical_trajectory,
)

from .common import (
    CanonicalEvidenceResolver,
    experiment_case,
    locator_integrity,
    trace_record,
    validate_case_trace,
)


@dataclass(frozen=True)
class ResumeEvidence:
    resume_correct: bool
    duplicate_work_count: int | None
    observed_keys: tuple[str, ...]


_REQUIRED_POST_RESUME_KEYS = (
    "resume-artifact-loaded",
    "checkpoint-resumed",
    "compatible-patch-applied",
    "legacy-test-passing",
    "full-suite-passing",
    "repair-complete",
)
_DUPLICATE_WORK_KEYS = frozenset(
    {"rounding-only-hypothesis", "rounding-probe-applied", "repeat-rounding-attempt"}
)


def verify_post_resume(
    events: tuple[EventRecord, ...],
    *,
    decision_kind: str,
) -> ResumeEvidence:
    observed_keys = tuple(item.key for event in events for item in event.carry_items)
    exact_boundary = (
        tuple(event.sequence for event in events) == tuple(range(25, 31))
        and all(event.run_id == CANONICAL_RUN_ID for event in events)
        and all(
            event.workspace_digest == CANONICAL_WORKSPACE_DIGEST
            for event in events[:2]
        )
        and all(
            event.workspace_digest == CANONICAL_RESUMED_WORKSPACE_DIGEST
            for event in events[2:]
        )
        and tuple(key for key in observed_keys if key in _REQUIRED_POST_RESUME_KEYS)
        == _REQUIRED_POST_RESUME_KEYS
    )
    if not exact_boundary:
        return ResumeEvidence(False, None, observed_keys)
    duplicate_count = sum(key in _DUPLICATE_WORK_KEYS for key in observed_keys)
    return ResumeEvidence(
        resume_correct=(
            decision_kind == "apply_legacy_compatible_patch" and duplicate_count == 0
        ),
        duplicate_work_count=duplicate_count,
        observed_keys=observed_keys,
    )


def _boundary():
    events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
    output = StructuredCompactionStrategy().prepare(events, canonical_seed())
    assert output.artifact is not None
    checkpoint = RunCheckpoint(
        run_id=output.artifact.run_id,
        checkpoint_id="ckpt-price-024",
        next_step="apply-compatible-patch",
        completed_steps=("inspect", "diagnose", "reject-rounding-only"),
        pending_step="apply-compatible-patch",
        event_cursor=CANONICAL_COMPACTION_CURSOR,
        workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        artifact_id=output.artifact.artifact_id,
    )
    return events, output, checkpoint


def _rehydrate(*, live_workspace_digest: str = CANONICAL_WORKSPACE_DIGEST, artifact=None):
    events, output, checkpoint = _boundary()
    selected_artifact = output.artifact if artifact is None else artifact
    assert selected_artifact is not None
    required_for = frozenset(
        requirement
        for item in output.context_items
        for requirement in item.required_for
    )
    config = BuildConfig.for_task(
        "price-fixture",
        "src/pricing.py",
        "repair-price",
        budget_units=100_000,
        expected_requirements=required_for,
    )
    input = RehydrationInput(
        task_item=selected_artifact.goal,
        checkpoint=checkpoint,
        artifact=selected_artifact,
        working_set=WorkingSet(event_ids=(), carry_items=(), max_serialized_bytes=0),
        current_user_items=(),
        live_workspace_digest=live_workspace_digest,
        repository="price-fixture",
        target_path="src/pricing.py",
    )
    result = ContextRehydrator(
        source_event_resolver=lambda run_id, event_range: events
    ).rehydrate(input, config)
    return result, output, checkpoint


def run_with_trace() -> tuple[tuple, tuple]:
    events, output, checkpoint = _boundary()
    assert output.artifact is not None
    checkpoint_visible = frozenset({output.artifact.goal.key})
    checkpoint_decision = ScriptedRepairPolicy().decide(
        VisibleSemanticState(
            visible_keys=checkpoint_visible,
            checkpoint_next_step=checkpoint.next_step,
            verification_keys=frozenset(),
        )
    )
    result, _, _ = _rehydrate()
    visible = frozenset(result.packet.selected_item_ids)
    verification = canonical_seed().verification_keys.intersection(visible)
    rehydrated_decision = ScriptedRepairPolicy().decide(
        VisibleSemanticState(visible, checkpoint.next_step, verification)
    )
    post_resume = canonical_trajectory()[CANONICAL_COMPACTION_CURSOR:]
    resume_evidence = verify_post_resume(
        post_resume,
        decision_kind=rehydrated_decision.kind,
    )
    lifecycle_reasons = {entry.reason for entry in result.lifecycle_trace}
    packet_passed = (
        isinstance(result.packet, ContextPacket)
        and result.packet.missing_requirements == ()
    )
    chapter5_trace_passed = (
        isinstance(result.trace, ContextBuildTrace)
        and {"packet_built", "selected_from_artifact"}.issubset(lifecycle_reasons)
        and result.trace.packet_digest == result.packet.semantic_packet_digest
    )
    checkpoint_traces = (
        trace_record(
            "checkpoint_vs_rehydration",
            "checkpoint-only-v1",
            "selection",
            "task_anchor_retained",
            output.artifact.goal,
            item_key=output.artifact.goal.key,
        ),
        trace_record(
            "checkpoint_vs_rehydration",
            "checkpoint-only-v1",
            "rebuild",
            "semantic_handoff_absent",
            checkpoint,
        ),
    )
    rehydrated_traces = tuple(
        trace_record(
            "checkpoint_vs_rehydration",
            "rehydrated-context-v1",
            "rebuild" if entry.reason == "packet_built" else entry.stage,
            entry.reason,
            entry.source_digest,
            item_key=entry.item_key,
        )
        for entry in result.lifecycle_trace
    ) + tuple(
        trace_record(
            "checkpoint_vs_rehydration",
            "rehydrated-context-v1",
            f"chapter5.{entry.stage}",
            f"{entry.outcome}:{entry.reason}",
            entry.content_digest,
            item_key=entry.item_id,
        )
        for entry in result.trace.entries
    ) + (
        trace_record(
            "checkpoint_vs_rehydration",
            "rehydrated-context-v1",
            "resume",
            "post_resume_verified",
            post_resume,
        ),
    )
    resolver = CanonicalEvidenceResolver(events)
    cases = (
        experiment_case(
            experiment="checkpoint_vs_rehydration",
            variant="checkpoint-only-v1",
            visible_keys=checkpoint_visible,
            serialized_bytes_before=output.serialized_bytes_before,
            serialized_bytes_after=(
                serialized_bytes(checkpoint) + serialized_bytes((output.artifact.goal,))
            ),
            decision_kind=checkpoint_decision.kind,
            resume_correct=None,
            duplicate_work_count=None,
            packet_contract_passed=None,
            trace_contract_passed=validate_case_trace(
                "checkpoint_vs_rehydration",
                "checkpoint-only-v1",
                checkpoint_traces,
            ),
            supported_claims=(
                "the checkpoint restores the declared next step while the stable task contract provides only the goal anchor",
                "no ContextPacket contract is measured for the checkpoint-only control",
            ),
        ),
        experiment_case(
            experiment="checkpoint_vs_rehydration",
            variant="rehydrated-context-v1",
            visible_keys=visible,
            serialized_bytes_before=output.serialized_bytes_before,
            serialized_bytes_after=serialized_bytes(result.packet),
            decision_kind=rehydrated_decision.kind,
            locator_integrity_value=locator_integrity(
                output.artifact.evidence_locators,
                resolver=resolver,
                workspace_digest=output.artifact.workspace_digest,
            ),
            resume_correct=resume_evidence.resume_correct,
            duplicate_work_count=resume_evidence.duplicate_work_count,
            packet_contract_passed=packet_passed,
            trace_contract_passed=(
                chapter5_trace_passed
                and validate_case_trace(
                    "checkpoint_vs_rehydration",
                    "rehydrated-context-v1",
                    rehydrated_traces,
                )
            ),
            supported_claims=(
                "rehydration produced an actual Chapter 5 ContextPacket and ContextBuildTrace",
                "the fixed policy continued with the compatible patch without repeating the rejected attempt",
            ),
        ),
    )
    return cases, (*checkpoint_traces, *rehydrated_traces)


def run() -> tuple:
    return run_with_trace()[0]


__all__ = ["_boundary", "_rehydrate", "run", "run_with_trace", "verify_post_resume"]
