"""Build the deterministic 72-trace teaching fixture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import SpanRecord, TraceRecord


SCENARIOS_PATH = Path(__file__).with_name("fixtures") / "scenarios.json"
RELEASE_MODIFIERS = {
    "stable": "baseline",
    "incident": "retry_scope_regression",
    "fixed": "bounded_retry_scope",
}


def _cost(input_tokens: int | None, output_tokens: int | None) -> float | None:
    if input_tokens is None and output_tokens is None:
        return None
    return round((input_tokens or 0) / 1000 + (output_tokens or 0) * 2 / 1000, 6)


def _span(
    trace_id: str,
    suffix: str,
    kind: str,
    name: str,
    start: int,
    end: int,
    *,
    parent: str,
    depends: tuple[str, ...] = (),
    status: str = "ok",
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cost_units: float | None = None,
    error_type: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> SpanRecord:
    return SpanRecord(
        trace_id=trace_id,
        span_id=f"{trace_id}:{suffix}",
        parent_span_id=parent,
        depends_on_span_ids=depends,
        kind=kind,
        name=name,
        start_ms=start,
        end_ms=end,
        status=status,
        attributes=attributes or {},
        input_digest=f"sha256:{suffix}-input" if kind in {"model", "retrieval", "tool"} else None,
        output_digest=f"sha256:{suffix}-output" if status == "ok" and kind in {"model", "retrieval", "tool"} else None,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_units=cost_units,
        error_type=error_type,
    )


def _work_spans(trace_id: str, slice_name: str, number: int, release: str) -> tuple[list[SpanRecord], int]:
    container = f"{trace_id}:agent-run"
    spans: list[SpanRecord] = []

    def add(
        suffix: str,
        kind: str,
        name: str,
        start: int,
        end: int,
        *,
        depends: tuple[str, ...] = (),
        status: str = "ok",
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_units: float | None = None,
        error_type: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        span = _span(
            trace_id,
            suffix,
            kind,
            name,
            start,
            end,
            parent=container,
            depends=depends,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_units=cost_units,
            error_type=error_type,
            attributes=attributes,
        )
        spans.append(span)
        return span.span_id

    if slice_name == "simple":
        model = add(
            "model-plan", "model", "model.plan", 10, 110 + number * 2,
            input_tokens=100 + number, output_tokens=40 + number,
            cost_units=_cost(100 + number, 40 + number), attributes={"phase": "plan"},
        )
        verifier = add("verify", "verifier", "verify.outcome", 120 + number * 2, 160 + number * 2, depends=(model,))
        return spans, next(span.end_ms for span in spans if span.span_id == verifier) + 5

    if slice_name == "retrieval":
        plan = add(
            "model-plan", "model", "model.plan", 10, 80,
            input_tokens=120, output_tokens=35, cost_units=_cost(120, 35), attributes={"phase": "plan"},
        )
        first = add(
            "retrieve-a", "retrieval", "knowledge.search", 85, 165 + number * 3,
            depends=(plan,), cost_units=0.25, attributes={"index": "handbook"},
        )
        second = add(
            "retrieve-b", "retrieval", "knowledge.search", 85, 145 + number * 2,
            depends=(plan,), cost_units=0.25, attributes={"index": "procedures"},
        )
        missing_output = number == 5
        answer = add(
            "model-answer", "model", "model.answer", 175 + number * 3, 275 + number * 3,
            depends=(first, second), input_tokens=240 + number * 5,
            output_tokens=None if missing_output else 80 + number,
            cost_units=_cost(240 + number * 5, None if missing_output else 80 + number),
            attributes={"phase": "answer"},
        )
        verify = add("verify", "verifier", "verify.outcome", 280 + number * 3, 320 + number * 3, depends=(answer,))
        return spans, next(span.end_ms for span in spans if span.span_id == verify) + 5

    if slice_name == "write":
        plan = add(
            "model-plan", "model", "model.plan", 10, 90,
            input_tokens=150, output_tokens=45, cost_units=_cost(150, 45), attributes={"phase": "plan"},
        )
        approval = add("approval", "approval", "policy.approval", 95, 125 + number, depends=(plan,))
        tool = add(
            "tool-write", "tool", "workspace.write", 130 + number, 220 + number * 2,
            depends=(approval,), cost_units=0.25, attributes={"operation": "bounded_write"},
        )
        verify = add("verify", "verifier", "verify.outcome", 225 + number * 2, 275 + number * 2, depends=(tool,))
        return spans, next(span.end_ms for span in spans if span.span_id == verify) + 5

    context = add(
        "context", "retrieval", "context.assemble", 10, 55,
        cost_units=0.25, attributes={"source_count": 2},
    )
    model = add(
        "model-plan", "model", "model.plan", 60, 150,
        depends=(context,), input_tokens=180, output_tokens=50, cost_units=_cost(180, 50),
        attributes={"phase": "plan"},
    )
    retryable = number in {1, 3, 5}
    permanent_error = number == 2
    first_status = "error" if retryable or permanent_error else "ok"
    first_tool = add(
        "tool-attempt-1", "tool", "remote.tool", 155, 250 + number * 4,
        depends=(model,), status=first_status, cost_units=0.25,
        error_type="timeout" if retryable else ("permission_denied" if permanent_error else None),
        attributes={"attempt": 1},
    )
    last = first_tool
    cursor = 255 + number * 4
    if retryable:
        retry = add(
            "retry", "retry", "retry.schedule", cursor, cursor + 20,
            depends=(first_tool,), attributes={"policy": RELEASE_MODIFIERS[release]},
        )
        cursor += 25
        if release == "incident":
            repeated_context = add(
                "context-repeated", "retrieval", "context.assemble", cursor, cursor + 50,
                depends=(retry,), cost_units=0.25, attributes={"source_count": 2, "repeated": True},
            )
            cursor += 55
            repeated_model = add(
                "model-repeated", "model", "model.plan", cursor, cursor + 120,
                depends=(repeated_context,), input_tokens=210, output_tokens=55,
                cost_units=_cost(210, 55), attributes={"phase": "retry_plan", "repeated": True},
            )
            cursor += 125
            retry_depends = (repeated_model,)
        else:
            retry_depends = (retry,)
        last = add(
            "tool-attempt-2", "tool", "remote.tool", cursor, cursor + 85,
            depends=retry_depends, cost_units=0.25, attributes={"attempt": 2},
        )
        cursor += 90
    verify_status = "error" if permanent_error else "ok"
    verify = add(
        "verify", "verifier", "verify.outcome", cursor, cursor + 45,
        depends=(last,), status=verify_status,
        error_type="outcome_failed" if permanent_error else None,
    )
    return spans, next(span.end_ms for span in spans if span.span_id == verify) + 5


def build_trace_fixture() -> tuple[TraceRecord, ...]:
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    traces: list[TraceRecord] = []
    for release in ("stable", "incident", "fixed"):
        for scenario in scenarios:
            slice_name = scenario["slice"]
            number = int(scenario["scenario_id"].rsplit("-", 1)[1])
            trace_id = f"trace-{release}-{slice_name}-{number:02d}"
            root_id = f"{trace_id}:root"
            container_id = f"{trace_id}:agent-run"
            work, ended_at = _work_spans(trace_id, slice_name, number, release)
            failed = slice_name == "recovery" and number == 2
            root_status = "error" if failed else "ok"
            spans = (
                SpanRecord(
                    trace_id, root_id, None, (), "root", "agent.request", 0, ended_at,
                    root_status, {"scope": "request"}, None, None, None, None, None,
                    "permission_denied" if failed else None,
                ),
                SpanRecord(
                    trace_id, container_id, root_id, (), "container", "agent.run", 5,
                    ended_at - 2, root_status, {"scope": "run"}, None, None, None, None,
                    None, "permission_denied" if failed else None,
                ),
                *work,
            )
            traces.append(
                TraceRecord(
                    trace_id=trace_id,
                    session_id=f"session-{slice_name}-{number:02d}",
                    release_id=release,
                    scenario_id=scenario["scenario_id"],
                    slice=slice_name,
                    started_at_ms=0,
                    ended_at_ms=ended_at,
                    status="failure" if failed else "success",
                    outcome_score=0.0 if failed else 1.0,
                    spans=spans,
                    tags={
                        "release_modifier": RELEASE_MODIFIERS[release],
                        "logical_operations": scenario["logical_operations"],
                        "fixture_version": "chapter14.trace-fixture.v1",
                    },
                    sampling=None,
                    telemetry_complete=bool(scenario.get("telemetry_complete", True)),
                )
            )
    return tuple(traces)


def build_shuffled_log_fixture(trace: TraceRecord) -> tuple[dict[str, object], ...]:
    """Flatten spans into deliberately unordered logs with no causal edges."""
    logs = [
        {
            "timestamp_ms": span.start_ms,
            "level": "error" if span.status == "error" else "info",
            "event": "span_started",
            "trace_id": trace.trace_id,
            "span_id": span.span_id,
            "name": span.name,
            "status": span.status,
        }
        for span in trace.spans
    ]
    return tuple(
        sorted(
            logs,
            key=lambda item: hashlib.sha256(f"{trace.trace_id}:{item['span_id']}".encode()).hexdigest(),
        )
    )
