import copy
import json
from pathlib import Path

import pytest

from chapter17.experiments import run_all
from chapter17.evidence import validate_report


def test_schema_rejects_missing_group():
    report = run_all()
    broken = copy.deepcopy(report)
    broken["groups"].pop()
    with pytest.raises(ValueError):
        validate_report(broken)


def test_schema_file_exists_and_matches_report():
    import jsonschema
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "report-v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(run_all(), schema)
