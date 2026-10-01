from dataclasses import replace

from chapter17.contracts import EventRecord
from chapter17.voice import reduce_events


def event(seq, kind, payload=()):
    return EventRecord(seq, seq * 10, "s", "t", "task", kind, payload)


def test_interrupt_stops_playback_not_running_task():
    state = reduce_events((event(1, "task_started"), event(2, "speech_started"),
                           event(3, "response_cancelled"), event(4, "playback_stopped")))
    assert state.playback == "stopped"
    assert state.backend_task == "running"
    assert state.conversation_tail == "present"


def test_truncate_removes_unplayed_tail():
    state = reduce_events((event(1, "task_started"), event(2, "conversation_truncated")))
    assert state.conversation_tail == "removed"
    assert state.backend_task == "running"


def test_explicit_task_cancel_is_separate():
    state = reduce_events((event(1, "task_started"), event(2, "task_cancelled")))
    assert state.backend_task == "cancelled"
    assert state.playback == "idle"


def test_committed_action_survives_late_cancel():
    state = reduce_events((event(1, "task_started"),
                           event(2, "action_committed", (("action_id", "a1"),)),
                           event(3, "task_completed"), event(4, "task_cancelled")))
    assert state.backend_task == "completed"
    assert state.committed_actions == ("a1",)
    assert "late-cancel-after-completion" in state.issues


def test_identical_duplicate_is_idempotent():
    action = event(2, "action_committed", (("action_id", "a1"),))
    state = reduce_events((event(1, "task_started"), action, action))
    assert state.committed_actions == ("a1",)
    assert state.issues == ()


def test_conflicting_duplicate_gap_and_reorder_are_unknown():
    start = event(1, "task_started")
    conflict = reduce_events((start, replace(start, kind="task_completed")))
    gap = reduce_events((start, event(3, "task_completed")))
    reverse = reduce_events((event(2, "task_completed"), start))
    for state in (conflict, gap, reverse):
        assert state.backend_task == "unknown"
        assert state.issues


def test_response_cancel_confirmation_does_not_claim_playback_stopped():
    state = reduce_events((event(1, "task_started"), event(2, "speech_started"),
                           event(3, "response_cancelled")))
    assert state.generation == "cancelled"
    assert state.playback == "interrupted"
    assert state.backend_task == "running"


def test_cancel_request_requires_a_separate_confirmation():
    requested = (event(1, "task_started"), event(2, "response_cancel_requested"))
    state = reduce_events(requested)
    assert state.generation == "cancel_requested"
    assert state.playback == "idle"
    assert state.backend_task == "running"
    confirmed = reduce_events((*requested, event(3, "response_cancelled")))
    assert confirmed.generation == "cancelled"
    assert confirmed.playback == "idle"
