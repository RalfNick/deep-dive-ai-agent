from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import pytest
from chapter18.tests.helpers import fixture_repo


def payloads(root):
    from chapter18.experiments import run_all
    from chapter18.exercise_solutions import solution_payload
    return run_all(root=root, workdir=root / "chapter18/.runs/report"), solution_payload(root=root, workdir=root / "chapter18/.runs/answers")


def test_nine_file_bundles_are_identical_and_manifest_hashes_eight_files(tmp_path):
    from chapter18.output import write_bundle
    root = fixture_repo(tmp_path)
    report, answers = payloads(root)
    a = write_bundle(root, root / "chapter18/reports/a", report, answers)
    b = write_bundle(root, root / "chapter18/reports/b", report, answers)
    assert len(a) == len(b) == 9
    assert {p.name: p.read_bytes() for p in a} == {p.name: p.read_bytes() for p in b}
    manifest = json.loads((root / "chapter18/reports/a/manifest.json").read_text())
    assert len(manifest["files"]) == 8
    for name, digest in manifest["files"].items():
        assert sha256((root / "chapter18/reports/a" / name).read_bytes()).hexdigest() == digest


def test_existing_empty_directory_outside_and_invalid_report_are_refused(tmp_path):
    from chapter18.output import write_bundle
    root = fixture_repo(tmp_path)
    report, answers = payloads(root)
    dest = root / "chapter18/reports/existing"
    dest.mkdir(parents=True)
    with pytest.raises(ValueError):
        write_bundle(root, dest, report, answers)
    with pytest.raises(ValueError):
        write_bundle(root, tmp_path / "outside", report, answers)
    bad = deepcopy(report)
    bad["groups"].pop()
    new = root / "chapter18/reports/invalid"
    with pytest.raises(ValueError):
        write_bundle(root, new, bad, answers)
    assert not new.exists()


def test_symlink_parent_and_nonfinite_json_are_refused(tmp_path):
    from chapter18.output import write_bundle, canonical_json
    root = fixture_repo(tmp_path)
    report, answers = payloads(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / "chapter18/reports/link"
    link.parent.mkdir(parents=True)
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError as error:
        pytest.skip(str(error))
    with pytest.raises(ValueError):
        write_bundle(root, link / "new", report, answers)
    with pytest.raises(ValueError):
        canonical_json({"usage": float("nan")})


def test_full_offline_run_never_calls_network_or_reads_provider_keys(tmp_path, monkeypatch):
    from chapter18.experiments import run_all
    root = fixture_repo(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError("network/provider key access")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    original = os.getenv
    def getenv(key, default=None):
        if "API_KEY" in key or "DEEPSEEK" in key:
            forbidden()
        return original(key, default)
    monkeypatch.setattr(os, "getenv", getenv)
    assert run_all(root=root, workdir=root / "chapter18/.runs/offline")["summary"]["cases_total"] == 20
