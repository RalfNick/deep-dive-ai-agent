"""Immutable contracts. Arbitrary payloads are data, never executable authority."""
from dataclasses import dataclass, fields
from datetime import datetime
from collections.abc import Mapping
import types
from typing import get_type_hints, get_origin, get_args
from .serialization import freeze, plain

CLOCK = "2026-09-28T00:00:00Z"
END = "2026-09-29T00:00:00Z"
STEPS = ("open_project", "open_data", "choose_destination", "export", "verify_receipt")

def utc(value: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError("explicit UTC clock required")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid UTC clock") from exc
    if "T" not in value:
        raise ValueError("clock needs time")
    return parsed

def typed(value, annotation):
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        return any(typed(value, a) for a in args)
    if origin in (tuple, frozenset):
        return isinstance(value, origin) and all(typed(v, args[0]) for v in value)
    if origin in (Mapping, dict) or annotation is Mapping:
        return isinstance(value, Mapping)
    if annotation is object:
        return True
    if annotation in (int, bool, str, float):
        return type(value) is annotation
    if annotation is type(None):
        return value is None
    return isinstance(value, annotation)


def decode(value, annotation):
    """Decode JSON containers recursively, never coerce authority scalars."""
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        for alternative in args:
            try:
                return decode(value, alternative)
            except ValueError:
                continue
        raise ValueError("invalid union value")
    if isinstance(annotation, type) and issubclass(annotation, Contract):
        return annotation.from_dict(value)
    if origin in (tuple, frozenset):
        if not isinstance(value, (list, tuple)):
            raise ValueError("JSON array required")
        members = tuple(decode(v, args[0]) for v in value)
        return frozenset(members) if origin is frozenset else members
    if not typed(value, annotation):
        raise ValueError("invalid JSON field type")
    return value

class Contract:
    def __post_init__(self):
        hints = get_type_hints(type(self))
        for field in fields(self):
            value = freeze(getattr(self, field.name))
            object.__setattr__(self, field.name, value)
            if not typed(value, hints[field.name]):
                raise ValueError(f"invalid type: {field.name}")
            if isinstance(value, str) and not value:
                raise ValueError(f"empty {field.name}")
            if isinstance(value, (tuple, frozenset)) and any(type(v) is str and not v for v in value):
                raise ValueError(f"empty reference/item: {field.name}")
            if field.name in ("valid_from", "valid_until", "frozen_clock", "issued_at"):
                utc(value)
            if field.name.endswith("_count") and (type(value) is not int or value < 0):
                raise ValueError("invalid count/budget")
        if hasattr(self, "valid_from") and utc(self.valid_until) <= utc(self.valid_from):
            raise ValueError("invalid validity interval")
        if isinstance(self, TaskSpec):
            if self.split not in ("development", "holdout") or self.slice not in ("knowledge", "procedure", "scope", "safety_recovery"):
                raise ValueError("invalid task split/slice")
            if self.target and self.split != "development":
                raise ValueError("target cannot be holdout")

    def to_dict(self) -> dict[str, object]:
        return plain(self)

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) != {f.name for f in fields(cls)}:
            raise ValueError(f"invalid fields for {cls.__name__}")
        hints = get_type_hints(cls)
        decoded = {name: decode(item, hints[name]) for name, item in value.items()}
        return cls(**decoded)

@dataclass(frozen=True)
class Scope(Contract):
    tenant_id: str
    user_id: str | None
    domain: str
    requested_version: str

    def matches(self, request):
        return (self.tenant_id == request.tenant_id and self.domain == request.domain
                and self.requested_version == request.requested_version
                and (self.user_id is None or self.user_id == request.user_id))

@dataclass(frozen=True)
class FeedbackRecord(Contract):
    feedback_id: str
    source_id: str
    source_role: str
    purpose: str
    family_id: str
    scope: Scope
    run_ref: str
    payload: Mapping
    source_sensitive: bool
    permission: bool
    complete: bool
    evidence_refs: tuple[str, ...]
    duplicate_of: str | None
    conflict_refs: tuple[str, ...]

@dataclass(frozen=True)
class SourceAuthority(Contract):
    source_id: str
    role: str
    allowed_purposes: tuple[str, ...]
    scope: Scope
    permission: bool
    revoked: bool

@dataclass(frozen=True)
class AgentInput(Contract):
    tenant_id: str
    user_id: str
    domain: str
    requested_version: str
    question: str
    operation: str
    tool_receipts: tuple[str, ...]

@dataclass(frozen=True)
class Document(Contract):
    document_id: str
    tenant_id: str
    domain: str
    version: str
    valid_from: str
    valid_until: str
    answer: str
    steps: tuple[str, ...]
    provenance: str

@dataclass(frozen=True)
class TaskSpec(Contract):
    task_id: str
    family_id: str
    split: str
    slice: str
    agent_input: AgentInput
    success_ref: str
    target: bool
    frozen_clock: str
    revoked_source_ids: tuple[str, ...]

@dataclass(frozen=True)
class SuccessCondition(Contract):
    success_ref: str
    expected_document_id: str | None
    required_steps: tuple[str, ...]
    answer_style: str
    refusal_reason: str | None
    allowed_scope: Scope
    truth_version: str

@dataclass(frozen=True)
class ReplayCase(Contract):
    case_id: str
    input: AgentInput
    documents: tuple[Document, ...]
    tool_tape: tuple[str, ...]
    permissions: tuple[str, ...]
    agent_version: str
    frozen_clock: str
    success_ref: str
    family_id: str
    missing: tuple[str, ...]

@dataclass(frozen=True)
class LessonProposal(Contract):
    proposal_id: str
    source_refs: tuple[str, ...]
    purpose: str
    family_id: str
    cause: str
    carrier: str
    scope: Scope
    content: Mapping
    evidence_refs: tuple[str, ...]
    unknown_reasons: tuple[str, ...]

@dataclass(frozen=True)
class ArtifactRevision(Contract):
    artifact_id: str
    kind: str
    parent_hash: str | None
    content: Mapping
    scope: Scope
    owner: str
    valid_from: str
    valid_until: str
    permission: bool
    source_refs: tuple[str, ...]
    content_hash: str

@dataclass(frozen=True)
class ArtifactSnapshot(Contract):
    revision_id: str
    parent_revision_id: str | None
    artifacts: tuple[ArtifactRevision, ...]
    snapshot_hash: str

@dataclass(frozen=True)
class RunResult(Contract):
    document_id: str | None
    steps: tuple[str, ...]
    answer_style: str
    refusal_reason: str | None
    applied_artifacts: tuple[str, ...]
    violations: tuple[str, ...]
    environment_error: str | None
    unknown_reasons: tuple[str, ...]
    step_count: int
    tool_call_count: int

@dataclass(frozen=True)
class UsePolicy(Contract):
    revoked_artifact_hashes: frozenset[str]
    revoked_source_ids: frozenset[str]
    allowed_steps: tuple[str, ...]

@dataclass(frozen=True)
class EvaluationContext(Contract):
    suite_hash: str
    truth_hash: str
    environment_hash: str
    safety_hash: str
    use_policy: UsePolicy
    admissions: tuple["AdmissionRecord", ...]
    frozen_clock: str
    valid_until: str

@dataclass(frozen=True)
class FixtureSet(Contract):
    feedback: tuple[FeedbackRecord, ...]
    sources: tuple[SourceAuthority, ...]
    documents: tuple[Document, ...]
    tasks: tuple[TaskSpec, ...]
    truth: tuple[SuccessCondition, ...]
    replays: tuple[ReplayCase, ...]

@dataclass(frozen=True)
class AdmissionRecord(Contract):
    feedback_id: str
    source_id: str
    purpose: str
    family_id: str
    scope: Scope
    run_ref: str
    disposition: str
    reason_codes: tuple[str, ...]
    sanitized_payload: Mapping
    source_sensitive: bool
    source_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]

@dataclass(frozen=True)
class ReplayResult(Contract):
    status: str
    outcome: RunResult
    missing: tuple[str, ...]
    evidence_refs: tuple[str, ...]

@dataclass(frozen=True)
class AttributionResult(Contract):
    cause: str
    interventions: tuple[Mapping, ...]
    unknown_reasons: tuple[str, ...]

@dataclass(frozen=True)
class GraderResult(Contract):
    task_id: str
    status: str
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]

@dataclass(frozen=True)
class GateDecision(Contract):
    status: str
    reason_codes: tuple[str, ...]

@dataclass(frozen=True)
class EvidenceBundle(Contract):
    baseline_hash: str
    candidate_hash: str
    context: EvaluationContext
    provenance_closure: tuple[AdmissionRecord, ...]
    paired_trials: tuple[Mapping, ...]
    slices: Mapping
    coverage: Mapping
    unknown_count: int
    environment_error_count: int
    violation_count: int
    unrelated_unknown_count: int
    evidence_hash: str

@dataclass(frozen=True)
class ApprovalReceipt(Contract):
    approval_id: str
    approver_id: str
    candidate_hash: str
    evidence_hash: str
    context_hash: str
    allowed_scopes: tuple[Scope, ...]
    issued_at: str
    valid_until: str
    decision: str

@dataclass(frozen=True)
class ReleaseRecord(Contract):
    record_id: str
    event: str
    from_revision: ArtifactSnapshot
    to_revision: ArtifactSnapshot
    approval_ref: str | None
    evidence_ref: str | None
    cohort: Mapping
    reason: str
    frozen_clock: str

@dataclass(frozen=True)
class ReleaseState(Contract):
    active: ArtifactSnapshot
    history: tuple[ReleaseRecord, ...]
    used_approvals: frozenset[str]

@dataclass(frozen=True)
class ImprovementReport(Contract):
    schema_version: str
    groups: tuple[Mapping, ...]
    summary: Mapping
    source_proof: Mapping
    limits: tuple[str, ...]
    report_hash: str
