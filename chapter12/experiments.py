"""Five reproducible experiment groups with evidence-rich canonical reports."""
from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time

from . import backends, executor
from .context import build_context
from .contracts import new_state, validate_call
from .prepare import control_path, create_workspace
from .providers.replay import ReplayModel
from .recovery import recover, resolve_approval
from .runtime import run
from .services import Services
from .state import Store
from .tools import (prepare_patch, read_file, safe_path, show_diff,
                    workspace_manifest, write_patch)
from .verifier import capture_baseline, verify

CANONICAL_KEYS = ("schema_version", "decision_source", "orchestration",
                  "backend", "scenarios", "evidence", "limits")
REGRESSION = '''from pathlib import Path
import unittest
from src.linkcheck import broken_links

class AgentRegression(unittest.TestCase):
    def test_nested_links_are_relative_to_document(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(["missing.md"], broken_links(root / "docs/guide/start.md", root))
'''


def canonicalize(report: dict) -> dict:
    if not all(key in report for key in CANONICAL_KEYS):
        raise ValueError("report_schema_invalid")
    return {key: copy.deepcopy(report[key]) for key in CANONICAL_KEYS}


def _case(expected, observed, criterion, passed, does_not_prove):
    result = {"expected": expected, "observed": observed, "criterion": criterion,
            "passed": bool(passed), "does_not_prove": does_not_prove}
    if isinstance(observed, dict) and "accepted" in observed:
        result["accepted"] = bool(observed["accepted"])
    return result


def exactly_one_write_and_receipt(events: list[dict]) -> bool:
    return (sum(event.get("kind") == "action_written" for event in events) == 1
            and sum(event.get("kind") == "action_receipt" for event in events) == 1)


def offline_completion_proved(observed: dict) -> bool:
    return (observed.get("status") == "completed"
            and observed.get("red_observed") is True
            and observed.get("writes") == 2
            and observed.get("diff_paths")
            == ["src/linkcheck.py", "tests/test_agent_nested.py"]
            and observed.get("candidate_tests") == 3
            and observed.get("verification_passed") is True
            and observed.get("acceptance_case_count") == 4)


def authoritative_summary_retained(summary: dict) -> bool:
    return (summary.get("kind") == "authoritative_run_state"
            and summary.get("user_requirements", {}).get("goal")
            == "retain required state"
            and summary.get("disk_facts")
            == {"workspace_hash": "a" * 64, "status": "ready"}
            and summary.get("runtime", {}).get("counters")
            == {"model_turns": 0, "tool_calls": 0})


def _base(group: int, orchestration: str = "manual", backend: str = "trusted_local"):
    return {"schema_version": 1, "decision_source": "replay",
            "orchestration": orchestration, "backend": backend,
            "scenarios": {}, "evidence": {"group": f"12-{group}"},
            "limits": {"live_model": "not_run", "container": "deferred_by_user",
                       "model_turns": 30, "tool_calls": 60,
                       "deadline_seconds": 300,
                       "platform_factors": {"os_name": os.name,
                                            "symlink_probe": "separate"}}}


def _tool(call_id: str, name: str, arguments: dict) -> dict:
    return {"kind": "tool", "text": "",
            "call": {"call_id": call_id, "name": name, "arguments": arguments}}


def _manual_complete(directory: Path) -> tuple[dict, list[dict]]:
    root = create_workspace(directory / "repo")
    source_version = read_file(root, "src/linkcheck.py")["version"]
    decisions = [
        _tool("read-source", "read_file", {"path": "src/linkcheck.py"}),
        _tool("add-test", "apply_patch", {"path": "tests/test_agent_nested.py",
              "version": "absent", "old": "", "new": REGRESSION}),
        _tool("red-tests", "run_tests", {"preset": "candidate_tests"}),
        _tool("fix-source", "apply_patch", {"path": "src/linkcheck.py",
              "version": source_version, "old": "candidate = root / target",
              "new": "candidate = document.parent / target"}),
        _tool("green-tests", "run_tests", {"preset": "candidate_tests"}),
        {"kind": "final", "text": "request independent verification", "call": None},
    ]
    store = Store(control_path(root) / "state.sqlite")
    state = new_state("experiment-run", "Repair nested Markdown links",
                      "trusted_local", time.time())
    model = ReplayModel(decisions)
    services = Services(root, store, model, "trusted_local", threading.Event())
    state = run(state, services)
    for _ in range(3):
        if state["status"] != "awaiting_approval":
            break
        state = resolve_approval(state, store, True)
        state = services.resume(state)
        state = run(state, services)
    return {"state": state, "diff": show_diff(root)}, store.events("experiment-run")


def _group1(directory: Path) -> dict:
    outcome, events = _manual_complete(directory)
    state = outcome["state"]
    red = [event for event in events if event["kind"] == "tool_observed"
           and event["payload"].get("error") == "tests_failed"]
    verification = state["evidence"]["verification"]
    observed = {"status": state["status"], "red_observed": len(red) == 1,
                "writes": sum(event["kind"] == "action_written" for event in events),
                "diff_paths": outcome["diff"]["paths"],
                "candidate_tests": verification["candidate_tests"]["discovered"],
                "verification_passed": verification["passed"],
                "acceptance_case_count": verification["acceptance"]["case_count"]}
    report = _base(1)
    report["scenarios"] = {
        "offline_complete": _case(
            "read → regression red → two approved patches → green → verifier",
            observed,
            "completed only after one failing candidate-test observation and independent acceptance",
            offline_completion_proved(observed),
            "Replay decisions do not measure live model capability."),
        "live_complete": _case(
            "container preflight then real model run",
            {"status": "deferred", "reason": "container_runtime_not_authorized"},
            "a complete sanitized live trace exists",
            False,
            "Offline success is not a substitute for a live model run."),
    }
    report["evidence"].update({"event_kinds": [event["kind"] for event in events],
                               "artifact": "logical:offline-complete"})
    return report


def _error_name(function):
    try:
        function()
    except Exception as error:
        return str(error) or type(error).__name__
    return None


def _group2(directory: Path) -> dict:
    root = create_workspace(directory / "repo")
    before = workspace_manifest(root)
    unknown = executor.dispatch(root, {"call_id": "bad", "name": "shell",
        "arguments": {}}, "trusted_local", threading.Event())
    invalid = _error_name(lambda: validate_call({"call_id": "bad-args",
        "name": "read_file", "arguments": {"path": "README.md", "extra": True}}))
    output = backends.run_preset(root, "probe_output", "trusted_local", 5, 256,
                                 threading.Event())

    stale_root = create_workspace(directory / "stale")
    version = read_file(stale_root, "src/linkcheck.py")["version"]
    (stale_root / "src/linkcheck.py").write_text(
        (stale_root / "src/linkcheck.py").read_text(encoding="utf-8") + "\n# external\n",
        encoding="utf-8", newline="\n")
    stale = _error_name(lambda: prepare_patch(stale_root, {"call_id": "stale",
        "name": "apply_patch", "arguments": {"path": "src/linkcheck.py",
        "version": version, "old": "root / target", "new": "document.parent / target"}}))

    false_root = create_workspace(directory / "false")
    baseline = capture_baseline(false_root)
    (false_root / "src/linkcheck.py").write_text(
        "def broken_links(document, root):\n    return []\n", encoding="utf-8", newline="\n")
    false_verdict = verify(false_root, "trusted_local", baseline, threading.Event())

    announce_root = create_workspace(directory / "announce")
    store = Store(control_path(announce_root) / "state.sqlite")
    announced = run(new_state("false-finish", "repair", "trusted_local", time.time()),
        Services(announce_root, store,
            ReplayModel([{"kind": "final", "text": "done", "call": None}]),
            "trusted_local", threading.Event()))
    unchanged = workspace_manifest(root) == before
    report = _base(2)
    report["scenarios"] = {
        "unknown_tool": _case("reject before dispatch",
            {"error": unknown["error"], "workspace_unchanged": unchanged},
            "unknown_tool and no side effect", unknown["error"] == "unknown_tool" and unchanged,
            "Schema rejection does not sandbox known tools."),
        "invalid_arguments": _case("strict fields", {"error": invalid},
            "extra fields rejected", invalid == "invalid_fields",
            "It does not prove semantic correctness of valid arguments."),
        "output_truncation": _case("drain pipes and cap bytes",
            {"truncated": output["truncated"],
             "stored_bytes": len((output["stdout"] + output["stderr"]).encode())},
            "truncated=true and stored_bytes<=256", output["truncated"] and
            len((output["stdout"] + output["stderr"]).encode()) <= 256,
            "This is a host-process output test, not container isolation."),
        "stale_patch": _case("reject old version", {"error": stale},
            "stale_version", stale == "stale_version",
            "It does not resolve the user's external edit."),
        "always_empty": _case("independent missing-link case fails",
            {"accepted": false_verdict["passed"],
             "failed_cases": false_verdict["failed_cases"]},
            "nested_missing is rejected", not false_verdict["passed"] and
            "nested_missing" in false_verdict["failed_cases"],
            "Cooperative acceptance is not hostile-code containment."),
        "false_finish": _case("model text triggers verifier, not completion",
            {"accepted": announced["status"] == "completed",
             "status": announced["status"]},
            "status is not completed", announced["status"] != "completed",
            "Replay output does not measure instruction following."),
    }
    report["evidence"].update({"logical_events": ["validation", "bounded_output",
        "version_conflict", "independent_acceptance", "completion_protocol"]})
    return report


def _paused(directory: Path, run_id: str):
    root = create_workspace(directory / "repo")
    store = Store(control_path(root) / "state.sqlite")
    version = read_file(root, "src/linkcheck.py")["version"]
    decisions = [_tool("patch", "apply_patch", {"path": "src/linkcheck.py",
        "version": version, "old": "candidate = root / target",
        "new": "candidate = document.parent / target"})]
    state = run(new_state(run_id, "repair", "trusted_local", time.time()),
                Services(root, store, ReplayModel(decisions),
                         "trusted_local", threading.Event()))
    return root, store, state, decisions


def _group3(directory: Path) -> dict:
    root, store, state, decisions = _paused(directory / "resume", "resume")
    action_id = state["pending"]["action_id"]
    state = resolve_approval(state, store, True)
    services = Services(root, store, ReplayModel(decisions, state["provider_state"]),
                        "trusted_local", threading.Event())
    state = services.resume(state)
    state = services.resume(state)
    events = store.events("resume")

    stale_root, stale_store, stale_state, _ = _paused(directory / "stale", "stale")
    stale_state = resolve_approval(stale_state, stale_store, True)
    (stale_root / "notes.txt").write_text("external", encoding="utf-8")
    stale_state = recover(stale_root, stale_store, stale_state)

    crash_root, crash_store, crash_state, _ = _paused(directory / "receipt", "receipt")
    crash_state = resolve_approval(crash_state, crash_store, True)
    action = crash_store.action(crash_state["pending"]["action_id"])
    write_patch(crash_root, action["patch"])
    crash_store.append_event("receipt", "action_written", {"path": action["patch"]["path"]},
                             action["call_id"], action["action_id"])
    crash_state = recover(crash_root, crash_store, crash_state)
    crash_events = crash_store.events("receipt")
    report = _base(3)
    report["scenarios"] = {
        "approval_resume": _case("one approved action, one write, one receipt",
            {"status": state["status"], "action_bound": bool(action_id),
             "writes": sum(e["kind"] == "action_written" for e in events),
             "receipts": sum(e["kind"] == "action_receipt" for e in events)},
            "repeated resume keeps write and receipt at one",
            state["status"] == "ready" and exactly_one_write_and_receipt(events),
            "This does not make filesystem and SQLite one atomic transaction."),
        "stale_approval": _case("preserve external edit and stop",
            {"status": stale_state["status"], "reason": stale_state["reason"]},
            "approval_stale", stale_state["reason"] == "approval_stale",
            "The Agent does not merge the external change."),
        "write_before_receipt": _case("record receipt without second write",
            {"status": crash_state["status"],
             "writes": sum(e["kind"] == "action_written" for e in crash_events),
             "receipts": sum(e["kind"] == "action_receipt" for e in crash_events)},
            "one write and one recovered receipt",
            crash_state["status"] == "ready"
            and exactly_one_write_and_receipt(crash_events),
            "Only the named cooperative crash window is covered."),
    }
    report["evidence"].update({"logical_events": ["action_intent", "approval_recorded",
        "action_written", "action_receipt", "recovery_uncertain"]})
    return report


def _group4(directory: Path) -> dict:
    root = create_workspace(directory / "repo")
    state = new_state("context", "retain required state", "trusted_local", 0)
    state["workspace_hash"] = "a" * 64
    for index in range(20):
        state["messages"].append({"role": "user", "content": f"old observation {index} " * 20})
    view = build_context(state, 1800)
    compacted = any("history_compaction" in item.get("content", "") for item in view)
    summary = json.loads(view[0]["content"])
    retained = authoritative_summary_retained(summary)
    denied = _error_name(lambda: safe_path(root, "../outside"))
    container = backends.probe_container()
    cancel = threading.Event(); cancel.set()
    stopped = backends.run_preset(root, "probe_sleep", "trusted_local", 0, 128, cancel)
    report = _base(4, backend="mixed:trusted_local+container_probe")
    report["scenarios"] = {
        "context_compaction": _case("bounded view retains authoritative summary",
            {"compacted": compacted, "view_bytes": len(json.dumps(view).encode()),
             "authoritative_summary_retained": retained},
            "compacted, <=1800 bytes, and authoritative facts retained",
            compacted and len(json.dumps(view).encode()) <= 1800 and retained,
            "Byte budget is not a tokenizer count."),
        "path_boundary": _case("parent traversal rejected", {"error": denied},
            "path_denied", denied == "path_denied",
            "A path validator is not an OS sandbox."),
        "container_isolation": _case("all real isolation probes pass",
            container, "isolation_passed=true", container["isolation_passed"] is True,
            "deferred container probes cannot be replaced by policy or replay."),
        "cancel_and_deadline": _case("both facts recorded, cancellation wins reason",
            {"cancelled": stopped["cancelled"], "timed_out": stopped["timed_out"],
             "reason": stopped["reason"]},
            "cancelled and timed_out, reason=cancelled",
            stopped["cancelled"] and stopped["timed_out"] and stopped["reason"] == "cancelled",
            "Host process cancellation is not container cleanup evidence."),
    }
    report["evidence"].update({"container_probe_source": "chapter12.backends.probe_container",
                               "policy_and_os_probe_separate": True})
    return report


def _group5(directory: Path) -> dict:
    from .tests.framework_cases import run_scenario

    manual, manual_events = _manual_complete(directory / "manual")
    graph = run_scenario("langgraph", "complete", directory / "langgraph")
    sdk = run_scenario("agents_sdk", "complete", directory / "agents-sdk")
    report = _base(5, orchestration="comparison")
    versions = {"python": sys.version.split()[0],
                "langgraph": importlib.metadata.version("langgraph"),
                "openai_agents": importlib.metadata.version("openai-agents")}
    observations = {
        "manual": {"status": manual["state"]["status"],
                   "writes": sum(e["kind"] == "action_written" for e in manual_events),
                   "candidate_tests": manual["state"]["evidence"]["verification"]
                        ["candidate_tests"]["discovered"]},
        "langgraph": {key: graph[key] for key in ("status", "writes", "candidate_tests")},
        "agents_sdk": {key: sdk[key] for key in ("status", "writes", "candidate_tests")},
    }
    report["scenarios"] = {name: _case("shared task, two approved writes, verifier passes",
        observed, "status=completed, writes=2, candidate_tests=3",
        observed == {"status": "completed", "writes": 2, "candidate_tests": 3},
        "One fixture does not rank framework quality or model capability.")
        for name, observed in observations.items()}
    report["evidence"].update({"versions": versions,
        "responsibility": {"manual": "application while-loop",
                           "langgraph": "StateGraph nodes and checkpoint",
                           "agents_sdk": "Runner, Model, function tools and RunState"}})
    return report


def run_group(group: int, directory: Path) -> dict:
    if type(group) is not int or group not in range(1, 6):
        raise ValueError("unknown_group")
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError("experiment_directory_exists")
    directory.mkdir(parents=True, exist_ok=True)
    return {1: _group1, 2: _group2, 3: _group3, 4: _group4, 5: _group5}[group](directory)


def _archive_existing(output: Path) -> None:
    index = 1
    while True:
        candidate = output.with_name(f"{output.name}.previous-{index}")
        if not candidate.exists():
            output.rename(candidate)
            return
        index += 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", required=True, choices=("1", "2", "3", "4", "5", "all"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.absolute()
    if output.exists():
        if not args.replace:
            print("output_exists: use a new directory or --replace", file=sys.stderr)
            return 2
        _archive_existing(output)
    output.mkdir(parents=True)
    groups = range(1, 6) if args.group == "all" else [int(args.group)]
    reports = {}
    for number in groups:
        report = canonicalize(run_group(number, output / ".work" / f"group-{number}"))
        reports[str(number)] = report
        (output / f"group-{number}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
    (output / "manifest.json").write_text(json.dumps({"schema_version": 1,
        "groups": list(reports), "decision_source": "replay"}, indent=2,
        sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if args.group == "all":
        (output / "offline-canonical.json").write_text(json.dumps({
            "schema_version": 1, "decision_source": "replay", "groups": reports},
            ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
