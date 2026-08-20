from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_loop import (  # noqa: E402
    BROKEN_SOURCE,
    Decision,
    Event,
    FIXED_SOURCE,
    TEST_SOURCE,
    AgentLoop,
    PriceRepo,
    RepairPolicy,
    ToolCall,
    ToolResult,
)
from loop_guards_demo import StuckPolicy  # noqa: E402
from verifier_demo import PrematurePolicy  # noqa: E402


class DuplicateIdPolicy:
    def decide(self, events: list[Event]) -> Decision:
        calls = [event for event in events if event.kind == "tool_call"]
        if not calls:
            return Decision(
                "tool",
                "先读取文件。",
                ToolCall("same-id", "read_file", {"path": "pricing.py"}),
            )
        if len(calls) == 1:
            return Decision(
                "tool",
                "错误地复用调用 ID。",
                ToolCall(
                    "same-id",
                    "apply_patch",
                    {
                        "path": "pricing.py",
                        "old": BROKEN_SOURCE,
                        "new": FIXED_SOURCE,
                    },
                ),
            )
        return Decision("final", "错误地宣布完成。", final="完成")


class TimeoutRepo(PriceRepo):
    def run_tests(self) -> ToolResult:
        raise subprocess.TimeoutExpired(
            [sys.executable, "-m", "unittest"], 10
        )


class AgentLoopTest(unittest.TestCase):
    def test_subprocess_timeout_becomes_typed_retryable_result(self) -> None:
        with TimeoutRepo() as repo:
            result = repo.execute(ToolCall("timeout-1", "run_tests", {}))

        self.assertFalse(result.ok)
        self.assertEqual(result.error_type, "tool_timeout")
        self.assertTrue(result.retryable)
        self.assertEqual(result.call_id, "timeout-1")

    def test_duplicate_call_id_is_rejected_before_second_side_effect(self) -> None:
        with PriceRepo() as repo:
            before = repo.state_digest()
            result = AgentLoop(repo).run(DuplicateIdPolicy())
            after = repo.state_digest()

        duplicate_results = [
            event
            for event in result.events
            if event.kind == "tool_result"
            and event.data.get("error_type") == "duplicate_call_id"
        ]
        self.assertEqual(result.status, "duplicate_call_id")
        self.assertEqual(len(duplicate_results), 1)
        self.assertFalse(duplicate_results[0].data["state_changed"])
        self.assertEqual(after, before)

    def test_fixed_source_rejects_an_internal_currency_symbol(self) -> None:
        namespace: dict[str, object] = {}
        exec(FIXED_SOURCE, namespace)
        parse_price = namespace["parse_price"]

        with self.assertRaises(ValueError):
            parse_price("1¥2")  # type: ignore[operator]

    def test_different_initial_source_is_repaired_from_observation(self) -> None:
        source = '''def parse_price(value: str) -> float:
    """Parse a price after trimming outer whitespace."""
    return float(value.strip())
'''
        with PriceRepo(pricing_source=source) as repo:
            result = AgentLoop(
                repo, completion_verifier=repo.verify_completion
            ).run(RepairPolicy())
            verification = repo.verify_completion()

        self.assertEqual(result.status, "completed")
        self.assertTrue(verification.accepted)

    def test_unrelated_failure_stops_without_editing_source(self) -> None:
        unrelated_test_source = TEST_SOURCE + '''

class UnrelatedTest(unittest.TestCase):
    def test_unrelated_failure(self) -> None:
        self.fail("independent failure")
'''
        with PriceRepo(test_source=unrelated_test_source) as repo:
            before = (repo.root / "pricing.py").read_text(encoding="utf-8")
            result = AgentLoop(
                repo, completion_verifier=repo.verify_completion
            ).run(RepairPolicy())
            after = (repo.root / "pricing.py").read_text(encoding="utf-8")

        self.assertEqual(result.status, "failed")
        self.assertEqual(after, before)

    def test_tampered_test_file_cannot_verify_broken_source(self) -> None:
        passing_but_tampered = TEST_SOURCE.replace(
            'parse_price("\\uffe519.90")', 'parse_price("19.90")'
        )
        with PriceRepo() as repo:
            patch_result = repo.apply_patch(
                "test_pricing.py", TEST_SOURCE, passing_but_tampered
            )
            verification = repo.verify_completion()

        self.assertTrue(patch_result.ok)
        self.assertFalse(verification.accepted)
        self.assertFalse(verification.protected_files_unchanged)

    def test_repair_loop_changes_environment_and_passes_tests(self) -> None:
        with PriceRepo() as repo:
            before = repo.state_digest()
            result = AgentLoop(
                repo, completion_verifier=repo.verify_completion
            ).run(RepairPolicy())
            self.assertEqual(result.status, "completed")
            self.assertNotEqual(before, repo.state_digest())
            self.assertTrue(repo.tests_pass())
            kinds = [event.kind for event in result.events]
            verification = next(
                event for event in result.events if event.kind == "verification"
            )
            self.assertIn("tests_passed", verification.data["rules"])
            self.assertIn("state_digest", verification.data)
            self.assertLess(
                kinds.index("verification"), kinds.index("run_finished")
            )

    def test_call_results_keep_their_call_id(self) -> None:
        with PriceRepo() as repo:
            result = AgentLoop(repo).run(RepairPolicy())
        calls = {
            event.data["call_id"]
            for event in result.events
            if event.kind == "tool_call"
        }
        results = {
            event.data["call_id"]
            for event in result.events
            if event.kind == "tool_result"
        }
        self.assertEqual(calls, results)

    def test_repeated_action_guard_stops_a_stuck_policy(self) -> None:
        with PriceRepo() as repo:
            result = AgentLoop(repo, max_steps=20, max_same_action=2).run(
                StuckPolicy()
            )
        self.assertEqual(result.status, "repeated_action")
        self.assertEqual(result.tool_calls, 3)

    def test_unknown_tool_becomes_typed_observation(self) -> None:
        from agent_loop import ToolCall

        with PriceRepo() as repo:
            result = repo.execute(ToolCall("missing-1", "does_not_exist", {}))
        self.assertFalse(result.ok)
        self.assertEqual(result.error_type, "tool_not_found")
        self.assertEqual(result.call_id, "missing-1")

    def test_path_escape_is_rejected(self) -> None:
        from agent_loop import ToolCall

        with PriceRepo() as repo:
            result = repo.execute(
                ToolCall("escape-1", "read_file", {"path": "../secret.txt"})
            )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_type, "invalid_arguments")

    def test_verifier_rejects_premature_completion(self) -> None:
        with PriceRepo() as repo:
            result = AgentLoop(
                repo, completion_verifier=repo.verify_completion
            ).run(PrematurePolicy())
            rejected = [
                event
                for event in result.events
                if event.kind == "verification" and not event.data["accepted"]
            ]
            self.assertTrue(rejected)
            self.assertTrue(repo.tests_pass())


if __name__ == "__main__":
    unittest.main()
