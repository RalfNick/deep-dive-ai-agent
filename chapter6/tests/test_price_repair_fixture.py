import unittest

from chapter6.context_continuity.compaction import StructuredCompactionStrategy
from chapter6.context_continuity.trace import stable_digest
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    CANONICAL_TRAJECTORY_DIGEST,
    CANONICAL_WORKSPACE_DIGEST,
    canonical_seed,
    canonical_trajectory,
)


class PriceRepairFixtureTest(unittest.TestCase):
    def test_canonical_trajectory_has_fixed_shape(self) -> None:
        events = canonical_trajectory()

        self.assertEqual(len(events), 30)
        self.assertEqual(tuple(event.sequence for event in events), tuple(range(1, 31)))
        self.assertEqual(events[0].event_id, "evt-001")
        self.assertEqual(events[-1].event_id, "evt-030")
        self.assertEqual(stable_digest(events), CANONICAL_TRAJECTORY_DIGEST)

    def test_fixture_places_constraint_and_failure_on_opposite_sides_of_cut(self) -> None:
        positions = {
            item.key: event.sequence
            for event in canonical_trajectory()
            for item in event.carry_items
        }

        self.assertLess(positions["public-signature"], 12)
        self.assertGreater(positions["legacy-config-open"], 12)
        self.assertLessEqual(positions["legacy-config-open"], CANONICAL_COMPACTION_CURSOR)

    def test_fixture_contains_reviewable_lifecycle_landmarks(self) -> None:
        events = canonical_trajectory()
        item_keys = {
            item.key
            for event in events
            for item in event.carry_items
        }
        payload_refs = {event.payload_ref for event in events if event.payload_ref}

        self.assertTrue(
            {
                "repair-price",
                "public-signature",
                "rounding-only-rejected",
                "legacy-config-open",
                "legacy-test-failing",
                "user-clarification",
                "next-intent",
                "compaction-boundary",
                "resume-artifact-loaded",
                "legacy-test-passing",
            }.issubset(item_keys)
        )
        self.assertTrue(
            {
                "src/pricing.py",
                "tests/test_pricing.py",
                "fixtures/legacy-pricing.json",
                "workspace://price-repair",
            }.issubset(payload_refs)
        )

    def test_compaction_prefix_has_an_authoritatively_verifiable_digest(self) -> None:
        events = canonical_trajectory()
        prefix = events[:CANONICAL_COMPACTION_CURSOR]
        output = StructuredCompactionStrategy().prepare(prefix, canonical_seed())

        self.assertIsNotNone(output.artifact)
        assert output.artifact is not None
        self.assertEqual(output.artifact.source_event_range, (1, CANONICAL_COMPACTION_CURSOR))
        self.assertEqual(output.artifact.source_digest, stable_digest(prefix))
        self.assertEqual(output.artifact.workspace_digest, CANONICAL_WORKSPACE_DIGEST)
        self.assertTrue(canonical_seed().required_keys.issubset(output.visible_keys))


if __name__ == "__main__":
    unittest.main()
