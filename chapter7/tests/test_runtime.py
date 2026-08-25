import unittest

from chapter7.memory_runtime.contracts import (
    Authority,
    MemoryCandidate,
    MemoryLifetime,
    MemoryNamespace,
    MemoryType,
    RecallQuery,
    Sensitivity,
    WriteDecisionKind,
)
from chapter7.memory_runtime.runtime import MemoryRuntime
from chapter7.memory_runtime.store import MemoryConflictError


NS = MemoryNamespace("tenant-a", "user-1", None, "coding-agent")


def candidate(content: str = "代码示例优先使用 Python", **overrides: object) -> MemoryCandidate:
    values: dict[str, object] = {
        "candidate_id": "cand-language-python",
        "namespace": NS,
        "memory_type": MemoryType.SEMANTIC,
        "subject": "preferred_language",
        "content": content,
        "source_id": "conversation-001#message-2",
        "authority": Authority.USER_EXPLICIT,
        "confidence": 1.0,
        "sensitivity": Sensitivity.INTERNAL,
        "lifetime": MemoryLifetime.CROSS_TASK,
        "proposed_at": "2026-08-25T01:00:00Z",
    }
    values.update(overrides)
    return MemoryCandidate(**values)


class MemoryRuntimeTest(unittest.TestCase):
    def test_allowed_candidate_becomes_deterministic_record(self) -> None:
        first = MemoryRuntime()
        second = MemoryRuntime()
        one = first.write(candidate())
        two = second.write(candidate())
        self.assertEqual(one.decision.kind, WriteDecisionKind.ALLOW)
        self.assertEqual(one.record, two.record)
        self.assertTrue(one.record.memory_id.startswith("mem-"))
        self.assertEqual(one.store_result, "written")

    def test_rejected_or_review_candidate_is_not_written(self) -> None:
        runtime = MemoryRuntime()
        secret = runtime.write(candidate(content="password=[REDACTED]", candidate_id="cand-secret"))
        inferred = runtime.write(
            candidate(candidate_id="cand-inferred", authority=Authority.MODEL_INFERENCE, confidence=0.9)
        )
        self.assertIsNone(secret.record)
        self.assertIsNone(inferred.record)
        self.assertEqual(runtime.store.events(), ())

    def test_correction_requires_approval_and_expected_current_record(self) -> None:
        runtime = MemoryRuntime()
        first = runtime.write(candidate()).record
        replacement = candidate(
            "代码示例优先使用 TypeScript",
            candidate_id="cand-language-typescript",
            source_id="conversation-009#message-4",
            proposed_at="2026-09-01T01:00:00Z",
        )
        with self.assertRaisesRegex(MemoryConflictError, "correction_not_approved"):
            runtime.correct(replacement, expected_record_id=first.record_id, approved=False)
        with self.assertRaisesRegex(MemoryConflictError, "stale_expected_record"):
            runtime.correct(replacement, expected_record_id="rec-stale", approved=True)
        corrected = runtime.correct(replacement, expected_record_id=first.record_id, approved=True)
        self.assertEqual(corrected.version, 2)
        self.assertEqual(corrected.supersedes, first.record_id)

    def test_stale_concurrent_correction_is_rejected(self) -> None:
        runtime = MemoryRuntime()
        first = runtime.write(candidate()).record
        runtime.correct(
            candidate("代码示例优先使用 TypeScript", candidate_id="cand-ts", proposed_at="2026-09-01T01:00:00Z"),
            expected_record_id=first.record_id,
            approved=True,
        )
        with self.assertRaisesRegex(MemoryConflictError, "stale_expected_record"):
            runtime.correct(
                candidate("代码示例优先使用 Go", candidate_id="cand-go", proposed_at="2026-09-01T01:01:00Z"),
                expected_record_id=first.record_id,
                approved=True,
            )

    def test_forget_returns_receipt_and_blocks_future_recall(self) -> None:
        runtime = MemoryRuntime()
        record = runtime.write(candidate()).record
        receipt = runtime.forget(
            namespace=NS,
            memory_id=record.memory_id,
            deleted_at="2026-09-02T00:00:00Z",
            source_id="conversation-010#message-1",
            reason="user_requested",
        )
        hits = runtime.recall(
            RecallQuery(NS, "Python examples", (), 3, "2026-09-03T00:00:00Z")
        )
        self.assertEqual(hits, ())
        self.assertNotIn("Python", str(receipt))

    def test_profile_is_projection_of_current_semantic_memories(self) -> None:
        runtime = MemoryRuntime()
        runtime.write(candidate())
        runtime.write(
            candidate(
                "修改 public API 前先确认",
                candidate_id="cand-api",
                subject="public_api_change",
                memory_type=MemoryType.PROCEDURAL,
                namespace=MemoryNamespace("tenant-a", "user-1", "pricing", "coding-agent"),
            )
        )
        profile = runtime.profile(NS, now="2026-08-26T00:00:00Z")
        self.assertEqual(profile, {"preferred_language": "代码示例优先使用 Python"})

    def test_audit_trace_contains_digest_not_memory_content(self) -> None:
        runtime = MemoryRuntime()
        runtime.write(candidate())
        trace = runtime.audit_events()
        self.assertEqual(len(trace), 1)
        self.assertNotIn("Python", str(trace))
        self.assertEqual(len(trace[0].content_digest), 64)


if __name__ == "__main__":
    unittest.main()
