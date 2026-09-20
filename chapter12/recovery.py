"""Reconcile durable intent, approval, filesystem state, and action receipts."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from .contracts import Record
from .state import Store
from .tools import manifest_hash, workspace_manifest


def classify(before_hash: str, after_hash: str, current_hash: str) -> str:
    if before_hash == after_hash:
        raise ValueError("no_op_patch")
    if current_hash == after_hash:
        return "record_receipt"
    if current_hash == before_hash:
        return "recheck_approval"
    return "uncertain"


def _assistant_call(call: Record) -> Record:
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": call["call_id"], "type": "function", "function": {
            "name": call["name"], "arguments": json.dumps(call["arguments"],
                                                              ensure_ascii=False,
                                                              sort_keys=True)}}]}


def _ensure_call_message(state: Record, call: Record) -> None:
    for item in reversed(state["messages"]):
        if any(tool.get("id") == call["call_id"] for tool in item.get("tool_calls", [])):
            return
    state["messages"].append(_assistant_call(call))


def _pending(action: Record, approval: str) -> Record:
    return {"call": copy.deepcopy(action["call"]), "call_id": action["call_id"],
            "action_id": action["action_id"],
            "arguments_hash": action["arguments_hash"],
            "workspace_hash": action["workspace_hash"],
            "path": action["patch"]["path"], "approval": approval}


def _finish_action(state: Record, store: Store, action: Record, result: Record) -> Record:
    _ensure_call_message(state, action["call"])
    already = any(item.get("role") == "tool"
                  and item.get("tool_call_id") == action["call_id"]
                  for item in state["messages"])
    if not already:
        state["messages"].append({"role": "tool", "tool_call_id": action["call_id"],
                                  "content": json.dumps(result, ensure_ascii=False,
                                                        sort_keys=True)})
    state["evidence"]["last_result"] = copy.deepcopy(result)
    state["pending"] = None
    state["status"] = "ready"
    state["reason"] = None
    store.complete_action(state, action["action_id"], result)
    return state


def resolve_approval(state: Record, store: Store, approved: bool) -> Record:
    pending = state.get("pending")
    if type(approved) is not bool or not isinstance(pending, dict) \
            or not isinstance(pending.get("action_id"), str):
        raise ValueError("approval_mismatch")
    action = store.action(pending["action_id"])
    if (state.get("run_id") != action["run_id"]
            or pending.get("call_id") != action["call_id"]
            or pending.get("arguments_hash") != action["arguments_hash"]
            or pending.get("workspace_hash") != action["workspace_hash"]):
        raise ValueError("approval_mismatch")
    approval = {key: action[key] for key in
                ("run_id", "action_id", "arguments_hash", "workspace_hash")}
    approval["approved"] = approved
    store.approve(approval)
    if not approved:
        result = {"call_id": action["call_id"], "ok": False, "data": {},
                  "error": "approval_denied", "truncated": False}
        return _finish_action(state, store, action, result)
    state["pending"] = _pending(action, "approved")
    state["status"] = "executing"
    state["reason"] = None
    store.save_with_event(state, "approval_resolved", {"approved": True},
                          action["call_id"], action["action_id"])
    return state


def _fail_stale(state: Record, store: Store, action: Record) -> Record:
    state["status"] = "failed"
    state["reason"] = "approval_stale"
    store.save_with_event(state, "recovery_uncertain", {
        "reason": "approval_stale", "path": action["patch"]["path"]},
        action["call_id"], action["action_id"])
    return state


def recover(root: Path, store: Store, state: Record) -> Record:
    pending = state.get("pending")
    if not isinstance(pending, dict) or not pending.get("action_id"):
        unresolved = store.unresolved_actions(state["run_id"])
        if not unresolved:
            return state
        if len(unresolved) != 1:
            state["status"] = "failed"
            state["reason"] = "recovery_ambiguous"
            store.save_with_event(state, "recovery_uncertain", {
                "reason": "multiple_unresolved_actions"})
            return state
        action = unresolved[0]
        _ensure_call_message(state, action["call"])
        state["pending"] = _pending(action, "required")
    else:
        action = store.action(pending["action_id"])
    if state["run_id"] != action["run_id"]:
        raise ValueError("approval_mismatch")

    if action["result"] is not None:
        return _finish_action(state, store, action, action["result"])
    approval = store.approval(action["action_id"])
    if approval is None:
        state["pending"] = _pending(action, "required")
        state["status"] = "awaiting_approval"
        store.save_with_event(state, "recovery_waiting_approval", {},
                              action["call_id"], action["action_id"])
        return state
    if approval["approved"] is False:
        result = {"call_id": action["call_id"], "ok": False, "data": {},
                  "error": "approval_denied", "truncated": False}
        return _finish_action(state, store, action, result)

    current = workspace_manifest(root)
    patch = action["patch"]
    current_target = current.get(patch["path"], "absent")
    outcome = classify(patch["before_hash"], patch["after_hash"], current_target)
    if outcome == "record_receipt" and current == patch["after_files"]:
        result = {"call_id": action["call_id"], "ok": True,
                  "data": {"path": patch["path"], "version": patch["after_hash"],
                           "workspace_hash": manifest_hash(current), "recovered": True},
                  "error": None, "truncated": False}
        return _finish_action(state, store, action, result)
    if outcome == "recheck_approval" and current == patch["before_files"]:
        state["pending"] = _pending(action, "approved")
        state["status"] = "executing"
        state["reason"] = None
        store.save_with_event(state, "recovery_recheck_passed", {},
                              action["call_id"], action["action_id"])
        return state
    return _fail_stale(state, store, action)
