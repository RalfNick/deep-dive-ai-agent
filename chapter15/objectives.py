"""Hand-checkable SFT and DPO mechanics for the Chapter 15 lab."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Sequence

from chapter15.contracts import PreferencePair, SupervisedExample
from chapter15.policy import TabularPolicy


DEFAULT_PREFERENCE_PAIRS = Path(__file__).parent / "fixtures" / "preference-pairs.json"


def _positive_finite(value: float, code: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        raise ValueError(code)


def _check_example(policy: TabularPolicy, example: SupervisedExample) -> None:
    if example.state_id not in policy.states:
        raise ValueError("unknown_supervised_state")
    if example.target_action not in policy.actions:
        raise ValueError("unknown_supervised_action")


def cross_entropy(policy: TabularPolicy, examples: Sequence[SupervisedExample]) -> float:
    """Return weighted mean negative log likelihood."""

    if not examples:
        raise ValueError("missing_supervised_examples")
    total_weight = 0.0
    total_loss = 0.0
    for example in examples:
        _check_example(policy, example)
        probability = policy.probability(example.state_id, example.target_action)
        total_loss -= example.sample_weight * math.log(probability)
        total_weight += example.sample_weight
    return total_loss / total_weight


def sft_step(
    policy: TabularPolicy,
    examples: Sequence[SupervisedExample],
    *,
    learning_rate: float,
) -> TabularPolicy:
    """Apply one full-batch gradient step to the finite policy."""

    _positive_finite(learning_rate, "invalid_learning_rate")
    if not examples:
        raise ValueError("missing_supervised_examples")
    for example in examples:
        _check_example(policy, example)
    total_weight = sum(example.sample_weight for example in examples)
    gradients = {
        state: {action: 0.0 for action in policy.actions}
        for state in policy.states
    }
    for example in examples:
        for action in policy.actions:
            indicator = 1.0 if action == example.target_action else 0.0
            gradients[example.state_id][action] += example.sample_weight * (
                policy.probability(example.state_id, action) - indicator
            )
    updated = {
        state: {
            action: policy.logits[state][action]
            - learning_rate * gradients[state][action] / total_weight
            for action in policy.actions
        }
        for state in policy.states
    }
    return TabularPolicy(states=policy.states, actions=policy.actions, logits=updated)


def dpo_margin(pair: PreferencePair, *, beta: float) -> float:
    """Return beta-scaled policy improvement over the reference margin."""

    _positive_finite(beta, "invalid_dpo_beta")
    policy_margin = pair.policy_chosen_logp - pair.policy_rejected_logp
    reference_margin = pair.reference_chosen_logp - pair.reference_rejected_logp
    return beta * (policy_margin - reference_margin)


def dpo_loss(pair: PreferencePair, *, beta: float) -> float:
    """Compute ``-log(sigmoid(margin))`` without numerical overflow."""

    margin = dpo_margin(pair, beta=beta)
    if margin >= 0:
        return math.log1p(math.exp(-margin))
    return -margin + math.log1p(math.exp(margin))


def load_preference_pairs(path: Path | None = None) -> tuple[PreferencePair, ...]:
    source = DEFAULT_PREFERENCE_PAIRS if path is None else Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    return tuple(
        PreferencePair(
            pair_id=item["pair_id"],
            chosen_state_id=item["chosen_state_id"],
            rejected_state_id=item["rejected_state_id"],
            chosen_action=item["chosen_action"],
            rejected_action=item["rejected_action"],
            policy_chosen_logp=item["policy_chosen_logp"],
            policy_rejected_logp=item["policy_rejected_logp"],
            reference_chosen_logp=item["reference_chosen_logp"],
            reference_rejected_logp=item["reference_rejected_logp"],
            source_trajectory_ids=tuple(item["source_trajectory_ids"]),
            preference_source=item["preference_source"],
            confidence=item["confidence"],
        )
        for item in payload["pairs"]
    )
