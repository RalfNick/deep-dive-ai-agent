from dataclasses import replace
import math
import pytest
from chapter16.contracts import Scope, FeedbackRecord, RunResult
from chapter16.serialization import canonical_bytes, digest

def test_strict_boolean_and_finite_values(lab):
    for bad in ("false", 1):
        with pytest.raises(ValueError):
            replace(lab.feedback[0], source_sensitive=bad)
    with pytest.raises(ValueError):
        replace(lab.feedback[0], payload={"value": math.nan})
    for bad in (-1, True):
        with pytest.raises(ValueError):
            RunResult(None, (), "normal", None, (), (), None, (), bad, 0)
    with pytest.raises(ValueError):
        Scope("", None, "export", "current")

def test_nested_payload_cannot_mutate_after_hash(lab):
    data = {"steps": ["open_project"]}
    record = replace(lab.feedback[0], payload=data)
    before = canonical_bytes(record)
    data["steps"].append("erase")
    assert canonical_bytes(record) == before
    with pytest.raises(TypeError):
        record.payload["steps"] = ()
    assert digest(record) == digest(record.to_dict())

def test_unknown_fields_and_clock_are_rejected(lab):
    with pytest.raises(ValueError):
        replace(lab.tasks[0], frozen_clock="2026-09-28")
    with pytest.raises(ValueError):
        FeedbackRecord.from_dict({**lab.feedback[0].to_dict(), "trusted": True})
