import copy
import os
import socket

import pytest

from chapter17.experiments import run_all, run_group
from chapter17.evidence import validate_report


def test_five_groups_show_claim_and_counterexample():
    report = run_all()
    assert [g["id"] for g in report["groups"]] == [1, 2, 3, 4, 5]
    cases = {c["id"]: c for group in report["groups"] for c in group["cases"]}
    assert cases["chart-base"]["value"] == "25"
    assert cases["chart-truncated"]["value"] == "25"
    assert cases["screen-stale"]["status"] == "refresh"
    assert cases["voice-interruption"]["details"]["backend_task"] == "running"
    assert cases["voice-interruption"]["details"]["playback"] == "stopped"
    assert all(c["evidence_ids"] for c in cases.values())
    assert report["summary"]["cases_total"] == len(cases)
    assert report["summary"]["security_violations"] == 0


def test_report_requires_evidence_and_unknown_reasons():
    report = run_all()
    validate_report(report)
    broken = copy.deepcopy(report)
    broken["groups"][0]["cases"][0]["evidence_ids"] = []
    with pytest.raises(ValueError):
        validate_report(broken)
    broken = copy.deepcopy(report)
    unknown = next(c for g in broken["groups"] for c in g["cases"] if c["status"] == "unknown")
    unknown["reasons"] = []
    with pytest.raises(ValueError):
        validate_report(broken)


def test_default_run_is_offline_and_does_not_read_key(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network")))
    monkeypatch.setattr(os, "getenv", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("env")))
    assert run_group(1)["cases"][0]["status"] == "answer"


def test_second_group_and_integrated_group_cover_specified_modalities():
    second = {case["id"]: case for case in run_group(2)["cases"]}
    assert second["chart-truncated-crosscheck"]["value"] == "25"
    integrated = {case["id"]: case for case in run_group(5)["cases"]}
    assert integrated["integrated-document-page"]["details"]["origin"] == "fixed-observation"
    assert integrated["integrated-voice-provenance"]["details"]["backend_task"] == "completed"
    assert integrated["integrated-untrusted-screen-text"]["status"] == "blocked"


def test_group_two_and_five_expose_all_promised_failure_modes():
    second = {case["id"]: case for case in run_group(2)["cases"]}
    for case_id in ("chart-missing-tick", "chart-double-legend",
                    "chart-missing-unit-crosscheck", "chart-zero-denominator"):
        assert second[case_id]["status"] == "unknown"
    assert second["chart-zero-denominator"]["reasons"] == ["zero-denominator"]
    integrated = {case["id"]: case for case in run_group(5)["cases"]}
    assert integrated["integrated-stale-chart"]["status"] == "refresh"
    assert run_all()["summary"] == {
        "cases_total": 25, "answers": 10, "unknown": 11, "blocked": 2,
        "refresh": 2, "security_violations": 0,
        "evidence_covered": 25, "evidence_total": 25,
    }


def test_faulty_unauthorized_execution_is_counted_and_cannot_hide_in_report(monkeypatch):
    from dataclasses import replace
    from chapter17 import experiments

    original = experiments.simulate_action

    def faulty(*args, **kwargs):
        receipt = original(*args, **kwargs)
        if kwargs["approved"] is False:
            return replace(receipt, status="verified", executed=True,
                           display_xy=(800, 450), post_frame_id="f2")
        return receipt

    monkeypatch.setattr(experiments, "simulate_action", faulty)
    report = experiments.run_all()
    assert report["summary"]["security_violations"] >= 2
    cases = {case["id"]: case for group in report["groups"] for case in group["cases"]}
    assert cases["screen-unapproved"]["security_violation"] is True
    assert cases["integrated-untrusted-screen-text"]["security_violation"] is True
    cases["screen-unapproved"]["security_violation"] = False
    with pytest.raises(ValueError):
        validate_report(report)


@pytest.mark.parametrize("case_id,filename,source_id,want_backend,want_issues", [
    ("voice-interruption", "voice-interruption.json", "voice:interruption-events", "running", ()),
    ("voice-task-cancel", "voice-task-cancel.json", "voice:cancel-events", "cancelled", ()),
    ("voice-conflict", "voice-conflict.json", "voice:conflict-events", "unknown", ("conflicting-duplicate-sequence",)),
])
def test_voice_case_replays_the_exact_source_bound_by_its_proof(
        case_id, filename, source_id, want_backend, want_issues):
    from hashlib import sha256
    import json
    from chapter17.contracts import EventRecord
    from chapter17.fixtures import load_fixture
    from chapter17.voice import reduce_events

    report = run_all()
    case = next(c for c in report["groups"][3]["cases"] if c["id"] == case_id)
    assert case["details"]["event_source"] == filename
    assert case["evidence_ids"] == [source_id]
    raw = load_fixture(filename)
    assert report["source_proof"][source_id] == sha256(raw).hexdigest()
    events = tuple(EventRecord(**{**row, "payload": tuple(tuple(p) for p in row["payload"])})
                   for row in json.loads(raw))
    state = reduce_events(events)
    assert state.backend_task == want_backend
    assert state.issues == want_issues
    for key in ("playback", "generation", "conversation_tail", "backend_task", "committed_actions", "issues"):
        assert case["details"][key] == getattr(state, key)
