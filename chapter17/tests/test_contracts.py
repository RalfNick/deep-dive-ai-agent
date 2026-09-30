from dataclasses import FrozenInstanceError
from hashlib import sha256
from decimal import Decimal

import pytest

from chapter17.contracts import Decision, Observation, EventRecord, make_media_ref


def test_media_ref_digest_and_immutability():
    ref = make_media_ref("svg", "chart-base", b"test", "chart-base.svg", 0, "book")
    assert ref.sha256 == sha256(b"test").hexdigest()
    with pytest.raises(FrozenInstanceError):
        ref.sha256 = "changed"
    with pytest.raises(ValueError):
        make_media_ref("svg", "bad", b"test", "x", -1, "book")


@pytest.mark.parametrize("status", ["answer", "unknown", "blocked", "refresh"])
def test_decision_status_is_explicit(status):
    decision = Decision(status, Decimal("25") if status == "answer" else None,
                        "percent" if status == "answer" else None, (), ())
    assert decision.status == status
    with pytest.raises(FrozenInstanceError):
        decision.status = "changed"


def test_invalid_decision_status_and_value_rejected():
    with pytest.raises(ValueError):
        Decision("done", None, None, (), ())
    with pytest.raises(ValueError):
        Decision("unknown", Decimal("25"), "percent", (), ())


def test_observation_and_event_are_immutable():
    ref = make_media_ref("svg", "x", b"x", "x.svg", 1, "book")
    observation = Observation(ref, "geometry", "bars", (("Jan", Decimal("80")),), "thousand", ())
    assert observation.values[0][1] == Decimal("80")
    with pytest.raises(FrozenInstanceError):
        observation.unit = "other"
    event = EventRecord(1, 0, "s", "t", "task", "speech_started", ())
    assert event.seq == 1
    with pytest.raises(ValueError):
        EventRecord(0, -1, "s", "t", "task", "speech_started", ())
