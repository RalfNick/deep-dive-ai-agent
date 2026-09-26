from __future__ import annotations

from dataclasses import replace

import pytest

from chapter14.contracts import SpanRecord, TraceRecord
from chapter14.trace_builder import build_trace_fixture
from chapter14.trace_validation import require_valid_trace, validate_trace


def _parallel_trace() -> TraceRecord:
    return next(trace for trace in build_trace_fixture() if trace.trace_id == "trace-stable-retrieval-02")


def _replace_span(trace: TraceRecord, span_id: str, **changes: object) -> TraceRecord:
    spans = tuple(replace(span, **changes) if span.span_id == span_id else span for span in trace.spans)
    return replace(trace, spans=spans)


def _unsafe_trace_with_spans(trace: TraceRecord, spans: tuple[SpanRecord, ...]) -> TraceRecord:
    unsafe = object.__new__(TraceRecord)
    for name in TraceRecord.__dataclass_fields__:
        object.__setattr__(unsafe, name, spans if name == "spans" else getattr(trace, name))
    return unsafe


def _codes(trace: TraceRecord) -> set[str]:
    return {issue.code for issue in validate_trace(trace)}


def test_valid_parallel_trace_passes_tree_and_dependency_validation() -> None:
    trace = _parallel_trace()

    assert validate_trace(trace) == ()
    assert require_valid_trace(trace) is None


def test_unknown_parent_and_child_outside_parent_are_rejected() -> None:
    trace = _parallel_trace()
    work = next(span for span in trace.spans if span.kind == "retrieval")
    unknown = _replace_span(trace, work.span_id, parent_span_id="missing-parent")
    outside = _replace_span(trace, work.span_id, end_ms=trace.ended_at_ms + 1)

    assert "unknown_parent" in _codes(unknown)
    assert "child_outside_parent" in _codes(outside)


def test_parent_and_dependency_cycles_are_checked_independently() -> None:
    trace = _parallel_trace()
    retrievals = [span for span in trace.spans if span.kind == "retrieval"]
    first, second = retrievals
    parent_cycle = _replace_span(trace, first.span_id, parent_span_id=second.span_id)
    parent_cycle = _replace_span(parent_cycle, second.span_id, parent_span_id=first.span_id)
    dependency_cycle = _replace_span(trace, first.span_id, depends_on_span_ids=(second.span_id,))
    dependency_cycle = _replace_span(dependency_cycle, second.span_id, depends_on_span_ids=(first.span_id,))

    assert "parent_cycle" in _codes(parent_cycle)
    assert "dependency_cycle" in _codes(dependency_cycle)
    assert "parent_cycle" not in _codes(dependency_cycle)


def test_dependency_on_container_span_is_rejected_before_metrics() -> None:
    trace = _parallel_trace()
    root = next(span for span in trace.spans if span.kind == "root")
    work = next(span for span in trace.spans if span.kind == "retrieval")
    invalid = _replace_span(trace, work.span_id, depends_on_span_ids=(root.span_id,))

    assert "dependency_on_container" in _codes(invalid)
    with pytest.raises(ValueError, match="dependency_on_container"):
        require_valid_trace(invalid)


def test_dependency_must_finish_before_dependent_work_starts() -> None:
    trace = _parallel_trace()
    retrievals = [span for span in trace.spans if span.kind == "retrieval"]
    first, second = retrievals
    invalid = _replace_span(trace, first.span_id, depends_on_span_ids=(second.span_id,))

    assert "dependency_time_order" in _codes(invalid)
    with pytest.raises(ValueError, match="dependency_time_order"):
        require_valid_trace(invalid)


def test_duplicate_ids_negative_usage_and_forbidden_attributes_are_rejected() -> None:
    trace = _parallel_trace()
    work = next(span for span in trace.spans if span.kind == "retrieval")
    duplicate = _unsafe_trace_with_spans(trace, (*trace.spans, work))
    negative = object.__new__(SpanRecord)
    for name in SpanRecord.__dataclass_fields__:
        object.__setattr__(negative, name, -1 if name == "input_tokens" else getattr(work, name))
    negative_trace = _unsafe_trace_with_spans(trace, tuple(negative if span is work else span for span in trace.spans))
    forbidden = _replace_span(trace, work.span_id, attributes={"nested": {"Authorization": "Bearer example"}})

    assert "duplicate_span_id" in _codes(duplicate)
    assert "negative_usage" in _codes(negative_trace)
    assert "forbidden_attribute" in _codes(forbidden)
