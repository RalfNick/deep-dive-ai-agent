from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.contracts import RunState, RunStatus, ToolCall  # noqa: E402
from chapter4.harness.policy import (  # noqa: E402
    ScriptedModel,
    canonical_repair_script,
)


class ContractsAndPolicyTest(unittest.TestCase):
    def test_canonical_script_is_deterministic(self) -> None:
        left = canonical_repair_script()
        right = canonical_repair_script()

        self.assertEqual(left, right)
        self.assertEqual("read-price-file", left[0].call.action_id)
        self.assertEqual("patch-price", left[1].call.action_id)

    def test_scripted_model_uses_state_cursor_without_hidden_memory(self) -> None:
        model = ScriptedModel(canonical_repair_script())
        state = RunState(run_id="run-policy")

        first = model.next_decision(state)
        state.decision_index = 1
        second = model.next_decision(state)

        self.assertEqual("read_file", first.call.name)
        self.assertEqual("apply_patch", second.call.name)

    def test_state_round_trip_preserves_pending_action(self) -> None:
        state = RunState(
            run_id="run-1",
            status=RunStatus.WAITING_APPROVAL,
            decision_index=2,
        )
        state.pending_call = ToolCall(
            call_id="call-2",
            action_id="patch-price",
            name="apply_patch",
            arguments={
                "path": "pricing.py",
                "old": "return float(text)",
                "new": "return float(text.replace('￥', ''))",
            },
        )

        restored = RunState.from_json(state.to_json())

        self.assertEqual(state, restored)
        self.assertEqual("patch-price", restored.pending_call.action_id)


if __name__ == "__main__":
    unittest.main()
