from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from chapter14.diagnosis import build_regression_tasks, diagnose_incident, run_ablations
from chapter14.metrics import summarize_release
from chapter14.trace_builder import build_trace_fixture


ROOT = Path(__file__).resolve().parents[2]


def _rate_card() -> dict[str, object]:
    return json.loads((ROOT / "chapter14" / "fixtures" / "rate-card.json").read_text(encoding="utf-8"))


def test_canonical_incident_has_stable_outcome_but_latency_cost_and_retry_regress() -> None:
    traces = build_trace_fixture()
    summaries = {
        release: summarize_release(tuple(trace for trace in traces if trace.release_id == release), _rate_card())
        for release in ("stable", "incident", "fixed")
    }

    assert summaries["incident"]["outcome_score_mean"] == summaries["stable"]["outcome_score_mean"]
    assert summaries["incident"]["latency_ms"]["p95"] > summaries["stable"]["latency_ms"]["p95"]
    assert summaries["incident"]["usage"]["cost_units_total"] > summaries["stable"]["usage"]["cost_units_total"]
    assert summaries["incident"]["retry_amplification"] > summaries["stable"]["retry_amplification"]
    assert summaries["fixed"]["latency_ms"]["p95"] == summaries["stable"]["latency_ms"]["p95"]


def test_only_retry_policy_ablation_removes_all_canonical_symptoms() -> None:
    results = run_ablations(build_trace_fixture())
    winners = [item for item in results if item["all_canonical_symptoms_removed"]]

    assert [item["hypothesis"] for item in results] == [
        "model", "prompt", "context_assembly", "tool_latency", "retry_policy"
    ]
    assert [item["hypothesis"] for item in winners] == ["retry_policy"]
    assert set(winners[0]["removed_symptoms"]) == {"latency", "cost", "retry_amplification"}


def test_confirmed_report_keeps_support_counterevidence_and_builds_regressions() -> None:
    report = diagnose_incident(build_trace_fixture())
    tasks = build_regression_tasks(report)

    assert report.conclusion == "confirmed"
    assert report.root_cause == "retry_policy"
    assert report.affected_slices == ("recovery",)
    assert report.supporting_trace_ids
    assert report.counterevidence_trace_ids
    assert all(trace_id.startswith("trace-incident-") for trace_id in report.supporting_trace_ids)
    assert {task["task_id"] for task in tasks} == {
        "reg-retry-latency", "reg-retry-cost", "reg-retry-amplification"
    }


def test_low_completeness_tied_explanations_or_slice_confounding_are_inconclusive() -> None:
    traces = build_trace_fixture()
    canonical = list(run_ablations(traces))
    tied = deepcopy(canonical)
    tied[3]["all_canonical_symptoms_removed"] = True

    low = diagnose_incident(traces, data_completeness=0.6)
    ambiguous = diagnose_incident(traces, ablation_results=tuple(tied))
    confounded = diagnose_incident(traces, slice_confounded=True)

    for report in (low, ambiguous, confounded):
        assert report.conclusion == "inconclusive"
        assert report.root_cause is None
        assert build_regression_tasks(report) == ()
