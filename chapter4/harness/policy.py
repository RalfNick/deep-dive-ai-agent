from __future__ import annotations

from collections.abc import Sequence

from .contracts import PolicyDecision, RunState, ToolCall


BROKEN_SOURCE = """def parse_price(text: str) -> float:
    return float(text)
"""

FIXED_SOURCE = """def parse_price(text: str) -> float:
    normalized = text.strip().replace("￥", "").replace("¥", "")
    return float(normalized)
"""


def canonical_repair_script() -> tuple[PolicyDecision, ...]:
    return (
        PolicyDecision.tool(
            ToolCall(
                call_id="call-read-1",
                action_id="read-price-file",
                name="read_file",
                arguments={"path": "pricing.py"},
            )
        ),
        PolicyDecision.tool(
            ToolCall(
                call_id="call-patch-1",
                action_id="patch-price",
                name="apply_patch",
                arguments={
                    "path": "pricing.py",
                    "old": BROKEN_SOURCE,
                    "new": FIXED_SOURCE,
                },
            )
        ),
        PolicyDecision.tool(
            ToolCall(
                call_id="call-test-1",
                action_id="run-price-tests",
                name="run_tests",
                arguments={},
            )
        ),
        PolicyDecision.final("价格解析问题已修复，测试已经通过。"),
    )


class ScriptedModel:
    """A deterministic stand-in that keeps all progress in RunState."""

    def __init__(self, decisions: Sequence[PolicyDecision]) -> None:
        self.decisions = tuple(decisions)

    def next_decision(self, state: RunState) -> PolicyDecision:
        if state.decision_index >= len(self.decisions):
            return PolicyDecision.final("决策脚本已经结束。")
        return self.decisions[state.decision_index]
