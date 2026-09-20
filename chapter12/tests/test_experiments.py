from __future__ import annotations

import json

import pytest

from chapter12.experiments import canonicalize, main, run_group
from chapter12 import quickstart


def test_reports_are_reproducible(tmp_path):
    left = canonicalize(run_group(2, tmp_path / "one"))
    right = canonicalize(run_group(2, tmp_path / "two"))
    assert left == right
    assert left["decision_source"] == "replay"
    assert left["scenarios"]["false_finish"]["accepted"] is False
    serialized = json.dumps(left)
    assert str(tmp_path) not in serialized


@pytest.mark.parametrize("group", [1, 2, 3, 4, 5])
def test_each_group_has_evidence_criteria_and_limits(group, tmp_path):
    report = canonicalize(run_group(group, tmp_path / f"group-{group}"))
    assert set(report) == {"schema_version", "decision_source", "orchestration",
                           "backend", "scenarios", "evidence", "limits"}
    assert report["schema_version"] == 1
    assert report["scenarios"]
    for scenario in report["scenarios"].values():
        assert set(scenario) >= {"expected", "observed", "criterion", "passed",
                                 "does_not_prove"}


def test_isolation_report_never_confuses_policy_with_os_probe(tmp_path):
    report = canonicalize(run_group(4, tmp_path))
    isolation = report["scenarios"]["container_isolation"]
    assert isolation["observed"]["isolation_passed"] is False
    assert isolation["passed"] is False
    assert "deferred" in isolation["does_not_prove"]


def test_framework_report_uses_all_three_real_entries(tmp_path):
    report = canonicalize(run_group(5, tmp_path))
    assert set(report["scenarios"]) == {"manual", "langgraph", "agents_sdk"}
    assert all(item["observed"]["status"] == "completed"
               for item in report["scenarios"].values())
    assert report["scenarios"]["langgraph"]["observed"]["writes"] == 2
    assert report["scenarios"]["agents_sdk"]["observed"]["writes"] == 2


def test_cli_refuses_overwrite_without_replace(tmp_path, capsys):
    output = tmp_path / "reports"
    assert main(["--group", "2", "--output", str(output)]) == 0
    first = (output / "group-2.json").read_bytes()
    assert main(["--group", "2", "--output", str(output)]) == 2
    assert (output / "group-2.json").read_bytes() == first
    assert "output_exists" in capsys.readouterr().err
    assert main(["--group", "2", "--output", str(output), "--replace"]) == 0


def test_live_quickstart_fails_preflight_before_workspace_or_api(tmp_path, monkeypatch, capsys):
    workspace = tmp_path / "live-repo"
    monkeypatch.setattr("chapter12.backends.probe_container", lambda: {
        "available": False, "image_pinned": True, "isolation_passed": False,
        "runtime": None, "reason": "runtime_unavailable"})
    assert quickstart.main(["start", "--workspace", str(workspace), "--run-id", "live1",
        "--model", "live", "--backend", "container", "--model-name", "not-called"]) == 2
    assert not workspace.exists()
    assert "isolation_unverified" in capsys.readouterr().out
