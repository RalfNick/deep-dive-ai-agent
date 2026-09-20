"""Small OpenAI-compatible Chat Completions protocol adapter."""
from __future__ import annotations

import copy
import json
from typing import Any

from ..contracts import Record, TOOL_SCHEMAS, validate_call


def _plain(value: Any) -> Record:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            return dumped
    raise ValueError("invalid_response")


def parse_response(value: Record) -> Record:
    value = _plain(value)
    choices = value.get("choices")
    if type(choices) is not list or len(choices) != 1 or type(choices[0]) is not dict:
        raise ValueError("empty_response")
    choice = choices[0]
    if choice.get("finish_reason") == "length":
        raise ValueError("truncated_response")
    message = choice.get("message")
    if type(message) is not dict:
        raise ValueError("empty_response")
    if message.get("refusal"):
        raise ValueError("model_refusal")
    calls = message.get("tool_calls") or []
    if type(calls) is not list:
        raise ValueError("invalid_tool_call")
    if len(calls) > 1:
        raise ValueError("multiple_tool_calls")
    if calls:
        call = calls[0]
        if type(call) is not dict or call.get("type") != "function":
            raise ValueError("invalid_tool_call")
        function = call.get("function")
        if type(function) is not dict:
            raise ValueError("invalid_tool_call")
        try:
            arguments = json.loads(function.get("arguments", ""))
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("invalid_arguments") from error
        try:
            normalized = validate_call({"call_id": call.get("id"),
                                        "name": function.get("name"),
                                        "arguments": arguments})
        except ValueError as error:
            if "call_id" in str(error):
                raise ValueError("invalid_call_id") from error
            raise
        return {"kind": "tool", "text": "", "call": normalized}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty_response")
    if choice.get("finish_reason") not in (None, "stop"):
        raise ValueError("model_response_incomplete")
    return {"kind": "final", "text": content, "call": None}


def _tool_descriptions() -> list[Record]:
    descriptions = {
        "read_file": "Read a bounded line range and its current version.",
        "search": "Search literal text in a bounded workspace directory.",
        "apply_patch": "Propose one exact version-bound replacement.",
        "run_tests": "Run the fixed candidate test preset.",
        "show_diff": "Show the bounded unified diff from the baseline.",
    }
    return [{"type": "function", "function": {
        "name": name, "description": descriptions[name],
        "parameters": copy.deepcopy(schema), "strict": True}}
        for name, schema in TOOL_SCHEMAS.items()]


class ChatModel:
    def __init__(self, config: Record, client: Any):
        if type(config) is not dict or not isinstance(config.get("model"), str):
            raise ValueError("invalid_model_config")
        self.config = copy.deepcopy(config)
        self.client = client
        self.last_usage: Record = {}
        self.provider_state: Record = {}

    def next(self, messages: list[Record]) -> Record:
        request: Record = {"model": self.config["model"],
                           "messages": copy.deepcopy(messages),
                           "tools": _tool_descriptions()}
        if self.config.get("parallel_tool_calls_supported", True):
            request["parallel_tool_calls"] = False
        if "timeout" in self.config:
            request["timeout"] = self.config["timeout"]
        try:
            response = self.client.chat.completions.create(**request)
        except TimeoutError as error:
            raise TimeoutError("model_timeout") from error
        except Exception as error:
            raise RuntimeError("model_request_failed") from error
        plain = _plain(response)
        usage = plain.get("usage")
        self.last_usage = copy.deepcopy(usage) if isinstance(usage, dict) else {}
        return parse_response(plain)
