from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from chapter9.tool_runtime.contracts import (
    CallerContext,
    RiskLevel,
    ToolCall,
    ToolDefinition,
)


class PolicyOutcome(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    outcome: PolicyOutcome
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("policy reason must be non-blank")


class PolicyEngine:
    def evaluate(
        self,
        definition: ToolDefinition,
        call: ToolCall,
        caller: CallerContext,
    ) -> PolicyDecision:
        if definition.risk_level is RiskLevel.READ:
            return PolicyDecision(PolicyOutcome.ALLOW, "read_only")

        severity = str(call.arguments.get("severity", ""))
        scope = f"incident:create:{severity.casefold()}"
        if scope in caller.grants:
            return PolicyDecision(PolicyOutcome.ALLOW, "explicit_grant")
        return PolicyDecision(PolicyOutcome.ASK, f"missing_grant:{scope}")

