"""Contrast model-owned completion with environment-owned acceptance."""

from __future__ import annotations

from agent_loop import (
    AgentLoop,
    BROKEN_SOURCE,
    Decision,
    Event,
    FIXED_SOURCE,
    PriceRepo,
    ToolCall,
    print_trace,
)


class PrematurePolicy:
    def decide(self, events: list[Event]) -> Decision:
        verification = [event for event in events if event.kind == "verification"]
        calls = [event.data["name"] for event in events if event.kind == "tool_call"]
        if not verification:
            return Decision("final", "代码看起来很简单，我宣布完成。", final="已修复。")
        if "apply_patch" not in calls:
            return Decision(
                "tool",
                "验收器拒绝了声明，执行实际修改。",
                ToolCall(
                    "repair-after-reject",
                    "apply_patch",
                    {"path": "pricing.py", "old": BROKEN_SOURCE, "new": FIXED_SOURCE},
                ),
            )
        if "run_tests" not in calls:
            return Decision(
                "tool",
                "用测试建立完成证据。",
                ToolCall("verify-after-repair", "run_tests", {}),
            )
        return Decision("final", "修改存在且测试已通过。", final="修复并验证完成。")


def main() -> None:
    print("[naive runner: accepts self-report]")
    with PriceRepo() as repo:
        naive = AgentLoop(repo).run(PrematurePolicy())
        print_trace(naive)
        print(f"tests_pass={repo.tests_pass()}")
        assert naive.status == "completed" and not repo.tests_pass()

    print("\n[verified runner: rejects, repairs, then accepts]")
    with PriceRepo() as repo:
        verified = AgentLoop(
            repo, completion_verifier=repo.verify_completion
        ).run(PrematurePolicy())
        print_trace(verified)
        print(f"tests_pass={repo.tests_pass()}")
        assert verified.status == "completed" and repo.tests_pass()


if __name__ == "__main__":
    main()
