from __future__ import annotations

import json

import pytest

from chapter12.experiments import (authoritative_summary_retained, canonicalize,
                                   exactly_one_write_and_receipt, main,
                                   offline_completion_proved, run_group)
from chapter12 import quickstart


@pytest.mark.parametrize("group", [2, 4])
def test_reports_are_reproducible(group, tmp_path):
    left = canonicalize(run_group(group, tmp_path / "one"))
    right = canonicalize(run_group(group, tmp_path / "two"))
    assert left == right
    assert left["decision_source"] == "replay"
    if group == 2:
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


@pytest.mark.parametrize(("writes", "receipts", "expected"), [
    (1, 1, True), (1, 0, False), (0, 1, False), (2, 1, False), (1, 2, False),
])
def test_recovery_criterion_requires_exactly_one_write_and_receipt(
        writes, receipts, expected):
    events = ([{"kind": "action_written"}] * writes
              + [{"kind": "action_receipt"}] * receipts)
    assert exactly_one_write_and_receipt(events) is expected


def test_offline_completion_criterion_rejects_partial_evidence():
    observed = {"status": "completed", "red_observed": True, "writes": 2,
                "diff_paths": ["src/linkcheck.py", "tests/test_agent_nested.py"],
                "candidate_tests": 3, "verification_passed": True,
                "acceptance_case_count": 4}
    assert offline_completion_proved(observed)
    for key, invalid in (("writes", 1), ("diff_paths", ["src/linkcheck.py"]),
                         ("candidate_tests", 0), ("verification_passed", False),
                         ("acceptance_case_count", 0)):
        changed = dict(observed, **{key: invalid})
        assert not offline_completion_proved(changed)


def test_authoritative_summary_criterion_rejects_missing_runtime_facts():
    summary = {"kind": "authoritative_run_state",
               "user_requirements": {"goal": "retain required state"},
               "disk_facts": {"workspace_hash": "a" * 64, "status": "ready"},
               "runtime": {"counters": {"model_turns": 0, "tool_calls": 0}}}
    assert authoritative_summary_retained(summary)
    changed = json.loads(json.dumps(summary))
    changed["runtime"].pop("counters")
    assert not authoritative_summary_retained(changed)


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
