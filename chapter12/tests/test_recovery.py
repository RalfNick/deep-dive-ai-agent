from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from chapter12.contracts import new_state
from chapter12.prepare import control_path, create_workspace
from chapter12.providers.replay import ReplayModel
from chapter12.recovery import classify, recover, resolve_approval
from chapter12.runtime import run
from chapter12.services import Services
from chapter12.state import Store, workspace_lock
from chapter12.tools import read_file


def patch_decisions(root: Path):
    return [
        {"kind": "tool", "text": "", "call": {"call_id": "patch-1",
         "name": "apply_patch", "arguments": {"path": "src/linkcheck.py",
         "version": read_file(root, "src/linkcheck.py")["version"],
         "old": "candidate = root / target",
         "new": "candidate = document.parent / target"}}},
        {"kind": "final", "text": "verify the result", "call": None},
    ]


def paused(tmp_path: Path):
    root = create_workspace(tmp_path / "repo")
    store = Store(control_path(root) / "state.sqlite")
    state = new_state("r1", "repair", "trusted_local", time.time())
    decisions = patch_decisions(root)
    result = run(state, Services(root, store, ReplayModel(decisions),
                                 "trusted_local", threading.Event()))
    return root, store, decisions, result


def test_crash_recovery_is_three_way():
    assert classify("before", "after", "after") == "record_receipt"
    assert classify("before", "after", "before") == "recheck_approval"
    assert classify("before", "after", "external") == "uncertain"
    with pytest.raises(ValueError, match="no_op_patch"):
        classify("same", "same", "same")


def test_approval_is_bound_to_exact_pending_action_and_rejection_is_observed(tmp_path):
    root, store, decisions, state = paused(tmp_path)
    action_id = state["pending"]["action_id"]
    with pytest.raises(ValueError, match="approval_mismatch"):
        resolve_approval(dict(state, run_id="other"), store, True)
    rejected = resolve_approval(state, store, False)
    assert rejected["status"] == "ready" and rejected["pending"] is None
    result = json.loads(rejected["messages"][-1]["content"])
    assert result["error"] == "approval_denied"
    action = store.action(action_id)
    assert action["result"]["ok"] is False


def test_approved_patch_executes_once_and_second_resume_is_idempotent(tmp_path):
    root, store, decisions, state = paused(tmp_path)
    action_id = state["pending"]["action_id"]
    state = resolve_approval(state, store, True)
    services = Services(root, store, ReplayModel(decisions, state["provider_state"]),
                        "trusted_local", threading.Event())
    state = services.resume(state)
    assert state["status"] == "ready"
    state = services.resume(state)
    assert (root / "src/linkcheck.py").read_text(encoding="utf-8").count(
        "candidate = document.parent / target") == 1
    events = store.events("r1")
    assert len([event for event in events if event["kind"] == "action_written"]) == 1
    assert len([event for event in events if event["kind"] == "action_receipt"]) == 1
    assert store.action(action_id)["result"]["ok"] is True


def test_external_edit_after_approval_is_preserved_and_marked_stale(tmp_path):
    root, store, decisions, state = paused(tmp_path)
    state = resolve_approval(state, store, True)
    external = root / "notes.txt"
    external.write_text("user edit", encoding="utf-8")
    recovered = recover(root, store, state)
    assert recovered["status"] == "failed"
    assert recovered["reason"] == "approval_stale"
    assert external.read_text(encoding="utf-8") == "user edit"


def test_workspace_lock_prevents_approved_writer(tmp_path):
    root, store, decisions, state = paused(tmp_path)
    state = resolve_approval(state, store, True)
    services = Services(root, store, ReplayModel(decisions, state["provider_state"]),
                        "trusted_local", threading.Event())
    with workspace_lock(root):
        with pytest.raises(RuntimeError, match="workspace_locked"):
            services.resume(state)


def _cli(repo: Path, args: list[str], env=None):
    return subprocess.run([sys.executable, "-B", "-m", "chapter12.quickstart", *args],
                          cwd=repo, env=env, text=True, capture_output=True, timeout=30)


def _write_cli_fixture(tmp_path: Path):
    # Prepare only to calculate the immutable shipped fixture version, then use
    # another path for the actual CLI-created workspace.
    probe = create_workspace(tmp_path / "probe")
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps(patch_decisions(probe)), encoding="utf-8")
    return tmp_path / "cli-repo", decisions


def _start_and_action(repo: Path, workspace: Path, decisions: Path):
    started = _cli(repo, ["start", "--workspace", str(workspace), "--run-id", "r1",
                          "--replay", str(decisions), "--trust-replay-file"])
    assert started.returncode == 0, started.stderr
    output = json.loads(started.stdout)
    assert output["status"] == "awaiting_approval"
    return output["action_id"]


def test_real_process_start_approve_resume_and_repeat_resume(tmp_path):
    repo = Path(__file__).parents[2]
    workspace, decisions = _write_cli_fixture(tmp_path)
    action_id = _start_and_action(repo, workspace, decisions)
    approved = _cli(repo, ["approve", "--workspace", str(workspace), "--run-id", "r1",
                           "--action-id", action_id])
    assert approved.returncode == 0, approved.stderr
    resumed = _cli(repo, ["resume", "--workspace", str(workspace), "--run-id", "r1",
                          "--replay", str(decisions), "--trust-replay-file"])
    assert resumed.returncode == 0 and json.loads(resumed.stdout)["status"] == "completed"
    again = _cli(repo, ["resume", "--workspace", str(workspace), "--run-id", "r1",
                        "--replay", str(decisions), "--trust-replay-file"])
    assert again.returncode == 0 and json.loads(again.stdout)["status"] == "completed"
    store = Store(control_path(workspace) / "state.sqlite")
    events = store.events("r1")
    assert len([event for event in events if event["kind"] == "action_written"]) == 1
    assert len([event for event in events if event["kind"] == "action_receipt"]) == 1
    assert store.load("r1")["counters"]["model_turns"] == 2


def test_real_process_resumes_verification_without_another_model_turn(tmp_path):
    repo = Path(__file__).parents[2]
    workspace, decisions = _write_cli_fixture(tmp_path)
    action_id = _start_and_action(repo, workspace, decisions)
    assert _cli(repo, ["approve", "--workspace", str(workspace), "--run-id", "r1",
                       "--action-id", action_id]).returncode == 0
    environment = dict(os.environ, CHAPTER12_TEST_MODE="1",
                       CHAPTER12_TEST_FAULT="during_verification")

    crashed = _cli(repo, ["resume", "--workspace", str(workspace), "--run-id", "r1",
                          "--replay", str(decisions), "--trust-replay-file"], environment)
    assert crashed.returncode == 73
    store = Store(control_path(workspace) / "state.sqlite")
    assert store.load("r1")["status"] == "verifying"
    assert store.load("r1")["counters"]["model_turns"] == 2

    resumed = _cli(repo, ["resume", "--workspace", str(workspace), "--run-id", "r1",
                          "--replay", str(decisions), "--trust-replay-file"])
    assert resumed.returncode == 0, resumed.stderr
    state = store.load("r1")
    assert state["status"] == "completed"
    assert state["counters"]["model_turns"] == 2
    kinds = [event["kind"] for event in store.events("r1")]
    assert kinds.count("verification_started") == 1
    assert kinds.count("verification_resumed") == 1


@pytest.mark.parametrize("fault,expected_code", [
    ("after_intent", 71), ("after_write_before_receipt", 72)])
def test_real_process_crash_windows_recover_without_duplicate_write(
        tmp_path, fault, expected_code):
    repo = Path(__file__).parents[2]
    workspace, decisions = _write_cli_fixture(tmp_path)
    environment = dict(os.environ, CHAPTER12_TEST_MODE="1", CHAPTER12_TEST_FAULT=fault)
    if fault == "after_intent":
        crashed = _cli(repo, ["start", "--workspace", str(workspace), "--run-id", "r1",
                              "--replay", str(decisions), "--trust-replay-file"], environment)
        assert crashed.returncode == expected_code
        # approve reconstructs the pending action from durable intent.
        store = Store(control_path(workspace) / "state.sqlite")
        action_id = store.unresolved_actions("r1")[0]["action_id"]
        approved = _cli(repo, ["approve", "--workspace", str(workspace), "--run-id", "r1",
                               "--action-id", action_id])
        assert approved.returncode == 0, approved.stderr
    else:
        action_id = _start_and_action(repo, workspace, decisions)
        assert _cli(repo, ["approve", "--workspace", str(workspace), "--run-id", "r1",
                           "--action-id", action_id]).returncode == 0
        crashed = _cli(repo, ["resume", "--workspace", str(workspace), "--run-id", "r1",
                              "--replay", str(decisions), "--trust-replay-file"], environment)
        assert crashed.returncode == expected_code
    resumed = _cli(repo, ["resume", "--workspace", str(workspace), "--run-id", "r1",
                          "--replay", str(decisions), "--trust-replay-file"])
    assert resumed.returncode == 0, resumed.stderr
    store = Store(control_path(workspace) / "state.sqlite")
    events = store.events("r1")
    assert len([event for event in events if event["kind"] == "action_written"]) == 1
    assert len([event for event in events if event["kind"] == "action_receipt"]) == 1
    assert store.load("r1")["counters"]["model_turns"] == 2
