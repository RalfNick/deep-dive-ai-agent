from __future__ import annotations

import copy
import json

import pytest

from chapter12.context import build_context, complete_groups
from chapter12.contracts import new_state


def state_with_history():
    state = new_state("r1", "repair nested Markdown links", "trusted_local", 0)
    state.update(status="awaiting_approval", plan="inspect, patch, test",
                 workspace_hash="a" * 64,
                 pending={"call_id": "pending-1", "action_id": "action-1",
                          "approval": "required", "path": "src/linkcheck.py"},
                 evidence={"verification": {"passed": False,
                                             "failed_cases": ["nested_valid"]},
                           "last_failure": {"error": "stale_version"}})
    state["messages"] = [
        {"role": "user", "content": "Please inspect the repository."},
        {"role": "assistant", "content": None, "tool_calls": [{
            "id": "c1", "type": "function",
            "function": {"name": "read_file", "arguments": '{"path":"README.md"}'}}]},
        {"role": "tool", "tool_call_id": "c1",
         "content": json.dumps({"ok": True, "data": {"version": "b" * 64}})},
        {"role": "assistant", "content": None, "tool_calls": [{
            "id": "c2", "type": "function",
            "function": {"name": "run_tests", "arguments": '{"preset":"candidate_tests"}'}}]},
        {"role": "tool", "tool_call_id": "c2",
         "content": json.dumps({"ok": False, "error": "tests_failed"})},
        # A proposed call waiting for approval is deliberately not sent half-paired.
        {"role": "assistant", "content": None, "tool_calls": [{
            "id": "pending-1", "type": "function",
            "function": {"name": "apply_patch", "arguments": "{}"}}]},
    ]
    return state


def test_complete_groups_rejects_orphans_and_mismatches():
    with pytest.raises(ValueError, match="orphan_tool_result"):
        complete_groups([{"role": "tool", "tool_call_id": "c1", "content": "{}"}])
    with pytest.raises(ValueError, match="unpaired_tool_call"):
        complete_groups([{"role": "assistant", "tool_calls": [{"id": "c1"}]},
                         {"role": "tool", "tool_call_id": "other"}])


def test_context_keeps_forced_state_and_complete_last_failure_group():
    state = state_with_history()
    original = copy.deepcopy(state)
    view = build_context(state, 5000)
    summary = json.loads(view[0]["content"])
    assert summary["user_requirements"]["goal"] == state["goal"]
    assert summary["user_requirements"]["constraints"] == state["constraints"]
    assert summary["model_working_note"] == state["plan"]
    assert summary["disk_facts"]["workspace_hash"] == "a" * 64
    assert summary["approval"] == state["pending"]
    assert summary["verification"] == state["evidence"]
    assert any(item.get("tool_call_id") == "c2" for item in view)
    assert not any(any(call.get("id") == "pending-1" for call in item.get("tool_calls", []))
                   for item in view)
    assert state == original
    assert build_context(state, 5000) == view


def test_context_compacts_only_whole_groups():
    state = state_with_history()
    full = build_context(state, 5000)
    forced_size = len(json.dumps(full[:1], ensure_ascii=False,
                                 sort_keys=True, separators=(",", ":")).encode())
    # Enough for forced state plus the last failed tool group, not all history.
    view = build_context(state, forced_size + 550)
    tool_ids = [item.get("tool_call_id") for item in view if item.get("role") == "tool"]
    assert tool_ids == ["c2"]
    assistant_ids = [item["tool_calls"][0]["id"] for item in view if item.get("tool_calls")]
    assert assistant_ids == ["c2"]
    assert json.loads(view[1]["content"])["kind"] == "history_compaction"


def test_too_small_for_forced_context_is_explicit():
    with pytest.raises(ValueError, match="context_budget_exhausted"):
        build_context(state_with_history(), 100)
