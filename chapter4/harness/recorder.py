from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from .contracts import RunEvent


@dataclass(frozen=True)
class TraceGrade:
    complete: bool
    missing_contracts: tuple[str, ...]


class EventRecorder:
    def __init__(
        self,
        run_id: str,
        events: Sequence[RunEvent] | None = None,
    ) -> None:
        self.run_id = run_id
        self.events = list(events or ())
        self._sequence = max((event.sequence for event in self.events), default=0)

    def emit(
        self,
        kind: str,
        *,
        cause_id: str | None,
        **data: object,
    ) -> RunEvent:
        self._sequence += 1
        event = RunEvent(
            event_id=f"{self.run_id}:{self._sequence:04d}",
            run_id=self.run_id,
            kind=kind,
            sequence=self._sequence,
            cause_id=cause_id,
            data=dict(data),
        )
        self.events.append(event)
        return event


def grade_trace(events: Sequence[RunEvent]) -> TraceGrade:
    missing: list[str] = []
    ordered = sorted(events, key=lambda event: event.sequence)

    checkpoint_positions = [
        index for index, event in enumerate(ordered)
        if event.kind == "checkpoint_saved"
    ]
    approval_positions = [
        index for index, event in enumerate(ordered)
        if event.kind == "approval_requested"
    ]
    if approval_positions and (
        not checkpoint_positions
        or checkpoint_positions[0] > approval_positions[0]
    ):
        missing.append("checkpoint_before_approval")

    calls = {
        str(event.data.get("call_id")): event
        for event in ordered
        if event.kind == "tool_call"
    }
    for event in ordered:
        if event.kind != "tool_result":
            continue
        call_id = str(event.data.get("call_id"))
        call = calls.get(call_id)
        if call is None or event.cause_id != call.event_id:
            missing.append(f"causal_tool_result:{call_id}")

    return TraceGrade(complete=not missing, missing_contracts=tuple(missing))
