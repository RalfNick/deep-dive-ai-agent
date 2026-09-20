from __future__ import annotations

import asyncio
import json
from pathlib import Path
import threading
import time

import pytest

from chapter12.adapters.sdk_agent import build_agent, run_sdk
from chapter12.adapters.sdk_compat import dump_state, load_state
from chapter12.adapters.sdk_replay_model import make_model
from chapter12.contracts import new_state
from chapter12.prepare import control_path, create_workspace
from chapter12.services import Services
from chapter12.state import Store
from chapter12.tests.framework_cases import run_scenario
from chapter12.tools import read_file


@pytest.mark.parametrize("scenario", ["complete", "approval_restart", "tool_error"])
def test_sdk_real_scenarios_complete(scenario, tmp_path):
    result = run_scenario("agents_sdk", scenario, tmp_path / scenario)
    assert result["status"] == "completed"
    assert result["writes"] == 2 and result["receipts"] == 2
    assert result["orchestration"] == "agents_sdk"
    assert result["framework_version"]
    assert result["sdk_tool_invocations"] >= 2


def test_sdk_native_pause_survives_process_exit(tmp_path):
    result = run_scenario("agents_sdk", "approval_restart", tmp_path)
    assert result["status"] == "completed"
    assert len(set(result["process_ids"])) >= 3
    assert any(event["kind"] == "sdk_interruption" for event in result["events"])
    assert result["snapshot_roundtrips"] >= 2


def test_sdk_final_output_is_not_acceptance(tmp_path):
    result = run_scenario("agents_sdk", "false_finish", tmp_path)
    assert result["status"] != "completed"
    assert result["writes"] == 0
    assert result["verification_failures"] >= 1


def test_sdk_does_not_wrap_manual_runtime(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("manual loop reached")
    monkeypatch.setattr("chapter12.runtime.run", forbidden)
    assert run_scenario("agents_sdk", "complete", tmp_path)["status"] == "completed"


def _one_patch(tmp_path: Path):
    root = create_workspace(tmp_path / "repo")
    call = {"call_id": "patch-1", "name": "apply_patch", "arguments": {
        "path": "src/linkcheck.py", "version": read_file(root, "src/linkcheck.py")["version"],
        "old": "candidate = root / target", "new": "candidate = document.parent / target"}}
    decisions = [{"kind": "tool", "text": "", "call": call},
                 {"kind": "final", "text": "verify", "call": None}]
    store = Store(control_path(root) / "state.sqlite")
    state = new_state("r1", "repair", "trusted_local", time.time())
    model = make_model(decisions)
    services = Services(root, store, model, "trusted_local", threading.Event())
    return root, store, state, services, decisions


def test_native_state_roundtrip_excludes_context_and_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-" + "EXAMPLE_NOT_REAL" * 2)
    root, store, state, services, decisions = _one_patch(tmp_path)
    snapshot = control_path(root) / "sdk-state.json"
    paused = run_sdk(state, services, snapshot)
    assert paused["status"] == "awaiting_approval"
    text = snapshot.read_text(encoding="utf-8")
    assert "EXAMPLE_NOT_REAL" not in text
    agent = build_agent(services)
    restored = asyncio.run(load_state(agent, text))
    assert len(restored.get_interruptions()) == 1
    redumped = dump_state(restored)
    assert "EXAMPLE_NOT_REAL" not in redumped
    assert json.loads(redumped)["$schemaVersion"] == json.loads(text)["$schemaVersion"]


def test_native_approval_cannot_bypass_workspace_guard(tmp_path):
    root, store, state, services, decisions = _one_patch(tmp_path)
    snapshot = control_path(root) / "sdk-state.json"
    paused = run_sdk(state, services, snapshot)
    (root / "notes.txt").write_text("external user edit", encoding="utf-8")
    resumed_model = make_model(decisions)
    resumed_services = Services(root, store, resumed_model, "trusted_local", threading.Event())
    result = run_sdk(store.load("r1"), resumed_services, snapshot, True)
    assert result["status"] == "failed"
    assert result["reason"] == "approval_stale"
    assert not [event for event in store.events("r1") if event["kind"] == "action_written"]


def test_make_model_is_real_sdk_model_not_application_simulator():
    from agents.models.interface import Model
    model = make_model([{"kind": "final", "text": "done", "call": None}])
    assert isinstance(model, Model)
    assert not hasattr(model, "services")
