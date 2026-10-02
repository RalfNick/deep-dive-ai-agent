from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import re
from typing import Literal

JsonObject = dict[str, object]
CaseResult = TeamReport = ExerciseReport = JsonObject
Scalar = str | int | bool | None
FinalStatus = Literal["answer", "verified", "unknown", "blocked", "conflict", "needs_approval", "stopped"]


@dataclass(frozen=True)
class BudgetLimits:
    tool_calls: int = 16
    verifier_reserve: int = 2
    inflight: int = 3
    depth: int = 2
    handoffs: int = 4
    worker_decisions: int = 4
    extra_retries: int = 1

    def __post_init__(self):
        if any(type(v) is not int or v < 0 for v in vars(self).values()):
            raise ValueError("nonnegative integer limits required")
        if self.verifier_reserve > self.tool_calls:
            raise ValueError("reserve is inside total budget")


@dataclass(frozen=True)
class TaskPacket:
    task_id: str
    parent_id: str | None
    worker_id: str
    goal: str
    principal: str
    target_version: str
    input_refs: tuple[str, ...]
    allowed_sources: frozenset[str]
    allowed_tools: frozenset[str]
    allowed_writes: frozenset[str]
    output_requirements: tuple[str, ...]
    base_hashes: tuple[tuple[str, str], ...]
    limits: BudgetLimits
    depth: int


@dataclass(frozen=True)
class SourceDoc:
    source_id: str
    location: str
    version: str
    principals: frozenset[str]
    eligible: bool
    text: str
    facts: tuple[tuple[str, str], ...]
    digest: str


@dataclass(frozen=True)
class EvidenceRef:
    source_id: str
    location: str
    digest: str
    version: str
    eligible: bool
    quote: str


@dataclass(frozen=True)
class Claim:
    key: str
    value: str
    evidence: tuple[EvidenceRef, ...]


@dataclass(frozen=True)
class ContextSnapshot:
    task_id: str
    principal: str
    target_version: str
    sent: tuple[tuple[str, str], ...]
    sent_digest: str
    source_digests: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool: str
    arguments: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ToolOutcome:
    call_id: str
    status: Literal["ok", "transient_error", "permanent_error", "timeout", "denied"]
    data: tuple[tuple[str, Scalar], ...] = ()


@dataclass(frozen=True)
class WorkerResult:
    task_id: str
    attempt_id: str
    worker_id: str
    state: Literal["done", "unknown", "failed", "cancelled"]
    claims: tuple[Claim, ...] = ()
    missing: tuple[str, ...] = ()
    patch_ids: tuple[str, ...] = ()
    decisions: int = 0
    tool_calls: int = 0


@dataclass(frozen=True)
class WorkerObservation:
    outcomes: tuple[ToolOutcome, ...] = ()
    results: tuple[WorkerResult, ...] = ()
    context: ContextSnapshot | None = None


@dataclass(frozen=True)
class Decision:
    kind: Literal["tool", "result", "delegate", "handoff"]
    call: ToolCall | None = None
    result: WorkerResult | None = None
    packet: TaskPacket | None = None
    next_controller: str | None = None

    def __post_init__(self):
        fields = (self.call, self.result, self.packet, self.next_controller)
        index = {"tool": 0, "result": 1, "delegate": 2, "handoff": 3}.get(self.kind)
        if index is None or any((v is not None) != (i == index) for i, v in enumerate(fields)):
            raise ValueError("exactly the kind-specific payload is required")


@dataclass(frozen=True)
class Event:
    event_id: str
    kind: str
    task_id: str
    attempt_id: str
    parent_event_id: str | None
    data: tuple[tuple[str, Scalar], ...] = ()


@dataclass(frozen=True)
class PatchProposal:
    proposal_id: str
    action_id: str
    task_id: str
    path: str
    before_digest: str
    replacement: str


@dataclass(frozen=True)
class Verification:
    passed: bool
    tests_passed: int
    tests_total: int
    behavior_passed: bool
    evidence: tuple[str, ...]
    reason_code: str


@dataclass(frozen=True)
class ActionReceipt:
    proposal_id: str
    action_id: str
    path: str
    allowed_writes: tuple[str, ...]
    before_digest: str | None
    after_digest: str | None
    executed: bool
    verification: Verification | None
    status: FinalStatus
    reason_code: str


@dataclass
class RunState:
    controller: str
    principal: str
    tasks: dict[str, TaskPacket] = field(default_factory=dict)
    attempts: dict[str, str] = field(default_factory=dict)
    results: tuple[WorkerResult, ...] = ()
    shared_version: str = "v2"
    tool_calls: int = 0
    handoffs: int = 0
    pending_approval: str | None = None
    status: FinalStatus | None = None
    reason_code: str | None = None
    receipts: tuple[ActionReceipt, ...] = ()
    acceptance: tuple[str, ...] = ()
    events: tuple[Event, ...] = ()


@dataclass(frozen=True)
class EvidenceVerdict:
    status: FinalStatus
    claims: tuple[Claim, ...]
    distinct_sources: tuple[str, ...]
    missing: tuple[str, ...]
    reason_code: str


def relative_path(value: str) -> PurePosixPath:
    if not value or "\\" in value or ":" in value or any(p in {"", ".", ".."} for p in value.split("/")):
        raise ValueError("canonical relative path required")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError("absolute path denied")
    return path


def validate_packet(packet: TaskPacket, parent: TaskPacket | None = None) -> None:
    if not all((packet.task_id, packet.worker_id, packet.goal, packet.principal, packet.target_version)):
        raise ValueError("task identity and goal required")
    if type(packet.depth) is not int or not 0 <= packet.depth <= packet.limits.depth:
        raise ValueError("delegation depth exceeded")
    for path in packet.allowed_writes:
        relative_path(path)
    for path, digest in packet.base_hashes:
        relative_path(path)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("SHA-256 required")
    if parent:
        if packet.parent_id != parent.task_id or packet.depth != parent.depth + 1:
            raise ValueError("parent/depth mismatch")
        if packet.principal != parent.principal or packet.target_version != parent.target_version:
            raise ValueError("identity/version cannot change")
        for name in ("allowed_sources", "allowed_tools", "allowed_writes"):
            if not getattr(packet, name) <= getattr(parent, name):
                raise ValueError("scope escalation denied")
        if any(getattr(packet.limits, k) > v for k, v in vars(parent.limits).items()):
            raise ValueError("child limits cannot increase")
        if packet.limits.tool_calls - packet.limits.verifier_reserve > parent.limits.tool_calls - parent.limits.verifier_reserve:
            raise ValueError("child cannot consume verifier reserve")
