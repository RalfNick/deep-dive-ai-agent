from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    APPROVAL_STALE = "approval_stale"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED_VERIFICATION = "failed_verification"
    FAILED = "failed"
    STOPPED = "stopped"
    CANCELLED = "cancelled"


class DecisionKind(str, Enum):
    TOOL = "tool"
    FINAL = "final"


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    action_id: str
    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCall":
        return cls(
            call_id=str(data["call_id"]),
            action_id=str(data["action_id"]),
            name=str(data["name"]),
            arguments=dict(data.get("arguments", {})),
        )


@dataclass(frozen=True)
class PolicyDecision:
    kind: DecisionKind
    call: ToolCall | None = None
    message: str = ""

    @classmethod
    def tool(cls, call: ToolCall) -> "PolicyDecision":
        return cls(kind=DecisionKind.TOOL, call=call)

    @classmethod
    def final(cls, message: str) -> "PolicyDecision":
        return cls(kind=DecisionKind.FINAL, message=message)


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    action_id: str
    ok: bool
    output: str = ""
    error_type: str | None = None
    retryable: bool = False
    state_digest: str | None = None
    side_effect_applied: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolResult":
        return cls(
            call_id=str(data["call_id"]),
            action_id=str(data["action_id"]),
            ok=bool(data["ok"]),
            output=str(data.get("output", "")),
            error_type=data.get("error_type"),
            retryable=bool(data.get("retryable", False)),
            state_digest=data.get("state_digest"),
            side_effect_applied=bool(data.get("side_effect_applied", False)),
        )


@dataclass(frozen=True)
class RunEvent:
    event_id: str
    run_id: str
    kind: str
    sequence: int
    cause_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunEvent":
        return cls(
            event_id=str(data["event_id"]),
            run_id=str(data["run_id"]),
            kind=str(data["kind"]),
            sequence=int(data["sequence"]),
            cause_id=data.get("cause_id"),
            data=dict(data.get("data", {})),
        )


@dataclass(frozen=True)
class VerificationEvidence:
    accepted: bool
    summary: str
    state_digest: str
    test_exit_code: int


@dataclass
class RunState:
    run_id: str
    status: RunStatus = RunStatus.RUNNING
    step: int = 0
    decision_index: int = 0
    pending_call: ToolCall | None = None
    final_message: str = ""
    failure_code: str | None = None
    state_digest: str | None = None
    completed_action_ids: set[str] = field(default_factory=set)
    attempts: dict[str, int] = field(default_factory=dict)
    events: list[RunEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "step": self.step,
            "decision_index": self.decision_index,
            "pending_call": asdict(self.pending_call) if self.pending_call else None,
            "final_message": self.final_message,
            "failure_code": self.failure_code,
            "state_digest": self.state_digest,
            "completed_action_ids": sorted(self.completed_action_ids),
            "attempts": dict(self.attempts),
            "events": [asdict(event) for event in self.events],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunState":
        pending = data.get("pending_call")
        return cls(
            run_id=str(data["run_id"]),
            status=RunStatus(data.get("status", RunStatus.RUNNING.value)),
            step=int(data.get("step", 0)),
            decision_index=int(data.get("decision_index", 0)),
            pending_call=ToolCall.from_dict(pending) if pending else None,
            final_message=str(data.get("final_message", "")),
            failure_code=data.get("failure_code"),
            state_digest=data.get("state_digest"),
            completed_action_ids=set(data.get("completed_action_ids", [])),
            attempts={str(k): int(v) for k, v in data.get("attempts", {}).items()},
            events=[RunEvent.from_dict(event) for event in data.get("events", [])],
        )

    @classmethod
    def from_json(cls, raw: str) -> "RunState":
        return cls.from_dict(json.loads(raw))


@dataclass(frozen=True)
class RunOutcome:
    state: RunState
    events: tuple[RunEvent, ...]
    evidence: VerificationEvidence | None = None
