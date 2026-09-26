from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from chapter14.contracts import (
    BenchmarkCard,
    IncidentReport,
    SamplingDecision,
    SpanRecord,
    TraceRecord,
    ValidationIssue,
)


ROOT = Path(__file__).resolve().parents[2]


def _span(**overrides: object) -> SpanRecord:
    values: dict[str, object] = {
        "trace_id": "trace-stable-simple-01",
        "span_id": "span-model-01",
        "parent_span_id": "span-root-01",
        "depends_on_span_ids": (),
        "kind": "model",
        "name": "plan",
        "start_ms": 10,
        "end_ms": 40,
        "status": "ok",
        "attributes": {"model_family": "teaching-model"},
        "input_digest": "sha256:input",
        "output_digest": None,
        "input_tokens": 12,
        "output_tokens": None,
        "cost_units": 1.25,
        "error_type": None,
    }
    values.update(overrides)
    return SpanRecord(**values)  # type: ignore[arg-type]


def _trace(**overrides: object) -> TraceRecord:
    values: dict[str, object] = {
        "trace_id": "trace-stable-simple-01",
        "session_id": "session-simple-01",
        "release_id": "stable",
        "scenario_id": "simple-01",
        "slice": "simple",
        "started_at_ms": 0,
        "ended_at_ms": 50,
        "status": "success",
        "outcome_score": 1.0,
        "spans": (_span(),),
        "tags": {"channel": "offline"},
        "sampling": None,
        "telemetry_complete": True,
    }
    values.update(overrides)
    return TraceRecord(**values)  # type: ignore[arg-type]


def test_valid_contracts_serialize_explicit_nulls() -> None:
    card = BenchmarkCard(
        benchmark_id="repo-repair",
        benchmark_version="2026-09",
        task_subset="verified",
        task_period="2026-q3",
        subject="agent-system",
        harness="harness-a",
        model="model-a",
        tools=("read", "edit", "test"),
        environment="python-3.11",
        step_budget=40,
        token_budget=None,
        timeout_ms=30_000,
        retry_policy="none",
        attempts_per_task=1,
        metric="resolved_percent",
        exclusions=(),
        contamination_risk="unknown",
        source="fixture://control",
        score=72.0,
    )
    trace = _trace()
    decision = SamplingDecision(
        trace_id=trace.trace_id,
        stage="head",
        decision="keep",
        reason_codes=("deterministic_bucket",),
        probability=0.1,
        policy_version="sampling.v1",
    )
    report = IncidentReport(
        symptom="p95 latency and retry amplification increased",
        affected_slices=("recovery",),
        data_completeness=0.95,
        candidate_causes=("retry_policy", "tool_latency"),
        supporting_trace_ids=(trace.trace_id,),
        counterevidence_trace_ids=("trace-control-01",),
        ablation_results=({"hypothesis": "retry_policy", "symptoms_removed": True},),
        root_cause="retry_policy",
        confidence=0.9,
        conclusion="confirmed",
        unknowns=("provider_usage_missing",),
        recommended_actions=("bound_retry_scope",),
        regression_task_ids=("reg-retry-01",),
    )
    issue = ValidationIssue(
        code="unknown_parent",
        message="parent span is missing",
        trace_id=trace.trace_id,
        span_id="span-model-01",
        field="parent_span_id",
    )

    assert card.to_dict()["token_budget"] is None
    assert trace.to_dict()["sampling"] is None
    assert trace.to_dict()["spans"][0]["output_tokens"] is None
    assert trace.to_dict()["spans"][0]["error_type"] is None
    assert decision.to_dict()["reason_codes"] == ["deterministic_bucket"]
    assert report.to_dict()["counterevidence_trace_ids"] == ["trace-control-01"]
    assert issue.to_dict()["field"] == "parent_span_id"
    with pytest.raises(FrozenInstanceError):
        trace.status = "failure"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("factory", "error_code"),
    [
        (lambda: _span(span_id=""), "missing_span_id"),
        (lambda: _span(kind="database"), "invalid_span_kind"),
        (lambda: _span(status="maybe"), "invalid_span_status"),
        (lambda: _span(start_ms=-1), "negative_span_time"),
        (lambda: _span(end_ms=9), "span_ends_before_start"),
        (lambda: _span(input_tokens=-1), "negative_usage"),
        (lambda: _span(cost_units=-0.01), "negative_usage"),
        (lambda: _trace(trace_id=""), "missing_trace_id"),
        (lambda: _trace(release_id="preview"), "invalid_release_id"),
        (lambda: _trace(slice="unknown"), "invalid_scenario_slice"),
        (lambda: _trace(status="maybe"), "invalid_trace_status"),
        (lambda: _trace(started_at_ms=-1), "negative_trace_time"),
        (lambda: _trace(ended_at_ms=-1), "trace_ends_before_start"),
        (lambda: _trace(outcome_score=1.1), "invalid_outcome_score"),
        (lambda: _trace(spans=(_span(), replace(_span(), name="duplicate"))), "duplicate_span_id"),
        (lambda: SamplingDecision("trace-1", "after", "keep", (), 0.1, "v1"), "invalid_sampling_stage"),
        (lambda: SamplingDecision("trace-1", "head", "maybe", (), 0.1, "v1"), "invalid_sampling_decision"),
        (lambda: SamplingDecision("trace-1", "head", "keep", (), 1.1, "v1"), "invalid_sampling_probability"),
        (lambda: IncidentReport("symptom", (), 1.0, (), (), (), (), None, 0.5, "certain", (), (), ()), "invalid_incident_conclusion"),
        (
            lambda: IncidentReport("symptom", (), 1.0, (), (), ("trace-control",), (), "cause", 0.9, "confirmed", (), (), ()),
            "confirmed_incident_requires_supporting_evidence",
        ),
        (
            lambda: IncidentReport("symptom", (), 1.0, (), ("trace-support",), (), (), "cause", 0.9, "confirmed", (), (), ()),
            "confirmed_incident_requires_counterevidence",
        ),
    ],
)
def test_invalid_contracts_fail_at_construction(factory, error_code: str) -> None:
    with pytest.raises(ValueError, match=error_code):
        factory()


def test_inconclusive_incident_can_preserve_evidence_gaps_as_unknowns() -> None:
    report = IncidentReport(
        "symptom", (), 0.4, (), (), (), (), None, 0.2, "inconclusive", ("more_traces_required",), (), ()
    )
    assert report.supporting_trace_ids == ()
    assert report.counterevidence_trace_ids == ()


def test_scenario_fixture_has_unique_balanced_safe_records() -> None:
    records = json.loads((ROOT / "chapter14" / "fixtures" / "scenarios.json").read_text(encoding="utf-8"))

    assert len(records) == 24
    assert len({item["scenario_id"] for item in records}) == 24
    assert {name: sum(item["slice"] == name for item in records) for name in (
        "simple", "retrieval", "write", "recovery"
    )} == {"simple": 6, "retrieval": 6, "write": 6, "recovery": 6}
    serialized = json.dumps(records, ensure_ascii=False).lower()
    for forbidden in ("authorization", "cookie", "api_key", "user_id", "hidden_answer", "chain_of_thought"):
        assert forbidden not in serialized


def test_rate_card_uses_versioned_teaching_cost_units() -> None:
    card = json.loads((ROOT / "chapter14" / "fixtures" / "rate-card.json").read_text(encoding="utf-8"))

    assert card["version"] == "chapter14.cost-units.v1"
    assert card["currency"] is None
    assert set(card["rates"]) == {"model_input_per_1k", "model_output_per_1k", "tool_call"}
    assert all(value >= 0 for value in card["rates"].values())
