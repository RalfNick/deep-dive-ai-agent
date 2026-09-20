"""Build a bounded, deterministic model view without deleting durable history."""
from __future__ import annotations

import copy
import json
from typing import Any

from .contracts import Record


_EXECUTION_FIELDS = (
    "returncode", "truncated", "timed_out", "cancelled", "duration_seconds",
    "discovered", "diagnostic", "reason",
)
_RESULT_DATA_FIELDS = (
    "path", "paths", "version", "workspace_hash", "start_line", "end_line",
    "total_lines", "returncode", "truncated", "timed_out", "cancelled",
    "duration_seconds", "discovered", "diagnostic", "reason", "case_count",
)
_RAW_RESULT_FIELDS = ("text", "stdout", "stderr", "diff")


def _encoded(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _bounded_text(value: Any, limit: int) -> Any:
    if not isinstance(value, str):
        return copy.deepcopy(value)
    raw = value.encode("utf-8")
    if len(raw) <= limit:
        return value
    prefix = raw[:limit].decode("utf-8", errors="ignore")
    return f"{prefix}...[truncated from {len(raw)} bytes]"


def _bounded_list(value: Any, limit: int = 20) -> Any:
    if not isinstance(value, list):
        return copy.deepcopy(value)
    result = copy.deepcopy(value[:limit])
    if len(value) > limit:
        result.append({"omitted_items": len(value) - limit})
    return result


def _execution_summary(value: Any) -> Record:
    if not isinstance(value, dict):
        return {}
    result = {key: copy.deepcopy(value[key]) for key in _EXECUTION_FIELDS
              if key in value}
    for key in ("stdout", "stderr"):
        payload = value.get(key)
        if isinstance(payload, str):
            result[f"{key}_bytes"] = len(payload.encode("utf-8"))
    return result


def _result_summary(value: Any) -> Record:
    if not isinstance(value, dict):
        return {}
    result = {key: copy.deepcopy(value.get(key))
              for key in ("call_id", "ok", "error", "truncated")
              if key in value}
    data = value.get("data")
    if isinstance(data, dict):
        compact = {key: _bounded_list(data[key])
                   for key in _RESULT_DATA_FIELDS if key in data}
        for key in _RAW_RESULT_FIELDS:
            payload = data.get(key)
            if isinstance(payload, str):
                compact[f"{key}_bytes"] = len(payload.encode("utf-8"))
        result["data"] = compact
    return result


def _verification_summary(value: Any) -> Record:
    if not isinstance(value, dict):
        return {}
    fields = ("passed", "reason", "protected_ok", "stable", "before_hash",
              "after_hash")
    result = {key: copy.deepcopy(value[key]) for key in fields if key in value}
    for key in ("failed_cases", "protected_changes"):
        if key in value:
            result[key] = _bounded_list(value[key])
    if "candidate_tests" in value:
        result["candidate_tests"] = _execution_summary(value["candidate_tests"])
    acceptance = value.get("acceptance")
    if isinstance(acceptance, dict):
        result["acceptance"] = {
            "case_count": acceptance.get("case_count"),
            "raw": _execution_summary(acceptance.get("raw")),
        }
    return result


def _evidence_summary(value: Any) -> Record:
    if not isinstance(value, dict):
        return {}
    result: Record = {}
    if "verification" in value:
        result["verification"] = _verification_summary(value["verification"])
    if "last_result" in value:
        result["last_result"] = _result_summary(value["last_result"])
    additional = sorted(set(value) - {"verification", "last_result"})
    if additional:
        result["additional_keys"] = additional
    return result


def _approval_summary(value: Any) -> Any:
    if not isinstance(value, dict) or len(_encoded(value)) <= 4096:
        return copy.deepcopy(value)
    fields = ("call_id", "action_id", "arguments_hash", "workspace_hash",
              "path", "approval")
    result = {key: copy.deepcopy(value[key]) for key in fields if key in value}
    call = value.get("call")
    if isinstance(call, dict):
        arguments = call.get("arguments")
        result["call"] = {
            "call_id": call.get("call_id"), "name": call.get("name"),
            "argument_keys": sorted(arguments) if isinstance(arguments, dict) else [],
        }
    result["details_compacted"] = True
    return result


def _argument_summary(value: Any) -> Record:
    if not isinstance(value, dict):
        return {}
    result: Record = {}
    for key, item in value.items():
        if key in {"old", "new"} and isinstance(item, str):
            result[f"{key}_bytes"] = len(item.encode("utf-8"))
        elif isinstance(item, str):
            result[key] = _bounded_text(item, 512)
        elif type(item) in (int, bool) or item is None:
            result[key] = item
    return result


def _compact_group(group: list[Record]) -> list[Record]:
    if len(group) == 2 and group[0].get("tool_calls"):
        original_call = group[0]["tool_calls"][0]
        function = original_call.get("function", {})
        try:
            arguments = json.loads(function.get("arguments", "{}"))
        except (TypeError, json.JSONDecodeError):
            arguments = {}
        call = {"role": "assistant", "content": None, "tool_calls": [{
            "id": original_call.get("id"), "type": "function",
            "function": {"name": function.get("name"),
                         "arguments": _encoded(_argument_summary(arguments)).decode("utf-8")},
        }]}
        content = group[1].get("content")
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
        except json.JSONDecodeError:
            parsed = None
        result = (_result_summary(parsed) if isinstance(parsed, dict)
                  else {"content_bytes": len(str(content).encode("utf-8"))})
        observation = {"role": "tool", "tool_call_id": group[1].get("tool_call_id"),
                       "content": _encoded(result).decode("utf-8")}
        return [call, observation]
    item = copy.deepcopy(group[0])
    item["content"] = _bounded_text(item.get("content"), 2048)
    return [item]


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
        "user_requirements": {"goal": _bounded_text(state.get("goal"), 4096),
                              "constraints": [_bounded_text(item, 1024)
                                              for item in state.get("constraints", [])]},
        "disk_facts": {"workspace_hash": state.get("workspace_hash", ""),
                       "status": state.get("status")},
        "approval": _approval_summary(state.get("pending")),
        "evidence": _evidence_summary(state.get("evidence", {})),
        "runtime": {"backend": state.get("backend"),
                    "counters": copy.deepcopy(state.get("counters", {})),
                    "deadline": state.get("deadline"),
                    "reason": state.get("reason")},
        "model_working_note": _bounded_text(state.get("plan", ""), 4096),
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

    def render(indices: set[int], projected: set[int] | None = None) -> list[Record]:
        projected = projected or set()
        omitted = len(groups) - len(indices)
        compact = {"role": "system", "content": _encoded({
            "kind": "history_compaction", "omitted_groups": omitted,
            "projected_groups": len(projected),
            "note": "Durable history remains in state and Trace."}).decode("utf-8")}
        return [forced, compact, *(
            item for number, group in enumerate(groups) if number in indices
            for item in (_compact_group(group) if number in projected else group))]

    minimum = render(selected)
    if len(_encoded(minimum)) > max_bytes:
        minimum = render(selected, selected)
        if len(_encoded(minimum)) > max_bytes:
            raise ValueError("context_budget_exhausted")
        projected = set(selected)
    else:
        projected = set()
    for index in reversed(range(len(groups))):
        if index in selected:
            continue
        candidate = selected | {index}
        if len(_encoded(render(candidate, projected))) <= max_bytes:
            selected = candidate
    return render(selected, projected)
