"""Small, dependency-free reliability statistics used by the experiments."""
from __future__ import annotations

from math import comb
import random


def _validate(n: int, c: int, k: int) -> None:
    if n < 0 or c < 0 or c > n:
        raise ValueError("invalid_trial_counts")
    if k <= 0 or k > n:
        raise ValueError("invalid_k")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased probability estimate that at least one of k samples passes."""
    _validate(n, c, k)
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_all_k(n: int, c: int, k: int) -> float:
    """Unbiased probability estimate that all k samples pass (pass^k)."""
    _validate(n, c, k)
    if c < k:
        return 0.0
    return comb(c, k) / comb(n, k)


def _percentile(values: list[float], proportion: float) -> float:
    index = round((len(values) - 1) * proportion)
    return values[index]


def bootstrap_paired_delta(
    baseline: dict[str, float], candidate: dict[str, float], *,
    iterations: int = 10_000, seed: int = 20260924,
) -> dict[str, float | int]:
    if set(baseline) != set(candidate) or not baseline:
        raise ValueError("paired_task_ids_mismatch")
    if iterations <= 0:
        raise ValueError("invalid_iterations")
    task_ids = sorted(baseline)
    deltas = [candidate[key] - baseline[key] for key in task_ids]
    rng = random.Random(seed)
    samples = []
    for _ in range(iterations):
        samples.append(sum(rng.choice(deltas) for _ in deltas) / len(deltas))
    samples.sort()
    return {
        "estimate": round(sum(deltas) / len(deltas), 6),
        "lower": round(_percentile(samples, 0.025), 6),
        "upper": round(_percentile(samples, 0.975), 6),
        "iterations": iterations,
        "seed": seed,
    }


def heterogeneous_bootstrap_example() -> dict[str, object]:
    """A fixed, non-degenerate teaching contrast excluded from release metrics."""
    baseline = {f"task-{index:02d}": 0.6 for index in range(12)}
    deltas = (0.2, 0.2, 0.2, 0.1, 0.1, 0.0, 0.0, -0.1, -0.1, -0.2, -0.2, 0.0)
    candidate = {key: baseline[key] + delta for key, delta in zip(baseline, deltas)}
    confidence = bootstrap_paired_delta(baseline, candidate)
    return {
        "task_deltas": list(deltas),
        "paired_confidence": confidence,
        "interpretation": ("inconclusive"
                           if confidence["lower"] < 0 <= confidence["upper"] else "decisive"),
        "scored_in_release": False,
    }
