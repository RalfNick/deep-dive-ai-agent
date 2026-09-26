"""Validation for trace trees, dependency DAGs, timing, usage, and safe attributes."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Iterable

from .contracts import TraceRecord, ValidationIssue


CONTAINER_KINDS = frozenset({"root", "container"})
FORBIDDEN_ATTRIBUTE_KEYS = frozenset(
    {"authorization", "cookie", "apikey", "userid", "hiddenanswer", "chainofthought"}
)


def _issue(trace: TraceRecord, code: str, message: str, *, span_id: str | None = None, field: str | None = None) -> ValidationIssue:
    return ValidationIssue(code, message, trace.trace_id, span_id, field)


def _has_cycle(nodes: Iterable[str], edges: Mapping[str, tuple[str, ...]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        marker = state.get(node, 0)
        if marker == 1:
            return True
        if marker == 2:
            return False
        state[node] = 1
        for neighbor in edges.get(node, ()):
            if neighbor in edges and visit(neighbor):
                return True
        state[node] = 2
        return False

    return any(visit(node) for node in nodes if state.get(node, 0) == 0)


def _forbidden_keys(value: Any) -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = "".join(character for character in str(key).lower() if character.isalnum())
            if normalized in FORBIDDEN_ATTRIBUTE_KEYS:
                found.append(str(key))
            found.extend(_forbidden_keys(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_forbidden_keys(item))
    return tuple(found)


def validate_trace(trace: TraceRecord) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    span_ids = [span.span_id for span in trace.spans]
    if len(set(span_ids)) != len(span_ids):
        issues.append(_issue(trace, "duplicate_span_id", "span IDs must be unique", field="spans"))

    by_id = {span.span_id: span for span in trace.spans}
    roots = [span for span in trace.spans if span.kind == "root"]
    if len(roots) != 1:
        issues.append(_issue(trace, "invalid_root_count", "trace must contain exactly one root span", field="spans"))
    elif roots[0].start_ms != trace.started_at_ms or roots[0].end_ms != trace.ended_at_ms:
        issues.append(_issue(trace, "trace_time_mismatch", "root span must match trace boundaries", span_id=roots[0].span_id))

    parent_edges: dict[str, tuple[str, ...]] = {}
    dependency_edges: dict[str, tuple[str, ...]] = {}
    for span in trace.spans:
        if span.trace_id != trace.trace_id:
            issues.append(_issue(trace, "span_trace_mismatch", "span belongs to another trace", span_id=span.span_id, field="trace_id"))
        if span.start_ms < 0 or span.end_ms < span.start_ms:
            issues.append(_issue(trace, "invalid_span_time", "span time is negative or reversed", span_id=span.span_id))
        if span.input_tokens is not None and span.input_tokens < 0 or span.output_tokens is not None and span.output_tokens < 0 or span.cost_units is not None and span.cost_units < 0:
            issues.append(_issue(trace, "negative_usage", "usage values cannot be negative", span_id=span.span_id))
        if _forbidden_keys(span.attributes):
            issues.append(_issue(trace, "forbidden_attribute", "span attributes contain forbidden fields", span_id=span.span_id, field="attributes"))

        if span.parent_span_id is not None:
            parent_edges[span.span_id] = (span.parent_span_id,)
            parent = by_id.get(span.parent_span_id)
            if parent is None:
                issues.append(_issue(trace, "unknown_parent", "parent span is missing", span_id=span.span_id, field="parent_span_id"))
            elif span.start_ms < parent.start_ms or span.end_ms > parent.end_ms:
                issues.append(_issue(trace, "child_outside_parent", "child timing exceeds its parent", span_id=span.span_id))
        else:
            parent_edges[span.span_id] = ()

        if span.kind not in CONTAINER_KINDS:
            dependency_edges[span.span_id] = tuple(span.depends_on_span_ids)
        for dependency_id in span.depends_on_span_ids:
            dependency = by_id.get(dependency_id)
            if dependency is None:
                issues.append(_issue(trace, "unknown_dependency", "dependency span is missing", span_id=span.span_id, field="depends_on_span_ids"))
            elif dependency.kind in CONTAINER_KINDS:
                issues.append(_issue(trace, "dependency_on_container", "work DAG cannot depend on grouping spans", span_id=span.span_id, field="depends_on_span_ids"))

    if _has_cycle(parent_edges, parent_edges):
        issues.append(_issue(trace, "parent_cycle", "parent tree contains a cycle", field="parent_span_id"))
    if _has_cycle(dependency_edges, dependency_edges):
        issues.append(_issue(trace, "dependency_cycle", "work dependency graph contains a cycle", field="depends_on_span_ids"))

    return tuple(sorted(issues, key=lambda item: (item.code, item.span_id or "", item.field or "")))


def require_valid_trace(trace: TraceRecord) -> None:
    issues = validate_trace(trace)
    if issues:
        codes = ",".join(sorted({issue.code for issue in issues}))
        raise ValueError(f"invalid_trace:{codes}")
