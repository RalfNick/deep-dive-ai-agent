"""先应用任务/安全硬门槛，再计算不同工作负载下的 Pareto 前沿。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    name: str
    simple_success: float
    hard_success: float
    tool_success: float
    safety_pass: float
    cost_per_1k: float
    p95_latency_s: float
    rpm_capacity: int


@dataclass(frozen=True)
class Scenario:
    weights: tuple[float, float, float]
    min_simple: float
    min_hard: float
    min_tool: float
    min_safety: float
    max_cost: float
    max_latency: float
    min_rpm: int


MODELS = (
    ModelProfile("swift", 0.94, 0.48, 0.80, 0.995, 0.18, 0.7, 2200),
    ModelProfile("balanced", 0.96, 0.72, 0.91, 0.998, 0.65, 1.5, 1200),
    ModelProfile("frontier", 0.98, 0.88, 0.95, 0.999, 2.40, 3.8, 520),
    ModelProfile("deliberate", 0.97, 0.93, 0.96, 0.999, 5.20, 11.0, 180),
    ModelProfile("legacy", 0.90, 0.55, 0.72, 0.982, 1.10, 2.8, 600),
)


SCENARIOS = {
    "support": Scenario(
        weights=(0.75, 0.10, 0.15),
        min_simple=0.95,
        min_hard=0.65,
        min_tool=0.88,
        min_safety=0.997,
        max_cost=3.00,
        max_latency=4.0,
        min_rpm=500,
    ),
    "coding-agent": Scenario(
        weights=(0.15, 0.45, 0.40),
        min_simple=0.95,
        min_hard=0.85,
        min_tool=0.94,
        min_safety=0.999,
        max_cost=6.00,
        max_latency=12.0,
        min_rpm=150,
    ),
}


def score(model: ModelProfile, weights: tuple[float, float, float]) -> float:
    return sum(
        value * weight
        for value, weight in zip(
            (model.simple_success, model.hard_success, model.tool_success), weights
        )
    )


def gate_failures(model: ModelProfile, scenario: Scenario) -> list[str]:
    failures = []
    if model.simple_success < scenario.min_simple:
        failures.append("simple")
    if model.hard_success < scenario.min_hard:
        failures.append("hard")
    if model.tool_success < scenario.min_tool:
        failures.append("tool")
    if model.safety_pass < scenario.min_safety:
        failures.append("safety")
    if model.cost_per_1k > scenario.max_cost:
        failures.append("cost")
    if model.p95_latency_s > scenario.max_latency:
        failures.append("latency")
    if model.rpm_capacity < scenario.min_rpm:
        failures.append("capacity")
    return failures


def dominates(a: ModelProfile, b: ModelProfile, scenario: Scenario) -> bool:
    """门槛之后才允许把非关键任务表现压成工作负载分数。"""
    a_score, b_score = score(a, scenario.weights), score(b, scenario.weights)
    no_worse = (
        a_score >= b_score
        and a.cost_per_1k <= b.cost_per_1k
        and a.p95_latency_s <= b.p95_latency_s
    )
    strictly_better = (
        a_score > b_score
        or a.cost_per_1k < b.cost_per_1k
        or a.p95_latency_s < b.p95_latency_s
    )
    return no_worse and strictly_better


def pareto_frontier(models: tuple[ModelProfile, ...], scenario: Scenario) -> set[str]:
    feasible = tuple(model for model in models if not gate_failures(model, scenario))
    return {
        model.name
        for model in feasible
        if not any(
            dominates(other, model, scenario) for other in feasible if other != model
        )
    }


def main() -> None:
    for scenario_name, scenario in SCENARIOS.items():
        frontier = pareto_frontier(MODELS, scenario)
        print(f"\nscenario={scenario_name} weights={scenario.weights}")
        print("model       score   safety cost/1k p95(s) rpm   gate/pareto")
        print("----------- ------- ------ ------- ------ ----- ----------------")
        for model in MODELS:
            failures = gate_failures(model, scenario)
            status = "gate:" + ",".join(failures) if failures else (
                "pareto" if model.name in frontier else "dominated"
            )
            print(
                f"{model.name:<11} {score(model, scenario.weights):>7.4f} "
                f"{model.safety_pass:>6.3f} {model.cost_per_1k:>7.2f} "
                f"{model.p95_latency_s:>6.1f} {model.rpm_capacity:>5} {status}"
            )

    print("\n观察：关键任务、安全、预算与容量先过硬门槛，之后才比较 Pareto 取舍。")
    print("边界：示例数据是教学夹具，不能用于比较任何真实厂商或型号。")


if __name__ == "__main__":
    main()
