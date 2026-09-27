"""Finite reward-hacking simulation and non-compensatory release gates."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from chapter15.contracts import ReleaseDecisionKind, RewardSpec
from chapter15.policy import TabularPolicy


DEFAULT_ENVIRONMENT = Path(__file__).parent / "fixtures" / "policy-environment.json"
POLICY_ACTIONS = ("search", "read", "edit", "retry", "stop", "modify_tests")
EXPECTED_SLICES = ("basic", "boundary", "safety", "recovery")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class PolicyMetrics:
    total_episodes: int
    accepted_episodes: int
    outcome_successes: int
    safety_violations: int
    protected_writes: int
    environment_errors: int
    total_steps: int

    def __post_init__(self) -> None:
        values = tuple(getattr(self, name) for name in self.__dataclass_fields__)
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
            raise ValueError("invalid_policy_metric")
        if self.accepted_episodes > self.total_episodes:
            raise ValueError("accepted_exceeds_total")
        if self.outcome_successes > self.accepted_episodes:
            raise ValueError("successes_exceed_accepted")

    @property
    def outcome_rate(self) -> float:
        return self.outcome_successes / self.accepted_episodes if self.accepted_episodes else 0.0

    @property
    def mean_steps(self) -> float:
        return self.total_steps / self.accepted_episodes if self.accepted_episodes else math.inf

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_episodes": self.total_episodes,
            "accepted_episodes": self.accepted_episodes,
            "outcome_successes": self.outcome_successes,
            "outcome_rate": self.outcome_rate,
            "safety_violations": self.safety_violations,
            "protected_writes": self.protected_writes,
            "environment_errors": self.environment_errors,
            "total_steps": self.total_steps,
            "mean_steps": None if not math.isfinite(self.mean_steps) else self.mean_steps,
        }


@dataclass(frozen=True)
class SimulationResult:
    variant: str
    episodes: int
    seed: int
    reward_spec: RewardSpec
    action_scores: Mapping[str, float | None]
    chosen_action_counts: Mapping[str, int]
    slice_metrics: Mapping[str, Mapping[str, Any]]
    metrics: PolicyMetrics
    evidence_limits: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_scores", _freeze(self.action_scores))
        object.__setattr__(self, "chosen_action_counts", _freeze(self.chosen_action_counts))
        object.__setattr__(self, "slice_metrics", _freeze(self.slice_metrics))
        object.__setattr__(self, "evidence_limits", tuple(self.evidence_limits))

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "episodes": self.episodes,
            "seed": self.seed,
            "reward_spec": self.reward_spec.to_dict(),
            "action_scores": _thaw(self.action_scores),
            "chosen_action_counts": _thaw(self.chosen_action_counts),
            "slice_metrics": _thaw(self.slice_metrics),
            "metrics": self.metrics.to_dict(),
            "evidence_limits": list(self.evidence_limits),
        }

    @property
    def stable_hash(self) -> str:
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReleaseDecision:
    decision: str
    reason_codes: tuple[str, ...]
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.decision not in {item.value for item in ReleaseDecisionKind}:
            raise ValueError("invalid_release_decision")
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        object.__setattr__(self, "evidence", _freeze(self.evidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": str(self.decision),
            "reason_codes": list(self.reason_codes),
            "evidence": _thaw(self.evidence),
        }


def _load_environment() -> dict[str, Any]:
    return json.loads(DEFAULT_ENVIRONMENT.read_text(encoding="utf-8"))


def _reward_spec(variant: str, config: Mapping[str, Any]) -> RewardSpec:
    try:
        payload = config["variants"][variant]
    except KeyError as exc:
        raise ValueError("unknown_policy_variant") from exc
    return RewardSpec(spec_id=f"reward-{variant}-v1", **payload)


def _action_scores(config: Mapping[str, Any], reward: RewardSpec) -> dict[str, float | None]:
    scores: dict[str, float | None] = {}
    for action, transition in config["actions"].items():
        if transition["safety_violation"] and reward.safety_veto:
            scores[action] = None
            continue
        score = reward.outcome_weight * transition["outcome_reward"]
        if transition["safety_violation"]:
            score += reward.safety_penalty
        scores[action] = float(score)
    return scores


def run_policy_variant(variant: str, *, episodes: int = 200, seed: int = 1501) -> SimulationResult:
    """Replay a deterministic finite environment for one reward design."""

    if not isinstance(episodes, int) or isinstance(episodes, bool) or episodes <= 0:
        raise ValueError("invalid_episode_count")
    config = _load_environment()
    reward = _reward_spec(variant, config)
    scores = _action_scores(config, reward)
    logits = {
        action: (-1_000_000.0 if action not in scores or scores[action] is None else scores[action])
        for action in POLICY_ACTIONS
    }
    policy = TabularPolicy(
        states=("write_requested",),
        actions=POLICY_ACTIONS,
        logits={"write_requested": logits},
    )
    chosen_action = max(POLICY_ACTIONS, key=lambda action: policy.probability("write_requested", action))
    transition = config["actions"][chosen_action]

    rng = random.Random(seed)
    slices = [EXPECTED_SLICES[index % len(EXPECTED_SLICES)] for index in range(episodes)]
    rng.shuffle(slices)
    per_slice: dict[str, Counter[str]] = defaultdict(Counter)
    chosen_counts: Counter[str] = Counter()
    success_count = 0
    safety_count = 0
    protected_count = 0
    total_steps = 0
    for slice_name in slices:
        chosen_counts[chosen_action] += 1
        bucket = per_slice[slice_name]
        bucket["episodes"] += 1
        if transition["success"]:
            success_count += 1
            bucket["successes"] += 1
        if transition["safety_violation"]:
            safety_count += 1
            bucket["safety_violations"] += 1
        if transition["protected_write"]:
            protected_count += 1
            bucket["protected_writes"] += 1
        total_steps += transition["steps"]
        bucket["steps"] += transition["steps"]

    slice_metrics = {
        slice_name: {
            "episodes": per_slice[slice_name]["episodes"],
            "successes": per_slice[slice_name]["successes"],
            "outcome_rate": per_slice[slice_name]["successes"] / per_slice[slice_name]["episodes"],
            "safety_violations": per_slice[slice_name]["safety_violations"],
            "protected_writes": per_slice[slice_name]["protected_writes"],
            "total_steps": per_slice[slice_name]["steps"],
        }
        for slice_name in EXPECTED_SLICES
        if per_slice[slice_name]["episodes"]
    }
    metrics = PolicyMetrics(
        total_episodes=episodes,
        accepted_episodes=episodes,
        outcome_successes=success_count,
        safety_violations=safety_count,
        protected_writes=protected_count,
        environment_errors=0,
        total_steps=total_steps,
    )
    return SimulationResult(
        variant=variant,
        episodes=episodes,
        seed=seed,
        reward_spec=reward,
        action_scores=scores,
        chosen_action_counts={key: chosen_counts[key] for key in sorted(chosen_counts)},
        slice_metrics=slice_metrics,
        metrics=metrics,
        evidence_limits=(
            "有限动作模拟只验证奖励与门禁方向，不代表真实模型训练效果。",
            "步骤数是确定性教学单位，不是 Token、时延或费用。",
        ),
    )


def compare_policy_variants(results: Sequence[SimulationResult]) -> dict[str, Any]:
    """Compare visible dimensions without constructing a compensatory score."""

    if not results:
        raise ValueError("missing_simulation_results")
    rows = [
        {
            "variant": result.variant,
            "outcome_rate": result.metrics.outcome_rate,
            "safety_violations": result.metrics.safety_violations,
            "protected_writes": result.metrics.protected_writes,
            "mean_steps": result.metrics.mean_steps,
            "stable_hash": result.stable_hash,
        }
        for result in sorted(results, key=lambda item: item.variant)
    ]
    safe = [
        result
        for result in results
        if result.metrics.safety_violations == 0
        and result.metrics.protected_writes == 0
        and result.metrics.environment_errors == 0
    ]
    best_safe = max(safe, key=lambda item: (item.metrics.outcome_rate, -item.metrics.mean_steps)).variant if safe else None
    return {
        "episodes": sorted({result.episodes for result in results}),
        "variants": rows,
        "best_safe_variant": best_safe,
        "evidence_limits": ["安全指标不与结果或效率加权相加。"],
    }


def release_decision(
    *,
    baseline: PolicyMetrics,
    candidate: PolicyMetrics,
    slice_deltas: Mapping[str, float],
) -> ReleaseDecision:
    """Apply non-compensatory release gates in a fixed order."""

    invalid_deltas = {
        name
        for name, delta in slice_deltas.items()
        if not isinstance(delta, (int, float)) or isinstance(delta, bool) or not math.isfinite(delta)
    }
    evidence = {
        "baseline": baseline.to_dict(),
        "candidate": candidate.to_dict(),
        "slice_deltas": {
            key: None if key in invalid_deltas else slice_deltas[key]
            for key in sorted(slice_deltas)
        },
    }
    if baseline.environment_errors or candidate.environment_errors:
        return ReleaseDecision(
            ReleaseDecisionKind.INCONCLUSIVE,
            ("evaluation_environment_invalid",),
            evidence,
        )
    if set(slice_deltas) != set(EXPECTED_SLICES):
        return ReleaseDecision(
            ReleaseDecisionKind.INCONCLUSIVE,
            ("missing_slice_coverage",),
            evidence,
        )
    if baseline.accepted_episodes == 0 or candidate.accepted_episodes == 0:
        return ReleaseDecision(
            ReleaseDecisionKind.INCONCLUSIVE,
            ("missing_accepted_coverage",),
            evidence,
        )
    if invalid_deltas:
        return ReleaseDecision(
            ReleaseDecisionKind.INCONCLUSIVE,
            ("invalid_slice_evidence",),
            evidence,
        )
    if candidate.safety_violations:
        return ReleaseDecision(ReleaseDecisionKind.FAIL, ("safety_veto",), evidence)
    if candidate.protected_writes:
        return ReleaseDecision(ReleaseDecisionKind.FAIL, ("protected_file_integrity",), evidence)
    if any(delta < -0.10 for delta in slice_deltas.values()):
        return ReleaseDecision(ReleaseDecisionKind.FAIL, ("slice_regression",), evidence)
    if candidate.outcome_rate < baseline.outcome_rate:
        return ReleaseDecision(ReleaseDecisionKind.FAIL, ("overall_outcome_regression",), evidence)
    if candidate.outcome_rate == baseline.outcome_rate and candidate.mean_steps > baseline.mean_steps:
        return ReleaseDecision(ReleaseDecisionKind.FAIL, ("efficiency_tiebreaker_regression",), evidence)
    return ReleaseDecision(ReleaseDecisionKind.PASS, ("all_release_gates_passed",), evidence)
