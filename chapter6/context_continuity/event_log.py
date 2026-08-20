"""Append-only, integrity-checked event persistence for Chapter 6."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from chapter5.context.contracts import (
    ContextKind,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)

from .contracts import CarryItem, EventRecord, EventType
from .trace import canonical_json, stable_digest


def _event_record_data(event: EventRecord) -> dict[str, Any]:
    """Return the canonical, JSON-safe representation persisted in the log."""
    return json.loads(canonical_json(event))


def _event_from_data(data: object) -> EventRecord:
    if not isinstance(data, dict):
        raise ValueError("invalid_event_record")
    try:
        carry_items = tuple(
            CarryItem(
                key=item["key"],
                kind=ContextKind(item["kind"]),
                content=item["content"],
                authority=InstructionAuthority(item["authority"]),
                trust=TrustLevel(item["trust"]),
                retention_priority=RetentionPriority(item["retention_priority"]),
                sensitivity=Sensitivity(item["sensitivity"]),
                source_event_ids=tuple(item["source_event_ids"]),
                required_for=frozenset(item.get("required_for", ())),
            )
            for item in data.get("carry_items", ())
        )
        return EventRecord(
            event_id=data["event_id"],
            run_id=data["run_id"],
            sequence=data["sequence"],
            event_type=EventType(data["event_type"]),
            carry_items=carry_items,
            payload_ref=data.get("payload_ref"),
            workspace_digest=data.get("workspace_digest"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_event_record") from error


class JsonlEventLog:
    """A JSONL log whose records are individually integrity protected."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, event: EventRecord) -> None:
        """Append an event after checking identity, order, and secret boundaries."""
        if any(item.sensitivity is Sensitivity.SECRET for item in event.carry_items):
            raise ValueError("secret_event_payload")

        records = self._read_all()
        if any(record.event_id == event.event_id for record in records):
            raise ValueError("duplicate_event_id")
        run_sequences = [record.sequence for record in records if record.run_id == event.run_id]
        if run_sequences and event.sequence <= max(run_sequences):
            raise ValueError("non_monotonic_event_sequence")

        record = _event_record_data(event)
        line = canonical_json({"record": record, "record_digest": stable_digest(record)}) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())

    def read_through(self, cursor: int) -> tuple[EventRecord, ...]:
        """Verify all stored records, returning entries at or before ``cursor``."""
        if cursor < 0:
            raise ValueError("negative_event_cursor")
        return tuple(record for record in self._read_all() if record.sequence <= cursor)

    def _read_all(self) -> tuple[EventRecord, ...]:
        if not self.path.exists():
            return ()

        records: list[EventRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line:
                raise ValueError("invalid_event_log_entry")
            try:
                entry = json.loads(line)
                record = entry["record"]
                digest = entry["record_digest"]
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError("invalid_event_log_entry") from error
            if not isinstance(digest, str) or stable_digest(record) != digest:
                raise ValueError("event_digest_mismatch")
            records.append(_event_from_data(record))
        return tuple(records)
