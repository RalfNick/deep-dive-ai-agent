from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from .contracts import (
    DeletionReceipt,
    MemoryNamespace,
    MemoryRecord,
    Tombstone,
    canonical_json,
    parse_utc_seconds,
    stable_digest,
)


class MemoryConflictError(ValueError):
    pass


class MemoryStore:
    """An append-only in-memory store with a rebuildable current projection."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, MemoryRecord] = {}
        self._chains: dict[tuple[str, str], list[str]] = {}
        self._tombstones: dict[tuple[str, str], Tombstone] = {}
        self._receipts: dict[str, DeletionReceipt] = {}
        self._event_order: list[MemoryRecord | Tombstone] = []

    @staticmethod
    def _key(namespace: MemoryNamespace, memory_id: str) -> tuple[str, str]:
        return namespace.key, memory_id

    def append(self, record: MemoryRecord) -> str:
        with self._lock:
            existing_by_id = self._records.get(record.record_id)
            if existing_by_id is not None:
                if existing_by_id == record:
                    return "idempotent"
                raise MemoryConflictError("record_id_conflict")

            key = self._key(record.namespace, record.memory_id)
            if key in self._tombstones:
                raise MemoryConflictError("memory_deleted")
            chain = self._chains.get(key, [])
            if not chain:
                if record.version != 1 or record.supersedes is not None:
                    raise MemoryConflictError("invalid_supersedes")
            else:
                current = self._records[chain[-1]]
                if record.version == 1:
                    raise MemoryConflictError("memory_id_conflict")
                if record.supersedes != current.record_id:
                    raise MemoryConflictError("invalid_supersedes")
                if record.version != current.version + 1:
                    raise MemoryConflictError("non_sequential_version")

            self._records[record.record_id] = record
            self._chains.setdefault(key, []).append(record.record_id)
            self._event_order.append(record)
            return "written"

    def versions(self, namespace: MemoryNamespace, memory_id: str) -> tuple[MemoryRecord, ...]:
        with self._lock:
            ids = tuple(self._chains.get(self._key(namespace, memory_id), ()))
            return tuple(self._records[record_id] for record_id in ids)

    def current(self, namespace: MemoryNamespace, memory_id: str, *, now: str) -> MemoryRecord | None:
        parse_utc_seconds(now, "invalid_store_time")
        with self._lock:
            key = self._key(namespace, memory_id)
            if key in self._tombstones:
                return None
            chain = self._chains.get(key)
            if not chain:
                return None
            record = self._records[chain[-1]]
            if record.expires_at is not None and parse_utc_seconds(record.expires_at, "invalid_expires_at") <= parse_utc_seconds(now, "invalid_store_time"):
                return None
            return record

    def all_current(self, *, now: str) -> tuple[MemoryRecord, ...]:
        parse_utc_seconds(now, "invalid_store_time")
        with self._lock:
            records: list[MemoryRecord] = []
            for (namespace_key, memory_id), chain in self._chains.items():
                if (namespace_key, memory_id) in self._tombstones:
                    continue
                record = self._records[chain[-1]]
                if record.expires_at is not None and parse_utc_seconds(record.expires_at, "invalid_expires_at") <= parse_utc_seconds(now, "invalid_store_time"):
                    continue
                records.append(record)
            return tuple(records)

    def forget(self, tombstone: Tombstone) -> DeletionReceipt:
        with self._lock:
            existing_receipt = self._receipts.get(tombstone.tombstone_id)
            if existing_receipt is not None:
                existing_tombstone = next(
                    event for event in self._event_order if isinstance(event, Tombstone) and event.tombstone_id == tombstone.tombstone_id
                )
                if existing_tombstone != tombstone:
                    raise MemoryConflictError("tombstone_id_conflict")
                return existing_receipt

            key = self._key(tombstone.namespace, tombstone.memory_id)
            chain = self._chains.get(key)
            if not chain:
                raise MemoryConflictError("unknown_memory")
            if key in self._tombstones:
                raise MemoryConflictError("memory_already_deleted")
            last = self._records[chain[-1]]
            if tombstone.version != last.version + 1:
                raise MemoryConflictError("non_sequential_tombstone_version")

            deleted_ids = tuple(chain)
            digest = stable_digest(
                tuple((record_id, stable_digest(self._records[record_id])) for record_id in deleted_ids)
            )
            receipt = DeletionReceipt(
                memory_id=tombstone.memory_id,
                namespace=tombstone.namespace,
                deleted_at=tombstone.deleted_at,
                deleted_record_ids=deleted_ids,
                tombstone_id=tombstone.tombstone_id,
                reason=tombstone.reason,
                content_digest=digest,
            )
            self._tombstones[key] = tombstone
            self._receipts[tombstone.tombstone_id] = receipt
            self._event_order.append(tombstone)
            return receipt

    def events(self) -> tuple[MemoryRecord | Tombstone, ...]:
        with self._lock:
            return tuple(self._event_order)

