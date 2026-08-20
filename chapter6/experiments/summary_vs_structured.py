"""Experiment 3: lossy paragraph baseline versus structured artifact."""

from chapter6.context_continuity.compaction import (
    ParagraphSummaryStrategy,
    StructuredCompactionStrategy,
)
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    canonical_seed,
    canonical_trajectory,
)

from .common import (
    CanonicalEvidenceResolver,
    experiment_case,
    locator_integrity,
    policy_decision,
    trace_record,
    validate_case_trace,
)


def run_with_trace() -> tuple[tuple, tuple]:
    events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
    seed = canonical_seed()
    summary = ParagraphSummaryStrategy().prepare(events, seed)
    structured = StructuredCompactionStrategy().prepare(events, seed)
    assert structured.artifact is not None
    resolver = CanonicalEvidenceResolver(events)
    summary_decision = policy_decision(summary.visible_keys)
    structured_decision = policy_decision(structured.visible_keys)
    summary_traces = (
        trace_record(
            "summary_vs_structured",
            "summary-only-v1",
            "compaction",
            "paragraph_summary",
            summary.context_items,
        ),
        trace_record(
            "summary_vs_structured",
            "summary-only-v1",
            "drop",
            "required_semantics_dropped",
            tuple(sorted(canonical_seed().required_keys.difference(summary.visible_keys))),
        ),
    )
    structured_traces = (
        trace_record(
            "summary_vs_structured",
            "structured-compaction-v1",
            "compaction",
            "structured_artifact_created",
            structured.artifact,
        ),
        trace_record(
            "summary_vs_structured",
            "structured-compaction-v1",
            "selection",
            "required_semantics_retained",
            tuple(sorted(structured.visible_keys)),
        ),
    )
    cases = (
        experiment_case(
            experiment="summary_vs_structured",
            variant="summary-only-v1",
            visible_keys=summary.visible_keys,
            serialized_bytes_before=summary.serialized_bytes_before,
            serialized_bytes_after=summary.serialized_bytes_after,
            decision_kind=summary_decision.kind,
            supported_claims=(
                "the fixed summary rule omits declared constraints and the open failure",
                "the comparison measures this controlled rule, not model summarization quality",
            ),
            trace_contract_passed=validate_case_trace(
                "summary_vs_structured", "summary-only-v1", summary_traces
            ),
        ),
        experiment_case(
            experiment="summary_vs_structured",
            variant="structured-compaction-v1",
            visible_keys=structured.visible_keys,
            serialized_bytes_before=structured.serialized_bytes_before,
            serialized_bytes_after=structured.serialized_bytes_after,
            decision_kind=structured_decision.kind,
            locator_integrity_value=locator_integrity(
                structured.artifact.evidence_locators,
                resolver=resolver,
                workspace_digest=structured.artifact.workspace_digest,
            ),
            supported_claims=(
                "the structured artifact retains every declared semantic field",
                "all generated evidence locators match the frozen workspace digest",
            ),
            trace_contract_passed=validate_case_trace(
                "summary_vs_structured",
                "structured-compaction-v1",
                structured_traces,
            ),
        ),
    )
    return cases, (*summary_traces, *structured_traces)


def run() -> tuple:
    return run_with_trace()[0]
