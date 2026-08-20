import unittest
from dataclasses import FrozenInstanceError

from chapter6.context_continuity.policy import (
    RepairDecision,
    ScriptedRepairPolicy,
    VisibleSemanticState,
)


class ScriptedRepairPolicyTest(unittest.TestCase):
    def test_missing_negative_constraint_proposes_signature_change(self) -> None:
        decision = ScriptedRepairPolicy().decide(
            VisibleSemanticState(
                visible_keys=frozenset({"repair-price", "legacy-config-open"}),
                checkpoint_next_step="apply-compatible-patch",
                verification_keys=frozenset(),
            )
        )

        self.assertEqual(decision.kind, "unsafe_signature_change")
        self.assertEqual(decision.required_keys, frozenset({"public-signature"}))
        self.assertIn("not visible", decision.reason)

    def test_checkpoint_only_repeats_rejected_hypothesis(self) -> None:
        decision = ScriptedRepairPolicy().decide(
            VisibleSemanticState(
                visible_keys=frozenset({"repair-price", "public-signature"}),
                checkpoint_next_step="run-tests",
                verification_keys=frozenset(),
            )
        )

        self.assertEqual(decision.kind, "repeat_rounding_attempt")
        self.assertEqual(
            decision.required_keys,
            frozenset({"rounding-only-rejected", "legacy-test-failing"}),
        )

    def test_complete_state_continues_with_legacy_compatible_patch(self) -> None:
        decision = ScriptedRepairPolicy().decide(
            VisibleSemanticState(
                visible_keys=frozenset(
                    {
                        "repair-price",
                        "public-signature",
                        "rounding-only-rejected",
                        "legacy-config-open",
                    }
                ),
                checkpoint_next_step="apply-compatible-patch",
                verification_keys=frozenset({"legacy-test-failing"}),
            )
        )

        self.assertEqual(decision.kind, "apply_legacy_compatible_patch")
        self.assertEqual(decision.required_keys, frozenset())

    def test_partial_state_requests_only_missing_evidence(self) -> None:
        decision = ScriptedRepairPolicy().decide(
            VisibleSemanticState(
                visible_keys=frozenset(
                    {
                        "repair-price",
                        "public-signature",
                        "rounding-only-rejected",
                    }
                ),
                checkpoint_next_step="apply-compatible-patch",
                verification_keys=frozenset(),
            )
        )

        self.assertEqual(decision.kind, "needs_context")
        self.assertEqual(
            decision.required_keys,
            frozenset({"legacy-config-open", "legacy-test-failing"}),
        )

    def test_policy_contracts_are_immutable(self) -> None:
        state = VisibleSemanticState(frozenset(), "inspect", frozenset())
        decision = RepairDecision("needs_context", "evidence missing", frozenset())

        with self.assertRaises(FrozenInstanceError):
            state.checkpoint_next_step = "mutated"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            decision.kind = "mutated"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
