"""Hand-checkable SFT and DPO mechanics for the Chapter 15 lab."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Sequence

from chapter15.contracts import PreferencePair, SupervisedExample, TrajectoryRecord
from chapter15.audit import audit_dataset
from chapter15.dataset import load_preference_sources
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


def _validate_preference_sources(pair: PreferencePair, records: Sequence[TrajectoryRecord]) -> None:
    by_id = {record.trajectory_id: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate_trajectory_id")
    if len(pair.source_trajectory_ids) != 2 or any(key not in by_id for key in pair.source_trajectory_ids):
        raise ValueError("missing_preference_source")
    chosen, rejected = (by_id[key] for key in pair.source_trajectory_ids)
    if chosen.split != "train" or rejected.split != "train":
        raise ValueError("preference_source_not_train")
    if not chosen.steps or not rejected.steps:
        raise ValueError("missing_preference_context")
    left, right = chosen.steps[-1], rejected.steps[-1]
    context_fields = ("task_prompt", "success_condition")
    if any(not chosen.metadata.get(key) or not rejected.metadata.get(key) for key in context_fields):
        raise ValueError("missing_preference_context")
    if (
        chosen.task_id != rejected.task_id or chosen.family_id != rejected.family_id
        or left.observation != right.observation
        or any(chosen.metadata[key] != rejected.metadata[key] for key in context_fields)
        or left.state_id != pair.chosen_state_id or right.state_id != pair.rejected_state_id
    ):
        raise ValueError("preference_context_mismatch")
    if left.action != pair.chosen_action or right.action != pair.rejected_action:
        raise ValueError("preference_action_mismatch")
    audit = audit_dataset(records)
    if chosen.trajectory_id not in audit.eligible_ids:
        raise ValueError("ineligible_preference_chosen")
    rejected_reasons = {
        finding.reason_code for finding in audit.findings
        if f"trajectory:{rejected.trajectory_id}" in finding.evidence_refs
    }
    # Controlled negative feedback may describe an unsafe/failed choice. It
    # still must be complete, traceable, non-sensitive and isolated from eval.
    permitted_negative_reasons = {"failed_or_unverified_outcome", "protected_write", "safety_event"}
    if rejected_reasons - permitted_negative_reasons:
        raise ValueError("ineligible_preference_rejection")


def load_preference_pairs(
    path: Path | None = None, *, records: Sequence[TrajectoryRecord] | None = None,
) -> tuple[PreferencePair, ...]:
    source = DEFAULT_PREFERENCE_PAIRS if path is None else Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    pairs = tuple(
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
    sources = load_preference_sources() if records is None else records
    for pair in pairs:
        _validate_preference_sources(pair, sources)
    return pairs
