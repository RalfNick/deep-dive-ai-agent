"""Immutable evidence contracts shared by chart, screen and voice experiments."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Literal


@dataclass(frozen=True)
class MediaRef:
    kind: str
    source_id: str
    sha256: str
    locator: str
    captured_at_ms: int
    scope: str

    def __post_init__(self) -> None:
        if self.captured_at_ms < 0 or not self.source_id or not self.sha256:
            raise ValueError("invalid media reference")


@dataclass(frozen=True)
class Observation:
    media_ref: MediaRef
    method: str
    region: str
    values: tuple[tuple[str, Decimal], ...]
    unit: str | None
    issues: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(not isinstance(v, Decimal) for _, v in self.values):
            raise ValueError("observation values must be Decimal")


@dataclass(frozen=True)
class Decision:
    status: Literal["answer", "unknown", "blocked", "refresh"]
    value: Decimal | None
    unit: str | None
    reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"answer", "unknown", "blocked", "refresh"}:
            raise ValueError("invalid decision status")
        if self.status == "answer" and (self.value is None or self.unit is None):
            raise ValueError("answer needs value and unit")
        if self.status != "answer" and self.value is not None:
            raise ValueError("non-answer cannot contain value")


@dataclass(frozen=True)
class EventRecord:
    seq: int
    event_ms: int
    session_id: str
    turn_id: str
    task_id: str
    kind: str
    payload: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if self.seq < 1 or self.event_ms < 0:
            raise ValueError("event sequence and time must be non-negative")


def make_media_ref(kind: str, source_id: str, content: bytes, locator: str,
                   captured_at_ms: int, scope: str) -> MediaRef:
    return MediaRef(kind, source_id, sha256(content).hexdigest(), locator, captured_at_ms, scope)
