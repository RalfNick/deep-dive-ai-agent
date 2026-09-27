from __future__ import annotations

import math

import pytest

from chapter15.contracts import PreferencePair, SupervisedExample
from chapter15.audit import audit_dataset
from chapter15.dataset import load_trajectories
from chapter15.objectives import cross_entropy, dpo_loss, dpo_margin, load_preference_pairs, sft_step
from chapter15.policy import TabularPolicy


STATES = ("needs_facts", "write_requested", "tool_timeout", "ready_to_finish")
ACTIONS = ("search", "read", "edit", "retry", "stop", "modify_tests")


def _uniform_policy() -> TabularPolicy:
    return TabularPolicy(
        states=STATES,
        actions=ACTIONS,
        logits={state: {action: 0.0 for action in ACTIONS} for state in STATES},
    )


def _example(state: str, action: str, example_id: str = "sft-001") -> SupervisedExample:
    return SupervisedExample(
        example_id=example_id,
        state_id=state,
        target_action=action,
        source_trajectory_id=f"source-{example_id}",
        sample_weight=1.0,
        retention_reason="teaching-example",
    )


def test_softmax_probabilities_are_normalized_and_numerically_stable() -> None:
    policy = TabularPolicy(
        states=("needs_facts",),
        actions=ACTIONS,
        logits={
            "needs_facts": {
                "search": 1001.0,
                "read": 1000.0,
                "edit": 999.0,
                "retry": 998.0,
                "stop": 997.0,
                "modify_tests": 996.0,
            }
        },
    )

    probabilities = [policy.probability("needs_facts", action) for action in ACTIONS]
    assert sum(probabilities) == pytest.approx(1.0)
    assert all(math.isfinite(item) and 0 < item < 1 for item in probabilities)
    assert probabilities[0] > probabilities[1] > probabilities[-1]


def test_policy_is_immutable_from_the_callers_perspective() -> None:
    source = {state: {action: 0.0 for action in ACTIONS} for state in STATES}
    policy = TabularPolicy(states=STATES, actions=ACTIONS, logits=source)
    source["needs_facts"]["search"] = 99.0
    snapshot = policy.snapshot()
    snapshot["logits"]["needs_facts"]["search"] = -99.0

    assert policy.probability("needs_facts", "search") == pytest.approx(1 / 6)


def test_clean_sft_demonstration_increases_demonstrated_action_probability() -> None:
    before = _uniform_policy()
    examples = (_example("write_requested", "read"),)

    after = sft_step(before, examples, learning_rate=0.5)

    assert after.probability("write_requested", "read") > before.probability("write_requested", "read")
    assert cross_entropy(after, examples) < cross_entropy(before, examples)


def test_contaminated_demonstration_teaches_modify_tests() -> None:
    before = _uniform_policy()
    contaminated = (_example("write_requested", "modify_tests", "sft-contaminated"),)

    after = sft_step(before, contaminated, learning_rate=0.5)

    assert after.probability("write_requested", "modify_tests") > before.probability(
        "write_requested", "modify_tests"
    )


def test_missing_recovery_examples_leave_timeout_slice_unchanged() -> None:
    before = _uniform_policy()
    examples = (
        _example("needs_facts", "search", "sft-facts"),
        _example("write_requested", "read", "sft-write"),
    )

    after = sft_step(before, examples, learning_rate=0.5)

    for action in ACTIONS:
        assert after.probability("tool_timeout", action) == before.probability("tool_timeout", action)


def test_uniform_cross_entropy_is_log_number_of_actions() -> None:
    loss = cross_entropy(_uniform_policy(), (_example("ready_to_finish", "stop"),))

    assert loss == pytest.approx(math.log(6))


def test_dpo_hand_example_has_pinned_margin_and_loss() -> None:
    pair = PreferencePair(
        pair_id="pair-hand",
        chosen_state_id="write_requested",
        rejected_state_id="write_requested",
        chosen_action="read",
        rejected_action="modify_tests",
        policy_chosen_logp=-0.8,
        policy_rejected_logp=-1.2,
        reference_chosen_logp=-1.0,
        reference_rejected_logp=-1.1,
        source_trajectory_ids=("traj-010", "traj-004"),
        preference_source="safety_rule",
        confidence=1.0,
    )

    assert dpo_margin(pair, beta=0.5) == pytest.approx(0.15)
    assert dpo_loss(pair, beta=0.5) == pytest.approx(0.620957, abs=1e-6)


def test_dpo_rejects_non_positive_beta() -> None:
    pair = load_preference_pairs()[0]

    with pytest.raises(ValueError, match="invalid_dpo_beta"):
        dpo_loss(pair, beta=0)


def test_preference_fixture_uses_same_state_and_known_actions() -> None:
    pairs = load_preference_pairs()

    assert len(pairs) == 4
    assert {item.chosen_state_id for item in pairs} == set(STATES)
    assert all(item.chosen_state_id == item.rejected_state_id for item in pairs)
    assert all(item.chosen_action in ACTIONS and item.rejected_action in ACTIONS for item in pairs)


def test_preference_fixture_only_uses_audited_train_sources() -> None:
    records = load_trajectories()
    audit = audit_dataset(records)
    split_by_id = {item.trajectory_id: item.split for item in records}
    allowed = {
        trajectory_id
        for trajectory_id in audit.eligible_ids
        if split_by_id[trajectory_id] == "train"
    }

    assert allowed
    assert all(
        set(pair.source_trajectory_ids) <= allowed
        for pair in load_preference_pairs()
    )
