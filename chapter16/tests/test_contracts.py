from dataclasses import replace
import math
import pytest
from chapter16.contracts import Scope, FeedbackRecord, RunResult, FixtureSet, UsePolicy, EvaluationContext, EvidenceBundle, ReleaseState
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


def test_nested_contracts_round_trip_without_losing_types(lab, baseline, candidate, evaluation_context):
    from chapter16.evaluation import evaluate_pair, decide_gate
    policy = UsePolicy(frozenset({"retired-hash"}), frozenset({"old-source"}), ("export",))
    assert UsePolicy.from_dict(policy.to_dict()) == policy
    assert FixtureSet.from_dict(lab.to_dict()) == lab
    decoded = EvaluationContext.from_dict(evaluation_context.to_dict())
    assert decoded == evaluation_context
    assert all(isinstance(a, type(evaluation_context.admissions[0])) for a in decoded.admissions)
    evidence = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, decoded)
    restored = EvidenceBundle.from_dict(evidence.to_dict())
    assert canonical_bytes(restored) == canonical_bytes(evidence)
    assert decide_gate(restored).status == "pass"
    state = ReleaseState(baseline, (), frozenset({"used-approval"}))
    assert ReleaseState.from_dict(state.to_dict()) == state


def test_array_fields_do_not_decode_strings_or_empty_references(lab):
    for bad in ("ref", [""], [1]):
        with pytest.raises(ValueError):
            FeedbackRecord.from_dict({**lab.feedback[0].to_dict(), "evidence_refs": bad})
