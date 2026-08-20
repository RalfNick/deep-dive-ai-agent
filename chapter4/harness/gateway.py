from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import ToolCall


class GatewayDecisionKind(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass(frozen=True)
class GatewayDecision:
    kind: GatewayDecisionKind
    reason: str


TOOL_ARGUMENTS: dict[str, frozenset[str]] = {
    "read_file": frozenset({"path"}),
    "apply_patch": frozenset({"path", "old", "new"}),
    "run_tests": frozenset(),
}


class ActionGateway:
    def __init__(
        self,
        *,
        require_approval_for_writes: bool = True,
        protected_paths: frozenset[str] = frozenset({".env", ".git"}),
    ) -> None:
        self.require_approval_for_writes = require_approval_for_writes
        self.protected_paths = protected_paths

    def evaluate(self, call: ToolCall) -> GatewayDecision:
        required = TOOL_ARGUMENTS.get(call.name)
        if required is None:
            return GatewayDecision(GatewayDecisionKind.DENY, "unknown_tool")
        if not required.issubset(call.arguments):
            return GatewayDecision(
                GatewayDecisionKind.DENY,
                "missing_required_arguments",
            )

        relative_path = str(call.arguments.get("path", "")).replace("\\", "/")
        first_part = relative_path.lower().split("/", maxsplit=1)[0]
        if first_part in self.protected_paths:
            return GatewayDecision(GatewayDecisionKind.DENY, "protected_path")

        if call.name == "apply_patch" and self.require_approval_for_writes:
            return GatewayDecision(
                GatewayDecisionKind.ASK,
                "side_effect_requires_approval",
            )
        return GatewayDecision(GatewayDecisionKind.ALLOW, "policy_allows")
