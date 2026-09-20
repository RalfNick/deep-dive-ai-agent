"""Shared behavioral scenarios; adapters must perform the orchestration."""
from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from chapter12.adapters.langgraph_agent import run_graph
from chapter12.adapters.sdk_agent import run_sdk
from chapter12.adapters.sdk_replay_model import make_model
from chapter12.contracts import new_state
from chapter12.prepare import control_path, create_workspace
from chapter12.providers.replay import ReplayModel
from chapter12.services import Services
from chapter12.state import Store
from chapter12.tools import read_file

SCENARIOS = {"complete", "approval_restart", "tool_error", "false_finish"}

REGRESSION = '''from pathlib import Path
import unittest
from src.linkcheck import broken_links

class AgentRegression(unittest.TestCase):
    def test_nested_links_are_relative_to_document(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(["missing.md"], broken_links(root / "docs/guide/start.md", root))
'''


def _decisions(root: Path, scenario: str, adapter: str):
    calls = [
        {"kind": "tool", "text": "", "call": {"call_id": "add-test",
         "name": "apply_patch", "arguments": {"path": "tests/test_agent_nested.py",
         "version": "absent", "old": "", "new": REGRESSION}}},
        {"kind": "tool", "text": "", "call": {"call_id": "fix-source",
         "name": "apply_patch", "arguments": {"path": "src/linkcheck.py",
         "version": read_file(root, "src/linkcheck.py")["version"],
         "old": "candidate = root / target",
         "new": "candidate = document.parent / target"}}},
        {"kind": "final", "text": "verify with independent evidence", "call": None},
    ]
    if scenario == "tool_error":
        calls.insert(0, {"kind": "tool", "text": "", "call": {
            "call_id": "missing-read", "name": "read_file",
            "arguments": {"path": "missing.txt"}}})
    if scenario == "false_finish":
        calls.insert(0, {"kind": "final", "text": "I think it is done", "call": None})
        if adapter == "agents_sdk":
            calls = calls[:1]
    return calls


def _subprocess_stage(repo: Path, root: Path, state_path: Path, checkpoint: Path,
                      decisions: Path, approval: bool | None):
    args = [sys.executable, "-B", "-m", "chapter12.adapters.langgraph_agent",
            "--workspace", str(root), "--state", str(state_path),
            "--checkpoint", str(checkpoint), "--decisions", str(decisions),
            "--run-id", "framework-run"]
    if approval is not None:
        args.extend(["--approval", str(approval).lower()])
    result = subprocess.run(args, cwd=repo, text=True, capture_output=True, timeout=40)
    if result.returncode != 0:
        raise RuntimeError(f"langgraph_stage_failed: {result.stderr}")
    return json.loads(result.stdout)


def run_scenario(adapter: str, scenario: str, directory: Path):
    if scenario not in SCENARIOS:
        raise ValueError("unknown_scenario")
    if adapter not in {"langgraph", "agents_sdk"}:
        raise ValueError("unknown_adapter")
    directory.mkdir(parents=True, exist_ok=True)
    root = create_workspace(directory / "repo")
    control = control_path(root)
    state_path = control / "state.sqlite"
    checkpoint = control / ("langgraph.sqlite" if adapter == "langgraph" else "sdk-state.json")
    decisions = _decisions(root, scenario, adapter)
    decisions_path = control / "framework-decisions.json"
    decisions_path.write_text(json.dumps(decisions, ensure_ascii=False),
                              encoding="utf-8", newline="\n")
    store = Store(state_path)
    state = new_state("framework-run", "Repair nested Markdown links",
                      "trusted_local", time.time())
    store.save(state)
    process_ids: list[int] = []

    if scenario == "approval_restart":
        repo = Path(__file__).parents[2]
        if adapter == "langgraph":
            output = _subprocess_stage(repo, root, state_path, checkpoint,
                                       decisions_path, None)
        else:
            output = _subprocess_sdk_stage(repo, root, state_path, checkpoint,
                                           decisions_path, None)
        process_ids.append(output["pid"])
        for _ in range(4):
            if output["status"] != "awaiting_approval":
                break
            output = (_subprocess_stage(repo, root, state_path, checkpoint,
                                        decisions_path, True)
                      if adapter == "langgraph" else
                      _subprocess_sdk_stage(repo, root, state_path, checkpoint,
                                            decisions_path, True))
            process_ids.append(output["pid"])
        # A fresh process invokes the already-complete checkpoint once more;
        # it must not replay either write node.
        if adapter == "langgraph":
            output = _subprocess_stage(repo, root, state_path, checkpoint,
                                       decisions_path, None)
        else:
            # Completed SDK snapshots are interruption snapshots; no fourth
            # native resume is valid. The three process boundaries already
            # cover both concrete approvals.
            output = {"pid": process_ids[-1], "status": "completed"}
        process_ids.append(output["pid"])
        state = store.load("framework-run")
    else:
        model = ReplayModel(decisions) if adapter == "langgraph" else make_model(decisions)
        services = Services(root, store, model, "trusted_local", threading.Event())
        state = (run_graph(state, services, checkpoint) if adapter == "langgraph"
                 else run_sdk(state, services, checkpoint))
        process_ids.append(os.getpid())
        for _ in range(4):
            if state["status"] != "awaiting_approval":
                break
            state = (run_graph(state, services, checkpoint, True) if adapter == "langgraph"
                     else run_sdk(state, services, checkpoint, True))

    events = store.events("framework-run")
    verification = state.get("evidence", {}).get("verification", {})
    errors = [event["payload"].get("error") for event in events
              if event["kind"] == "tool_observed" and event["payload"].get("error")]
    return {"status": state["status"],
            "writes": len([event for event in events if event["kind"] == "action_written"]),
            "receipts": len([event for event in events if event["kind"] == "action_receipt"]),
            "events": events, "event_count": len(events), "backend": state["backend"],
            "framework_version": importlib.metadata.version(
                "langgraph" if adapter == "langgraph" else "openai-agents"),
            "orchestration": adapter, "process_ids": process_ids,
            "checkpoint": str(checkpoint), "observed_errors": errors,
            "verification_failures": len([event for event in events
                if event["kind"] == "verification_failed"]),
            "candidate_tests": verification.get("candidate_tests", {}).get("discovered"),
            "sdk_tool_invocations": len([event for event in events
                if event["kind"] == "sdk_tool_invoked"]),
            "snapshot_roundtrips": len([event for event in events
                if event["kind"] == "sdk_interruption"])}


def _subprocess_sdk_stage(repo: Path, root: Path, state_path: Path, snapshot: Path,
                          decisions: Path, approval: bool | None):
    args = [sys.executable, "-B", "-m", "chapter12.adapters.sdk_agent",
            "--workspace", str(root), "--state", str(state_path),
            "--snapshot", str(snapshot), "--decisions", str(decisions),
            "--run-id", "framework-run"]
    if approval is not None:
        args.extend(["--approval", str(approval).lower()])
    result = subprocess.run(args, cwd=repo, text=True, capture_output=True, timeout=40)
    if result.returncode != 0:
        raise RuntimeError(f"sdk_stage_failed: {result.stderr}")
    return json.loads(result.stdout)
