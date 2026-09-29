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
        decoded = {}
        for name, item in value.items():
            hint = hints[name]
            origin, args = get_origin(hint), get_args(hint)
            if isinstance(hint, type) and issubclass(hint, Contract):
                item = hint.from_dict(item)
            elif origin is tuple and isinstance(args[0], type) and issubclass(args[0], Contract):
                item = tuple(args[0].from_dict(v) for v in item)
            decoded[name] = item
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
    admissions: tuple[object, ...]
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
