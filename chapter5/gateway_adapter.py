from __future__ import annotations

from dataclasses import dataclass

from chapter4.harness.contracts import ToolCall
from chapter4.harness.gateway import ActionGateway, GatewayDecision

from .context.contracts import DecisionKind
from .context.trace import stable_digest
from .probes import ProbeDecision, ToolProposal


@dataclass(frozen=True)
class GatewayObservation:
    call: ToolCall
    decision: GatewayDecision


class ToolCallFactory:
    """Create Harness-owned identifiers from a model's untrusted proposal."""

    def create(self, run_id: str, ordinal: int, proposal: ToolProposal) -> ToolCall:
        arguments = {
            str(key): value
            for key, value in proposal.arguments.items()
            if key not in {"call_id", "action_id"}
        }
        semantic_action = {"name": proposal.name, "arguments": arguments}
        action_id = f"action-{stable_digest(semantic_action)[:20]}"
        call_identity = {
            "run_id": run_id,
            "ordinal": ordinal,
            "action": semantic_action,
        }
        call_id = f"call-{stable_digest(call_identity)[:20]}"
        return ToolCall(
            call_id=call_id,
            action_id=action_id,
            name=proposal.name,
            arguments=arguments,
        )


def evaluate_proposal(
    decision: ProbeDecision,
    *,
    run_id: str,
    ordinal: int,
    gateway: ActionGateway,
) -> GatewayObservation:
    if decision.kind is not DecisionKind.TOOL or decision.tool is None:
        raise ValueError("tool_decision_required")
    call = ToolCallFactory().create(run_id, ordinal, decision.tool)
    return GatewayObservation(call=call, decision=gateway.evaluate(call))
