"""Show why an Agent needs more than a generous context window."""

from __future__ import annotations

from agent_loop import AgentLoop, Decision, Event, PriceRepo, ToolCall, print_trace


class StuckPolicy:
    def decide(self, events: list[Event]) -> Decision:
        index = 1 + sum(event.kind == "tool_call" for event in events)
        return Decision(
            "tool",
            "没有利用上一次观察，机械地再次读取同一文件。",
            ToolCall(f"repeat-{index}", "read_file", {"path": "pricing.py"}),
        )


def main() -> None:
    with PriceRepo() as repo:
        result = AgentLoop(repo, max_steps=20, max_same_action=2).run(StuckPolicy())
        print_trace(result)
        assert result.status == "repeated_action"
        assert result.tool_calls == 3
        assert not repo.tests_pass()


if __name__ == "__main__":
    main()
