from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .contracts import (
    Authority,
    MemoryNamespace,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    Sensitivity,
    Tombstone,
    canonical_json,
)
from .store import MemoryStore


def write_event_log(path: Path, events: Iterable[MemoryRecord | Tombstone]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for event in events:
        event_type = "record" if isinstance(event, MemoryRecord) else "tombstone"
        lines.append(canonical_json({"event_type": event_type, "event": event}))
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
    return path


def _namespace(payload: dict[str, object]) -> MemoryNamespace:
    return MemoryNamespace(
        tenant_id=str(payload["tenant_id"]),
        user_id=str(payload["user_id"]),
        project_id=None if payload["project_id"] is None else str(payload["project_id"]),
        agent_id=str(payload["agent_id"]),
    )


def _record(payload: dict[str, object]) -> MemoryRecord:
    namespace = payload["namespace"]
    if not isinstance(namespace, dict):
        raise ValueError("invalid_memory_namespace")
    return MemoryRecord(
        record_id=str(payload["record_id"]),
        memory_id=str(payload["memory_id"]),
        namespace=_namespace(namespace),
        memory_type=MemoryType(str(payload["memory_type"])),
        subject=str(payload["subject"]),
        content=str(payload["content"]),
        source_id=str(payload["source_id"]),
        authority=Authority(str(payload["authority"])),
        confidence=float(payload["confidence"]),
        sensitivity=Sensitivity(str(payload["sensitivity"])),
        valid_from=str(payload["valid_from"]),
        expires_at=None if payload["expires_at"] is None else str(payload["expires_at"]),
        created_at=str(payload["created_at"]),
        version=int(payload["version"]),
        supersedes=None if payload["supersedes"] is None else str(payload["supersedes"]),
        status=MemoryStatus(str(payload["status"])),
    )


def _tombstone(payload: dict[str, object]) -> Tombstone:
    namespace = payload["namespace"]
    if not isinstance(namespace, dict):
        raise ValueError("invalid_memory_namespace")
    return Tombstone(
        tombstone_id=str(payload["tombstone_id"]),
        memory_id=str(payload["memory_id"]),
        namespace=_namespace(namespace),
        deleted_at=str(payload["deleted_at"]),
        reason=str(payload["reason"]),
        source_id=str(payload["source_id"]),
        version=int(payload["version"]),
    )


def load_event_log(path: Path) -> MemoryStore:
    store = MemoryStore()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            wrapper = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid_memory_event_json:{line_number}") from exc
        if not isinstance(wrapper, dict) or "event_type" not in wrapper:
            raise ValueError(f"invalid_memory_event_wrapper:{line_number}")
        if wrapper["event_type"] not in {"record", "tombstone"}:
            raise ValueError(f"unknown_memory_event_type:{line_number}")
        if "event" not in wrapper:
            raise ValueError(f"invalid_memory_event_wrapper:{line_number}")
        payload = wrapper["event"]
        if not isinstance(payload, dict):
            raise ValueError(f"invalid_memory_event_payload:{line_number}")
        if wrapper["event_type"] == "record":
            store.append(_record(payload))
        elif wrapper["event_type"] == "tombstone":
            store.forget(_tombstone(payload))
    return store
