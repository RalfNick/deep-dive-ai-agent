"""Deterministic trace metrics with explicit completeness semantics."""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import math
from typing import Any

from .contracts import TraceRecord
from .trace_validation import CONTAINER_KINDS, require_valid_trace


def nearest_rank(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("empty_values")
    if not 0 < percentile <= 100:
        raise ValueError("percentile_out_of_range")
    ordered = sorted(values)
    rank = math.ceil(percentile / 100 * len(ordered))
    return ordered[rank - 1]


def critical_path(trace: TraceRecord) -> dict[str, object]:
    """Measure the longest observed work chain, not total user wait.

    The DAG contains instrumented work spans. Queueing, scheduling and
    uninstrumented gaps remain in the endpoint-minus-path residual and must not
    be silently attributed to one cause.
    """
    require_valid_trace(trace)
    work = {span.span_id: span for span in trace.spans if span.kind not in CONTAINER_KINDS}
    memo: dict[str, tuple[float, tuple[str, ...]]] = {}

    def longest_to(span_id: str) -> tuple[float, tuple[str, ...]]:
        if span_id in memo:
            return memo[span_id]
        span = work[span_id]
        duration = span.end_ms - span.start_ms
        candidates = [longest_to(dependency) for dependency in span.depends_on_span_ids]
        if candidates:
            prior_duration, prior_path = max(candidates, key=lambda item: (item[0], item[1]))
        else:
            prior_duration, prior_path = 0.0, ()
        memo[span_id] = (prior_duration + duration, (*prior_path, span_id))
        return memo[span_id]

    duration, path = max((longest_to(span_id) for span_id in sorted(work)), key=lambda item: (item[0], item[1]))
    endpoint_duration = trace.ended_at_ms - trace.started_at_ms
    return {
        "trace_id": trace.trace_id,
        "endpoint_duration_ms": endpoint_duration,
        "work_span_duration_sum_ms": sum(span.end_ms - span.start_ms for span in work.values()),
        "critical_path_duration_ms": duration,
        "critical_path_unattributed_elapsed_ms": endpoint_duration - duration,
        "critical_path_span_ids": list(path),
        "algorithm": "work-dag-longest-path.v1",
    }


def _slice_summary(traces: Sequence[TraceRecord]) -> dict[str, object]:
    latencies = [trace.ended_at_ms - trace.started_at_ms for trace in traces]
    return {
        "trace_count": len(traces),
        "success_rate": round(sum(trace.status == "success" for trace in traces) / len(traces), 6),
        "outcome_score_mean": round(sum(trace.outcome_score for trace in traces) / len(traces), 6),
        "latency_p95_ms": nearest_rank(latencies, 95),
    }


def summarize_release(traces: Sequence[TraceRecord], rate_card: Mapping[str, Any]) -> dict[str, object]:
    if not traces:
        raise ValueError("empty_release")
    releases = {trace.release_id for trace in traces}
    if len(releases) != 1:
        raise ValueError("mixed_releases")
    for trace in traces:
        require_valid_trace(trace)

    release_id = next(iter(releases))
    latencies = [trace.ended_at_ms - trace.started_at_ms for trace in traces]
    paths = [critical_path(trace) for trace in traces]
    model_spans = [span for trace in traces for span in trace.spans if span.kind == "model"]
    billable_spans = [span for trace in traces for span in trace.spans if span.kind in {"model", "retrieval", "tool"}]
    token_values = [
        value
        for span in model_spans
        for value in (span.input_tokens, span.output_tokens)
        if value is not None
    ]
    total_token_fields = len(model_spans) * 2
    missing_token_fields = total_token_fields - len(token_values)
    known_costs = [span.cost_units for span in billable_spans if span.cost_units is not None]
    actual_attempts = len(billable_spans)
    logical_operations = sum(int(trace.tags["logical_operations"]) for trace in traces)
    slices = {
        slice_name: _slice_summary(tuple(trace for trace in traces if trace.slice == slice_name))
        for slice_name in ("simple", "retrieval", "write", "recovery")
    }

    return {
        "release_id": release_id,
        "trace_count": len(traces),
        "success_count": sum(trace.status == "success" for trace in traces),
        "status_counts": dict(sorted(Counter(trace.status for trace in traces).items())),
        "outcome_score_mean": round(sum(trace.outcome_score for trace in traces) / len(traces), 6),
        "latency_ms": {
            "p50": nearest_rank(latencies, 50),
            "p95": nearest_rank(latencies, 95),
            "max": max(latencies),
        },
        "critical_path_ms": {
            "p50": nearest_rank([float(item["critical_path_duration_ms"]) for item in paths], 50),
            "p95": nearest_rank([float(item["critical_path_duration_ms"]) for item in paths], 95),
        },
        "work_span_duration_sum_ms": sum(int(item["work_span_duration_sum_ms"]) for item in paths),
        "retry_amplification": round(actual_attempts / logical_operations, 6),
        "usage": {
            "input_tokens_total": sum(span.input_tokens or 0 for span in model_spans),
            "output_tokens_total": sum(span.output_tokens or 0 for span in model_spans),
            "cost_units_total": round(sum(known_costs), 6),
            "token_field_coverage": round(len(token_values) / total_token_fields, 6),
            "missing_token_fields": missing_token_fields,
            "cost_field_coverage": round(len(known_costs) / len(billable_spans), 6),
        },
        "telemetry_complete_count": sum(trace.telemetry_complete for trace in traces),
        "telemetry_complete_rate": round(sum(trace.telemetry_complete for trace in traces) / len(traces), 6),
        "error_span_count": sum(span.status == "error" for trace in traces for span in trace.spans),
        "slices": slices,
        "rate_card_version": rate_card.get("version"),
        "algorithm_versions": {
            "percentile": "nearest-rank.v1",
            "critical_path": "work-dag-longest-path.v1",
            "retry_amplification": "billable-attempts-per-declared-operation.v1",
        },
    }


def _delta(current: Mapping[str, Any], baseline: Mapping[str, Any]) -> dict[str, float]:
    return {
        "outcome_score_mean_delta": round(current["outcome_score_mean"] - baseline["outcome_score_mean"], 6),
        "latency_p95_ms_delta": round(current["latency_ms"]["p95"] - baseline["latency_ms"]["p95"], 6),
        "cost_units_total_delta": round(current["usage"]["cost_units_total"] - baseline["usage"]["cost_units_total"], 6),
        "retry_amplification_delta": round(current["retry_amplification"] - baseline["retry_amplification"], 6),
    }


def compare_releases(summaries: Mapping[str, Mapping[str, Any]]) -> dict[str, object]:
    required = ("stable", "incident", "fixed")
    if any(release not in summaries for release in required):
        raise ValueError("missing_release_summary")
    return {
        "release_order": list(required),
        "incident_vs_stable": _delta(summaries["incident"], summaries["stable"]),
        "fixed_vs_incident": _delta(summaries["fixed"], summaries["incident"]),
        "limits": ["deterministic_fixture_only", "cost_units_are_not_provider_prices"],
    }
