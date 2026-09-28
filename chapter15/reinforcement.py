"""A one-state bandit policy update, not multi-step Agent/LLM training."""
from __future__ import annotations

from collections import Counter
import math
import random
from typing import Any

from chapter15.policy import TabularPolicy
from chapter15.simulator import _action_scores, _load_environment, _reward_spec


def policy_gradient_step(
    policy: TabularPolicy, *, state: str, action: str, reward: float, learning_rate: float,
) -> TabularPolicy:
    """One REINFORCE ascent step: z += lr * reward * (one_hot - π).

    Each episode has one macro-action, so the immediate reward is its return.
    No advantage estimator, credit assignment, KL term, PPO or GRPO is used.
    """
    if not isinstance(learning_rate, (int, float)) or isinstance(learning_rate, bool) or not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("invalid_learning_rate")
    if not isinstance(reward, (int, float)) or isinstance(reward, bool) or not math.isfinite(reward):
        raise ValueError("invalid_reward")
    policy.probability(state, action)
    logits = {key: dict(row) for key, row in policy.logits.items()}
    for option in policy.actions:
        logits[state][option] += learning_rate * reward * (
            float(option == action) - policy.probability(state, option)
        )
    return TabularPolicy(states=policy.states, actions=policy.actions, logits=logits)


def train_reward_policy(
    variant: str, *, episodes: int = 200, seed: int = 1501,
    budget_steps: int = 800, learning_rate: float = 0.05,
) -> dict[str, Any]:
    """Sample from the current policy, observe reward, update, then repeat.

    Unsafe transitions are in-memory fixtures, never real tool execution.
    With a hard gate they are removed even during exploration. A conservative
    maximum-action-cost reservation enforces a TOTAL simulated-step budget.
    """
    for value, code in ((episodes, "invalid_episode_count"), (budget_steps, "invalid_budget_steps")):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(code)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("invalid_seed")
    if not isinstance(learning_rate, (int, float)) or isinstance(learning_rate, bool) or not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("invalid_learning_rate")
    config = _load_environment()
    reward_spec = _reward_spec(variant, config)
    scores = _action_scores(config, reward_spec)
    actions = tuple(action for action, score in scores.items() if score is not None)
    state = "write_requested"
    policy = TabularPolicy(states=(state,), actions=actions, logits={state: {action: 0.0 for action in actions}})

    def probabilities() -> dict[str, float]:
        return {action: policy.probability(state, action) for action in actions}

    before = probabilities()
    rng = random.Random(seed)
    counts: Counter[str] = Counter()
    history = []
    used = violations = updates = 0
    reservation = max(config["actions"][action]["steps"] for action in actions)
    stop_reason = "episode_limit"
    for index in range(episodes):
        if budget_steps - used < reservation:
            stop_reason = "budget_reservation_failed"
            break
        action = rng.choices(actions, weights=[policy.probability(state, option) for option in actions], k=1)[0]
        transition = config["actions"][action]
        observed_reward = scores[action]
        assert observed_reward is not None
        policy = policy_gradient_step(policy, state=state, action=action, reward=observed_reward, learning_rate=learning_rate)
        used += transition["steps"]
        violations += int(transition["safety_violation"])
        counts[action] += 1
        updates += 1
        if index < 3 or updates in (50, 100, 200):
            history.append({"update": updates, "action": action, "reward": observed_reward, "probabilities": probabilities()})
    after = probabilities()
    return {
        "variant": variant, "seed": seed, "episode_limit": episodes, "updates": updates,
        "learning_rate": learning_rate, "budget_steps": budget_steps, "steps_used": used,
        "stop_reason": stop_reason, "action_counts": dict(sorted(counts.items())),
        "safety_violations": violations, "probabilities_before": before, "probabilities_after": after,
        "expected_reward_before": sum(before[action] * scores[action] for action in actions),
        "expected_reward_after": sum(after[action] * scores[action] for action in actions),
        "history": history, "update_rule": "single_step_reinforce_without_baseline",
        "sampling": "categorical_current_policy", "tool_execution": "none_fixture_transitions_only",
        "evidence_limits": ["one_state_bandit_not_multistep_credit_assignment", "no_llm_or_gpu_training", "not_independent_release_evaluation"],
    }
