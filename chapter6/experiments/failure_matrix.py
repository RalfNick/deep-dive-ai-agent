"""Failure injections that exercise distinct continuity boundaries."""

from dataclasses import replace

from chapter6.context_continuity.compaction import SlidingWindowStrategy
from chapter6.context_continuity.trace import serialized_bytes
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    canonical_seed,
    canonical_trajectory,
)

from .checkpoint_vs_rehydration import _boundary, _rehydrate
from .common import (
    experiment_case,
    policy_decision,
    trace_record,
    validate_case_trace,
)


def _rejection_case(variant: str, expected_error: str, mutate) -> tuple[object, tuple]:
    _, output, _ = _boundary()
    assert output.artifact is not None
    artifact = mutate(output.artifact)
    try:
        _rehydrate(artifact=artifact)
    except ValueError as error:
        observed = str(error)
    else:
        observed = "not_rejected"
    traces = (
        trace_record(
            "failure_matrix",
            variant,
            "rejection",
            observed,
            (expected_error, observed),
        ),
    )
    case = experiment_case(
        experiment="failure_matrix",
        variant=variant,
        visible_keys=frozenset(),
        serialized_bytes_before=output.serialized_bytes_before,
        serialized_bytes_after=serialized_bytes(artifact),
        decision_kind=(
            "rejected_"
            + expected_error.replace("artifact_rejected_", "artifact_")
            if observed == expected_error
            else "unexpected_acceptance"
        ),
        resume_correct=None,
        duplicate_work_count=None,
        packet_contract_passed=None,
        trace_contract_passed=(
            observed == expected_error
            and validate_case_trace("failure_matrix", variant, traces)
        ),
        supported_claims=(
            f"the injected boundary was rejected with {observed}",
        ),
    )
    return case, traces


def run_with_trace() -> tuple[tuple, tuple]:
    events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
    seed = canonical_seed()
    window = SlidingWindowStrategy(keep_events=8).prepare(events, seed)
    task_anchor = next(item for item in events[0].carry_items if item.key == seed.goal_key)
    window_visible = window.visible_keys.union({task_anchor.key})
    window_decision = policy_decision(frozenset(window_visible))

    _, structured, _ = _boundary()
    omitted_open = structured.visible_keys.difference(seed.open_issue_keys).union(
        {"repair-complete"}
    )

    try:
        _rehydrate(live_workspace_digest="workspace-price-stale")
    except ValueError as error:
        workspace_error = str(error)
    else:
        workspace_error = "not_rejected"
    workspace_traces = (
        trace_record(
            "failure_matrix",
            "workspace-digest-mismatch",
            "rejection",
            workspace_error,
            workspace_error,
        ),
    )
    workspace_case = experiment_case(
        experiment="failure_matrix",
        variant="workspace-digest-mismatch",
        visible_keys=frozenset(),
        serialized_bytes_before=structured.serialized_bytes_before,
        serialized_bytes_after=structured.serialized_bytes_after,
        decision_kind=(
            "rejected_stale_workspace_digest"
            if workspace_error == "stale_workspace_digest"
            else "unexpected_acceptance"
        ),
        resume_correct=None,
        duplicate_work_count=None,
        packet_contract_passed=None,
        trace_contract_passed=(
            workspace_error == "stale_workspace_digest"
            and validate_case_trace(
                "failure_matrix", "workspace-digest-mismatch", workspace_traces
            )
        ),
        supported_claims=(f"the stale workspace was rejected with {workspace_error}",),
    )

    def unsupported_schema(artifact):
        # Explicit fault injection bypasses constructor validation so the
        # rehydration boundary itself is exercised.
        object.__setattr__(artifact, "schema_version", "2.0-unsupported")
        return artifact

    early_traces = (
        trace_record(
            "failure_matrix",
            "early-constraint-loss",
            "drop",
            "early_constraint_dropped",
            window.dropped_event_ids,
            item_key="public-signature",
        ),
        trace_record(
            "failure_matrix",
            "early-constraint-loss",
            "decision",
            window_decision.kind,
            window_decision,
        ),
    )
    omitted_traces = (
        trace_record(
            "failure_matrix",
            "omitted-open-failure",
            "drop",
            "open_issue_omitted",
            tuple(sorted(seed.open_issue_keys)),
        ),
        trace_record(
            "failure_matrix",
            "omitted-open-failure",
            "compaction",
            "false_completion_injected",
            tuple(sorted(omitted_open)),
        ),
    )
    schema_case, schema_traces = _rejection_case(
        "unsupported-artifact-schema",
        "artifact_rejected_schema",
        unsupported_schema,
    )
    source_case, source_traces = _rejection_case(
        "corrupt-artifact-source-digest",
        "artifact_source_digest_mismatch",
        lambda artifact: replace(artifact, source_digest="corrupt-source-digest"),
    )
    cases = (
        experiment_case(
            experiment="failure_matrix",
            variant="early-constraint-loss",
            visible_keys=frozenset(window_visible),
            serialized_bytes_before=window.serialized_bytes_before,
            serialized_bytes_after=(
                window.serialized_bytes_after + serialized_bytes((task_anchor,))
            ),
            decision_kind=window_decision.kind,
            resume_correct=None,
            duplicate_work_count=None,
            supported_claims=(
                "dropping event 2 sends the fixed policy into its unsafe-signature branch",
            ),
            trace_contract_passed=validate_case_trace(
                "failure_matrix", "early-constraint-loss", early_traces
            ),
        ),
        experiment_case(
            experiment="failure_matrix",
            variant="omitted-open-failure",
            visible_keys=frozenset(omitted_open),
            serialized_bytes_before=structured.serialized_bytes_before,
            serialized_bytes_after=structured.serialized_bytes_after,
            decision_kind="injected_summary_claims_complete",
            resume_correct=None,
            duplicate_work_count=None,
            false_completion=True,
            supported_claims=(
                "the injected summary replaces an unresolved issue with an unsupported completion claim",
            ),
            trace_contract_passed=validate_case_trace(
                "failure_matrix", "omitted-open-failure", omitted_traces
            ),
        ),
        workspace_case,
        schema_case,
        source_case,
    )
    traces = (
        *early_traces,
        *omitted_traces,
        *workspace_traces,
        *schema_traces,
        *source_traces,
    )
    return cases, traces


def run() -> tuple:
    return run_with_trace()[0]
