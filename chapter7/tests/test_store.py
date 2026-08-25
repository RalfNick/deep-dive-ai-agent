import threading
import unittest

from chapter7.memory_runtime.contracts import (
    Authority,
    MemoryNamespace,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    Sensitivity,
    Tombstone,
)
from chapter7.memory_runtime.store import MemoryConflictError, MemoryStore


NS = MemoryNamespace("tenant-a", "user-1", None, "coding-agent")


def record(**overrides: object) -> MemoryRecord:
    values: dict[str, object] = {
        "record_id": "rec-language-v1",
        "memory_id": "mem-language",
        "namespace": NS,
        "memory_type": MemoryType.SEMANTIC,
        "subject": "preferred_language",
        "content": "代码示例优先使用 Python",
        "source_id": "conversation-001#message-2",
        "authority": Authority.USER_EXPLICIT,
        "confidence": 1.0,
        "sensitivity": Sensitivity.INTERNAL,
        "valid_from": "2026-08-25T01:00:00Z",
        "expires_at": None,
        "created_at": "2026-08-25T01:00:00Z",
        "version": 1,
        "supersedes": None,
        "status": MemoryStatus.ACTIVE,
    }
    values.update(overrides)
    return MemoryRecord(**values)


class MemoryStoreTest(unittest.TestCase):
    def test_first_write_and_identical_retry_are_idempotent(self) -> None:
        store = MemoryStore()
        self.assertEqual(store.append(record()), "written")
        self.assertEqual(store.append(record()), "idempotent")
        self.assertEqual(len(store.events()), 1)

    def test_same_record_id_with_different_payload_is_conflict(self) -> None:
        store = MemoryStore()
        store.append(record())
        with self.assertRaisesRegex(MemoryConflictError, "record_id_conflict"):
            store.append(record(content="TypeScript"))

    def test_correction_requires_exact_previous_version(self) -> None:
        store = MemoryStore()
        first = record()
        store.append(first)
        with self.assertRaisesRegex(MemoryConflictError, "invalid_supersedes"):
            store.append(record(record_id="rec-language-v2", version=2, supersedes="rec-missing", content="TypeScript"))
        with self.assertRaisesRegex(MemoryConflictError, "non_sequential_version"):
            store.append(record(record_id="rec-language-v3", version=3, supersedes=first.record_id, content="TypeScript"))

    def test_correction_changes_current_but_preserves_versions(self) -> None:
        store = MemoryStore()
        first = record()
        second = record(
            record_id="rec-language-v2",
            version=2,
            supersedes=first.record_id,
            content="代码示例优先使用 TypeScript",
            source_id="conversation-009#message-4",
            created_at="2026-09-01T01:00:00Z",
            valid_from="2026-09-01T01:00:00Z",
        )
        store.append(first)
        store.append(second)
        self.assertEqual(store.current(NS, "mem-language", now="2026-09-02T00:00:00Z"), second)
        self.assertEqual(store.versions(NS, "mem-language"), (first, second))

    def test_expired_record_is_not_current(self) -> None:
        store = MemoryStore()
        store.append(record(expires_at="2026-08-26T00:00:00Z"))
        self.assertIsNone(store.current(NS, "mem-language", now="2026-08-27T00:00:00Z"))

    def test_tombstone_hides_all_versions_and_is_idempotent(self) -> None:
        store = MemoryStore()
        store.append(record())
        tombstone = Tombstone(
            tombstone_id="tomb-language-v2",
            memory_id="mem-language",
            namespace=NS,
            deleted_at="2026-08-27T00:00:00Z",
            reason="user_requested",
            source_id="conversation-010#message-1",
            version=2,
        )
        receipt = store.forget(tombstone)
        retry = store.forget(tombstone)
        self.assertEqual(receipt, retry)
        self.assertIsNone(store.current(NS, "mem-language", now="2026-08-28T00:00:00Z"))
        self.assertNotIn("Python", str(receipt))

    def test_tombstone_for_unknown_memory_fails_closed(self) -> None:
        store = MemoryStore()
        tombstone = Tombstone("tomb-missing", "missing", NS, "2026-08-27T00:00:00Z", "user_requested", "msg-1", 1)
        with self.assertRaisesRegex(MemoryConflictError, "unknown_memory"):
            store.forget(tombstone)

    def test_two_concurrent_different_first_writes_have_one_winner(self) -> None:
        store = MemoryStore()
        barrier = threading.Barrier(2)
        results: list[str] = []

        def write(value: str, record_id: str) -> None:
            barrier.wait()
            try:
                results.append(store.append(record(record_id=record_id, content=value)))
            except MemoryConflictError as exc:
                results.append(str(exc))

        threads = [
            threading.Thread(target=write, args=("Python", "rec-a")),
            threading.Thread(target=write, args=("TypeScript", "rec-b")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(results.count("written"), 1)
        self.assertEqual(sum("memory_id_conflict" in item for item in results), 1)


if __name__ == "__main__":
    unittest.main()
