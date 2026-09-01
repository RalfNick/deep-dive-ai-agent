from __future__ import annotations

from collections.abc import Callable, Mapping

from chapter9.tool_runtime.contracts import (
    DomainError,
    ResultStatus,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


ToolHandler = Callable[[Mapping[str, object]], Mapping[str, object]]


class ToolRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, tuple[ToolDefinition, ToolHandler]] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        if definition.name in self._entries:
            raise ValueError(f"duplicate tool: {definition.name}")
        self._entries[definition.name] = (definition, handler)

    def definition(self, name: str) -> ToolDefinition | None:
        entry = self._entries.get(name)
        return None if entry is None else entry[0]

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._entries[name][0] for name in sorted(self._entries))

    def invoke(self, call: ToolCall) -> ToolResult:
        entry = self._entries.get(call.tool_name)
        if entry is None:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.BUSINESS_ERROR,
                "unknown_tool",
                f"未注册工具：{call.tool_name}",
            )

        _, handler = entry
        try:
            data = handler(call.arguments)
            if not isinstance(data, Mapping):
                raise TypeError("tool handler must return a mapping")
            return ToolResult.succeeded(call.call_id, dict(data))
        except DomainError as error:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.BUSINESS_ERROR,
                error.code,
                error.message,
                retryable=error.retryable,
            )
        except Exception:
            return ToolResult.failed(
                call.call_id,
                ResultStatus.EXECUTION_ERROR,
                "tool_execution_failed",
                "工具执行失败，详细信息仅保留在受保护日志中。",
            )
