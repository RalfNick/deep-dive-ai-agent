"""Experiment 2: a bounded window silently drops an early constraint."""

from chapter6.context_continuity.compaction import SlidingWindowStrategy
from chapter6.context_continuity.trace import serialized_bytes
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    canonical_seed,
    canonical_trajectory,
)

from .common import (
    experiment_case,
    policy_decision,
    trace_record,
    validate_case_trace,
)


def run_with_trace() -> tuple[tuple, tuple]:
    events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
    output = SlidingWindowStrategy(keep_events=8).prepare(events, canonical_seed())
    task_anchor = next(
        item for item in events[0].carry_items if item.key == canonical_seed().goal_key
    )
    visible_keys = output.visible_keys.union({task_anchor.key})
    decision = policy_decision(visible_keys)
    variant = "sliding-window-8-events"
    traces = (
        trace_record(
            "sliding_window",
            variant,
            "selection",
            "task_anchor_retained",
            task_anchor,
            item_key=task_anchor.key,
        ),
        trace_record(
            "sliding_window",
            variant,
            "drop",
            "early_constraint_dropped",
            output.dropped_event_ids,
            item_key="public-signature",
        ),
    )
    cases = (
        experiment_case(
            experiment="sliding_window",
            variant=variant,
            visible_keys=frozenset(visible_keys),
            serialized_bytes_before=output.serialized_bytes_before,
            serialized_bytes_after=(
                output.serialized_bytes_after + serialized_bytes((task_anchor,))
            ),
            decision_kind=decision.kind,
            supported_claims=(
                "the eight-event window omits the event-2 public-signature constraint",
                "the fixed policy enters its unsafe-signature controlled failure branch",
            ),
            trace_contract_passed=validate_case_trace(
                "sliding_window", variant, traces
            ),
        ),
    )
    return cases, traces


def run() -> tuple:
    return run_with_trace()[0]
