from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ContextKind(str, Enum):
    INSTRUCTION = "instruction"
    TASK = "task"
    FACT = "fact"
    OBSERVATION = "observation"
    ARTIFACT = "artifact"
    TOOL_SCHEMA = "tool_schema"


class InstructionAuthority(str, Enum):
    NONE = "none"
    SYSTEM = "system"
    DEVELOPER = "developer"
    REPOSITORY = "repository"
    USER = "user"
    UNTRUSTED = "untrusted"


class TrustLevel(str, Enum):
    UNKNOWN = "unknown"
    VERIFIED = "verified"
    TRUSTED_SOURCE = "trusted_source"
    UNVERIFIED = "unverified"
    HOSTILE = "hostile"


class RetentionPriority(str, Enum):
    REQUIRED = "required"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Sensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SECRET = "secret"


class DecisionKind(str, Enum):
    TOOL = "tool"
    ANSWER = "answer"
    NEEDS_CONTEXT = "needs_context"
    REFUSE = "refuse"


class ProbeStatus(str, Enum):
    OK = "ok"
    AUTH_MISSING = "auth_missing"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    INVALID_RESPONSE = "invalid_response"


class TaskOutcome(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    FALSE_COMPLETION = "false_completion"
    NEEDS_CONTEXT = "needs_context"
    REFUSED = "refused"
    SAFETY_BLOCKED = "safety_blocked"


@dataclass(frozen=True)
class Scope:
    repository: str
    path_prefix: str | None
    task_id: str | None

    def __post_init__(self) -> None:
        if not self.repository.strip():
            raise ValueError("blank_scope_repository")


@dataclass(frozen=True)
class Provenance:
    source_type: str
    source_id: str
    version: str | None
    observed_at: str | None
    content_digest: str


@dataclass(frozen=True)
class RawSource:
    source_id: str
    channel: str
    content: str
    path: str | None = None
    version: str | None = None
    observed_at: str | None = None


@dataclass(frozen=True)
class ContextItem:
    item_id: str
    kind: ContextKind
    content: str
    scope: Scope
    authority: InstructionAuthority
    trust: TrustLevel
    retention_priority: RetentionPriority
    sensitivity: Sensitivity
    provenance: Provenance
    required_for: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("blank_item_id")
        if not self.content.strip():
            raise ValueError("blank_item_content")
        if self.kind is ContextKind.INSTRUCTION:
            if self.authority is InstructionAuthority.NONE:
                raise ValueError("instruction_authority_required")
        elif self.authority is not InstructionAuthority.NONE:
            raise ValueError("non_instruction_authority")


DEFAULT_SECTION_ORDER: tuple[ContextKind, ...] = (
    ContextKind.INSTRUCTION,
    ContextKind.TASK,
    ContextKind.FACT,
    ContextKind.ARTIFACT,
    ContextKind.OBSERVATION,
    ContextKind.TOOL_SCHEMA,
)


@dataclass(frozen=True)
class BuildConfig:
    repository: str
    target_path: str
    task_id: str
    provider_boundary: str
    allowed_sensitivities: frozenset[Sensitivity]
    expected_requirements: frozenset[str]
    budget_units: int
    section_order: tuple[ContextKind, ...]

    def __post_init__(self) -> None:
        if self.budget_units < 0:
            raise ValueError("negative_budget")
        if len(set(self.section_order)) != len(self.section_order):
            raise ValueError("duplicate_section_kind")

    @classmethod
    def for_task(
        cls,
        repository: str,
        target_path: str,
        task_id: str,
        *,
        budget_units: int,
        section_order: tuple[ContextKind, ...] | None = None,
        provider_boundary: str = "external-model",
        allowed_sensitivities: frozenset[Sensitivity] = frozenset(
            {Sensitivity.PUBLIC, Sensitivity.INTERNAL}
        ),
        expected_requirements: frozenset[str] = frozenset(),
    ) -> "BuildConfig":
        return cls(
            repository=repository,
            target_path=target_path,
            task_id=task_id,
            provider_boundary=provider_boundary,
            allowed_sensitivities=allowed_sensitivities,
            expected_requirements=expected_requirements,
            budget_units=budget_units,
            section_order=section_order or DEFAULT_SECTION_ORDER,
        )


@dataclass(frozen=True)
class ContextSection:
    kind: ContextKind
    item_ids: tuple[str, ...]
    serialized_content: str
    budget_units: int


@dataclass(frozen=True)
class ContextPacket:
    task_id: str
    sections: tuple[ContextSection, ...]
    tools: tuple[str, ...]
    budget_limit: int
    budget_used: int
    selected_required_units: int
    all_required_candidate_units: int
    requirement_evidence_units: int
    selected_item_ids: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    semantic_packet_digest: str


@dataclass(frozen=True)
class TraceEntry:
    item_id: str
    content_digest: str
    stage: str
    outcome: str
    reason: str
    estimated_units: int


@dataclass(frozen=True)
class ContextBuildTrace:
    entries: tuple[TraceEntry, ...]
    stage_counts: tuple[tuple[str, int], ...]
    selected_item_ids: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    packet_digest: str


@dataclass(frozen=True)
class BuildResult:
    packet: ContextPacket
    trace: ContextBuildTrace
