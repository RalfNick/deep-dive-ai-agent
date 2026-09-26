from __future__ import annotations

from collections import Counter
import json

from chapter14.trace_builder import build_shuffled_log_fixture, build_trace_fixture


def _stable_bytes() -> bytes:
    payload = [trace.to_dict() for trace in build_trace_fixture()]
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def test_fixture_has_exact_balanced_release_and_slice_counts() -> None:
    traces = build_trace_fixture()

    assert len(traces) == 72
    assert Counter(trace.release_id for trace in traces) == {
        "stable": 24,
        "incident": 24,
        "fixed": 24,
    }
    assert Counter((trace.release_id, trace.slice) for trace in traces) == {
        (release, slice_name): 6
        for release in ("stable", "incident", "fixed")
        for slice_name in ("simple", "retrieval", "write", "recovery")
    }


def test_fixture_ids_and_bytes_are_stable() -> None:
    first = build_trace_fixture()
    second = build_trace_fixture()

    assert [trace.trace_id for trace in first] == [
        f"trace-{release}-{slice_name}-{number:02d}"
        for release in ("stable", "incident", "fixed")
        for slice_name in ("simple", "retrieval", "write", "recovery")
        for number in range(1, 7)
    ]
    assert _stable_bytes() == json.dumps(
        [trace.to_dict() for trace in second],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def test_release_variation_is_declared_and_recovery_contains_teaching_failures() -> None:
    traces = build_trace_fixture()
    declared = {
        "stable": "baseline",
        "incident": "retry_scope_regression",
        "fixed": "bounded_retry_scope",
    }

    assert {trace.tags["release_modifier"] for trace in traces if trace.release_id == "stable"} == {
        declared["stable"]
    }
    assert {trace.tags["release_modifier"] for trace in traces if trace.release_id == "incident"} == {
        declared["incident"]
    }
    assert {trace.tags["release_modifier"] for trace in traces if trace.release_id == "fixed"} == {
        declared["fixed"]
    }
    recovery = [trace for trace in traces if trace.slice == "recovery"]
    assert any(any(span.kind == "retry" for span in trace.spans) for trace in recovery)
    assert any(any(span.status == "error" for span in trace.spans) for trace in recovery)
    assert any(not trace.telemetry_complete for trace in recovery)
    assert any(any(span.output_tokens is None for span in trace.spans if span.kind == "model") for trace in traces)


def test_root_spans_never_enter_dependency_dag_and_logs_are_deterministically_shuffled() -> None:
    trace = next(item for item in build_trace_fixture() if item.trace_id == "trace-incident-retrieval-02")
    roots = {span.span_id for span in trace.spans if span.kind == "root"}
    dependency_ids = {dependency for span in trace.spans for dependency in span.depends_on_span_ids}
    first = build_shuffled_log_fixture(trace)
    second = build_shuffled_log_fixture(trace)

    assert roots.isdisjoint(dependency_ids)
    assert first == second
    assert {item["span_id"] for item in first} == {span.span_id for span in trace.spans}
    assert [item["timestamp_ms"] for item in first] != sorted(item["timestamp_ms"] for item in first)
    assert all("parent_span_id" not in item and "depends_on_span_ids" not in item for item in first)
