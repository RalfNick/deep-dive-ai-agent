from __future__ import annotations

from pathlib import Path

import pytest

from chapter12.tests.framework_cases import run_scenario


@pytest.mark.parametrize("scenario", ["complete", "approval_restart",
                                       "tool_error", "false_finish"])
def test_langgraph_scenarios_use_real_orchestration(tmp_path, scenario):
    result = run_scenario("langgraph", scenario, tmp_path / scenario)
    assert result["status"] == "completed"
    assert result["orchestration"] == "langgraph"
    assert result["framework_version"]
    assert result["backend"] == "trusted_local"
    assert result["writes"] == 2
    assert result["candidate_tests"] == 3
    if scenario == "tool_error":
        assert "file_missing" in result["observed_errors"]
    if scenario == "false_finish":
        assert result["verification_failures"] >= 1


def test_graph_does_not_wrap_manual_runtime(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("manual loop reached")
    monkeypatch.setattr("chapter12.runtime.run", forbidden)
    result = run_scenario("langgraph", "complete", tmp_path)
    assert result["status"] == "completed"
    assert result["orchestration"] == "langgraph"


def test_sqlite_checkpoint_resumes_in_new_processes_without_duplicate_writes(tmp_path):
    result = run_scenario("langgraph", "approval_restart", tmp_path)
    assert len(set(result["process_ids"])) >= 3
    assert result["writes"] == 2
    assert result["receipts"] == 2
    assert Path(result["checkpoint"]).read_bytes().startswith(b"SQLite format 3")


def test_unknown_scenario_and_missing_framework_fail_explicitly(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="unknown_scenario"):
        run_scenario("langgraph", "magic", tmp_path)
    monkeypatch.setattr("chapter12.adapters.langgraph_agent.importlib.util.find_spec",
                        lambda name: None)
    with pytest.raises(RuntimeError, match="langgraph_unavailable"):
        run_scenario("langgraph", "complete", tmp_path / "missing")
