import json
from copy import deepcopy
import pytest
from chapter18.tests.helpers import ROOT, fixture_repo


def test_versioned_schema_accepts_actual_report_and_rejects_invalid_status(tmp_path):
    from jsonschema import Draft202012Validator
    from chapter18.experiments import run_all
    root = fixture_repo(tmp_path)
    report = run_all(root=root, workdir=root / "chapter18/.runs/schema")
    schema = json.loads((ROOT / "chapter18/schemas/report-v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    validator.validate(report)
    report["groups"][0]["cases"][0]["status"] = "done"
    assert list(validator.iter_errors(report))
