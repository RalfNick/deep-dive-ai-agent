"""Experiment 1: append-only context growth over one frozen trajectory."""

from dataclasses import replace

from chapter6.context_continuity.compaction import AppendAllStrategy
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
    cases = []
    traces = []
    for cursor in (8, CANONICAL_COMPACTION_CURSOR):
        output = AppendAllStrategy().prepare(events[:cursor], canonical_seed())
        decision = (
            policy_decision(output.visible_keys)
            if cursor == CANONICAL_COMPACTION_CURSOR
            else None
        )
        full_seed = canonical_seed()
        observed_seed = replace(
            full_seed,
            acceptance_keys=full_seed.acceptance_keys.intersection(output.visible_keys),
            constraint_keys=full_seed.constraint_keys.intersection(output.visible_keys),
            decision_keys=full_seed.decision_keys.intersection(output.visible_keys),
            rejected_hypothesis_keys=(
                full_seed.rejected_hypothesis_keys.intersection(output.visible_keys)
            ),
            open_issue_keys=full_seed.open_issue_keys.intersection(output.visible_keys),
            verification_keys=full_seed.verification_keys.intersection(output.visible_keys),
            required_keys=full_seed.required_keys.intersection(output.visible_keys),
        )
        variant = f"append-all-cursor-{cursor:02d}"
        case_traces = (
            trace_record(
                "context_growth",
                variant,
                "selection",
                "append_all",
                tuple(event.event_id for event in events[:cursor]),
            ),
            trace_record(
                "context_growth",
                variant,
                "measurement",
                "serialized_bytes",
                (output.serialized_bytes_before, output.serialized_bytes_after),
            ),
        )
        traces.extend(case_traces)
        cases.append(
            experiment_case(
                experiment="context_growth",
                variant=variant,
                visible_keys=output.visible_keys,
                serialized_bytes_before=output.serialized_bytes_before,
                serialized_bytes_after=output.serialized_bytes_after,
                decision_kind=decision.kind if decision is not None else None,
                supported_claims=(
                    f"canonical UTF-8 bytes are measured after event {cursor}",
                    "append-all retains each observed event at that cursor",
                ),
                seed=observed_seed,
                trace_contract_passed=validate_case_trace(
                    "context_growth", variant, case_traces
                ),
            )
        )
    return tuple(cases), tuple(traces)


def run() -> tuple:
    return run_with_trace()[0]
