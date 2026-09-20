"""Build a bounded, deterministic model view without deleting durable history."""
from __future__ import annotations

import copy
import json
from typing import Any

from .contracts import Record


def _encoded(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def complete_groups(messages: list[Record]) -> list[list[Record]]:
    groups: list[list[Record]] = []
    index = 0
    while index < len(messages):
        item = messages[index]
        calls = item.get("tool_calls")
        if calls:
            if type(calls) is not list or len(calls) != 1 or index + 1 >= len(messages):
                raise ValueError("unpaired_tool_call")
            result = messages[index + 1]
            if result.get("role") != "tool" or result.get("tool_call_id") != calls[0].get("id"):
                raise ValueError("unpaired_tool_call")
            groups.append([item, result])
            index += 2
        else:
            if item.get("role") == "tool":
                raise ValueError("orphan_tool_result")
            groups.append([item])
            index += 1
    return groups


def _failed(group: list[Record]) -> bool:
    if len(group) != 2 or group[1].get("role") != "tool":
        return False
    content = group[1].get("content")
    try:
        value = json.loads(content) if isinstance(content, str) else content
    except json.JSONDecodeError:
        return True
    return isinstance(value, dict) and (value.get("ok") is False
                                        or value.get("error") not in (None, ""))


def _history_without_pending(state: Record) -> list[Record]:
    messages = copy.deepcopy(state.get("messages", []))
    if type(messages) is not list:
        raise ValueError("invalid_history")
    if messages and messages[-1].get("tool_calls"):
        pending = state.get("pending")
        calls = messages[-1]["tool_calls"]
        if (type(calls) is list and len(calls) == 1 and isinstance(pending, dict)
                and calls[0].get("id") == pending.get("call_id")):
            messages.pop()
    return messages


def build_context(state: Record, max_bytes: int) -> list[Record]:
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError("invalid_context_budget")
    summary = {
        "kind": "authoritative_run_state",
        "user_requirements": {"goal": state.get("goal"),
                              "constraints": copy.deepcopy(state.get("constraints", []))},
        "disk_facts": {"workspace_hash": state.get("workspace_hash", ""),
                       "status": state.get("status")},
        "approval": copy.deepcopy(state.get("pending")),
        "verification": copy.deepcopy(state.get("evidence", {})),
        "model_working_note": state.get("plan", ""),
    }
    forced = {"role": "system", "content": _encoded(summary).decode("utf-8")}
    groups = complete_groups(_history_without_pending(state))
    full = [forced, *(item for group in groups for item in group)]
    if len(_encoded(full)) <= max_bytes:
        return full

    required: set[int] = set()
    failures = [index for index, group in enumerate(groups) if _failed(group)]
    if failures:
        required.add(failures[-1])
    elif groups:
        required.add(len(groups) - 1)

    selected = set(required)

    def render(indices: set[int]) -> list[Record]:
        omitted = len(groups) - len(indices)
        compact = {"role": "system", "content": _encoded({
            "kind": "history_compaction", "omitted_groups": omitted,
            "note": "Durable history remains in state and Trace."}).decode("utf-8")}
        return [forced, compact, *(item for number, group in enumerate(groups)
                                   if number in indices for item in group)]

    minimum = render(selected)
    if len(_encoded(minimum)) > max_bytes:
        raise ValueError("context_budget_exhausted")
    for index in reversed(range(len(groups))):
        if index in selected:
            continue
        candidate = selected | {index}
        if len(_encoded(render(candidate))) <= max_bytes:
            selected = candidate
    return render(selected)
