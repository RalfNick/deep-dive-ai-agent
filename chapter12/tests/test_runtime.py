from __future__ import annotations

import copy
import json
from pathlib import Path
import threading
import time

import pytest

from chapter12.contracts import new_state, validate_result
from chapter12.prepare import create_workspace
from chapter12.providers.replay import ReplayModel
from chapter12.quickstart import main
from chapter12.runtime import run
from chapter12.services import Services
from chapter12.state import Store
from chapter12.tools import read_file, workspace_manifest
from chapter12.tests.test_verifier import CORRECT


def setup(tmp_path: Path, decisions, state=None):
    root = create_workspace(tmp_path / "repo")
    db = Store(tmp_path / "state.sqlite")
    value = state or new_state("r1", "repair nested links", "trusted_local", time.time())
    model = ReplayModel(decisions, value.get("provider_state") or None)
    return root, db, model, value, Services(root, db, model, "trusted_local",
                                             threading.Event())


def call(call_id, name, arguments):
    return {"kind": "tool", "text": "",
            "call": {"call_id": call_id, "name": name, "arguments": arguments}}


@pytest.mark.parametrize("value", [
    {"call_id": "c1", "ok": True, "data": {}, "error": "contradiction",
     "truncated": False},
    {"call_id": "c1", "ok": False, "data": {}, "error": None,
     "truncated": False},
    {"call_id": "c1", "ok": True, "data": [], "error": None,
     "truncated": False},
])
def test_tool_result_contract_rejects_ambiguous_records(value):
    with pytest.raises(ValueError, match="invalid_tool_result"):
        validate_result(value)


def test_model_cannot_announce_success(tmp_path):
    root, db, model, state, services = setup(
        tmp_path, [{"kind": "final", "text": "完成了", "call": None}])
    result = run(state, services)
    assert result["status"] != "completed"
    assert any(event["kind"] == "verification_failed" for event in db.events("r1"))


def test_valid_patch_stops_for_approval_without_mutation(tmp_path):
    root = create_workspace(tmp_path / "repo")
    before = (root / "src/linkcheck.py").read_bytes()
    version = read_file(root, "src/linkcheck.py")["version"]
    decision = call("c1", "apply_patch", {"path": "src/linkcheck.py", "version": version,
        "old": "candidate = root / target", "new": "candidate = document.parent / target"})
    db = Store(tmp_path / "state.sqlite")
    state = new_state("r1", "repair", "trusted_local", time.time())
    model = ReplayModel([decision])
    result = run(state, Services(root, db, model, "trusted_local", threading.Event()))
    assert result["status"] == "awaiting_approval"
    assert result["pending"]["action_id"]
    assert (root / "src/linkcheck.py").read_bytes() == before
    assert result["provider_state"] == {"cursor": 1}


def test_failed_tool_result_is_a_complete_observation(tmp_path):
    decisions = [call("c1", "read_file", {"path": "missing.txt"}),
                 {"kind": "final", "text": "done", "call": None}]
    root, db, model, state, services = setup(tmp_path, decisions)
    result = run(state, services)
    tool_messages = [item for item in result["messages"] if item.get("role") == "tool"]
    assert json.loads(tool_messages[0]["content"])["error"] == "file_missing"
    assert tool_messages[0]["tool_call_id"] == "c1"
    assert result["counters"]["tool_calls"] == 1


def test_unknown_tool_has_no_side_effect_and_becomes_observation(tmp_path):
    class InvalidModel:
        provider_state = {}
        def next(self, messages):
            return call("bad1", "shell", {"command": "remove everything"})

    root = create_workspace(tmp_path / "repo")
    before = workspace_manifest(root)
    db = Store(tmp_path / "state.sqlite")
    state = new_state("r1", "repair", "trusted_local", time.time())
    result = run(state, Services(root, db, InvalidModel(), "trusted_local",
                                 threading.Event(), max_model_turns=1))
    assert workspace_manifest(root) == before
    observation = next(item for item in result["messages"] if item.get("role") == "tool")
    assert json.loads(observation["content"])["error"] == "unknown_tool"


def test_cancel_and_budgets_stop_before_model_or_tool(tmp_path):
    root, db, model, state, services = setup(
        tmp_path, [{"kind": "final", "text": "unused", "call": None}])
    services.cancel.set()
    assert run(state, services)["status"] == "cancelled"
    assert model.provider_state == {"cursor": 0}

    expired = new_state("r2", "repair", "trusted_local", 0)
    expired["deadline"] = 1
    second = ReplayModel([{"kind": "final", "text": "unused", "call": None}])
    result = run(expired, Services(root, db, second, "trusted_local", threading.Event()))
    assert result["status"] == "budget_exhausted" and result["reason"] == "deadline"

    limited = new_state("r3", "repair", "trusted_local", time.time())
    limited["counters"]["model_turns"] = 30
    third = ReplayModel([{"kind": "final", "text": "unused", "call": None}])
    result = run(limited, Services(root, db, third, "trusted_local", threading.Event()))
    assert result["status"] == "budget_exhausted" and result["reason"] == "model_budget"


def test_final_completes_only_after_live_verifier_passes(tmp_path):
    root, db, model, state, services = setup(
        tmp_path, [{"kind": "final", "text": "ready for verification", "call": None}])
    (root / "src/linkcheck.py").write_text(CORRECT, encoding="utf-8", newline="\n")
    result = run(state, services)
    assert result["status"] == "completed"
    assert result["evidence"]["verification"]["passed"] is True
    assert any(event["kind"] == "verification_passed" for event in db.events("r1"))


def test_live_hash_change_after_verdict_prevents_completion(tmp_path, monkeypatch):
    root, db, model, state, services = setup(
        tmp_path, [{"kind": "final", "text": "done", "call": None}])
    (root / "src/linkcheck.py").write_text(CORRECT, encoding="utf-8", newline="\n")
    from chapter12 import verifier
    real = verifier.verify

    def stale_verdict(root, backend, baseline, cancel):
        verdict = real(root, backend, baseline, cancel)
        with (root / "src/linkcheck.py").open("a", encoding="utf-8") as handle:
            handle.write("\n# post-verification change\n")
        return verdict

    monkeypatch.setattr(verifier, "verify", stale_verdict)
    result = run(state, services)
    assert result["status"] != "completed"
    assert result["evidence"]["verification"]["reason"] == "post_verification_change"


def test_plan_is_visible_and_persisted_before_next_decision(tmp_path):
    root, db, model, state, services = setup(tmp_path, [
        {"kind": "plan", "text": "read, patch, test", "call": None},
        {"kind": "final", "text": "done", "call": None}])
    result = run(state, services)
    assert result["plan"] == "read, patch, test"
    assert any(event["kind"] == "plan_updated" for event in db.events("r1"))


def test_transient_model_failures_retry_with_budget_and_permanent_errors_do_not(tmp_path):
    class FlakyModel:
        provider_state = {}
        def __init__(self):
            self.attempts = 0
        def next(self, messages):
            self.attempts += 1
            if self.attempts < 3:
                raise TimeoutError("temporary")
            return {"kind": "final", "text": "verify", "call": None}

    root = create_workspace(tmp_path / "repo")
    (root / "src/linkcheck.py").write_text(CORRECT, encoding="utf-8", newline="\n")
    db = Store(tmp_path / "state.sqlite")
    state = new_state("r1", "repair", "trusted_local", time.time())
    model = FlakyModel()
    result = run(state, Services(root, db, model, "trusted_local", threading.Event()))
    assert result["status"] == "completed"
    assert result["counters"]["model_turns"] == 3
    assert len([event for event in db.events("r1") if event["kind"] == "model_retry"]) == 2

    class PermanentModel:
        provider_state = {}
        calls = 0
        def next(self, messages):
            self.calls += 1
            raise ValueError("bad_request")

    state2 = new_state("r2", "repair", "trusted_local", time.time())
    permanent = PermanentModel()
    result2 = run(state2, Services(root, db, permanent, "trusted_local", threading.Event()))
    assert result2["status"] == "failed" and permanent.calls == 1


def test_model_timeout_is_capped_by_remaining_deadline(tmp_path):
    class ConfigModel:
        provider_state = {}
        def __init__(self):
            self.config = {"model": "fake"}
            self.seen_timeout = None
        def next(self, messages):
            self.seen_timeout = self.config["timeout"]
            return {"kind": "final", "text": "verify", "call": None}

    root = create_workspace(tmp_path / "repo")
    (root / "src/linkcheck.py").write_text(CORRECT, encoding="utf-8", newline="\n")
    db = Store(tmp_path / "state.sqlite")
    state = new_state("r1", "repair", "trusted_local", 100)
    state["deadline"] = 102
    model = ConfigModel()
    result = run(state, Services(root, db, model, "trusted_local", threading.Event(),
                                 clock=lambda: 100.5))
    assert result["status"] == "completed"
    assert 0 < model.seen_timeout <= 1.5
    assert "timeout" not in model.config


def test_quickstart_help_start_and_trace(tmp_path, capsys):
    assert main(["--help"]) == 0
    assert "start" in capsys.readouterr().out
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps([
        {"kind": "final", "text": "verify", "call": None}]), encoding="utf-8")
    workspace = tmp_path / "cli-repo"
    code = main(["start", "--workspace", str(workspace), "--run-id", "cli1",
                 "--replay", str(decisions)])
    assert code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["run_id"] == "cli1" and output["status"] == "failed"
    assert main(["trace", "--workspace", str(workspace), "--run-id", "cli1"]) == 0
    trace = json.loads(capsys.readouterr().out)
    assert trace and trace[0]["run_id"] == "cli1"
