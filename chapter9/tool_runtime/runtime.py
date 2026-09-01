from __future__ import annotations

from chapter9.tool_runtime.contracts import (
    CallerContext,
    ExecutionReceipt,
    ResultStatus,
    RiskLevel,
    ToolCall,
    ToolResult,
    stable_digest,
)
from chapter9.tool_runtime.policy import PolicyEngine, PolicyOutcome
from chapter9.tool_runtime.registry import ToolRegistry
from chapter9.tool_runtime.schema import validate_arguments


class ToolRuntime:
    """Execute one proposal through identity, contract, policy, and receipt gates."""

    def __init__(self, registry: ToolRegistry, policy: PolicyEngine) -> None:
        self._registry = registry
        self._policy = policy
        self._seen_call_ids: set[str] = set()

    def execute(self, call: ToolCall, caller: CallerContext) -> ToolResult:
        if call.call_id in self._seen_call_ids:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.BUSINESS_ERROR,
                "duplicate_call_id",
                "同一运行中不得重复使用 call_id。",
            )
        self._seen_call_ids.add(call.call_id)

        definition = self._registry.definition(call.tool_name)
        if definition is None:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.BUSINESS_ERROR,
                "unknown_tool",
                f"未注册工具：{call.tool_name}",
            )

        issues = validate_arguments(definition.input_schema, call.arguments)
        if issues:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.INVALID_ARGUMENTS,
                "invalid_arguments",
                "工具参数不符合声明的合同。",
                issues=issues,
            )

        decision = self._policy.evaluate(definition, call, caller)
        if decision.outcome is PolicyOutcome.ASK:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.DENIED,
                "approval_required",
                "写工具需要由 Host 提供明确授权。",
            )
        if decision.outcome is PolicyOutcome.DENY:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.DENIED,
                "policy_denied",
                "当前策略拒绝执行该工具。",
            )

        result = self._registry.invoke(call)
        if result.status is not ResultStatus.SUCCEEDED:
            return result
        if definition.risk_level is RiskLevel.READ:
            return result

        external_id = result.data.get("ticket_id") if result.data is not None else None
        if not isinstance(external_id, str) or not external_id.strip():
            return ToolResult.failed(
                call.call_id,
                ResultStatus.EXECUTION_ERROR,
                "missing_external_id",
                "写工具未返回可验证的外部对象标识。",
            )

        action_payload = {
            "tool_name": call.tool_name,
            "arguments": call.arguments,
            "external_id": external_id,
        }
        receipt = ExecutionReceipt(
            action_id=f"action-{stable_digest(action_payload)[:16]}",
            tool_name=call.tool_name,
            arguments_digest=stable_digest(call.arguments),
            external_id=external_id,
            status="committed",
            occurred_at=caller.now,
        )
        return ToolResult.succeeded(call.call_id, result.data, receipt)
