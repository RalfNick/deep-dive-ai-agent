import unittest

from chapter7.memory_runtime.contracts import (
    Authority,
    MemoryCandidate,
    MemoryLifetime,
    MemoryNamespace,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    Sensitivity,
    WriteDecisionKind,
)
from chapter7.memory_runtime.policy import MemoryWritePolicy


NS = MemoryNamespace("tenant-a", "user-1", None, "coding-agent")


def candidate(**overrides: object) -> MemoryCandidate:
    values: dict[str, object] = {
        "candidate_id": "cand-001",
        "namespace": NS,
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


def existing(**overrides: object) -> MemoryRecord:
    values: dict[str, object] = {
        "record_id": "rec-001",
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


class MemoryWritePolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = MemoryWritePolicy()

    def test_explicit_cross_task_preference_is_allowed(self) -> None:
        decision = self.policy.evaluate(candidate(), current=())
        self.assertEqual(decision.kind, WriteDecisionKind.ALLOW)
        self.assertEqual(decision.reason, "explicit_cross_task_memory")

    def test_secret_marker_is_rejected_even_if_sensitivity_is_wrong(self) -> None:
        decision = self.policy.evaluate(
            candidate(content="请记住 API_KEY=[REDACTED]"), current=()
        )
        self.assertEqual((decision.kind, decision.reason), (WriteDecisionKind.REJECT, "sensitive_content"))

    def test_secret_sensitivity_is_rejected(self) -> None:
        decision = self.policy.evaluate(candidate(sensitivity=Sensitivity.SECRET), current=())
        self.assertEqual(decision.reason, "sensitive_content")

    def test_one_time_authorization_and_task_state_are_rejected(self) -> None:
        one_time = self.policy.evaluate(candidate(lifetime=MemoryLifetime.ONE_TIME), current=())
        task = self.policy.evaluate(candidate(lifetime=MemoryLifetime.CURRENT_TASK), current=())
        self.assertEqual(one_time.reason, "one_time_content")
        self.assertEqual(task.reason, "current_task_state")

    def test_model_inference_requires_review(self) -> None:
        decision = self.policy.evaluate(
            candidate(authority=Authority.MODEL_INFERENCE, confidence=0.91), current=()
        )
        self.assertEqual((decision.kind, decision.reason), (WriteDecisionKind.REVIEW, "inferred_memory_requires_review"))

    def test_low_confidence_is_rejected_before_review(self) -> None:
        decision = self.policy.evaluate(
            candidate(authority=Authority.MODEL_INFERENCE, confidence=0.4), current=()
        )
        self.assertEqual((decision.kind, decision.reason), (WriteDecisionKind.REJECT, "low_confidence"))

    def test_exact_duplicate_is_rejected_as_noop(self) -> None:
        decision = self.policy.evaluate(candidate(), current=(existing(),))
        self.assertEqual((decision.kind, decision.reason), (WriteDecisionKind.REJECT, "duplicate_memory"))

    def test_conflicting_value_requires_explicit_correction(self) -> None:
        decision = self.policy.evaluate(
            candidate(content="代码示例优先使用 TypeScript"), current=(existing(),)
        )
        self.assertEqual((decision.kind, decision.reason), (WriteDecisionKind.REVIEW, "conflict_requires_correction"))

    def test_same_subject_in_other_namespace_does_not_create_conflict(self) -> None:
        other = MemoryNamespace("tenant-a", "user-2", None, "coding-agent")
        decision = self.policy.evaluate(candidate(namespace=other), current=(existing(),))
        self.assertEqual(decision.kind, WriteDecisionKind.ALLOW)


if __name__ == "__main__":
    unittest.main()
