from pathlib import Path
import tempfile
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
from chapter7.memory_runtime.persistence import load_event_log, write_event_log
from chapter7.memory_runtime.store import MemoryStore


NS = MemoryNamespace("tenant-a", "user-1", None, "coding-agent")


def first_record() -> MemoryRecord:
    return MemoryRecord(
        "rec-language-v1",
        "mem-language",
        NS,
        MemoryType.SEMANTIC,
        "preferred_language",
        "代码示例优先使用 Python",
        "conversation-001#message-2",
        Authority.USER_EXPLICIT,
        1.0,
        Sensitivity.INTERNAL,
        "2026-08-25T01:00:00Z",
        None,
        "2026-08-25T01:00:00Z",
        1,
        None,
        MemoryStatus.ACTIVE,
    )


class PersistenceTest(unittest.TestCase):
    def test_event_log_round_trip_preserves_record_and_tombstone_semantics(self) -> None:
        store = MemoryStore()
        store.append(first_record())
        store.forget(
            Tombstone(
                "tomb-language-v2",
                "mem-language",
                NS,
                "2026-09-02T00:00:00Z",
                "user_requested",
                "conversation-010#message-1",
                2,
            )
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "memory-events.jsonl"
            write_event_log(path, store.events())
            restored = load_event_log(path)
            self.assertEqual(restored.events(), store.events())
            self.assertIsNone(restored.current(NS, "mem-language", now="2026-09-03T00:00:00Z"))

    def test_event_log_is_utf8_lf_and_byte_reproducible(self) -> None:
        events = (first_record(),)
        with tempfile.TemporaryDirectory() as temp_dir:
            left = Path(temp_dir) / "left.jsonl"
            right = Path(temp_dir) / "right.jsonl"
            write_event_log(left, events)
            write_event_log(right, events)
            self.assertEqual(left.read_bytes(), right.read_bytes())
            self.assertNotIn(b"\r\n", left.read_bytes())
            self.assertTrue(left.read_bytes().endswith(b"\n"))

    def test_loader_rejects_unknown_event_type_and_truncated_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.jsonl"
            path.write_text('{"event_type":"unknown"}\n', encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "unknown_memory_event_type"):
                load_event_log(path)
            path.write_text('{"event_type":', encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "invalid_memory_event_json"):
                load_event_log(path)


if __name__ == "__main__":
    unittest.main()
