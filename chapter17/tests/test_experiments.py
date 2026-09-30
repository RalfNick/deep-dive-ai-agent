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
