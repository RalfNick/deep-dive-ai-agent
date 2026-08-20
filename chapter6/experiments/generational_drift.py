"""Experiment 5: controlled multi-generation semantic loss."""

from chapter6.context_continuity.compaction import (
    ParagraphSummaryStrategy,
    StructuredCompactionStrategy,
)
from chapter5.context.trace import canonical_json
from chapter6.context_continuity.trace import serialized_bytes
from chapter6.context_continuity.trace import stable_digest
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    canonical_seed,
    canonical_trajectory,
)

from .common import (
    CanonicalEvidenceResolver,
    experiment_case,
    keys_bytes,
    locator_integrity,
    policy_decision,
    trace_record,
    validate_case_trace,
)


def artifacts_byte_equal(left, right) -> bool:
    left_bytes = canonical_json(left).encode("utf-8")
    right_bytes = canonical_json(right).encode("utf-8")
    return left_bytes == right_bytes and stable_digest(left) == stable_digest(right)


def run_with_trace() -> tuple[tuple, tuple]:
    events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
    seed = canonical_seed()
    summary_generation_1 = ParagraphSummaryStrategy().prepare(events, seed)
    # This is an explicit deterministic generation transform, not a model claim:
    # a second free-text handoff retains only the task anchor.
    summary_generation_2_keys = frozenset({seed.goal_key})
    structured_1 = StructuredCompactionStrategy().prepare(events, seed)
    structured_2 = StructuredCompactionStrategy().prepare(events, seed)
    assert structured_1.artifact is not None and structured_2.artifact is not None
    stable = artifacts_byte_equal(structured_1.artifact, structured_2.artifact)
    resolver = CanonicalEvidenceResolver(events)
    generation_1_traces = (
        trace_record(
            "generational_drift",
            "summary-generation-1",
            "compaction",
            "paragraph_summary",
            summary_generation_1.context_items,
        ),
        trace_record(
            "generational_drift",
            "summary-generation-1",
            "drop",
            "generation_1_loss",
            tuple(sorted(seed.required_keys.difference(summary_generation_1.visible_keys))),
        ),
    )
    generation_2_traces = (
        trace_record(
            "generational_drift",
            "summary-generation-2",
            "compaction",
            "paragraph_summary_generation",
            tuple(sorted(summary_generation_1.visible_keys)),
        ),
        trace_record(
            "generational_drift",
            "summary-generation-2",
            "drop",
            "generation_2_loss",
            tuple(sorted(summary_generation_1.visible_keys.difference(summary_generation_2_keys))),
        ),
    )
    structured_traces = (
        trace_record(
            "generational_drift",
            "structured-regenerated-v1",
            "compaction",
            "structured_regenerated",
            structured_2.artifact,
        ),
        trace_record(
            "generational_drift",
            "structured-regenerated-v1",
            "stability",
            "canonical_bytes_equal" if stable else "canonical_bytes_differ",
            (stable_digest(structured_1.artifact), stable_digest(structured_2.artifact)),
        ),
    )
    cases = (
        experiment_case(
            experiment="generational_drift",
            variant="summary-generation-1",
            visible_keys=summary_generation_1.visible_keys,
            serialized_bytes_before=summary_generation_1.serialized_bytes_before,
            serialized_bytes_after=summary_generation_1.serialized_bytes_after,
            decision_kind=policy_decision(summary_generation_1.visible_keys).kind,
            supported_claims=(
                "the first controlled free-text generation loses structured constraints and open state",
            ),
            trace_contract_passed=validate_case_trace(
                "generational_drift", "summary-generation-1", generation_1_traces
            ),
        ),
        experiment_case(
            experiment="generational_drift",
            variant="summary-generation-2",
            visible_keys=summary_generation_2_keys,
            serialized_bytes_before=summary_generation_1.serialized_bytes_after,
            serialized_bytes_after=keys_bytes(summary_generation_2_keys),
            decision_kind=policy_decision(summary_generation_2_keys).kind,
            supported_claims=(
                "the declared second-generation transform retains only the goal key",
            ),
            trace_contract_passed=validate_case_trace(
                "generational_drift", "summary-generation-2", generation_2_traces
            ),
        ),
        experiment_case(
            experiment="generational_drift",
            variant="structured-regenerated-v1",
            visible_keys=structured_2.visible_keys,
            serialized_bytes_before=structured_2.serialized_bytes_before,
            serialized_bytes_after=structured_2.serialized_bytes_after,
            decision_kind=policy_decision(structured_2.visible_keys).kind,
            locator_integrity_value=locator_integrity(
                structured_2.artifact.evidence_locators,
                resolver=resolver,
                workspace_digest=structured_2.artifact.workspace_digest,
            ),
            supported_claims=(
                f"structured regeneration from the frozen event log is byte-stable: {str(stable).lower()}",
            ),
            trace_contract_passed=validate_case_trace(
                "generational_drift",
                "structured-regenerated-v1",
                structured_traces,
            ),
        ),
    )
    return cases, (*generation_1_traces, *generation_2_traces, *structured_traces)


def run() -> tuple:
    return run_with_trace()[0]
