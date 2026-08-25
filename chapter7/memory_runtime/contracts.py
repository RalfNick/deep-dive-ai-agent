from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any


UTC_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def parse_utc_seconds(value: str, reason: str) -> datetime:
    if not isinstance(value, str) or not UTC_SECONDS.fullmatch(value):
        raise ValueError(reason)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(reason) from exc


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_plain(item) for item in value), key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_plain(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class MemoryType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"


class MemoryLifetime(str, Enum):
    CROSS_TASK = "cross_task"
    CURRENT_TASK = "current_task"
    ONE_TIME = "one_time"


class Authority(str, Enum):
    USER_EXPLICIT = "user_explicit"
    USER_INFERRED = "user_inferred"
    HUMAN_REVIEWED = "human_reviewed"
    REPOSITORY_VERIFIED = "repository_verified"
    TOOL_OBSERVED = "tool_observed"
    MODEL_INFERENCE = "model_inference"


class Sensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SECRET = "secret"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DELETED = "deleted"
    EXPIRED = "expired"


class WriteDecisionKind(str, Enum):
    ALLOW = "allow"
    REJECT = "reject"
    REVIEW = "review"


@dataclass(frozen=True)
class MemoryNamespace:
    tenant_id: str
    user_id: str
    project_id: str | None
    agent_id: str

    def __post_init__(self) -> None:
        for name in ("tenant_id", "user_id", "agent_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"blank_{name}")
        if self.project_id is not None and not self.project_id.strip():
            raise ValueError("blank_project_id")
        for value in (self.tenant_id, self.user_id, self.project_id, self.agent_id):
            if value is not None and "/" in value:
                raise ValueError("namespace_component_contains_slash")

    @property
    def key(self) -> str:
        return canonical_json(
            {
                "tenant_id": self.tenant_id,
                "user_id": self.user_id,
                "project_id": self.project_id,
                "agent_id": self.agent_id,
            }
        )


@dataclass(frozen=True)
class MemoryCandidate:
    candidate_id: str
    namespace: MemoryNamespace
    memory_type: MemoryType
    subject: str
    content: str
    source_id: str
    authority: Authority
    confidence: float
    sensitivity: Sensitivity
    lifetime: MemoryLifetime
    proposed_at: str

    def __post_init__(self) -> None:
        for name in ("candidate_id", "subject", "content", "source_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                label = "candidate_content" if name == "content" else name
                raise ValueError(f"blank_{label}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("invalid_candidate_confidence")
        parse_utc_seconds(self.proposed_at, "invalid_proposed_at")


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    memory_id: str
    namespace: MemoryNamespace
    memory_type: MemoryType
    subject: str
    content: str
    source_id: str
    authority: Authority
    confidence: float
    sensitivity: Sensitivity
    valid_from: str
    expires_at: str | None
    created_at: str
    version: int
    supersedes: str | None
    status: MemoryStatus = MemoryStatus.ACTIVE

    def __post_init__(self) -> None:
        for name in ("record_id", "memory_id", "subject", "content", "source_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"blank_{name}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("invalid_record_confidence")
        if self.version <= 0:
            raise ValueError("non_positive_memory_version")
        if self.version == 1 and self.supersedes is not None:
            raise ValueError("first_version_has_supersedes")
        if self.version > 1 and (self.supersedes is None or not self.supersedes.strip()):
            raise ValueError("later_version_requires_supersedes")
        valid_from = parse_utc_seconds(self.valid_from, "invalid_valid_from")
        parse_utc_seconds(self.created_at, "invalid_created_at")
        if self.expires_at is not None:
            expires_at = parse_utc_seconds(self.expires_at, "invalid_expires_at")
            if expires_at <= valid_from:
                raise ValueError("expiry_not_after_valid_from")
        if self.status is not MemoryStatus.ACTIVE:
            raise ValueError("record_input_must_be_active")


@dataclass(frozen=True)
class Tombstone:
    tombstone_id: str
    memory_id: str
    namespace: MemoryNamespace
    deleted_at: str
    reason: str
    source_id: str
    version: int

    def __post_init__(self) -> None:
        for name in ("tombstone_id", "memory_id", "reason", "source_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"blank_{name}")
        if self.version <= 0:
            raise ValueError("non_positive_tombstone_version")
        parse_utc_seconds(self.deleted_at, "invalid_deleted_at")


@dataclass(frozen=True)
class DeletionReceipt:
    memory_id: str
    namespace: MemoryNamespace
    deleted_at: str
    deleted_record_ids: tuple[str, ...]
    tombstone_id: str
    reason: str
    content_digest: str

    def __post_init__(self) -> None:
        if not self.deleted_record_ids:
            raise ValueError("empty_deleted_record_ids")
        if not re.fullmatch(r"[0-9a-f]{64}", self.content_digest):
            raise ValueError("invalid_deletion_content_digest")
        parse_utc_seconds(self.deleted_at, "invalid_deleted_at")


@dataclass(frozen=True)
class WriteDecision:
    candidate_id: str
    kind: WriteDecisionKind
    reason: str


@dataclass(frozen=True)
class RecallQuery:
    namespace: MemoryNamespace
    query: str
    memory_types: tuple[MemoryType, ...]
    top_k: int
    now: str
    allowed_sensitivities: tuple[Sensitivity, ...] = (Sensitivity.PUBLIC, Sensitivity.INTERNAL)

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("blank_recall_query")
        if self.top_k <= 0:
            raise ValueError("non_positive_top_k")
        parse_utc_seconds(self.now, "invalid_recall_time")
        if len(set(self.memory_types)) != len(self.memory_types):
            raise ValueError("duplicate_memory_type_filter")
        if len(set(self.allowed_sensitivities)) != len(self.allowed_sensitivities):
            raise ValueError("duplicate_sensitivity_filter")


@dataclass(frozen=True)
class ScoreBreakdown:
    task_match: float
    authority: float
    recency: float
    confidence: float
    total: float


@dataclass(frozen=True)
class RecallHit:
    record: MemoryRecord
    score: ScoreBreakdown
