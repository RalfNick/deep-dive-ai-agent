from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.contracts import (  # noqa: E402
    RunEvent,
    RunState,
    RunStatus,
    ToolCall,
    ToolResult,
)
from chapter4.harness.recorder import EventRecorder, grade_trace  # noqa: E402
from chapter4.harness.state import (  # noqa: E402
    ActionReceiptStore,
    JsonCheckpointStore,
)


def _waiting_state(run_id: str) -> RunState:
    return RunState(
        run_id=run_id,
        status=RunStatus.WAITING_APPROVAL,
        pending_call=ToolCall(
            call_id="call-patch-1",
            action_id="patch-price",
            name="apply_patch",
            arguments={"path": "pricing.py", "old": "bad", "new": "good"},
        ),
    )


def _ok_result(call_id: str) -> ToolResult:
    return ToolResult(
        call_id=call_id,
        action_id="patch-price",
        ok=True,
        output="patched",
        side_effect_applied=True,
    )


class StateAndRecorderTest(unittest.TestCase):
    def test_checkpoint_survives_new_store_instance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="chapter4-state-") as raw:
            root = Path(raw)
            first = JsonCheckpointStore(root)
            first.save(_waiting_state("run-7"))

            restored = JsonCheckpointStore(root).load("run-7")

        self.assertEqual(RunStatus.WAITING_APPROVAL, restored.status)
        self.assertEqual("patch-price", restored.pending_call.action_id)

    def test_receipt_store_uses_stable_action_id(self) -> None:
        with tempfile.TemporaryDirectory(prefix="chapter4-receipt-") as raw:
            receipts = ActionReceiptStore(Path(raw))
            receipts.record("patch-price", _ok_result("call-1"))

            restored = ActionReceiptStore(Path(raw)).get("patch-price")

        self.assertEqual("call-1", restored.call_id)
        self.assertTrue(restored.side_effect_applied)

    def test_recorder_emits_monotonic_event_ids_and_causes(self) -> None:
        recorder = EventRecorder("run-order")
        call = recorder.emit("tool_call", cause_id=None, call_id="call-1")
        result = recorder.emit(
            "tool_result", cause_id=call.event_id, call_id="call-1"
        )

        self.assertEqual(1, call.sequence)
        self.assertEqual(2, result.sequence)
        self.assertEqual(call.event_id, result.cause_id)

    def test_trace_requires_checkpoint_before_approval_request(self) -> None:
        reversed_events = (
            RunEvent("run:0001", "run", "approval_requested", 1),
            RunEvent("run:0002", "run", "checkpoint_saved", 2),
            RunEvent("run:0003", "run", "waiting_approval", 3),
        )

        grade = grade_trace(reversed_events)

        self.assertFalse(grade.complete)
        self.assertIn("checkpoint_before_approval", grade.missing_contracts)


if __name__ == "__main__":
    unittest.main()
