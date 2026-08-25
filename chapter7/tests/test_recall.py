import unittest

from chapter7.memory_runtime.contracts import (
    Authority,
    MemoryNamespace,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    RecallQuery,
    Sensitivity,
)
from chapter7.memory_runtime.recall import MemoryRecall
from chapter7.memory_runtime.store import MemoryStore


QUERY_NS = MemoryNamespace("tenant-a", "user-1", "pricing", "coding-agent")


def record(
    memory_id: str,
    subject: str,
    content: str,
    *,
    namespace: MemoryNamespace = QUERY_NS,
    memory_type: MemoryType = MemoryType.SEMANTIC,
    authority: Authority = Authority.USER_EXPLICIT,
    confidence: float = 1.0,
    sensitivity: Sensitivity = Sensitivity.INTERNAL,
    valid_from: str = "2026-08-01T00:00:00Z",
    expires_at: str | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        record_id=f"rec-{memory_id}-v1",
        memory_id=memory_id,
        namespace=namespace,
        memory_type=memory_type,
        subject=subject,
        content=content,
        source_id=f"source-{memory_id}",
        authority=authority,
        confidence=confidence,
        sensitivity=sensitivity,
        valid_from=valid_from,
        expires_at=expires_at,
        created_at=valid_from,
        version=1,
        supersedes=None,
        status=MemoryStatus.ACTIVE,
    )


class MemoryRecallTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore()
        self.recall = MemoryRecall(self.store)

    def query(self, text: str, *, top_k: int = 3, allowed: tuple[Sensitivity, ...] = (Sensitivity.PUBLIC, Sensitivity.INTERNAL)) -> RecallQuery:
        return RecallQuery(
            namespace=QUERY_NS,
            query=text,
            memory_types=(),
            top_k=top_k,
            now="2026-08-25T00:00:00Z",
            allowed_sensitivities=allowed,
        )

    def test_global_user_memory_and_current_project_memory_are_recalled(self) -> None:
        global_ns = MemoryNamespace("tenant-a", "user-1", None, "coding-agent")
        self.store.append(record("language", "preferred_language", "代码示例优先使用 Python", namespace=global_ns))
        self.store.append(record("api", "public_api", "修改 public API 前先确认"))
        hits = self.recall.search(self.query("Python public API"))
        self.assertEqual({hit.record.memory_id for hit in hits}, {"language", "api"})

    def test_other_tenant_user_project_and_agent_are_hard_filtered(self) -> None:
        namespaces = (
            MemoryNamespace("tenant-b", "user-1", "pricing", "coding-agent"),
            MemoryNamespace("tenant-a", "user-2", "pricing", "coding-agent"),
            MemoryNamespace("tenant-a", "user-1", "payments", "coding-agent"),
            MemoryNamespace("tenant-a", "user-1", "pricing", "review-agent"),
        )
        for index, ns in enumerate(namespaces):
            self.store.append(record(f"leak-{index}", "preferred_language", "Python secret preference", namespace=ns))
        self.assertEqual(self.recall.search(self.query("Python preference")), ())

    def test_expired_deleted_and_disallowed_sensitive_records_are_filtered_before_scoring(self) -> None:
        self.store.append(record("expired", "preferred_language", "Python", expires_at="2026-08-20T00:00:00Z"))
        self.store.append(record("secret", "preferred_language", "Python", sensitivity=Sensitivity.SECRET))
        self.assertEqual(self.recall.search(self.query("Python")), ())

    def test_type_filter_and_top_k_are_enforced(self) -> None:
        self.store.append(record("semantic", "python", "Python style", memory_type=MemoryType.SEMANTIC))
        self.store.append(record("episode", "python", "Python test failed once", memory_type=MemoryType.EPISODIC))
        query = RecallQuery(QUERY_NS, "Python", (MemoryType.EPISODIC,), 1, "2026-08-25T00:00:00Z")
        hits = self.recall.search(query)
        self.assertEqual(tuple(hit.record.memory_id for hit in hits), ("episode",))

    def test_score_breakdown_is_visible_and_sums_to_total(self) -> None:
        self.store.append(record("language", "preferred_language", "代码示例优先使用 Python"))
        hit = self.recall.search(self.query("Python language", top_k=1))[0]
        score = hit.score
        self.assertAlmostEqual(score.total, score.task_match + score.authority + score.recency + score.confidence)
        self.assertGreater(score.task_match, 0)

    def test_explicit_authority_beats_inference_when_relevance_is_equal(self) -> None:
        self.store.append(record("explicit", "language", "Python examples", authority=Authority.USER_EXPLICIT))
        self.store.append(record("inferred", "language", "Python examples", authority=Authority.MODEL_INFERENCE))
        hits = self.recall.search(self.query("Python examples"))
        self.assertEqual(tuple(hit.record.memory_id for hit in hits), ("explicit", "inferred"))

    def test_sorting_is_stable_when_scores_tie(self) -> None:
        self.store.append(record("b", "language", "Python examples"))
        self.store.append(record("a", "language", "Python examples"))
        self.assertEqual(tuple(hit.record.memory_id for hit in self.recall.search(self.query("Python"))), ("a", "b"))

    def test_unrelated_records_do_not_fill_top_k(self) -> None:
        self.store.append(record("noise", "lunch", "今天午饭吃面"))
        self.assertEqual(self.recall.search(self.query("Python API")), ())


if __name__ == "__main__":
    unittest.main()
