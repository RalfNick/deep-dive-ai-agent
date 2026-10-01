"""Provider-neutral reducer for a fixed realtime voice event stream."""

from dataclasses import dataclass

from .contracts import EventRecord

_KINDS = frozenset({"speech_started", "response_cancel_requested", "response_cancelled", "playback_stopped",
                    "conversation_truncated", "task_started", "task_completed",
                    "task_cancelled", "action_committed"})


@dataclass(frozen=True)
class VoiceState:
    playback: str
    generation: str
    conversation_tail: str
    backend_task: str
    committed_actions: tuple[str, ...]
    issues: tuple[str, ...]


def reduce_events(events: tuple[EventRecord, ...]) -> VoiceState:
    playback = "idle"
    generation = "unknown"
    tail = "present"
    task = "not_started"
    committed: list[str] = []
    issues: list[str] = []
    seen: dict[int, EventRecord] = {}
    previous_seq = 0
    previous_ms = -1
    identity: tuple[str, str, str] | None = None
    ordering_broken = False

    for event in events:
        if event.seq in seen:
            if seen[event.seq] != event:
                issues.append("conflicting-duplicate-sequence")
                ordering_broken = True
            continue
        seen[event.seq] = event
        if event.seq != previous_seq + 1 or event.event_ms < previous_ms:
            issues.append("sequence-gap-or-reorder")
            ordering_broken = True
        previous_seq, previous_ms = event.seq, event.event_ms
        current_identity = (event.session_id, event.turn_id, event.task_id)
        if identity is None:
            identity = current_identity
        elif current_identity != identity:
            issues.append("event-identity-conflict")
            ordering_broken = True
        if event.kind not in _KINDS:
            issues.append("unsupported-event-kind")
            ordering_broken = True
            continue
        if ordering_broken:
            continue
        if event.kind == "speech_started":
            playback = "interrupted"
        elif event.kind == "response_cancel_requested":
            generation = "cancel_requested"
        elif event.kind == "response_cancelled":
            generation = "cancelled"
        elif event.kind == "playback_stopped":
            playback = "stopped"
        elif event.kind == "conversation_truncated":
            tail = "removed"
        elif event.kind == "task_started":
            if task not in {"not_started"}:
                issues.append("task-restarted")
                ordering_broken = True
            else:
                task = "running"
        elif event.kind == "task_completed":
            if task == "running":
                task = "completed"
            else:
                issues.append("completion-without-running-task")
                ordering_broken = True
        elif event.kind == "task_cancelled":
            if task == "completed":
                issues.append("late-cancel-after-completion")
            elif task == "running":
                task = "cancelled"
            else:
                issues.append("cancel-without-running-task")
                ordering_broken = True
        elif event.kind == "action_committed":
            action_ids = [value for key, value in event.payload if key == "action_id"]
            if task != "running" or len(action_ids) != 1 or not action_ids[0]:
                issues.append("invalid-commit-event")
                ordering_broken = True
            elif action_ids[0] not in committed:
                committed.append(action_ids[0])

    return VoiceState(playback, "unknown" if ordering_broken else generation,
                      tail, "unknown" if ordering_broken else task,
                      tuple(committed), tuple(issues))
