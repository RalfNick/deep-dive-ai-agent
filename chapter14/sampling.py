"""Deterministic Head/Tail sampling with separate population counters."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from typing import Any

from .contracts import SamplingDecision, TraceRecord
from .privacy import redact_trace, validate_export_safe


def _bucket(trace_id: str) -> float:
    integer = int.from_bytes(hashlib.sha256(trace_id.encode()).digest()[:8], "big")
    return integer / 2**64


def head_sample(trace: TraceRecord, probability: float, policy_version: str) -> SamplingDecision:
    if not 0 <= probability <= 1:
        raise ValueError("invalid_sampling_probability")
    keep = _bucket(trace.trace_id) < probability
    return SamplingDecision(
        trace.trace_id,
        "head",
        "keep" if keep else "drop",
        ("deterministic_bucket_keep" if keep else "deterministic_bucket_drop",),
        probability,
        policy_version,
    )


def tail_sample(trace: TraceRecord, thresholds: Mapping[str, Any], policy_version: str) -> SamplingDecision:
    if validate_export_safe(trace.to_dict()):
        raise ValueError("unsafe_trace_before_tail_sampling")
    reasons: list[str] = []
    latency = trace.ended_at_ms - trace.started_at_ms
    if trace.status != "success" or any(span.status == "error" for span in trace.spans):
        reasons.append("trace_error")
    if latency >= int(thresholds.get("slow_ms", 2**63 - 1)):
        reasons.append("slow_trace")
    if any(span.kind == "approval" or span.attributes.get("security_event") is True for span in trace.spans):
        reasons.append("approval_or_security")
    if not trace.telemetry_complete:
        reasons.append("telemetry_incomplete")
    if trace.release_id in tuple(thresholds.get("new_releases", ())):
        reasons.append("new_release")
    return SamplingDecision(
        trace.trace_id,
        "tail",
        "keep" if reasons else "drop",
        tuple(reasons or ("no_tail_rule_matched",)),
        None,
        policy_version,
    )


def combined_sample(
    trace: TraceRecord,
    probability: float,
    thresholds: Mapping[str, Any],
    policy_version: str,
) -> SamplingDecision:
    if validate_export_safe(trace.to_dict()):
        raise ValueError("unsafe_trace_before_sampling")
    head = head_sample(trace, probability, f"{policy_version}.head")
    tail = tail_sample(trace, thresholds, f"{policy_version}.tail")
    keep = head.decision == "keep" or tail.decision == "keep"
    reasons = (
        ("head_sample_keep",) if head.decision == "keep" else ("head_sample_drop",)
    ) + tuple(tail.reason_codes)
    return SamplingDecision(
        trace.trace_id,
        "combined",
        "keep" if keep else "drop",
        reasons,
        probability,
        policy_version,
    )


def sampling_report(
    traces: Sequence[TraceRecord],
    decisions: Sequence[SamplingDecision],
    *,
    salt: str,
) -> dict[str, object]:
    by_trace = {decision.trace_id: decision for decision in decisions}
    if set(by_trace) != {trace.trace_id for trace in traces}:
        raise ValueError("sampling_decisions_do_not_match_traces")
    # Transform and validate every full trace before selecting a retained
    # representation. Tail decisions may inspect only an already-safe trace.
    safe_traces = [redact_trace(trace, salt=salt) for trace in traces]
    retained = [trace for trace in safe_traces if by_trace[trace.trace_id].decision == "keep"]

    retained_metadata: list[dict[str, object]] = []
    for trace in retained:
        redacted = trace.to_dict()
        issues = validate_export_safe(redacted)
        if issues:
            raise ValueError("unsafe_trace_after_redaction")
        assert isinstance(redacted, dict)
        retained_metadata.append(
            {
                "trace_id": redacted["trace_id"],
                "release_id": redacted["release_id"],
                "slice": redacted["slice"],
                "status": redacted["status"],
                "telemetry_complete": redacted["telemetry_complete"],
            }
        )

    reason_counts = {
        reason: sum(reason in by_trace[trace.trace_id].reason_codes for trace in retained)
        for reason in ("trace_error", "slow_trace", "approval_or_security", "telemetry_incomplete", "new_release")
    }
    return {
        "policy_versions": sorted({decision.policy_version for decision in decisions}),
        "population_metrics": {
            "request_count": len(traces),
            "failed_request_count": sum(trace.status != "success" for trace in traces),
        },
        "diagnostic_retained_counts": {
            "retained_trace_count": len(retained),
            **reason_counts,
        },
        "trace_coverage": len(retained) / len(traces) if traces else 0.0,
        "telemetry_completeness": sum(trace.telemetry_complete for trace in traces) / len(traces) if traces else 0.0,
        "retained_trace_metadata": retained_metadata,
        "limits": ["tail_retention_is_diagnostic_not_an_unbiased_denominator"],
    }
