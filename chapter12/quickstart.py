"""Offline-first command line for the chapter lab."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import threading
import time

from . import backends
from .contracts import new_state
from .preflight import check as preflight_check
from .prepare import control_path, create_workspace
from .providers.chat import ChatModel
from .providers.replay import ReplayModel
from .recovery import recover, resolve_approval
from .runtime import run
from .services import Services
from .state import Store


TRUSTED_REPLAY = Path(__file__).parent / "fixtures" / "replay" / "canonical.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m chapter12.quickstart")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "resume", "approve", "reject", "trace"):
        command = sub.add_parser(name)
        command.add_argument("--workspace", type=Path, required=True)
        command.add_argument("--run-id", required=True)
        if name in {"start", "resume"}:
            command.add_argument("--model", choices=("replay", "live"), default="replay")
            command.add_argument("--backend", choices=("trusted_local", "container"),
                                 default="trusted_local")
            command.add_argument("--replay", type=Path)
            command.add_argument(
                "--trust-replay-file", action="store_true",
                help=("assert that a non-canonical replay file is trusted; "
                      "trusted_local may execute tests written by its decisions"))
            command.add_argument("--model-name")
            command.add_argument("--base-url")
            command.add_argument("--parallel-tool-calls-unsupported", action="store_true")
        if name in {"approve", "reject"}:
            command.add_argument("--action-id", required=True)
    return parser


def _paths(root: Path) -> tuple[Path, Path]:
    control = control_path(root.absolute())
    return control / "state.sqlite", control / "binding.json"


def _binding(root: Path, run_id: str, state_path: Path) -> dict[str, str]:
    return {"schema_version": 1, "run_id": run_id,
            "workspace": str(root.absolute()), "state": str(state_path.absolute())}


def _check_binding(root: Path, run_id: str) -> tuple[Path, dict[str, str]]:
    state_path, binding_path = _paths(root)
    try:
        saved = json.loads(binding_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise ValueError("binding_missing") from error
    if saved != _binding(root, run_id, state_path):
        raise ValueError("binding_mismatch")
    return state_path, saved


def _read_decisions(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not list:
        raise ValueError("invalid_replay_file")
    return value


def _model(args, backend: str):
    if args.model == "replay":
        if args.replay is None:
            raise ValueError("replay_file_required")
        canonical = TRUSTED_REPLAY.resolve()
        supplied = args.replay.resolve()
        if (backend == "trusted_local" and supplied != canonical
                and not args.trust_replay_file):
            raise ValueError("trusted_replay_confirmation_required")
        return ReplayModel(_read_decisions(args.replay))
    if backend != "container":
        raise ValueError("live_requires_container")
    readiness = preflight_check(backend, True, backends.probe_container)
    if not readiness["ready"]:
        print(json.dumps(readiness, sort_keys=True))
        return None
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("live_api_key_missing")
    model_name = args.model_name or os.environ.get("OPENAI_MODEL")
    if not model_name:
        raise ValueError("live_model_name_missing")
    from openai import OpenAI
    kwargs = {"api_key": os.environ["OPENAI_API_KEY"]}
    if args.base_url:
        kwargs["base_url"] = args.base_url
    client = OpenAI(**kwargs)
    return ChatModel({"model": model_name, "timeout": 45,
        "parallel_tool_calls_supported": not args.parallel_tool_calls_unsupported}, client)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    root = args.workspace.absolute()
    fault = None
    if os.environ.get("CHAPTER12_TEST_MODE") == "1":
        fault = os.environ.get("CHAPTER12_TEST_FAULT") or None
    if args.command == "start":
        try:
            model = _model(args, args.backend)
        except ValueError as error:
            print(json.dumps({"ready": False, "reason": str(error)}, sort_keys=True))
            return 2
        if model is None:
            return 2
        root = create_workspace(root)
        state_path, binding_path = _paths(root)
        binding_path.write_text(json.dumps(_binding(root, args.run_id, state_path),
                                           sort_keys=True), encoding="utf-8", newline="\n")
        store = Store(state_path)
        state = new_state(args.run_id, "Repair nested local Markdown link checks",
                          args.backend, time.time())
        result = run(state, Services(root, store, model, args.backend,
                                     threading.Event(), fault=fault))
        payload = {key: result.get(key) for key in ("run_id", "status", "reason")}
        payload["action_id"] = (result.get("pending") or {}).get("action_id")
        print(json.dumps(payload, ensure_ascii=False,
                         sort_keys=True))
        return 0 if result["status"] in {"completed", "awaiting_approval"} else 1
    state_path, _ = _check_binding(root, args.run_id)
    store = Store(state_path)
    if args.command == "trace":
        print(json.dumps(store.events(args.run_id), ensure_ascii=False, sort_keys=True))
        return 0
    state = recover(root, store, store.load(args.run_id))
    if args.command in {"approve", "reject"}:
        pending = state.get("pending") or {}
        if pending.get("action_id") != args.action_id:
            raise ValueError("approval_mismatch")
        state = resolve_approval(state, store, args.command == "approve")
        print(json.dumps({"run_id": state["run_id"], "status": state["status"],
                          "reason": state["reason"], "action_id": args.action_id},
                         ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "resume":
        try:
            model = _model(args, state["backend"])
        except ValueError as error:
            print(json.dumps({"ready": False, "reason": str(error)}, sort_keys=True))
            return 2
        if model is None:
            return 2
        if isinstance(model, ReplayModel):
            model = ReplayModel(_read_decisions(args.replay),
                                state.get("provider_state") or None)
        services = Services(root, store, model, state["backend"], threading.Event(),
                            fault=fault)
        state = services.resume(state)
        state = run(state, services)
        print(json.dumps({key: state.get(key) for key in ("run_id", "status", "reason")},
                         ensure_ascii=False, sort_keys=True))
        return 0 if state["status"] in {"completed", "awaiting_approval"} else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
