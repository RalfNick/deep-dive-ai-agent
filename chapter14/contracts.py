"""Stable, immutable, JSON-friendly contracts for the Chapter 14 lab."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class ReleaseId(StrEnum):
    STABLE = "stable"
    INCIDENT = "incident"
    FIXED = "fixed"


class ScenarioSlice(StrEnum):
    SIMPLE = "simple"
    RETRIEVAL = "retrieval"
    WRITE = "write"
    RECOVERY = "recovery"


class SpanKind(StrEnum):
    ROOT = "root"
    MODEL = "model"
    RETRIEVAL = "retrieval"
    TOOL = "tool"
    RETRY = "retry"
    APPROVAL = "approval"
    VERIFIER = "verifier"


class SpanStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class TraceStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


class SamplingStage(StrEnum):
    HEAD = "head"
    TAIL = "tail"
    COMBINED = "combined"


class SamplingDecisionKind(StrEnum):
    KEEP = "keep"
    DROP = "drop"


class IncidentConclusion(StrEnum):
    CONFIRMED = "confirmed"
    INCONCLUSIVE = "inconclusive"
    RULED_OUT = "ruled_out"


def _values(enum_type: type[StrEnum]) -> frozenset[str]:
    return frozenset(item.value for item in enum_type)


def _required(value: str, code: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(code)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, StrEnum):
        return value.value
    return value


@dataclass(frozen=True)
class BenchmarkCard:
    benchmark_id: str
    benchmark_version: str
    task_subset: str
    task_period: str
    subject: str
    harness: str
    model: str
    tools: tuple[str, ...]
    environment: str
    step_budget: int
    token_budget: int | None
    timeout_ms: int
    retry_policy: str
    attempts_per_task: int
    metric: str
    exclusions: tuple[str, ...]
    contamination_risk: str
    source: str
    score: float | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "benchmark_id", "benchmark_version", "task_subset", "task_period", "subject",
            "harness", "model", "environment", "retry_policy", "metric",
            "contamination_risk", "source",
        ):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if self.step_budget <= 0 or self.timeout_ms <= 0 or self.attempts_per_task <= 0:
            raise ValueError("invalid_benchmark_budget")
        if self.token_budget is not None and self.token_budget <= 0:
            raise ValueError("invalid_benchmark_budget")
        if self.score is not None and not 0 <= self.score <= 100:
            raise ValueError("invalid_benchmark_score")
        object.__setattr__(self, "tools", tuple(self.tools))
        object.__setattr__(self, "exclusions", tuple(self.exclusions))

    def to_dict(self) -> dict[str, Any]:
        return {name: _thaw(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    depends_on_span_ids: tuple[str, ...]
    kind: str
    name: str
    start_ms: int
    end_ms: int
    status: str
    attributes: Mapping[str, Any]
    input_digest: str | None
    output_digest: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost_units: float | None
    error_type: str | None

    def __post_init__(self) -> None:
        _required(self.trace_id, "missing_trace_id")
        _required(self.span_id, "missing_span_id")
        _required(self.name, "missing_span_name")
        if self.kind not in _values(SpanKind):
            raise ValueError("invalid_span_kind")
        if self.status not in _values(SpanStatus):
            raise ValueError("invalid_span_status")
        if self.start_ms < 0:
            raise ValueError("negative_span_time")
        if self.end_ms < self.start_ms:
            raise ValueError("span_ends_before_start")
        for usage in (self.input_tokens, self.output_tokens, self.cost_units):
            if usage is not None and usage < 0:
                raise ValueError("negative_usage")
        object.__setattr__(self, "depends_on_span_ids", tuple(self.depends_on_span_ids))
        object.__setattr__(self, "attributes", _freeze(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        return {name: _thaw(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class TraceRecord:
    trace_id: str
    session_id: str
    release_id: str
    scenario_id: str
    slice: str
    started_at_ms: int
    ended_at_ms: int
    status: str
    outcome_score: float
    spans: tuple[SpanRecord, ...]
    tags: Mapping[str, Any]
    sampling: Mapping[str, Any] | None
    telemetry_complete: bool

    def __post_init__(self) -> None:
        for field_name in ("trace_id", "session_id", "scenario_id"):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if self.release_id not in _values(ReleaseId):
            raise ValueError("invalid_release_id")
        if self.slice not in _values(ScenarioSlice):
            raise ValueError("invalid_scenario_slice")
        if self.status not in _values(TraceStatus):
            raise ValueError("invalid_trace_status")
        if self.started_at_ms < 0:
            raise ValueError("negative_trace_time")
        if self.ended_at_ms < self.started_at_ms:
            raise ValueError("trace_ends_before_start")
        if not 0 <= self.outcome_score <= 1:
            raise ValueError("invalid_outcome_score")
        spans = tuple(self.spans)
        if len({span.span_id for span in spans}) != len(spans):
            raise ValueError("duplicate_span_id")
        object.__setattr__(self, "spans", spans)
        object.__setattr__(self, "tags", _freeze(self.tags))
        object.__setattr__(self, "sampling", None if self.sampling is None else _freeze(self.sampling))

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "release_id": self.release_id,
            "scenario_id": self.scenario_id,
            "slice": self.slice,
            "started_at_ms": self.started_at_ms,
            "ended_at_ms": self.ended_at_ms,
            "status": self.status,
            "outcome_score": self.outcome_score,
            "spans": [span.to_dict() for span in self.spans],
            "tags": _thaw(self.tags),
            "sampling": _thaw(self.sampling),
            "telemetry_complete": self.telemetry_complete,
        }


@dataclass(frozen=True)
class SamplingDecision:
    trace_id: str
    stage: str
    decision: str
    reason_codes: tuple[str, ...]
    probability: float | None
    policy_version: str

    def __post_init__(self) -> None:
        _required(self.trace_id, "missing_trace_id")
        _required(self.policy_version, "missing_sampling_policy")
        if self.stage not in _values(SamplingStage):
            raise ValueError("invalid_sampling_stage")
        if self.decision not in _values(SamplingDecisionKind):
            raise ValueError("invalid_sampling_decision")
        if self.probability is not None and not 0 <= self.probability <= 1:
            raise ValueError("invalid_sampling_probability")
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))

    def to_dict(self) -> dict[str, Any]:
        return {name: _thaw(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class IncidentReport:
    symptom: str
    affected_slices: tuple[str, ...]
    data_completeness: float
    candidate_causes: tuple[str, ...]
    supporting_trace_ids: tuple[str, ...]
    counterevidence_trace_ids: tuple[str, ...]
    ablation_results: tuple[Mapping[str, Any], ...]
    root_cause: str | None
    confidence: float
    conclusion: str
    unknowns: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    regression_task_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.symptom, "missing_incident_symptom")
        if self.conclusion not in _values(IncidentConclusion):
            raise ValueError("invalid_incident_conclusion")
        if not 0 <= self.data_completeness <= 1 or not 0 <= self.confidence <= 1:
            raise ValueError("invalid_incident_confidence")
        for name in (
            "affected_slices", "candidate_causes", "supporting_trace_ids",
            "counterevidence_trace_ids", "unknowns", "recommended_actions",
            "regression_task_ids",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "ablation_results", tuple(_freeze(item) for item in self.ablation_results))

    def to_dict(self) -> dict[str, Any]:
        return {name: _thaw(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    trace_id: str | None = None
    span_id: str | None = None
    field: str | None = None

    def __post_init__(self) -> None:
        _required(self.code, "missing_issue_code")
        _required(self.message, "missing_issue_message")

    def to_dict(self) -> dict[str, Any]:
        return {name: _thaw(getattr(self, name)) for name in self.__dataclass_fields__}
