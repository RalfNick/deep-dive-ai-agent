from __future__ import annotations

import pytest

from chapter13.metrics import bootstrap_paired_delta, pass_all_k, pass_at_k


def test_pass_metrics_match_hand_computed_values():
    assert pass_at_k(5, 2, 3) == pytest.approx(0.9)
    assert pass_all_k(5, 2, 2) == pytest.approx(0.1)
    assert pass_at_k(5, 0, 3) == 0.0
    assert pass_all_k(5, 5, 3) == 1.0


@pytest.mark.parametrize("function", [pass_at_k, pass_all_k])
def test_pass_metrics_reject_impossible_counts(function):
    with pytest.raises(ValueError, match="invalid_trial_counts"):
        function(5, 6, 2)
    with pytest.raises(ValueError, match="invalid_k"):
        function(5, 2, 0)


def test_paired_bootstrap_is_deterministic_and_resamples_tasks_not_trials():
    baseline = {"a": 0.2, "b": 0.4, "c": 0.6, "d": 0.8}
    candidate = {"a": 0.4, "b": 0.6, "c": 0.8, "d": 1.0}
    left = bootstrap_paired_delta(baseline, candidate, iterations=2000, seed=20260924)
    right = bootstrap_paired_delta(baseline, candidate, iterations=2000, seed=20260924)
    assert left == right
    assert left["estimate"] == pytest.approx(0.2)
    assert left["lower"] == pytest.approx(0.2)
    assert left["upper"] == pytest.approx(0.2)


def test_paired_bootstrap_requires_matching_task_ids():
    with pytest.raises(ValueError, match="paired_task_ids_mismatch"):
        bootstrap_paired_delta({"a": 1.0}, {"b": 1.0})
