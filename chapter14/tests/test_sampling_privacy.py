from __future__ import annotations

import json

from chapter14.privacy import redact_payload, validate_export_safe
from chapter14.sampling import combined_sample, head_sample, sampling_report, tail_sample
from chapter14.trace_builder import build_trace_fixture


def test_redaction_handles_nested_secrets_identity_and_tool_arguments_before_export() -> None:
    raw = {
        "headers": {"Authorization": "Bearer demo-secret", "Cookie": "sid=demo"},
        "api_key": "sk-example-not-real",
        "actor": {"email": "reader@example.com", "user_id": "user-42"},
        "tool_arguments": {"path": "private/answer.txt", "content": "complete file"},
        "safe": "keep me",
    }

    first = redact_payload(raw, salt="chapter14-test-salt")
    second = redact_payload(raw, salt="chapter14-test-salt")

    assert first == second
    assert first["headers"] == {"Authorization": "[REDACTED]", "Cookie": "[REDACTED]"}
    assert first["api_key"] == "[REDACTED]"
    assert first["actor"]["email"].startswith("hash:")
    assert first["actor"]["user_id"].startswith("hash:")
    assert first["tool_arguments"]["redacted"] is True
    assert first["safe"] == "keep me"
    assert validate_export_safe(first) == ()


def test_export_gate_rejects_forbidden_keys_and_values() -> None:
    raw = {
        "nested": {"chain_of_thought": "private reasoning"},
        "note": "contact reader@example.com",
        "token": "Bearer secret-value",
    }

    codes = {issue.code for issue in validate_export_safe(raw)}

    assert codes == {"forbidden_export_field", "pii_in_export", "secret_in_export"}


def test_head_sampling_is_trace_id_deterministic_and_can_miss_a_rare_error() -> None:
    traces = build_trace_fixture()
    first = [head_sample(trace, 0.1, "head.v1") for trace in traces]
    second = [head_sample(trace, 0.1, "head.v1") for trace in reversed(traces)]
    reversed_by_id = {item.trace_id: item.to_dict() for item in second}

    assert all(item.to_dict() == reversed_by_id[item.trace_id] for item in first)
    error_trace_ids = {trace.trace_id for trace in traces if trace.status != "success"}
    kept = {item.trace_id for item in first if item.decision == "keep"}
    assert error_trace_ids - kept


def test_tail_sampling_retains_diagnostic_cases_without_claiming_population_rates() -> None:
    traces = build_trace_fixture()
    by_id = {trace.trace_id: trace for trace in traces}
    thresholds = {"slow_ms": 450, "new_releases": ("incident",)}
    examples = {
        "error": by_id["trace-stable-recovery-02"],
        "slow": by_id["trace-incident-recovery-01"],
        "approval": by_id["trace-stable-write-01"],
        "incomplete": by_id["trace-stable-recovery-06"],
        "new_release": by_id["trace-incident-simple-01"],
    }

    decisions = {name: tail_sample(trace, thresholds, "tail.v1") for name, trace in examples.items()}

    assert all(item.decision == "keep" for item in decisions.values())
    assert "trace_error" in decisions["error"].reason_codes
    assert "slow_trace" in decisions["slow"].reason_codes
    assert "approval_or_security" in decisions["approval"].reason_codes
    assert "telemetry_incomplete" in decisions["incomplete"].reason_codes
    assert "new_release" in decisions["new_release"].reason_codes


def test_combined_sampling_and_report_keep_population_and_diagnostic_denominators_separate() -> None:
    traces = build_trace_fixture()
    thresholds = {"slow_ms": 450, "new_releases": ("incident",)}
    decisions = tuple(combined_sample(trace, 0.1, thresholds, "combined.v1") for trace in traces)
    report = sampling_report(traces, decisions, salt="chapter14-report-salt")
    serialized = json.dumps(report, sort_keys=True)

    assert report["population_metrics"] == {"request_count": 72, "failed_request_count": 3}
    assert report["diagnostic_retained_counts"]["retained_trace_count"] >= 24
    assert 0 < report["trace_coverage"] <= 1
    assert report["telemetry_completeness"] == 69 / 72
    assert "tail_sample_error_rate" not in serialized
    assert "diagnostic_error_rate" not in serialized
    assert report["limits"] == ["tail_retention_is_diagnostic_not_an_unbiased_denominator"]
    assert validate_export_safe(report) == ()
