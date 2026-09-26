"""Deterministic hypothesis testing for the Chapter 14 incident."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import IncidentReport, TraceRecord
from .metrics import summarize_release


RATE_CARD_PATH = Path(__file__).with_name("fixtures") / "rate-card.json"
HYPOTHESES = ("model", "prompt", "context_assembly", "tool_latency", "retry_policy")


def _summaries(traces: Sequence[TraceRecord]) -> dict[str, dict[str, object]]:
    rate_card = json.loads(RATE_CARD_PATH.read_text(encoding="utf-8"))
    return {
        release: summarize_release(tuple(trace for trace in traces if trace.release_id == release), rate_card)
        for release in ("stable", "incident", "fixed")
    }


def run_ablations(traces: Sequence[TraceRecord]) -> tuple[dict[str, object], ...]:
    summaries = _summaries(traces)
    stable = summaries["stable"]
    incident = summaries["incident"]
    fixed = summaries["fixed"]
    stable_latency = float(stable["latency_ms"]["p95"])
    stable_cost = float(stable["usage"]["cost_units_total"])
    stable_retry = float(stable["retry_amplification"])

    simulations: dict[str, dict[str, float]] = {
        "model": {
            "latency_p95_ms": float(incident["latency_ms"]["p95"]),
            "cost_units_total": float(incident["usage"]["cost_units_total"]),
            "retry_amplification": float(incident["retry_amplification"]),
        },
        "prompt": {
            "latency_p95_ms": float(incident["latency_ms"]["p95"]),
            "cost_units_total": float(incident["usage"]["cost_units_total"]),
            "retry_amplification": float(incident["retry_amplification"]),
        },
        "context_assembly": {
            "latency_p95_ms": float(incident["latency_ms"]["p95"]),
            "cost_units_total": round((float(incident["usage"]["cost_units_total"]) + stable_cost) / 2, 6),
            "retry_amplification": float(incident["retry_amplification"]),
        },
        "tool_latency": {
            "latency_p95_ms": stable_latency,
            "cost_units_total": float(incident["usage"]["cost_units_total"]),
            "retry_amplification": float(incident["retry_amplification"]),
        },
        "retry_policy": {
            "latency_p95_ms": float(fixed["latency_ms"]["p95"]),
            "cost_units_total": float(fixed["usage"]["cost_units_total"]),
            "retry_amplification": float(fixed["retry_amplification"]),
        },
    }

    results: list[dict[str, object]] = []
    for hypothesis in HYPOTHESES:
        simulation = simulations[hypothesis]
        removed: list[str] = []
        if simulation["latency_p95_ms"] <= stable_latency:
            removed.append("latency")
        if simulation["cost_units_total"] <= stable_cost:
            removed.append("cost")
        if simulation["retry_amplification"] <= stable_retry:
            removed.append("retry_amplification")
        results.append(
            {
                "hypothesis": hypothesis,
                "intervention": f"hold_{hypothesis}_at_stable_contract",
                **simulation,
                "outcome_score_mean": incident["outcome_score_mean"],
                "removed_symptoms": removed,
                "all_canonical_symptoms_removed": len(removed) == 3,
                "evidence_mode": "deterministic_counterfactual_fixture",
            }
        )
    return tuple(results)


def diagnose_incident(
    traces: Sequence[TraceRecord],
    *,
    data_completeness: float | None = None,
    ablation_results: Sequence[Mapping[str, Any]] | None = None,
    slice_confounded: bool = False,
) -> IncidentReport:
    completeness = (
        data_completeness
        if data_completeness is not None
        else sum(trace.telemetry_complete for trace in traces) / len(traces)
    )
    ablations = tuple(dict(item) for item in (ablation_results or run_ablations(traces)))
    winners = [item for item in ablations if item.get("all_canonical_symptoms_removed") is True]
    unknowns = ["provider_usage_partially_missing", "fixture_does_not_prove_real_world_causality"]
    if completeness < 0.9:
        unknowns.append("telemetry_completeness_below_threshold")
    if len(winners) != 1:
        unknowns.append("competing_or_missing_causal_explanations")
    if slice_confounded:
        unknowns.append("slice_confounding_not_resolved")

    conclusive = completeness >= 0.9 and len(winners) == 1 and not slice_confounded
    root_cause = str(winners[0]["hypothesis"]) if conclusive else None
    supporting = tuple(
        trace.trace_id
        for trace in traces
        if trace.release_id == "incident" and trace.slice == "recovery" and trace.scenario_id in {"recovery-01", "recovery-03", "recovery-05"}
    )
    counterevidence = tuple(
        trace.trace_id
        for trace in traces
        if trace.release_id == "incident" and (
            trace.slice == "simple" or trace.scenario_id in {"recovery-04", "recovery-06"}
        )
    )[:4]
    regression_ids = (
        "reg-retry-latency",
        "reg-retry-cost",
        "reg-retry-amplification",
    ) if conclusive else ()

    return IncidentReport(
        symptom="outcome stable while p95 latency, cost units, and retry amplification regress",
        affected_slices=("recovery",),
        data_completeness=round(completeness, 6),
        candidate_causes=HYPOTHESES,
        supporting_trace_ids=supporting,
        counterevidence_trace_ids=counterevidence,
        ablation_results=ablations,
        root_cause=root_cause,
        confidence=0.92 if conclusive else min(0.49, round(completeness / 2, 6)),
        conclusion="confirmed" if conclusive else "inconclusive",
        unknowns=tuple(unknowns),
        recommended_actions=(
            "bound_retry_scope_to_the_failed_tool_call",
            "replay_recovery_slices_before_release",
            "retain_population_counters_when_traces_are_sampled",
        ),
        regression_task_ids=regression_ids,
    )


def build_regression_tasks(report: IncidentReport) -> tuple[dict[str, object], ...]:
    if report.conclusion != "confirmed" or report.root_cause is None:
        return ()
    evidence = list(report.supporting_trace_ids)
    return (
        {
            "task_id": "reg-retry-latency",
            "slice": "recovery",
            "assertion": "fixed p95 latency is no worse than stable",
            "source_trace_ids": evidence,
        },
        {
            "task_id": "reg-retry-cost",
            "slice": "recovery",
            "assertion": "retry does not repeat context assembly or model planning",
            "source_trace_ids": evidence,
        },
        {
            "task_id": "reg-retry-amplification",
            "slice": "recovery",
            "assertion": "retry amplification returns to the stable bound",
            "source_trace_ids": evidence,
        },
    )
