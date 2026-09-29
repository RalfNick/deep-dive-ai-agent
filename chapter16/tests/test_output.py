from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from chapter16.experiments import run_all
from chapter16.output import write_report_bundle, write_new_json

def test_new_bundles_equal_and_existing_empty_dir_rejected(lab, tmp_path):
    report = run_all(lab)
    one, two = (tmp_path/"chapter16/.runs"/name for name in ("one","two"))
    paths = write_report_bundle(report, one, root=tmp_path)
    write_report_bundle(report, two, root=tmp_path)
    assert len(paths) == 8
    assert {p.name:p.read_bytes() for p in one.iterdir()} == {p.name:p.read_bytes() for p in two.iterdir()}
    empty = tmp_path/"chapter16/.runs/empty"
    empty.mkdir()
    with pytest.raises(FileExistsError):
        write_report_bundle(report, empty, root=tmp_path)

def test_outside_symlink_nan_and_concurrent_reservation(lab, tmp_path):
    report = run_all(lab)
    with pytest.raises(ValueError):
        write_report_bundle(report,tmp_path.parent/"outside",root=tmp_path)
    dest = tmp_path/"chapter16/.runs/race"
    def worker(_):
        try:
            write_report_bundle(report,dest,root=tmp_path)
            return "ok"
        except FileExistsError:
            return "exists"
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(worker, (1,2))) == ["exists","ok"]
    with pytest.raises(ValueError):
        write_new_json({"n":float("nan")},tmp_path/"chapter16/.runs/nan.json",root=tmp_path)
    with pytest.raises(ValueError):
        write_new_json({"path":"C:/private"},tmp_path/"chapter16/.runs/path.json",root=tmp_path)

def test_dangerous_parent_rejected(lab, tmp_path, monkeypatch):
    from chapter16 import output
    root = tmp_path/"chapter16/.runs"
    root.mkdir(parents=True)
    original = output.is_linklike
    monkeypatch.setattr(output,"is_linklike",lambda p: p == root or original(p))
    with pytest.raises(ValueError, match="link"):
        write_report_bundle(run_all(lab),root/"linked",root=tmp_path)

def test_partial_error_keeps_explainable_directory(lab, tmp_path, monkeypatch):
    from chapter16 import output
    original = output.exclusive_bytes
    def broken(path, data):
        if path.name == "group-2.json":
            raise OSError("injected disk failure")
        return original(path,data)
    monkeypatch.setattr(output,"exclusive_bytes",broken)
    target = tmp_path/"chapter16/.runs/partial"
    with pytest.raises(OSError):
        write_report_bundle(run_all(lab),target,root=tmp_path)
    assert (target/"group-1.json").is_file() and (target/"PARTIAL-OUTPUT.txt").is_file()
