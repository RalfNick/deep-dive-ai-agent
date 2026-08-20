from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_loop import (  # noqa: E402
    AgentLoop,
    Event,
    PriceRepo,
    RepairPolicy,
    RunResult,
)
from trace_audit import audit_trace  # noqa: E402


def call(step: int, call_id: str) -> Event:
    return Event(
        step,
        "tool_call",
        {"call_id": call_id, "name": "read_file", "arguments": {}},
    )


def result(step: int, call_id: str) -> Event:
    return Event(
        step,
        "tool_result",
        {
            "call_id": call_id,
            "ok": True,
            "content": "ok",
            "error_type": None,
            "retryable": False,
            "state_changed": False,
            "tool_name": "read_file",
        },
    )


class TraceAuditTest(unittest.TestCase):
    def test_normal_completed_run_has_a_complete_trace(self) -> None:
        with PriceRepo() as repo:
            run = AgentLoop(
                repo, completion_verifier=repo.verify_completion
            ).run(RepairPolicy())

        audit = audit_trace(run)

        self.assertTrue(audit.ok)
        self.assertEqual(audit.duplicate_call_ids, ())
        self.assertEqual(audit.missing_result_ids, ())

    def test_duplicate_calls_and_results_are_not_hidden_by_deduplication(self) -> None:
        run = RunResult(
            "failed",
            None,
            [call(1, "same"), result(1, "same"), call(2, "same"), result(2, "same")],
        )

        audit = audit_trace(run)

        self.assertEqual(audit.duplicate_call_ids, ("same",))
        self.assertEqual(audit.duplicate_result_ids, ("same",))
        self.assertFalse(audit.ok)

    def test_missing_and_orphan_results_are_reported(self) -> None:
        run = RunResult("failed", None, [call(1, "missing"), result(2, "orphan")])

        audit = audit_trace(run)

        self.assertEqual(audit.missing_result_ids, ("missing",))
        self.assertEqual(audit.orphan_result_ids, ("orphan",))
        self.assertFalse(audit.ok)

    def test_result_before_call_is_reported(self) -> None:
        run = RunResult("failed", None, [result(1, "late-call"), call(2, "late-call")])

        audit = audit_trace(run)

        self.assertEqual(audit.result_before_call_ids, ("late-call",))
        self.assertFalse(audit.ok)

    def test_completed_run_without_verification_breaks_completion_contract(self) -> None:
        run = RunResult(
            "completed",
            "done",
            [Event(1, "run_finished", {"status": "completed"})],
        )

        audit = audit_trace(run)

        self.assertFalse(audit.completion_contract_ok)
        self.assertFalse(audit.ok)


if __name__ == "__main__":
    unittest.main()
