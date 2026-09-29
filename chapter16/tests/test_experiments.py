import json
from pathlib import Path
import socket
import os
import pytest
import jsonschema
from chapter16.experiments import run_all, run_group, main, validate_report
from chapter16.serialization import canonical_bytes

def test_report_stable_offline_and_schema(lab, monkeypatch):
    def denied(*a, **kw):
        raise AssertionError("offline boundary")
    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(os, "getenv", denied)
    first, second = run_all(lab), run_all(lab)
    assert canonical_bytes(first) == canonical_bytes(second)
    assert first.schema_version == "chapter16.improvement.v1"
    schema = json.loads((Path(__file__).parents[1]/"schemas/improvement-report-v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(first.to_dict(), schema)
    validate_report(first)
    assert run_group(1, lab)["counts"] == {"accepted":6,"quarantined":3,"merged":1,"unknown":2}
    assert run_group(2, lab)["coverage"] == {"total":4,"replayed":2,"environment_error":1,"unknown":1}
    assert set(run_group(4, lab)["gates"].values()) == {"pass","fail","inconclusive"}
    assert run_group(5, lab)["cohort_counts"] == {"candidate":4,"baseline":12}

def test_bad_args_and_report_hash(lab):
    with pytest.raises(SystemExit) as e:
        main(["--group","9"])
    assert e.value.code == 2
    from dataclasses import replace
    with pytest.raises(ValueError):
        validate_report(replace(run_all(lab), groups=()))
