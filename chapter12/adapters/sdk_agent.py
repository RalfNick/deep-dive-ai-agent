"""OpenAI Agents SDK owns model/tool turns and native approval interruptions."""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
from pathlib import Path
import tempfile
import threading
from typing import Any

from agents import Agent, ModelSettings, RunConfig, Runner, function_tool
from agents.run_context import RunContextWrapper
from agents.tool_context import ToolContext

from ..contracts import Record
from ..providers.replay import validate_decision
from ..recovery import recover, resolve_approval
from ..services import Services
from ..state import Store
from .sdk_compat import dump_state, load_state_with_context
from .sdk_replay_model import make_model


def _state(services: Services) -> Record:
    value = getattr(services, "sdk_run_state", None)
    if not isinstance(value, dict):
        raise RuntimeError("sdk_application_state_missing")
    return value


async def _invoke(context: ToolContext[Services], name: str, arguments: Record) -> str:
    services = context.context
    state = _state(services)
    call = {"call_id": context.tool_call_id, "name": name, "arguments": arguments}
    pending = state.get("pending") or {}
    if name == "apply_patch":
        if pending.get("call_id") != context.tool_call_id \
                or pending.get("approval") != "approved":
            raise RuntimeError("sdk_approval_guard_failed")
    else:
        state = services.propose(state, call)
        services.sdk_run_state = state
        if state.get("pending") is None:
            return json.dumps(state["evidence"]["last_result"], ensure_ascii=False,
                              sort_keys=True)
    result = services.execute(state)
    state = services.observe(state, result)
    services.sdk_run_state = state
    services.store.append_event(state["run_id"], "sdk_tool_invoked", {
        "name": name, "call_id": context.tool_call_id}, call_id=context.tool_call_id)
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


async def _approval(context: RunContextWrapper[Services], arguments: dict[str, Any],
                    call_id: str) -> bool:
    services = context.context
    state = _state(services)
    pending = state.get("pending") or {}
    if pending.get("call_id") != call_id:
        call = {"call_id": call_id, "name": "apply_patch",
                "arguments": copy.deepcopy(arguments)}
        state = services.propose(state, call)
        services.sdk_run_state = state
    # Always use a native interruption. If proposal validation failed, run_sdk
    # detects the absence of a concrete pending action and fails closed.
    return True


def build_agent(services: Services) -> Agent[Services]:
    @function_tool(name_override="read_file")
    async def read_file_tool(context: ToolContext[Services], path: str,
                             start: int = 1, end: int | None = None) -> str:
        """Read a bounded range from one workspace file."""
        arguments: Record = {"path": path, "start": start}
        if end is not None:
            arguments["end"] = end
        return await _invoke(context, "read_file", arguments)

    @function_tool(name_override="search")
    async def search_tool(context: ToolContext[Services], query: str,
                          directory: str = ".") -> str:
        """Search literal text in the workspace."""
        return await _invoke(context, "search", {"query": query, "directory": directory})

    @function_tool(name_override="run_tests")
    async def run_tests_tool(context: ToolContext[Services], preset: str) -> str:
        """Run a fixed test preset."""
        return await _invoke(context, "run_tests", {"preset": preset})

    @function_tool(name_override="show_diff")
    async def show_diff_tool(context: ToolContext[Services]) -> str:
        """Show the bounded diff from the host baseline."""
        return await _invoke(context, "show_diff", {})

    @function_tool(name_override="apply_patch", needs_approval=_approval)
    async def apply_patch_tool(context: ToolContext[Services], path: str, version: str,
                               old: str, new: str) -> str:
        """Apply one exact, version-bound replacement after approval."""
        return await _invoke(context, "apply_patch", {
            "path": path, "version": version, "old": old, "new": new})

    return Agent(name="Chapter12CodingAgent",
        instructions=("Work only through the five registered tools. A completion statement "
                      "is a request for host verification, not proof of success."),
        tools=[read_file_tool, search_tool, run_tests_tool, show_diff_tool, apply_patch_tool],
        model=services.model,
        model_settings=ModelSettings(parallel_tool_calls=False))


def _write_snapshot(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="sdk-state-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def _interruption_call_id(item: Any) -> str | None:
    raw = getattr(item, "raw_item", None)
    return getattr(raw, "call_id", None) or (raw.get("call_id") if isinstance(raw, dict) else None)


async def _run_async(state: Record, services: Services, snapshot: Path,
                     approval: bool | None) -> Record:
    services.sdk_run_state = state
    model = services.model
    if hasattr(model, "cursor"):
        model.cursor = int(state.get("provider_state", {}).get("cursor", 0))
    agent = build_agent(services)
    sdk_input: Any
    if snapshot.is_file():
        sdk_input = await load_state_with_context(
            agent, snapshot.read_text(encoding="utf-8"), services)
        runner_context: Services | None = None
        interruptions = sdk_input.get_interruptions()
        if approval is None:
            return state
        if len(interruptions) != 1:
            return services.fail(state, "sdk_interruption_mismatch")
        state = recover(services.root, services.store, state)
        pending = state.get("pending") or {}
        if state["status"] == "failed":
            return state
        if _interruption_call_id(interruptions[0]) != pending.get("call_id"):
            return services.fail(state, "sdk_interruption_mismatch")
        state = resolve_approval(state, services.store, approval)
        services.sdk_run_state = state
        if approval:
            # Native SDK approval is necessary but not sufficient: recheck the
            # bound full-workspace intent immediately before approving the SDK
            # interruption, so its tool body cannot bypass a stale host guard.
            state = recover(services.root, services.store, state)
            services.sdk_run_state = state
            if state["status"] == "failed":
                return state
            sdk_input.approve(interruptions[0])
        else:
            sdk_input.reject(interruptions[0], rejection_message="approval_denied")
    else:
        sdk_input = state["goal"]
        runner_context = services
        services.store.save(state)

    for _ in range(4):
        before_cursor = int(getattr(model, "cursor", 0))
        try:
            result = await Runner.run(agent, sdk_input, context=runner_context,
                max_turns=max(1, 30 - state["counters"]["model_turns"]),
                run_config=RunConfig(tracing_disabled=True,
                                     trace_include_sensitive_data=False))
        except (RuntimeError, ValueError) as error:
            state = services.sdk_run_state
            state["counters"]["model_turns"] += max(
                0, int(getattr(model, "cursor", before_cursor)) - before_cursor)
            state["provider_state"] = {"cursor": int(getattr(model, "cursor", before_cursor))}
            return services.fail(state, str(error) or type(error).__name__)
        state = services.sdk_run_state
        state["counters"]["model_turns"] += max(
            0, int(getattr(model, "cursor", before_cursor)) - before_cursor)
        state["provider_state"] = {"cursor": int(getattr(model, "cursor", before_cursor))}
        services.store.save(state)
        if result.interruptions:
            if not isinstance(state.get("pending"), dict) or not state["pending"].get("action_id"):
                return services.fail(state, "sdk_approval_without_action")
            _write_snapshot(snapshot, dump_state(result.to_state()))
            services.store.save_with_event(state, "sdk_interruption", {
                "call_id": state["pending"]["call_id"],
                "action_id": state["pending"]["action_id"]},
                state["pending"]["call_id"], state["pending"]["action_id"])
            return state
        state["messages"].append({"role": "assistant",
                                  "content": str(result.final_output)})
        state = services.finish(state)
        services.sdk_run_state = state
        if state["status"] == "completed":
            return state
        sdk_input = result.to_input_list() + [{"role": "user", "content": json.dumps({
            "kind": "verification_failed",
            "evidence": state["evidence"]["verification"]},
            ensure_ascii=False, sort_keys=True)}]
        runner_context = services
    return services.fail(state, "sdk_continuation_limit")


def run_sdk(state: Record, services: Services, snapshot: Path,
            approval: bool | None = None) -> Record:
    return asyncio.run(_run_async(state, services, Path(snapshot).absolute(), approval))


def _stage(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--approval", choices=("true", "false"))
    args = parser.parse_args(argv)
    store = Store(args.state)
    state = store.load(args.run_id)
    decisions = [validate_decision(item) for item in
                 json.loads(args.decisions.read_text(encoding="utf-8"))]
    model = make_model(decisions)
    services = Services(args.workspace, store, model, state["backend"], threading.Event())
    approval = None if args.approval is None else args.approval == "true"
    result = run_sdk(state, services, args.snapshot, approval)
    print(json.dumps({"pid": os.getpid(), "status": result["status"],
                      "reason": result["reason"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_stage())
