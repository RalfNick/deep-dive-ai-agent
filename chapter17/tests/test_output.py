from pathlib import Path

import pytest

from chapter17.experiments import run_all
from chapter17.output import write_bundle


def test_two_runs_have_identical_canonical_bytes(tmp_path):
    report = run_all()
    a = tmp_path / "chapter17" / ".runs" / "a"
    b = tmp_path / "chapter17" / ".runs" / "b"
    aa = write_bundle(tmp_path, a, report)
    bb = write_bundle(tmp_path, b, report)
    assert [p.name for p in aa] == [p.name for p in bb]
    assert [p.read_bytes() for p in aa] == [p.read_bytes() for p in bb]


def test_existing_empty_output_is_refused(tmp_path):
    dest = tmp_path / "chapter17" / ".runs" / "exists"
    dest.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        write_bundle(tmp_path, dest, run_all())


def test_output_outside_root_or_reparse_parent_is_refused(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        write_bundle(tmp_path, tmp_path / "elsewhere", run_all())
    parent = tmp_path / "chapter17" / ".runs"
    parent.mkdir(parents=True)
    from chapter17 import output
    original = output._is_reparse
    monkeypatch.setattr(output, "_is_reparse", lambda p: p == parent or original(p))
    with pytest.raises(ValueError):
        write_bundle(tmp_path, parent / "linked" / "bundle", run_all())
