from __future__ import annotations

from dataclasses import dataclass

from chapter9.tool_runtime.contracts import ToolCall, ToolResult, stable_digest


@dataclass(frozen=True, slots=True)
class TraceEvent:
    event_id: str
    event_type: str
    step_id: str | None = None
    call_id: str | None = None
    tool_name: str | None = None
    result_status: str | None = None
    error_code: str | None = None
    argument_digest: str | None = None
    action_id: str | None = None
    reason: str | None = None


class TraceRecorder:
    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    def _next_id(self) -> str:
        return f"event-{len(self._events) + 1:03d}"

    def record_call(self, call: ToolCall) -> None:
        self._events.append(
            TraceEvent(
                event_id=self._next_id(),
                event_type="tool_call",
                step_id=call.step_id,
                call_id=call.call_id,
                tool_name=call.tool_name,
                argument_digest=stable_digest(call.arguments),
            )
        )

    def record_result(self, call: ToolCall, result: ToolResult) -> None:
        self._events.append(
            TraceEvent(
                event_id=self._next_id(),
                event_type="tool_result",
                step_id=call.step_id,
                call_id=call.call_id,
                tool_name=call.tool_name,
                result_status=result.status.value,
                error_code=None if result.failure is None else result.failure.code,
                action_id=None if result.receipt is None else result.receipt.action_id,
            )
        )

    def record_final(self, *, status: str, reason: str) -> None:
        self._events.append(
            TraceEvent(
                event_id=self._next_id(),
                event_type="final_answer",
                result_status=status,
                reason=reason,
            )
        )

    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

