from __future__ import annotations

import unittest

from chapter4.harness.gateway import ActionGateway, GatewayDecisionKind
from chapter5.context.contracts import DecisionKind
from chapter5.gateway_adapter import ToolCallFactory, evaluate_proposal
from chapter5.probes import ProbeDecision, ToolProposal


def _patch_decision(path: str) -> ProbeDecision:
    return ProbeDecision(
        kind=DecisionKind.TOOL,
        tool=ToolProposal(
            name="apply_patch",
            arguments={"path": path, "old": "bad", "new": "good"},
        ),
    )


class GatewayAdapterTest(unittest.TestCase):
    def test_factory_ignores_model_supplied_identifier_fields(self) -> None:
        proposal = ToolProposal(
            name="apply_patch",
            arguments={
                "path": "pricing.py",
                "old": "bad",
                "new": "good",
                "call_id": "model-call",
                "action_id": "model-action",
            },
        )

        call = ToolCallFactory().create("run-7", 2, proposal)

        self.assertNotEqual("model-call", call.call_id)
        self.assertNotEqual("model-action", call.action_id)
        self.assertNotIn("call_id", call.arguments)
        self.assertNotIn("action_id", call.arguments)
        self.assertEqual(call, ToolCallFactory().create("run-7", 2, proposal))

    def test_retry_changes_call_id_but_preserves_semantic_action_id(self) -> None:
        proposal = ToolProposal(
            name="apply_patch",
            arguments={"path": "pricing.py", "old": "bad", "new": "good"},
        )

        first = ToolCallFactory().create("run-7", 1, proposal)
        retry = ToolCallFactory().create("run-7", 2, proposal)

        self.assertNotEqual(first.call_id, retry.call_id)
        self.assertEqual(first.action_id, retry.action_id)

    def test_hostile_path_proposal_is_denied_by_existing_gateway(self) -> None:
        observation = evaluate_proposal(
            _patch_decision(".env"),
            run_id="run-8",
            ordinal=1,
            gateway=ActionGateway(),
        )

        self.assertEqual(GatewayDecisionKind.DENY, observation.decision.kind)
        self.assertEqual("protected_path", observation.decision.reason)

    def test_normal_patch_still_requires_chapter4_approval(self) -> None:
        observation = evaluate_proposal(
            _patch_decision("pricing.py"),
            run_id="run-9",
            ordinal=1,
            gateway=ActionGateway(),
        )

        self.assertEqual(GatewayDecisionKind.ASK, observation.decision.kind)
        self.assertEqual("side_effect_requires_approval", observation.decision.reason)

    def test_non_tool_decision_cannot_cross_action_boundary(self) -> None:
        with self.assertRaisesRegex(ValueError, "tool_decision_required"):
            evaluate_proposal(
                ProbeDecision(kind=DecisionKind.ANSWER, message="done"),
                run_id="run-10",
                ordinal=1,
                gateway=ActionGateway(),
            )


if __name__ == "__main__":
    unittest.main()
