import unittest
from dataclasses import replace

from chapter5.context.contracts import (
    ContextKind,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)
from chapter6.context_continuity.compaction import (
    AppendAllStrategy,
    ParagraphSummaryStrategy,
    SlidingWindowStrategy,
    StructuredCompactionStrategy,
)
from chapter6.context_continuity.contracts import CarryItem, CompactionSeed, EventRecord, EventType
from chapter6.context_continuity.trace import stable_digest


def strategy_fixture() -> tuple[tuple[EventRecord, ...], CompactionSeed]:
    keys = (
        ("repair-price", ContextKind.TASK, "repair price calculation"),
        ("public-signature", ContextKind.INSTRUCTION, "do not change the public signature"),
        ("rounding-only-rejected", ContextKind.FACT, "rounding-only hypothesis was rejected"),
        ("legacy-config-open", ContextKind.OBSERVATION, "legacy configuration test still fails"),
    )
    events = []
    for sequence, (key, kind, content) in enumerate(keys, start=1):
        authority = InstructionAuthority.USER if kind is ContextKind.INSTRUCTION else InstructionAuthority.NONE
        item = CarryItem(
            key=key,
            kind=kind,
            content=content,
            authority=authority,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=(f"evt-{sequence:03d}",),
        )
        events.append(
            EventRecord(
                f"evt-{sequence:03d}",
                "run-price",
                sequence,
                EventType.OBSERVATION,
                (item,),
                payload_ref="tests/test_pricing.py" if sequence in (2, 4) else None,
                workspace_digest="workspace-v1",
            )
        )
    seed = CompactionSeed(
        run_id="run-price",
        goal_key="repair-price",
        acceptance_keys=frozenset(),
        constraint_keys=frozenset({"public-signature"}),
        decision_keys=frozenset(),
        rejected_hypothesis_keys=frozenset({"rounding-only-rejected"}),
        open_issue_keys=frozenset({"legacy-config-open"}),
        verification_keys=frozenset(),
        required_keys=frozenset(key for key, _, _ in keys),
    )
    return tuple(events), seed


class CompactionStrategyTest(unittest.TestCase):
    def test_append_all_retains_canonical_history_and_reports_teaching_budget_overflow(self) -> None:
        events, seed = strategy_fixture()

        output = AppendAllStrategy().prepare(events, seed)

        self.assertEqual(output.visible_keys, seed.required_keys)
        self.assertEqual(output.serialized_bytes_before, output.serialized_bytes_after)
        self.assertTrue(output.overflowed)
        self.assertEqual(output.dropped_event_ids, ())

    def test_sliding_window_silently_drops_early_negative_constraint(self) -> None:
        events, seed = strategy_fixture()

        output = SlidingWindowStrategy(keep_events=2).prepare(events, seed)

        self.assertNotIn("public-signature", output.visible_keys)
        self.assertFalse(output.overflowed)
        self.assertEqual(output.dropped_event_ids, ("evt-001", "evt-002"))

    def test_paragraph_summary_keeps_goal_but_loses_rejected_hypothesis(self) -> None:
        events, seed = strategy_fixture()

        output = ParagraphSummaryStrategy().prepare(events, seed)

        self.assertIn("repair-price", output.visible_keys)
        self.assertNotIn("public-signature", output.visible_keys)
        self.assertNotIn("rounding-only-rejected", output.visible_keys)
        self.assertNotIn("legacy-config-open", output.visible_keys)
        self.assertIsNone(output.artifact)

    def test_paragraph_summary_keeps_only_the_latest_declared_decision(self) -> None:
        events, seed = strategy_fixture()
        first_decision = CarryItem(
            key="choose-patch-a",
            kind=ContextKind.FACT,
            content="first patch was selected",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.HIGH,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-005",),
        )
        latest_decision = CarryItem(
            key="choose-patch-b",
            kind=ContextKind.FACT,
            content="compatible patch is the final decision",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.HIGH,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-006",),
        )
        events = (*events, EventRecord("evt-005", "run-price", 5, EventType.DECISION, (first_decision,)), EventRecord("evt-006", "run-price", 6, EventType.DECISION, (latest_decision,)))
        seed = replace(
            seed,
            decision_keys=frozenset({"choose-patch-a", "choose-patch-b"}),
            required_keys=seed.required_keys | {"choose-patch-a", "choose-patch-b"},
        )

        output = ParagraphSummaryStrategy().prepare(events, seed)

        self.assertIn("choose-patch-b", output.visible_keys)
        self.assertNotIn("choose-patch-a", output.visible_keys)

    def test_structured_compaction_preserves_all_required_keys(self) -> None:
        events, seed = strategy_fixture()

        output = StructuredCompactionStrategy().prepare(events, seed)

        self.assertEqual(output.visible_keys, seed.required_keys)
        self.assertIsNotNone(output.artifact)
        self.assertLess(output.serialized_bytes_after, output.serialized_bytes_before)
        self.assertEqual(
            output.artifact.source_digest,
            stable_digest(events),
        )
        self.assertEqual(output.artifact.constraints[0].authority, InstructionAuthority.USER)
        self.assertEqual(output.artifact.constraints[0].source_event_ids, ("evt-002",))
        self.assertEqual(len(output.artifact.evidence_locators), 2)

    def test_structured_compaction_does_not_deduplicate_same_reference_with_different_content(self) -> None:
        events, seed = strategy_fixture()

        output = StructuredCompactionStrategy().prepare(events, seed)

        locators = output.artifact.evidence_locators
        self.assertEqual([locator.ref for locator in locators], ["tests/test_pricing.py", "tests/test_pricing.py"])
        self.assertNotEqual(locators[0].content_digest, locators[1].content_digest)

    def test_structured_compaction_reuses_existing_next_intent_without_duplicate_category_item(self) -> None:
        events, seed = strategy_fixture()
        next_intent = CarryItem(
            key="next-intent",
            kind=ContextKind.TASK,
            content="rerun the legacy configuration test",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-005",),
        )
        events = (*events, EventRecord("evt-005", "run-price", 5, EventType.TASK, (next_intent,)))
        seed = replace(
            seed,
            decision_keys=frozenset({"next-intent"}),
            required_keys=seed.required_keys | {"next-intent"},
        )

        output = StructuredCompactionStrategy().prepare(events, seed)

        self.assertEqual(output.artifact.next_intent, next_intent)
        self.assertNotIn("next-intent", {item.key for item in output.artifact.decisions})
        self.assertIn("next-intent", output.visible_keys)

    def test_structured_compaction_drops_nonrequired_uncategorized_items(self) -> None:
        events, seed = strategy_fixture()
        transient = CarryItem(
            key="transient-note",
            kind=ContextKind.OBSERVATION,
            content="a nonrequired diagnostic note",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.UNVERIFIED,
            retention_priority=RetentionPriority.LOW,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-005",),
        )
        events = (*events, EventRecord("evt-005", "run-price", 5, EventType.OBSERVATION, (transient,)))

        output = StructuredCompactionStrategy().prepare(events, seed)

        self.assertNotIn("transient-note", output.visible_keys)
        self.assertNotIn("transient-note", {item.key for item in output.artifact.decisions})

    def test_structured_compaction_rejects_required_uncategorized_items(self) -> None:
        events, seed = strategy_fixture()
        required_note = CarryItem(
            key="must-preserve-note",
            kind=ContextKind.OBSERVATION,
            content="a required note without a semantic category",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-005",),
        )
        events = (*events, EventRecord("evt-005", "run-price", 5, EventType.OBSERVATION, (required_note,)))
        seed = replace(seed, required_keys=seed.required_keys | {"must-preserve-note"})

        with self.assertRaisesRegex(ValueError, "required_carry_item_without_category"):
            StructuredCompactionStrategy().prepare(events, seed)

    def test_structured_compaction_is_canonical_for_identical_inputs(self) -> None:
        events, seed = strategy_fixture()

        first = StructuredCompactionStrategy().prepare(events, seed)
        second = StructuredCompactionStrategy().prepare(events, seed)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
