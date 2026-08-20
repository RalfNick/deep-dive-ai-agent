import unittest

from chapter5.context.contracts import ContextKind, InstructionAuthority, RetentionPriority, Sensitivity, TrustLevel
from chapter6.context_continuity.contracts import (
    CarryItem,
    CompactionArtifact,
    EventRecord,
    EventType,
    EvidenceLocator,
    WorkingSet,
)
from chapter6.context_continuity.trace import serialized_bytes, stable_digest


class ContractTest(unittest.TestCase):
    def test_non_instruction_cannot_carry_instruction_authority(self) -> None:
        with self.assertRaisesRegex(ValueError, "non_instruction_authority"):
            CarryItem(
                key="open-test",
                kind=ContextKind.OBSERVATION,
                content="legacy case still fails",
                authority=InstructionAuthority.USER,
                trust=TrustLevel.VERIFIED,
                retention_priority=RetentionPriority.REQUIRED,
                sensitivity=Sensitivity.INTERNAL,
                source_event_ids=("evt-018",),
                required_for=frozenset({"legacy-config"}),
            )

    def test_artifact_requires_source_events_and_open_issue_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "open_issue_without_source"):
            CompactionArtifact.minimal_for_test(open_issue_source_event_ids=())

    def test_canonical_size_and_digest_are_order_independent_for_mappings(self) -> None:
        left = {"goal": "repair", "step": 2}
        right = {"step": 2, "goal": "repair"}
        self.assertEqual(stable_digest(left), stable_digest(right))
        self.assertEqual(serialized_bytes(left), len('{"goal":"repair","step":2}'.encode("utf-8")))

    def test_lifecycle_contracts_reject_invalid_identity_and_budget_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "blank_evidence_locator_id"):
            EvidenceLocator(" ", "file", "tests/test_pricing.py", "content", "workspace")
        with self.assertRaisesRegex(ValueError, "non_positive_event_sequence"):
            EventRecord("evt-001", "run-price", 0, EventType.TASK)
        with self.assertRaisesRegex(ValueError, "negative_max_serialized_bytes"):
            WorkingSet((), (), -1)

    def test_artifact_rejects_invalid_version_ranges_duplicate_keys_and_open_issue_evidence(self) -> None:
        artifact = CompactionArtifact.minimal_for_test()
        with self.assertRaisesRegex(ValueError, "invalid_schema_version"):
            CompactionArtifact(**{**artifact.__dict__, "schema_version": "2.0"})
        with self.assertRaisesRegex(ValueError, "unordered_source_event_range"):
            CompactionArtifact(**{**artifact.__dict__, "source_event_range": (20, 1)})
        duplicate = CarryItem(
            key=artifact.goal.key,
            kind=ContextKind.FACT,
            content="duplicate key",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.HIGH,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-021",),
        )
        with self.assertRaisesRegex(ValueError, "duplicate_carry_item_key"):
            CompactionArtifact(**{**artifact.__dict__, "constraints": (duplicate,)})
