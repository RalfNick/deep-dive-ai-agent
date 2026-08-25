from dataclasses import FrozenInstanceError, replace
import unittest

from chapter7.memory_runtime.contracts import (
    Authority,
    DeletionReceipt,
    MemoryCandidate,
    MemoryLifetime,
    MemoryNamespace,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    RecallQuery,
    Sensitivity,
    canonical_json,
    stable_digest,
)


def namespace(*, tenant: str = "tenant-a", user: str = "user-1", project: str | None = "pricing") -> MemoryNamespace:
    return MemoryNamespace(tenant_id=tenant, user_id=user, project_id=project, agent_id="coding-agent")


def candidate(**overrides: object) -> MemoryCandidate:
    values: dict[str, object] = {
        "candidate_id": "cand-python",
        "namespace": namespace(project=None),
        "memory_type": MemoryType.SEMANTIC,
        "subject": "preferred_language",
        "content": "代码示例优先使用 Python",
        "source_id": "conversation-001#message-2",
        "authority": Authority.USER_EXPLICIT,
        "confidence": 1.0,
        "sensitivity": Sensitivity.INTERNAL,
        "lifetime": MemoryLifetime.CROSS_TASK,
        "proposed_at": "2026-08-25T01:00:00Z",
    }
    values.update(overrides)
    return MemoryCandidate(**values)


def record(**overrides: object) -> MemoryRecord:
    values: dict[str, object] = {
        "record_id": "rec-python-v1",
        "memory_id": "mem-python",
        "namespace": namespace(project=None),
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


class ContractTest(unittest.TestCase):
    def test_namespace_requires_tenant_user_and_agent(self) -> None:
        with self.assertRaisesRegex(ValueError, "blank_tenant_id"):
            namespace(tenant=" ")
        with self.assertRaisesRegex(ValueError, "blank_user_id"):
            namespace(user=" ")
        with self.assertRaisesRegex(ValueError, "blank_agent_id"):
            MemoryNamespace("tenant", "user", "project", " ")

    def test_namespace_key_is_stable_and_keeps_scope_components(self) -> None:
        self.assertEqual(
            namespace().key,
            '{"agent_id":"coding-agent","project_id":"pricing","tenant_id":"tenant-a","user_id":"user-1"}',
        )
        self.assertEqual(
            namespace(project=None).key,
            '{"agent_id":"coding-agent","project_id":null,"tenant_id":"tenant-a","user_id":"user-1"}',
        )

    def test_global_namespace_does_not_collide_with_literal_underscore_project(self) -> None:
        self.assertNotEqual(namespace(project=None).key, namespace(project="_").key)

    def test_candidate_rejects_blank_fields_invalid_confidence_and_bad_time(self) -> None:
        with self.assertRaisesRegex(ValueError, "blank_candidate_content"):
            candidate(content=" ")
        with self.assertRaisesRegex(ValueError, "invalid_candidate_confidence"):
            candidate(confidence=1.1)
        with self.assertRaisesRegex(ValueError, "invalid_proposed_at"):
            candidate(proposed_at="tomorrow")

    def test_record_rejects_invalid_version_chain(self) -> None:
        with self.assertRaisesRegex(ValueError, "first_version_has_supersedes"):
            record(supersedes="rec-old")
        with self.assertRaisesRegex(ValueError, "later_version_requires_supersedes"):
            record(version=2)
        with self.assertRaisesRegex(ValueError, "non_positive_memory_version"):
            record(version=0)

    def test_record_rejects_expiry_before_validity_and_non_active_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "expiry_not_after_valid_from"):
            record(expires_at="2026-08-24T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "record_input_must_be_active"):
            record(status=MemoryStatus.SUPERSEDED)

    def test_recall_query_requires_positive_top_k_and_utc_time(self) -> None:
        with self.assertRaisesRegex(ValueError, "non_positive_top_k"):
            RecallQuery(namespace(), "python example", (), 0, "2026-08-25T02:00:00Z")
        with self.assertRaisesRegex(ValueError, "invalid_recall_time"):
            RecallQuery(namespace(), "python example", (), 3, "2026-08-25 02:00")

    def test_canonical_json_and_digest_ignore_mapping_insertion_order(self) -> None:
        left = {"subject": "preferred_language", "version": 1}
        right = {"version": 1, "subject": "preferred_language"}
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(stable_digest(left), stable_digest(right))
        self.assertFalse(canonical_json(left).endswith("\n"))

    def test_receipt_contains_no_deleted_content(self) -> None:
        receipt = DeletionReceipt(
            memory_id="mem-python",
            namespace=namespace(project=None),
            deleted_at="2026-08-25T03:00:00Z",
            deleted_record_ids=("rec-python-v1",),
            tombstone_id="tomb-mem-python-v2",
            reason="user_requested",
            content_digest="a" * 64,
        )
        payload = canonical_json(receipt)
        self.assertNotIn("代码示例", payload)
        self.assertIn("user_requested", payload)

    def test_records_are_frozen(self) -> None:
        item = record()
        with self.assertRaises(FrozenInstanceError):
            item.memory_id = "mem-replacement"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
