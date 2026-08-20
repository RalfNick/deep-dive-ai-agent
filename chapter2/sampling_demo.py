"""用固定 logits 观察 greedy、temperature、top-p 与 seed 的边界。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


LOGITS = {
    "run_tests": 2.2,
    "read_file": 2.0,
    "apply_patch": 1.5,
    "explain": 1.1,
    "delete_tests": 0.5,
}
SAFE_FIRST_ACTIONS = {"run_tests", "read_file"}


@dataclass(frozen=True)
class SamplingConfig:
    name: str
    temperature: float | None
    top_p: float | None = None


CONFIGS = (
    SamplingConfig("greedy", None),
    SamplingConfig("temp=0.3", 0.3),
    SamplingConfig("temp=1.0", 1.0),
    SamplingConfig("temp=1.0, top_p=0.70", 1.0, 0.70),
)


def probabilities(temperature: float) -> dict[str, float]:
    if temperature <= 0:
        raise ValueError("temperature must be positive; use greedy for argmax")
    scaled = {token: logit / temperature for token, logit in LOGITS.items()}
    offset = max(scaled.values())
    weights = {token: math.exp(value - offset) for token, value in scaled.items()}
    total = sum(weights.values())
    return {token: value / total for token, value in weights.items()}


def nucleus_filter(distribution: dict[str, float], top_p: float) -> dict[str, float]:
    if not 0 < top_p <= 1:
        raise ValueError("top_p must be in (0, 1]")
    kept: dict[str, float] = {}
    cumulative = 0.0
    for token, probability in sorted(
        distribution.items(), key=lambda item: item[1], reverse=True
    ):
        kept[token] = probability
        cumulative += probability
        if cumulative >= top_p:
            break
    total = sum(kept.values())
    return {token: probability / total for token, probability in kept.items()}


def draw(distribution: dict[str, float], rng: random.Random) -> str:
    tokens = list(distribution)
    return rng.choices(tokens, weights=distribution.values(), k=1)[0]


def run(config: SamplingConfig, draws: int, seed: int) -> tuple[dict[str, int], float]:
    if config.temperature is None:
        winner = max(LOGITS, key=LOGITS.get)  # type: ignore[arg-type]
        counts = {token: draws if token == winner else 0 for token in LOGITS}
    else:
        distribution = probabilities(config.temperature)
        if config.top_p is not None:
            distribution = nucleus_filter(distribution, config.top_p)
        rng = random.Random(seed)
        counts = {token: 0 for token in LOGITS}
        for _ in range(draws):
            counts[draw(distribution, rng)] += 1
    safe_rate = sum(counts[token] for token in SAFE_FIRST_ACTIONS) / draws
    return counts, safe_rate


def main() -> None:
    draws = 20_000
    seed = 20_260_809
    print(f"fixed logits={LOGITS}")
    print(f"draws={draws} seed={seed}\n")
    print("config                     unique  safe-first  distribution")
    print("-------------------------  ------  ----------  ------------")
    for config in CONFIGS:
        counts, safe_rate = run(config, draws, seed)
        nonzero = sum(count > 0 for count in counts.values())
        summary = ", ".join(
            f"{token}:{counts[token] / draws:.3f}"
            for token in sorted(counts, key=counts.get, reverse=True)  # type: ignore[arg-type]
            if counts[token]
        )
        print(f"{config.name:<25}  {nonzero:>6}  {safe_rate:>10.3f}  {summary}")

    print("\n观察 1：低温度集中既有概率，不会把错误候选自动变正确。")
    print("观察 2：top-p 先截断候选集合，再在保留集合内重新归一化。")
    print("边界：seed 只固定本地随机数；真实 API 的可复现性取决于模型、版本和服务。")


if __name__ == "__main__":
    main()
