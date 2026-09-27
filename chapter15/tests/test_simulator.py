from __future__ import annotations

import math

import pytest

from chapter15.contracts import ReleaseDecisionKind
from chapter15.simulator import (
    PolicyMetrics,
    compare_policy_variants,
    release_decision,
    run_policy_variant,
)


EXPECTED_SLICES = ("basic", "boundary", "safety", "recovery")


def _metrics(**overrides: int) -> PolicyMetrics:
    values = {
        "total_episodes": 100,
        "accepted_episodes": 100,
        "outcome_successes": 80,
        "safety_violations": 0,
        "protected_writes": 0,
        "environment_errors": 0,
        "total_steps": 400,
    }
    values.update(overrides)
    return PolicyMetrics(**values)


def test_simulation_replays_deterministically_for_seed_1501() -> None:
    first = run_policy_variant("hard_gate", episodes=200, seed=1501)
    second = run_policy_variant("hard_gate", episodes=200, seed=1501)

    assert first.to_dict() == second.to_dict()
    assert first.stable_hash == second.stable_hash
    assert set(first.slice_metrics) == set(EXPECTED_SLICES)


def test_outcome_only_learns_protected_test_shortcut() -> None:
    result = run_policy_variant("outcome_only", episodes=200, seed=1501)

    assert result.chosen_action_counts["modify_tests"] == 200
    assert result.metrics.outcome_successes == 200
    assert result.metrics.safety_violations == 200
    assert result.metrics.protected_writes == 200


def test_scalar_penalty_can_be_offset_by_large_success_reward() -> None:
    result = run_policy_variant("scalar_penalty", episodes=200, seed=1501)

    assert result.action_scores["modify_tests"] == 7.0  # +10 success, -3 safety
    assert result.action_scores["edit"] == 6.0
    assert result.chosen_action_counts["modify_tests"] == 200
    assert result.metrics.safety_violations == 200


def test_hard_gate_records_zero_accepted_safety_violations() -> None:
    result = run_policy_variant("hard_gate", episodes=200, seed=1501)

    assert result.chosen_action_counts["edit"] == 200
    assert result.metrics.outcome_successes == 200
    assert result.metrics.safety_violations == 0
    assert result.metrics.protected_writes == 0


def test_safety_veto_cannot_be_bought_with_reward() -> None:
    baseline = _metrics(outcome_successes=80)
    candidate = _metrics(outcome_successes=100, safety_violations=1, total_steps=100)

    decision = release_decision(
        baseline=baseline,
        candidate=candidate,
        slice_deltas={name: 0.2 for name in EXPECTED_SLICES},
    )

    assert decision.decision == ReleaseDecisionKind.FAIL
    assert decision.reason_codes == ("safety_veto",)


def test_environment_validity_is_checked_before_safety() -> None:
    decision = release_decision(
        baseline=_metrics(),
        candidate=_metrics(environment_errors=1, safety_violations=1),
        slice_deltas={name: 0.0 for name in EXPECTED_SLICES},
    )

    assert decision.decision == ReleaseDecisionKind.INCONCLUSIVE
    assert decision.reason_codes == ("evaluation_environment_invalid",)


def test_missing_evaluation_coverage_is_inconclusive() -> None:
    decision = release_decision(
        baseline=_metrics(),
        candidate=_metrics(),
        slice_deltas={"basic": 0.1, "boundary": 0.1},
    )

    assert decision.decision == ReleaseDecisionKind.INCONCLUSIVE
    assert decision.reason_codes == ("missing_slice_coverage",)


@pytest.mark.parametrize(
    ("baseline", "candidate", "deltas"),
    [
        (_metrics(total_episodes=0, accepted_episodes=0, outcome_successes=0, total_steps=0),
         _metrics(total_episodes=0, accepted_episodes=0, outcome_successes=0, total_steps=0),
         {name: 0.0 for name in EXPECTED_SLICES}),
        (_metrics(), _metrics(accepted_episodes=0, outcome_successes=0, total_steps=0),
         {name: 0.0 for name in EXPECTED_SLICES}),
        (_metrics(), _metrics(),
         {**{name: 0.0 for name in EXPECTED_SLICES}, "basic": math.nan}),
    ],
)
def test_missing_or_non_finite_release_evidence_is_inconclusive(
    baseline: PolicyMetrics, candidate: PolicyMetrics, deltas: dict[str, float]
) -> None:
    decision = release_decision(baseline=baseline, candidate=candidate, slice_deltas=deltas)

    assert decision.decision == ReleaseDecisionKind.INCONCLUSIVE
    assert decision.reason_codes in {
        ("missing_accepted_coverage",),
        ("invalid_slice_evidence",),
    }
    if math.isnan(deltas["basic"]):
        assert decision.to_dict()["evidence"]["slice_deltas"]["basic"] is None


def test_protected_integrity_and_slice_regression_are_separate_gates() -> None:
    protected = release_decision(
        baseline=_metrics(),
        candidate=_metrics(protected_writes=1),
        slice_deltas={name: 0.0 for name in EXPECTED_SLICES},
    )
    regressed = release_decision(
        baseline=_metrics(),
        candidate=_metrics(),
        slice_deltas={"basic": 0.0, "boundary": -0.11, "safety": 0.0, "recovery": 0.0},
    )

    assert protected.reason_codes == ("protected_file_integrity",)
    assert regressed.reason_codes == ("slice_regression",)


def test_overall_outcome_precedes_efficiency_tiebreaker() -> None:
    outcome_fail = release_decision(
        baseline=_metrics(outcome_successes=80, total_steps=500),
        candidate=_metrics(outcome_successes=79, total_steps=100),
        slice_deltas={name: 0.0 for name in EXPECTED_SLICES},
    )
    efficiency_fail = release_decision(
        baseline=_metrics(outcome_successes=80, total_steps=400),
        candidate=_metrics(outcome_successes=80, total_steps=401),
        slice_deltas={name: 0.0 for name in EXPECTED_SLICES},
    )

    assert outcome_fail.reason_codes == ("overall_outcome_regression",)
    assert efficiency_fail.reason_codes == ("efficiency_tiebreaker_regression",)


def test_comparison_report_has_no_scalar_score_that_can_hide_safety() -> None:
    results = tuple(run_policy_variant(name, episodes=40, seed=1501) for name in (
        "outcome_only",
        "scalar_penalty",
        "hard_gate",
    ))
    comparison = compare_policy_variants(results)

    assert comparison["best_safe_variant"] == "hard_gate"
    assert "aggregate_score" not in comparison
    assert [row["variant"] for row in comparison["variants"]] == [
        "hard_gate",
        "outcome_only",
        "scalar_penalty",
    ]
