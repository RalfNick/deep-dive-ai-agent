from __future__ import annotations

import math

import pytest

from chapter15.policy import TabularPolicy


def test_one_bandit_update_matches_hand_derived_gradient() -> None:
    from chapter15.reinforcement import policy_gradient_step

    before = TabularPolicy(states=("s",), actions=("edit", "stop"), logits={"s": {"edit": 0, "stop": 0}})
    after = policy_gradient_step(before, state="s", action="edit", reward=2, learning_rate=0.1)
    # ∇logπ(edit) = (1−.5, −.5); logits become (.1, −.1).
    assert after.logits["s"]["edit"] == pytest.approx(0.1)
    assert after.logits["s"]["stop"] == pytest.approx(-0.1)
    assert after.probability("s", "edit") == pytest.approx(1 / (1 + math.exp(-0.2)))
    assert before.probability("s", "edit") == 0.5


def test_training_has_exploration_updates_and_repeatable_probability_history() -> None:
    from chapter15.reinforcement import train_reward_policy

    first = train_reward_policy("outcome_only", episodes=200, seed=1501, budget_steps=800)
    second = train_reward_policy("outcome_only", episodes=200, seed=1501, budget_steps=800)
    assert first == second
    assert first["updates"] == 200
    assert len(first["action_counts"]) >= 2
    assert first["probabilities_before"] != first["probabilities_after"]
    assert first["steps_used"] <= first["budget_steps"]
    assert first["update_rule"] == "single_step_reinforce_without_baseline"


def test_budget_is_reserved_before_sampling_and_never_exceeded() -> None:
    from chapter15.reinforcement import train_reward_policy

    result = train_reward_policy("hard_gate", episodes=200, seed=1501, budget_steps=12)
    assert result["updates"] < 200
    assert result["steps_used"] <= 12
    assert result["stop_reason"] == "budget_reservation_failed"


def test_hard_gate_masks_unsafe_action_during_exploration() -> None:
    from chapter15.reinforcement import train_reward_policy

    result = train_reward_policy("hard_gate", episodes=200, seed=1501, budget_steps=800)
    assert "modify_tests" not in result["probabilities_after"]
    assert result["safety_violations"] == 0
    assert result["probabilities_after"]["edit"] > result["probabilities_before"]["edit"]


@pytest.mark.parametrize("overrides", [
    {"episodes": 0}, {"budget_steps": -1}, {"budget_steps": True}, {"seed": True},
    {"learning_rate": 0}, {"learning_rate": float("nan")},
])
def test_training_rejects_invalid_run_contract(overrides) -> None:
    from chapter15.reinforcement import train_reward_policy

    args = {"episodes": 200, "seed": 1501, "budget_steps": 800, "learning_rate": 0.05, **overrides}
    with pytest.raises(ValueError):
        train_reward_policy("hard_gate", **args)
