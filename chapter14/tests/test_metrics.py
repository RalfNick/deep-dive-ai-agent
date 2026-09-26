from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from chapter14.metrics import critical_path, compare_releases, nearest_rank, summarize_release
from chapter14.trace_builder import build_trace_fixture


ROOT = Path(__file__).resolve().parents[2]


def test_nearest_rank_uses_hand_calculable_positions() -> None:
    values = [10, 20, 30, 40, 50]

    assert nearest_rank(values, 50) == 30
    assert nearest_rank(values, 95) == 50
    assert nearest_rank([50, 10, 30, 20, 40], 20) == 10
    with pytest.raises(ValueError, match="percentile_out_of_range"):
        nearest_rank(values, 0)


def test_critical_path_excludes_containers_and_handles_parallel_work() -> None:
    trace = next(item for item in build_trace_fixture() if item.trace_id == "trace-stable-retrieval-02")
    result = critical_path(trace)

    assert result["endpoint_duration_ms"] == 331
    assert result["work_span_duration_sum_ms"] == 360
    assert result["work_span_duration_sum_ms"] > result["endpoint_duration_ms"]
    assert result["critical_path_duration_ms"] == 296
    assert [item.rsplit(":", 1)[-1] for item in result["critical_path_span_ids"]] == [
        "model-plan", "retrieve-a", "model-answer", "verify"
    ]


def test_invalid_dependency_graph_fails_before_metrics() -> None:
    trace = next(item for item in build_trace_fixture() if item.trace_id == "trace-stable-retrieval-02")
    retrievals = [span for span in trace.spans if span.kind == "retrieval"]
    first, second = retrievals
    spans = tuple(
        replace(span, depends_on_span_ids=(second.span_id,)) if span.span_id == first.span_id
        else replace(span, depends_on_span_ids=(first.span_id,)) if span.span_id == second.span_id
        else span
        for span in trace.spans
    )
    invalid = replace(trace, spans=spans)

    with pytest.raises(ValueError, match="dependency_cycle"):
        critical_path(invalid)


def test_release_summary_preserves_known_usage_and_lowers_coverage() -> None:
    traces = tuple(item for item in build_trace_fixture() if item.release_id == "stable")
    rate_card = json.loads((ROOT / "chapter14" / "fixtures" / "rate-card.json").read_text(encoding="utf-8"))
    summary = summarize_release(traces, rate_card)

    assert summary["trace_count"] == 24
    assert summary["success_count"] == 23
    assert summary["outcome_score_mean"] == pytest.approx(23 / 24)
    assert summary["usage"]["input_tokens_total"] > 0
    assert summary["usage"]["output_tokens_total"] > 0
    assert 0 < summary["usage"]["token_field_coverage"] < 1
    assert summary["usage"]["missing_token_fields"] == 1
    assert summary["telemetry_complete_rate"] == pytest.approx(23 / 24)
    assert summary["rate_card_version"] == "chapter14.cost-units.v1"


def test_release_comparison_exposes_retry_regression_and_fixed_recovery() -> None:
    traces = build_trace_fixture()
    rate_card = json.loads((ROOT / "chapter14" / "fixtures" / "rate-card.json").read_text(encoding="utf-8"))
    summaries = {
        release: summarize_release(tuple(item for item in traces if item.release_id == release), rate_card)
        for release in ("stable", "incident", "fixed")
    }
    comparison = compare_releases(summaries)

    assert summaries["incident"]["outcome_score_mean"] == summaries["stable"]["outcome_score_mean"]
    assert summaries["incident"]["latency_ms"]["p95"] > summaries["stable"]["latency_ms"]["p95"]
    assert summaries["incident"]["usage"]["cost_units_total"] > summaries["stable"]["usage"]["cost_units_total"]
    assert summaries["incident"]["retry_amplification"] > summaries["stable"]["retry_amplification"]
    assert summaries["fixed"]["latency_ms"]["p95"] < summaries["incident"]["latency_ms"]["p95"]
    assert comparison["incident_vs_stable"]["outcome_score_mean_delta"] == 0
    assert comparison["fixed_vs_incident"]["latency_p95_ms_delta"] < 0
