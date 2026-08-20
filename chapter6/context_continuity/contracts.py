from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from chapter5.context.contracts import (
    ContextKind,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)


class EventType(str, Enum):
    TASK = "task"
    OBSERVATION = "observation"
    DECISION = "decision"
    TOOL_RESULT = "tool_result"
    VERIFICATION = "verification"
    USER_UPDATE = "user_update"


def _require_non_blank(value: str, error_code: str) -> None:
    if not value.strip():
        raise ValueError(error_code)


def _require_non_blank_ids(values: tuple[str, ...], error_code: str) -> None:
    if not values or any(not value.strip() for value in values):
        raise ValueError(error_code)


def _validate_distinct_keys(items: tuple[CarryItem, ...]) -> None:
    keys = tuple(item.key for item in items)
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate_carry_item_key")


@dataclass(frozen=True)
class EvidenceLocator:
    locator_id: str
    kind: str
    ref: str
    content_digest: str
    workspace_digest: str

    def __post_init__(self) -> None:
        _require_non_blank(self.locator_id, "blank_evidence_locator_id")
        _require_non_blank(self.kind, "blank_evidence_locator_kind")
        _require_non_blank(self.ref, "blank_evidence_locator_ref")
        _require_non_blank(self.content_digest, "blank_evidence_content_digest")
        _require_non_blank(self.workspace_digest, "blank_evidence_workspace_digest")


@dataclass(frozen=True)
class CarryItem:
    key: str
    kind: ContextKind
    content: str
    authority: InstructionAuthority
    trust: TrustLevel
    retention_priority: RetentionPriority
    sensitivity: Sensitivity
    source_event_ids: tuple[str, ...]
    required_for: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _require_non_blank(self.key, "blank_carry_item_key")
        _require_non_blank(self.content, "blank_carry_item_content")
        _require_non_blank_ids(self.source_event_ids, "carry_item_without_source")
        if self.kind is ContextKind.INSTRUCTION:
            if self.authority is InstructionAuthority.NONE:
                raise ValueError("instruction_authority_required")
        elif self.authority is not InstructionAuthority.NONE:
            raise ValueError("non_instruction_authority")


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    run_id: str
    sequence: int
    event_type: EventType
    carry_items: tuple[CarryItem, ...] = ()
    payload_ref: str | None = None
    workspace_digest: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank(self.event_id, "blank_event_id")
        _require_non_blank(self.run_id, "blank_run_id")
        if self.sequence <= 0:
            raise ValueError("non_positive_event_sequence")
        _validate_distinct_keys(self.carry_items)


@dataclass(frozen=True)
class RunCheckpoint:
    run_id: str
    checkpoint_id: str
    next_step: str
    completed_steps: tuple[str, ...]
    pending_step: str | None
    event_cursor: int
    workspace_digest: str
    artifact_id: str

    def __post_init__(self) -> None:
        _require_non_blank(self.run_id, "blank_run_id")
        _require_non_blank(self.checkpoint_id, "blank_checkpoint_id")
        _require_non_blank(self.artifact_id, "blank_artifact_id")
        if self.event_cursor < 0:
            raise ValueError("negative_event_cursor")


@dataclass(frozen=True)
class WorkingSet:
    event_ids: tuple[str, ...]
    carry_items: tuple[CarryItem, ...]
    max_serialized_bytes: int

    def __post_init__(self) -> None:
        if self.max_serialized_bytes < 0:
            raise ValueError("negative_max_serialized_bytes")
        if any(not event_id.strip() for event_id in self.event_ids):
            raise ValueError("blank_event_id")
        _validate_distinct_keys(self.carry_items)


@dataclass(frozen=True)
class CompactionSeed:
    run_id: str
    goal_key: str
    acceptance_keys: frozenset[str]
    constraint_keys: frozenset[str]
    decision_keys: frozenset[str]
    rejected_hypothesis_keys: frozenset[str]
    open_issue_keys: frozenset[str]
    verification_keys: frozenset[str]
    required_keys: frozenset[str]

    def __post_init__(self) -> None:
        _require_non_blank(self.run_id, "blank_run_id")
        _require_non_blank(self.goal_key, "blank_goal_key")
        key_groups = (
            self.acceptance_keys,
            self.constraint_keys,
            self.decision_keys,
            self.rejected_hypothesis_keys,
            self.open_issue_keys,
            self.verification_keys,
            self.required_keys,
        )
        if any(not key.strip() for keys in key_groups for key in keys):
            raise ValueError("blank_compaction_seed_key")


@dataclass(frozen=True)
class CompactionArtifact:
    artifact_id: str
    run_id: str
    source_event_range: tuple[int, int]
    goal: CarryItem
    acceptance_criteria: tuple[CarryItem, ...]
    constraints: tuple[CarryItem, ...]
    decisions: tuple[CarryItem, ...]
    rejected_hypotheses: tuple[CarryItem, ...]
    open_issues: tuple[CarryItem, ...]
    verification_state: tuple[CarryItem, ...]
    evidence_locators: tuple[EvidenceLocator, ...]
    next_intent: CarryItem
    created_at: str
    source_digest: str
    workspace_digest: str
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        _require_non_blank(self.artifact_id, "blank_artifact_id")
        _require_non_blank(self.run_id, "blank_run_id")
        if self.schema_version != "1.0":
            raise ValueError("invalid_schema_version")
        if self.source_event_range[0] > self.source_event_range[1]:
            raise ValueError("unordered_source_event_range")
        _validate_distinct_keys(
            (
                self.goal,
                *self.acceptance_criteria,
                *self.constraints,
                *self.decisions,
                *self.rejected_hypotheses,
                *self.open_issues,
                *self.verification_state,
                self.next_intent,
            )
        )
        if any(not issue.source_event_ids for issue in self.open_issues):
            raise ValueError("open_issue_without_source")

    @classmethod
    def minimal_for_test(
        cls,
        *,
        artifact_id: str = "cmp-test",
        open_issue_source_event_ids: tuple[str, ...] = ("evt-018",),
    ) -> CompactionArtifact:
        if not open_issue_source_event_ids:
            raise ValueError("open_issue_without_source")
        goal = CarryItem(
            key="repair-price",
            kind=ContextKind.TASK,
            content="repair price calculation",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-001",),
            required_for=frozenset({"goal"}),
        )
        acceptance = CarryItem(
            key="legacy-config",
            kind=ContextKind.FACT,
            content="legacy configuration test must pass",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-004",),
            required_for=frozenset({"legacy-config"}),
        )
        open_issue = CarryItem(
            key="legacy-config-open",
            kind=ContextKind.OBSERVATION,
            content="legacy configuration test still fails",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=open_issue_source_event_ids,
            required_for=frozenset({"legacy-config"}),
        )
        next_intent = CarryItem(
            key="run-legacy-test",
            kind=ContextKind.TASK,
            content="apply compatible patch and rerun legacy test",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.HIGH,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-020",),
        )
        return cls(
            artifact_id=artifact_id,
            run_id="run-price",
            source_event_range=(1, 20),
            goal=goal,
            acceptance_criteria=(acceptance,),
            constraints=(),
            decisions=(),
            rejected_hypotheses=(),
            open_issues=(open_issue,),
            verification_state=(),
            evidence_locators=(
                EvidenceLocator(
                    locator_id="loc-test",
                    kind="file",
                    ref="tests/test_pricing.py",
                    content_digest="content-test",
                    workspace_digest="workspace-v1",
                ),
            ),
            next_intent=next_intent,
            created_at="2026-08-17T00:00:00Z",
            source_digest="source-test",
            workspace_digest="workspace-v1",
        )


@dataclass(frozen=True)
class StrategyOutput:
    strategy: str
    visible_keys: frozenset[str]
    context_items: tuple[CarryItem, ...]
    artifact: CompactionArtifact | None
    serialized_bytes_before: int
    serialized_bytes_after: int
    overflowed: bool
    dropped_event_ids: tuple[str, ...]
