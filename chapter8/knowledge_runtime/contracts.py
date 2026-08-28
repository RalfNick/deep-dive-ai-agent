from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Mapping


_VERSION = re.compile(r"^\d+(?:\.\d+)*$")


class DocumentStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"
    WITHDRAWN = "withdrawn"


class Visibility(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"


class TrustLevel(str, Enum):
    AUTHORITATIVE = "authoritative"
    CURATED = "curated"
    COMMUNITY = "community"


class AnswerStatus(str, Enum):
    ANSWER = "answer"
    PARTIAL = "partial"
    ABSTAIN = "abstain"


def _json_ready(payload: object) -> object:
    if isinstance(payload, Enum):
        return payload.value
    if is_dataclass(payload) and not isinstance(payload, type):
        return _json_ready(asdict(payload))
    if isinstance(payload, Mapping):
        return {str(key): _json_ready(value) for key, value in payload.items()}
    if isinstance(payload, tuple):
        return [_json_ready(value) for value in payload]
    if isinstance(payload, list):
        return [_json_ready(value) for value in payload]
    return payload


def canonical_json(payload: object) -> str:
    return json.dumps(_json_ready(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def parse_utc_seconds(value: str, reason: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z") or "." in value:
        raise ValueError(reason)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError(reason) from error
    return parsed


def _version_tuple(value: str, reason: str) -> tuple[int, ...]:
    if not isinstance(value, str) or not _VERSION.fullmatch(value):
        raise ValueError(reason)
    return tuple(int(part) for part in value.split("."))


def _require_text(value: str, reason: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(reason)


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    source_path: str
    version_min: str
    version_max: str | None
    valid_from: str
    valid_until: str | None
    allowed_roles: tuple[str, ...]
    source_type: str
    status: DocumentStatus
    visibility: Visibility
    trust: TrustLevel
    fact_ids: tuple[str, ...]
    content: str
    content_digest: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.document_id, "blank_document_id")
        _require_text(self.title, "blank_document_title")
        _require_text(self.source_path, "blank_source_path")
        _require_text(self.source_type, "blank_source_type")
        _require_text(self.content, "blank_document_content")
        minimum = _version_tuple(self.version_min, "invalid_version_min")
        maximum = None if self.version_max is None else _version_tuple(self.version_max, "invalid_version_max")
        if maximum is not None and maximum < minimum:
            raise ValueError("version_window_reversed")
        start = parse_utc_seconds(self.valid_from, "invalid_valid_from")
        if self.valid_until is not None:
            end = parse_utc_seconds(self.valid_until, "invalid_valid_until")
            if end <= start:
                raise ValueError("valid_until_not_after_valid_from")
        if not self.allowed_roles or any(not role.strip() for role in self.allowed_roles):
            raise ValueError("empty_allowed_roles")
        if len(set(self.allowed_roles)) != len(self.allowed_roles):
            raise ValueError("duplicate_allowed_role")
        if any(not fact_id.strip() for fact_id in self.fact_ids):
            raise ValueError("blank_fact_id")
        actual_digest = stable_digest(self.content)
        if self.content_digest is not None and self.content_digest != actual_digest:
            raise ValueError("content_digest_mismatch")
        object.__setattr__(self, "content_digest", actual_digest)

    def valid_at(self, now: str) -> bool:
        instant = parse_utc_seconds(now, "invalid_query_time")
        start = parse_utc_seconds(self.valid_from, "invalid_valid_from")
        if instant < start:
            return False
        if self.valid_until is None:
            return True
        return instant < parse_utc_seconds(self.valid_until, "invalid_valid_until")

    def supports_version(self, target_version: str) -> bool:
        target = _version_tuple(target_version, "invalid_target_version")
        minimum = _version_tuple(self.version_min, "invalid_version_min")
        maximum = None if self.version_max is None else _version_tuple(self.version_max, "invalid_version_max")
        return target >= minimum and (maximum is None or target <= maximum)

    def visible_to(self, role: str) -> bool:
        return bool(role.strip()) and role in self.allowed_roles


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    ordinal: int
    heading_path: tuple[str, ...]
    content: str
    context_prefix: str
    content_digest: str
    document_digest: str
    source_path: str
    version_min: str
    version_max: str | None
    allowed_roles: tuple[str, ...]
    source_type: str
    trust: TrustLevel
    fact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.chunk_id, "blank_chunk_id")
        _require_text(self.document_id, "blank_chunk_document_id")
        _require_text(self.content, "blank_chunk_content")
        if self.ordinal < 0:
            raise ValueError("negative_chunk_ordinal")
        if self.content_digest != stable_digest(self.content):
            raise ValueError("chunk_content_digest_mismatch")
        if not re.fullmatch(r"[0-9a-f]{64}", self.document_digest):
            raise ValueError("invalid_document_digest")

    @classmethod
    def from_document(
        cls,
        document: KnowledgeDocument,
        ordinal: int,
        heading_path: tuple[str, ...],
        content: str,
        context_prefix: str = "",
    ) -> "Chunk":
        content_digest = stable_digest(content)
        chunk_id = "chk-" + stable_digest(
            {
                "document_id": document.document_id,
                "ordinal": ordinal,
                "heading_path": heading_path,
                "content_digest": content_digest,
            }
        )[:16]
        return cls(
            chunk_id=chunk_id,
            document_id=document.document_id,
            ordinal=ordinal,
            heading_path=heading_path,
            content=content,
            context_prefix=context_prefix,
            content_digest=content_digest,
            document_digest=document.content_digest or "",
            source_path=document.source_path,
            version_min=document.version_min,
            version_max=document.version_max,
            allowed_roles=document.allowed_roles,
            source_type=document.source_type,
            trust=document.trust,
            fact_ids=document.fact_ids,
        )


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    role: str
    target_version: str
    now: str
    top_k: int = 3
    candidate_k: int = 8

    def __post_init__(self) -> None:
        _require_text(self.text, "blank_query_text")
        _require_text(self.role, "blank_query_role")
        _version_tuple(self.target_version, "invalid_target_version")
        parse_utc_seconds(self.now, "invalid_query_time")
        if self.top_k <= 0:
            raise ValueError("non_positive_top_k")
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k_below_top_k")


@dataclass(frozen=True)
class QuestionCase:
    case_id: str
    query: RetrievalQuery
    relevant_document_ids: tuple[str, ...]
    relevant_chunk_ids: tuple[str, ...]
    required_fact_ids: tuple[str, ...]
    expected_claims: tuple[str, ...]
    expected_status: AnswerStatus

    def __post_init__(self) -> None:
        _require_text(self.case_id, "blank_case_id")
        if self.expected_status is AnswerStatus.ANSWER and not self.expected_claims:
            raise ValueError("answer_case_requires_claims")
        if self.expected_status is AnswerStatus.ABSTAIN and self.expected_claims:
            raise ValueError("abstain_case_has_claims")


@dataclass(frozen=True)
class ScoreBreakdown:
    lexical: float | None = None
    semantic: float | None = None
    fusion: float | None = None
    rerank: float | None = None


@dataclass(frozen=True)
class RankedChunk:
    chunk: Chunk
    score: float
    rank: int


@dataclass(frozen=True)
class RetrievalHit:
    chunk: Chunk
    score: float
    breakdown: ScoreBreakdown


@dataclass(frozen=True)
class Citation:
    citation_id: str
    document_id: str
    chunk_id: str
    source_path: str
    version: str
    content_digest: str
    fact_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidencePacket:
    query: RetrievalQuery
    citations: tuple[Citation, ...]
    evidence: tuple[RetrievalHit, ...]
    present_fact_ids: tuple[str, ...]
    missing_fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class AnswerDecision:
    status: AnswerStatus
    claims: tuple[str, ...]
    citation_ids: tuple[str, ...]
    missing_fact_ids: tuple[str, ...]
    reason: str
