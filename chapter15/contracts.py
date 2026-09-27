"""Stable, immutable and JSON-ready contracts for the Chapter 15 lab.

The lab deliberately separates evidence records from the later teaching
simulations.  Invalid provenance, split or safety semantics fail at the
boundary instead of becoming silent assumptions in an experiment report.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math
from types import MappingProxyType
from typing import Any, Mapping


class InterventionKind(StrEnum):
    """The smallest intervention that may explain a recurring failure."""

    RAG_CONTEXT = "rag_context"
    HARNESS = "harness"
    PROMPT_SKILL = "prompt_skill"
    MODEL_ROUTE = "model_route"
    POST_TRAINING = "post_training"
    INCONCLUSIVE = "inconclusive"


class DataSplit(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    EVAL = "eval"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class ReleaseDecisionKind(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


def _values(enum_type: type[StrEnum]) -> frozenset[str]:
    return frozenset(item.value for item in enum_type)


def _required(value: str, code: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(code)


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


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


def _as_dict(instance: object) -> dict[str, Any]:
    fields = getattr(instance, "__dataclass_fields__")
    return {name: _thaw(getattr(instance, name)) for name in fields}


@dataclass(frozen=True)
class FailureObservation:
    observation_id: str
    task_id: str
    symptom: str
    repeated_across_tasks: bool
    missing_facts: bool
    deterministic_boundary_available: bool
    instruction_ambiguous: bool
    model_capacity_evidence: bool
    reusable_supervision: bool
    counterfactual_checks: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("observation_id", "task_id", "symptom"):
            _required(getattr(self, field_name), f"missing_{field_name}")
        counterfactual_checks = tuple(self.counterfactual_checks)
        evidence_refs = tuple(self.evidence_refs)
        if not counterfactual_checks or not evidence_refs:
            raise ValueError("missing_failure_evidence")
        object.__setattr__(self, "counterfactual_checks", counterfactual_checks)
        object.__setattr__(self, "evidence_refs", evidence_refs)

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)


@dataclass(frozen=True)
class TaskCase:
    task_id: str
    family_id: str
    prompt: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    success_condition: str
    budget_steps: int
    tags: tuple[str, ...]
    split: str

    def __post_init__(self) -> None:
        for field_name in ("task_id", "family_id", "prompt", "success_condition"):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if self.split not in _values(DataSplit):
            raise ValueError("invalid_data_split")
        if not isinstance(self.budget_steps, int) or isinstance(self.budget_steps, bool) or self.budget_steps <= 0:
            raise ValueError("invalid_budget_steps")
        allowed = tuple(self.allowed_actions)
        forbidden = tuple(self.forbidden_actions)
        if not allowed:
            raise ValueError("missing_allowed_actions")
        if set(allowed) & set(forbidden):
            raise ValueError("action_policy_overlap")
        object.__setattr__(self, "allowed_actions", allowed)
        object.__setattr__(self, "forbidden_actions", forbidden)
        object.__setattr__(self, "tags", tuple(self.tags))

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)


@dataclass(frozen=True)
class TrajectoryStep:
    step_index: int
    state_id: str
    observation: str
    action: str
    tool_name: str | None
    tool_arguments: Mapping[str, Any]
    tool_result: Mapping[str, Any] | None
    action_probability: float | None
    reward_components: Mapping[str, float]
    safety_events: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.step_index, int) or isinstance(self.step_index, bool) or self.step_index < 0:
            raise ValueError("invalid_step_index")
        for field_name in ("state_id", "observation", "action"):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if self.action_probability is not None and (
            not _finite_number(self.action_probability) or not 0 <= self.action_probability <= 1
        ):
            raise ValueError("invalid_action_probability")
        if any(not _finite_number(value) for value in self.reward_components.values()):
            raise ValueError("invalid_reward_component")
        object.__setattr__(self, "tool_arguments", _freeze(self.tool_arguments))
        object.__setattr__(self, "tool_result", None if self.tool_result is None else _freeze(self.tool_result))
        object.__setattr__(self, "reward_components", _freeze(self.reward_components))
        object.__setattr__(self, "safety_events", tuple(self.safety_events))

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)


@dataclass(frozen=True)
class TrajectoryRecord:
    trajectory_id: str
    task_id: str
    family_id: str
    split: str
    slice: str
    source_run_id: str
    model_fingerprint: str
    harness_fingerprint: str
    transform_history: tuple[str, ...]
    steps: tuple[TrajectoryStep, ...]
    outcome: str
    verifier_passed: bool
    protected_writes: tuple[str, ...]
    safety_events: tuple[str, ...]
    contains_sensitive_data: bool
    accessed_hidden_answer: bool
    telemetry_complete: bool
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        for field_name in ("trajectory_id", "task_id", "family_id", "slice", "outcome"):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if self.split not in _values(DataSplit):
            raise ValueError("invalid_data_split")
        provenance = (
            self.source_run_id,
            self.model_fingerprint,
            self.harness_fingerprint,
        )
        history = tuple(self.transform_history)
        if any(not isinstance(value, str) or not value.strip() for value in provenance) or not history:
            raise ValueError("missing_trajectory_provenance")
        steps = tuple(self.steps)
        indexes = [step.step_index for step in steps]
        if len(indexes) != len(set(indexes)):
            raise ValueError("duplicate_step_index")
        if indexes != sorted(indexes):
            raise ValueError("unordered_step_index")
        object.__setattr__(self, "transform_history", history)
        object.__setattr__(self, "steps", steps)
        object.__setattr__(self, "protected_writes", tuple(self.protected_writes))
        object.__setattr__(self, "safety_events", tuple(self.safety_events))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        payload = _as_dict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload


@dataclass(frozen=True)
class SupervisedExample:
    example_id: str
    state_id: str
    target_action: str
    source_trajectory_id: str
    sample_weight: float
    retention_reason: str

    def __post_init__(self) -> None:
        for field_name in ("example_id", "state_id", "target_action", "source_trajectory_id", "retention_reason"):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if not _finite_number(self.sample_weight) or self.sample_weight <= 0:
            raise ValueError("invalid_sample_weight")

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)


@dataclass(frozen=True)
class PreferencePair:
    pair_id: str
    chosen_state_id: str
    rejected_state_id: str
    chosen_action: str
    rejected_action: str
    policy_chosen_logp: float
    policy_rejected_logp: float
    reference_chosen_logp: float
    reference_rejected_logp: float
    source_trajectory_ids: tuple[str, ...]
    preference_source: str
    confidence: float

    def __post_init__(self) -> None:
        for field_name in (
            "pair_id",
            "chosen_state_id",
            "rejected_state_id",
            "chosen_action",
            "rejected_action",
            "preference_source",
        ):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if self.chosen_state_id != self.rejected_state_id:
            raise ValueError("preference_state_mismatch")
        if self.chosen_action == self.rejected_action:
            raise ValueError("preference_action_tie")
        logps = (
            self.policy_chosen_logp,
            self.policy_rejected_logp,
            self.reference_chosen_logp,
            self.reference_rejected_logp,
        )
        if any(not _finite_number(value) for value in logps):
            raise ValueError("invalid_preference_log_probability")
        if not _finite_number(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("invalid_preference_confidence")
        source_ids = tuple(self.source_trajectory_ids)
        if not source_ids:
            raise ValueError("missing_preference_provenance")
        object.__setattr__(self, "source_trajectory_ids", source_ids)

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)


@dataclass(frozen=True)
class RewardSpec:
    spec_id: str
    outcome_weight: float
    process_weight: float
    efficiency_weight: float
    safety_penalty: float
    safety_veto: bool

    def __post_init__(self) -> None:
        _required(self.spec_id, "missing_reward_spec_id")
        if any(
            not _finite_number(value) or value < 0
            for value in (self.outcome_weight, self.process_weight, self.efficiency_weight)
        ):
            raise ValueError("invalid_reward_weight")
        if not _finite_number(self.safety_penalty) or self.safety_penalty > 0:
            raise ValueError("invalid_safety_penalty")
        if type(self.safety_veto) is not bool:
            raise ValueError("invalid_safety_veto")

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)


@dataclass(frozen=True)
class AuditFinding:
    finding_id: str
    severity: str
    reason_code: str
    evidence_refs: tuple[str, ...]
    recommended_action: str
    blocks_training: bool

    def __post_init__(self) -> None:
        for field_name in ("finding_id", "reason_code", "recommended_action"):
            _required(getattr(self, field_name), f"missing_{field_name}")
        if self.severity not in _values(FindingSeverity):
            raise ValueError("invalid_finding_severity")
        evidence_refs = tuple(self.evidence_refs)
        if not evidence_refs:
            raise ValueError("missing_finding_evidence")
        if type(self.blocks_training) is not bool:
            raise ValueError("invalid_blocks_training")
        object.__setattr__(self, "evidence_refs", evidence_refs)

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)


@dataclass(frozen=True)
class PostTrainingReport:
    schema_version: str
    fixture_version: str
    data_summary: Mapping[str, Any]
    objective_summary: Mapping[str, Any]
    simulation_summary: Mapping[str, Any]
    release_decision: str
    evidence_limits: tuple[str, ...]
    findings: tuple[AuditFinding, ...]

    def __post_init__(self) -> None:
        _required(self.schema_version, "missing_schema_version")
        _required(self.fixture_version, "missing_fixture_version")
        if self.release_decision not in _values(ReleaseDecisionKind):
            raise ValueError("invalid_release_decision")
        limits = tuple(self.evidence_limits)
        if not limits:
            raise ValueError("missing_evidence_limits")
        object.__setattr__(self, "data_summary", _freeze(self.data_summary))
        object.__setattr__(self, "objective_summary", _freeze(self.objective_summary))
        object.__setattr__(self, "simulation_summary", _freeze(self.simulation_summary))
        object.__setattr__(self, "evidence_limits", limits)
        object.__setattr__(self, "findings", tuple(self.findings))

    def to_dict(self) -> dict[str, Any]:
        payload = _as_dict(self)
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        return payload
