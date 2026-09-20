"""Single-step services used by the manual loop and later framework adapters."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import threading
import time
from typing import Any

from . import executor, verifier
from .context import build_context
from .contracts import Record, TERMINAL, validate_call, validate_result
from .recovery import recover
from .state import Store, workspace_lock
from .tools import manifest_hash, prepare_patch, workspace_manifest, write_patch


class Services:
    def __init__(self, root: Path, store: Store, model: Any, backend: str,
                 cancel: threading.Event, *, max_model_turns: int = 30,
                 max_tool_calls: int = 60, context_bytes: int = 32768,
                 clock: Any = time.time, fault: str | None = None):
        self.root = Path(root).absolute()
        self.store = store
        self.model = model
        self.backend = backend
        self.cancel = cancel
        self.max_model_turns = max_model_turns
        self.max_tool_calls = max_tool_calls
        self.context_bytes = context_bytes
        self.clock = clock
        if fault not in {None, "after_intent", "after_write_before_receipt"}:
            raise ValueError("unknown_fault_point")
        self.fault = fault
        self.baseline = verifier.capture_baseline(self.root)

    def _transition(self, state: Record, status: str, reason: str,
                    event: str) -> bool:
        state["status"] = status
        state["reason"] = reason
        self.store.save_with_event(state, event, {"reason": reason})
        return True

    def stopped(self, state: Record) -> bool:
        if state["status"] in TERMINAL or state["status"] == "awaiting_approval":
            return True
        if state["status"] == "verifying":
            return False
        if self.cancel.is_set():
            return self._transition(state, "cancelled", "cancelled", "run_cancelled")
        if self.clock() >= state["deadline"]:
            return self._transition(state, "budget_exhausted", "deadline",
                                    "budget_exhausted")
        if state["counters"]["model_turns"] >= self.max_model_turns:
            return self._transition(state, "budget_exhausted", "model_budget",
                                    "budget_exhausted")
        if state["counters"]["tool_calls"] >= self.max_tool_calls:
            return self._transition(state, "budget_exhausted", "tool_budget",
                                    "budget_exhausted")
        return False

    def decide(self, state: Record) -> Record:
        if self.stopped(state):
            raise ValueError("run_stopped")
        state["workspace_hash"] = manifest_hash(workspace_manifest(self.root))
        state["counters"]["model_turns"] += 1
        # Save the consumed turn before the transport call: a crash cannot grant
        # another free request. Replay cursor is saved immediately after success.
        self.store.save_with_event(state, "model_requested", {
            "turn": state["counters"]["model_turns"]})
        config = getattr(self.model, "config", None)
        had_timeout = isinstance(config, dict) and "timeout" in config
        previous_timeout = config.get("timeout") if isinstance(config, dict) else None
        if isinstance(config, dict):
            remaining = max(0.001, state["deadline"] - self.clock())
            configured = previous_timeout if isinstance(previous_timeout, (int, float)) else 45
            config["timeout"] = min(45, configured, remaining)
        try:
            decision = self.model.next(build_context(state, self.context_bytes))
        finally:
            if isinstance(config, dict):
                if had_timeout:
                    config["timeout"] = previous_timeout
                else:
                    config.pop("timeout", None)
        if (type(decision) is not dict or decision.get("kind") not in {"plan", "tool", "final"}
                or not isinstance(decision.get("text"), str)
                or set(decision) != {"kind", "text", "call"}):
            raise ValueError("invalid_decision")
        if decision["kind"] == "tool" and type(decision["call"]) is not dict:
            raise ValueError("invalid_decision")
        if decision["kind"] != "tool" and decision["call"] is not None:
            raise ValueError("invalid_decision")
        provider_state = getattr(self.model, "provider_state", {})
        state["provider_state"] = copy.deepcopy(provider_state)
        self.store.save_with_event(state, "model_decision", {
            "kind": decision["kind"], "text": decision["text"],
            "call_id": decision["call"].get("call_id") if decision["call"] else None})
        return copy.deepcopy(decision)

    @staticmethod
    def _assistant_call(call: Record) -> Record:
        return {"role": "assistant", "content": None, "tool_calls": [{
            "id": call.get("call_id", "invalid"), "type": "function",
            "function": {"name": call.get("name", "invalid"),
                         "arguments": json.dumps(call.get("arguments", {}),
                                                 ensure_ascii=False, sort_keys=True)}}]}

    def propose(self, state: Record, call: Record) -> Record:
        state["messages"].append(self._assistant_call(call))
        state["counters"]["tool_calls"] += 1
        try:
            validated = validate_call(call)
            if validated["name"] == "apply_patch":
                patch = prepare_patch(self.root, validated)
                action = self.store.intent(state["run_id"], validated, patch)
                if self.fault == "after_intent":
                    os._exit(71)
                state["pending"] = {"call": validated,
                                    "call_id": validated["call_id"],
                                    "action_id": action["action_id"],
                                    "arguments_hash": action["arguments_hash"],
                                    "workspace_hash": action["workspace_hash"],
                                    "path": patch["path"], "approval": "required"}
                state["status"] = "awaiting_approval"
                self.store.save_with_event(state, "approval_requested", {
                    "path": patch["path"], "arguments_hash": action["arguments_hash"]})
                return state
            self.store.register_call(state["run_id"], validated)
            state["pending"] = {"call": validated, "call_id": validated["call_id"]}
            state["status"] = "executing"
            self.store.save_with_event(state, "tool_proposed", {
                "name": validated["name"], "call_id": validated["call_id"]})
            return state
        except (OSError, UnicodeError, ValueError, RuntimeError) as error:
            call_id = call.get("call_id", "invalid")
            state["pending"] = {"call": copy.deepcopy(call), "call_id": call_id}
            return self.observe(state, {"call_id": call_id, "ok": False, "data": {},
                "error": str(error) or type(error).__name__, "truncated": False})

    def execute(self, state: Record) -> Record:
        if self.cancel.is_set():
            return {"call_id": state["pending"]["call_id"], "ok": False, "data": {},
                    "error": "cancelled", "truncated": False}
        if self.clock() >= state["deadline"]:
            return {"call_id": state["pending"]["call_id"], "ok": False, "data": {},
                    "error": "deadline", "truncated": False}
        return executor.dispatch(self.root, state["pending"]["call"], self.backend,
                                 self.cancel)

    def observe(self, state: Record, result: Record) -> Record:
        result = validate_result(result)
        pending = state.get("pending")
        if not isinstance(pending, dict) or result.get("call_id") != pending.get("call_id"):
            raise ValueError("result_call_mismatch")
        state["messages"].append({"role": "tool", "tool_call_id": result["call_id"],
                                  "content": json.dumps(result, ensure_ascii=False,
                                                        sort_keys=True)})
        state["evidence"]["last_result"] = copy.deepcopy(result)
        state["pending"] = None
        state["status"] = "ready"
        state["reason"] = None
        self.store.save_with_event(state, "tool_observed", result,
                                   call_id=result["call_id"])
        return state

    def resume(self, state: Record) -> Record:
        state = recover(self.root, self.store, state)
        if state["status"] != "executing":
            return state
        with workspace_lock(self.root):
            state = recover(self.root, self.store, state)
            if state["status"] != "executing":
                return state
            action = self.store.action(state["pending"]["action_id"])
            data = write_patch(self.root, action["patch"])
            self.store.append_event(state["run_id"], "action_written", {
                "path": data["path"], "version": data["version"]},
                action["call_id"], action["action_id"])
            if self.fault == "after_write_before_receipt":
                os._exit(72)
            result = {"call_id": action["call_id"], "ok": True, "data": data,
                      "error": None, "truncated": False}
            state["messages"].append({"role": "tool", "tool_call_id": action["call_id"],
                                      "content": json.dumps(result, ensure_ascii=False,
                                                            sort_keys=True)})
            state["evidence"]["last_result"] = copy.deepcopy(result)
            state["pending"] = None
            state["status"] = "ready"
            state["reason"] = None
            self.store.complete_action(state, action["action_id"], result)
            return state

    def finish(self, state: Record) -> Record:
        state["status"] = "verifying"
        self.store.save_with_event(state, "verification_started", {})
        verdict = verifier.verify(self.root, self.backend, self.baseline, self.cancel)
        live_hash = manifest_hash(workspace_manifest(self.root))
        if verdict.get("passed") and verdict.get("after_hash") != live_hash:
            verdict = copy.deepcopy(verdict)
            verdict["passed"] = False
            verdict["reason"] = "post_verification_change"
        state["evidence"]["verification"] = verdict
        state["workspace_hash"] = live_hash
        if verdict.get("passed"):
            state["status"] = "completed"
            state["reason"] = None
            self.store.save_with_event(state, "verification_passed", verdict)
        else:
            state["status"] = "ready"
            state["reason"] = verdict.get("reason") or "verification_failed"
            state["messages"].append({"role": "user", "content": json.dumps({
                "kind": "verification_failed", "evidence": verdict},
                ensure_ascii=False, sort_keys=True)})
            self.store.save_with_event(state, "verification_failed", verdict)
        return state

    def fail(self, state: Record, reason: str) -> Record:
        state["status"] = "failed"
        state["reason"] = reason
        self.store.save_with_event(state, "run_failed", {"reason": reason})
        return state
