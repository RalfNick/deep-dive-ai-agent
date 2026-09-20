"""Offline-first command line for the chapter lab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import threading
import time

from .contracts import new_state
from .prepare import control_path, create_workspace
from .providers.replay import ReplayModel
from .runtime import run
from .services import Services
from .state import Store


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m chapter12.quickstart")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "resume", "approve", "reject", "trace"):
        command = sub.add_parser(name)
        command.add_argument("--workspace", type=Path, required=True)
        command.add_argument("--run-id", required=True)
        if name in {"start", "resume"}:
            command.add_argument("--replay", type=Path, required=True)
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


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    root = args.workspace.absolute()
    if args.command == "start":
        root = create_workspace(root)
        state_path, binding_path = _paths(root)
        binding_path.write_text(json.dumps(_binding(root, args.run_id, state_path),
                                           sort_keys=True), encoding="utf-8", newline="\n")
        store = Store(state_path)
        state = new_state(args.run_id, "Repair nested local Markdown link checks",
                          "trusted_local", time.time())
        model = ReplayModel(_read_decisions(args.replay))
        result = run(state, Services(root, store, model, "trusted_local",
                                     threading.Event()))
        print(json.dumps({key: result.get(key) for key in
                          ("run_id", "status", "reason")}, ensure_ascii=False,
                         sort_keys=True))
        return 0 if result["status"] in {"completed", "awaiting_approval"} else 1
    state_path, _ = _check_binding(root, args.run_id)
    store = Store(state_path)
    if args.command == "trace":
        print(json.dumps(store.events(args.run_id), ensure_ascii=False, sort_keys=True))
        return 0
    # Task 8 supplies mutation semantics; exposing the commands now keeps the
    # CLI surface stable without pretending they already work.
    if args.command in {"approve", "reject", "resume"}:
        print(json.dumps({"error": "command_not_available_until_recovery_stage"}))
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
