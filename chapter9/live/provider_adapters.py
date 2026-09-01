from __future__ import annotations

import json
from typing import Mapping

from chapter9.tool_runtime.contracts import ToolCall, ToolResult


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or blank provider field: {key}")
    return value


class OpenAIResponsesAdapter:
    def to_tool_call(self, item: Mapping[str, object], step_id: str) -> ToolCall:
        if item.get("type") != "function_call":
            raise ValueError("expected an OpenAI function_call item")
        raw_arguments = item.get("arguments")
        if not isinstance(raw_arguments, str):
            raise ValueError("OpenAI function_call arguments must be a JSON string")
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as error:
            raise ValueError("OpenAI function_call arguments are malformed JSON") from error
        if not isinstance(arguments, dict):
            raise ValueError("OpenAI function_call arguments must decode to an object")
        return ToolCall(
            call_id=_required_text(item, "call_id"),
            tool_name=_required_text(item, "name"),
            arguments=arguments,
            step_id=step_id,
        )

    def render_result(self, result: ToolResult) -> dict[str, object]:
        return {
            "type": "function_call_output",
            "call_id": result.call_id,
            "output": json.dumps(
                _model_visible_result(result),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        }


class AnthropicMessagesAdapter:
    def to_tool_call(self, block: Mapping[str, object], step_id: str) -> ToolCall:
        if block.get("type") != "tool_use":
            raise ValueError("expected an Anthropic tool_use block")
        arguments = block.get("input")
        if not isinstance(arguments, dict):
            raise ValueError("Anthropic tool_use input must be an object")
        return ToolCall(
            call_id=_required_text(block, "id"),
            tool_name=_required_text(block, "name"),
            arguments=dict(arguments),
            step_id=step_id,
        )

    def render_result(self, result: ToolResult) -> dict[str, object]:
        return {
            "type": "tool_result",
            "tool_use_id": result.call_id,
            "is_error": result.failure is not None,
            "content": json.dumps(
                _model_visible_result(result),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        }


def _model_visible_result(result: ToolResult) -> dict[str, object]:
    if result.failure is not None:
        return {
            "status": result.status.value,
            "error": {
                "code": result.failure.code,
                "message": result.failure.message,
                "retryable": result.failure.retryable,
            },
        }
    return {"status": result.status.value, "data": result.data}

