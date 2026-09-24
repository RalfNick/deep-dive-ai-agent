"""Stable, JSON-friendly contracts for the chapter 13 evaluation harness."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

TASK_SLICES = frozenset({"basic", "edge", "safety", "recovery"})
TRIAL_STATUSES = frozenset({"completed", "agent_failed", "environment_error", "invalid"})
GRADER_VERDICTS = frozenset({"pass", "fail", "unknown", "not_applicable"})


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    prompt: str
    slice: str
    split: str
    expected_output: str
    allowed_write_prefixes: tuple[str, ...]
    protected_paths: tuple[str, ...]
    max_steps: int
    max_tool_calls: int
    baseline_successes: int
    candidate_successes: int
    fixture_id: str = "linkcheck-v1"
    labels: tuple[str, ...] = ("teaching",)
    success_conditions: tuple[str, ...] = ("solution_matches",)
    seed_strategy: str = "fixed-five-v1"

    def __post_init__(self) -> None:
        if self.slice not in TASK_SLICES:
            raise ValueError("unknown_task_slice")
        if self.max_steps <= 0 or self.max_tool_calls <= 0:
            raise ValueError("invalid_budget")
        if not 0 <= self.baseline_successes <= 5 or not 0 <= self.candidate_successes <= 5:
            raise ValueError("invalid_success_schedule")
        if not self.task_id or not self.prompt or not self.expected_output:
            raise ValueError("missing_task_field")
        if not self.fixture_id or not self.labels or not self.success_conditions or not self.seed_strategy:
            raise ValueError("missing_task_metadata")


@dataclass(frozen=True)
class GraderResult:
    name: str
    verdict: str
    reason_codes: tuple[str, ...]
    evidence: tuple[str, ...]
    metrics: dict[str, Any]

    def __post_init__(self) -> None:
        if self.verdict not in GRADER_VERDICTS:
            raise ValueError("invalid_grader_verdict")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reason_codes"] = list(self.reason_codes)
        payload["evidence"] = list(self.evidence)
        return payload


@dataclass(frozen=True)
class TrialRecord:
    task_id: str
    variant: str
    trial_id: str
    seed: int
    environment_id: str
    status: str
    final_answer: str
    outcome: dict[str, Any]
    events: tuple[dict[str, Any], ...]
    usage: dict[str, int | float | None]
    error: str | None
    graders: tuple[GraderResult, ...]

    def __post_init__(self) -> None:
        if self.status not in TRIAL_STATUSES:
            raise ValueError("invalid_trial_status")
        if self.variant not in {"baseline", "candidate"}:
            raise ValueError("invalid_variant")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "variant": self.variant,
            "trial_id": self.trial_id,
            "seed": self.seed,
            "environment_id": self.environment_id,
            "status": self.status,
            "final_answer": self.final_answer,
            "outcome": dict(self.outcome),
            "events": [dict(item) for item in self.events],
            "usage": dict(self.usage),
            "error": self.error,
            "graders": [item.to_dict() for item in self.graders],
        }


@dataclass(frozen=True)
class EvaluationReport:
    """Versioned aggregate contract; all fields are stable JSON data."""

    schema_version: str
    decision_source: str
    task_count: int
    trial_count: int
    seeds: tuple[int, ...]
    variants: dict[str, Any]
    slice_deltas: dict[str, float]
    paired_confidence: dict[str, Any]
    release: dict[str, Any]
    judge_calibration: dict[str, Any]
    usage_boundary: dict[str, Any]
    provenance: dict[str, Any]
    summary: dict[str, Any]
    diagnostics: dict[str, Any]
    failures: tuple[dict[str, Any], ...]
    trials: tuple[dict[str, Any], ...]
    limits: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.schema_version or self.task_count <= 0 or self.trial_count <= 0:
            raise ValueError("invalid_evaluation_report")
        if self.release.get("decision") not in {"pass", "fail", "inconclusive"}:
            raise ValueError("invalid_release_decision")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_source": self.decision_source,
            "task_count": self.task_count,
            "trial_count": self.trial_count,
            "seeds": list(self.seeds),
            "variants": self.variants,
            "slice_deltas": self.slice_deltas,
            "paired_confidence": self.paired_confidence,
            "release": self.release,
            "judge_calibration": self.judge_calibration,
            "usage_boundary": self.usage_boundary,
            "provenance": self.provenance,
            "summary": self.summary,
            "diagnostics": self.diagnostics,
            "failures": [dict(item) for item in self.failures],
            "trials": [dict(item) for item in self.trials],
            "limits": list(self.limits),
        }
