"""Deterministic probe for observing semantic continuity failures.

This module does not execute tools and is not a stand-in for a language model.
It maps an explicitly visible semantic state to a stable decision so Chapter 6
can compare context strategies without changing model behavior.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisibleSemanticState:
    visible_keys: frozenset[str]
    checkpoint_next_step: str
    verification_keys: frozenset[str]


@dataclass(frozen=True)
class RepairDecision:
    kind: str
    reason: str
    required_keys: frozenset[str]


class ScriptedRepairPolicy:
    """Return a reviewed action solely from visible keys and checkpoint intent."""

    _GOAL_KEY = "repair-price"
    _SIGNATURE_KEY = "public-signature"
    _REJECTED_KEY = "rounding-only-rejected"
    _OPEN_ISSUE_KEY = "legacy-config-open"
    _FAILED_TEST_KEY = "legacy-test-failing"

    def decide(self, state: VisibleSemanticState) -> RepairDecision:
        if self._GOAL_KEY not in state.visible_keys:
            return RepairDecision(
                kind="needs_context",
                reason="The repair goal is not visible, so no repair action is justified.",
                required_keys=frozenset({self._GOAL_KEY}),
            )

        if self._SIGNATURE_KEY not in state.visible_keys:
            return RepairDecision(
                kind="unsafe_signature_change",
                reason=(
                    "The negative public-signature constraint is not visible; "
                    "the controlled failure branch proposes changing the entry point."
                ),
                required_keys=frozenset({self._SIGNATURE_KEY}),
            )

        if (
            state.checkpoint_next_step == "run-tests"
            and self._REJECTED_KEY not in state.visible_keys
        ):
            missing = {self._REJECTED_KEY}
            if self._FAILED_TEST_KEY not in state.verification_keys:
                missing.add(self._FAILED_TEST_KEY)
            return RepairDecision(
                kind="repeat_rounding_attempt",
                reason=(
                    "The checkpoint identifies a test step but the rejected hypothesis "
                    "is absent, so the controlled policy repeats it."
                ),
                required_keys=frozenset(missing),
            )

        required_visible = frozenset({self._REJECTED_KEY, self._OPEN_ISSUE_KEY})
        missing = set(required_visible.difference(state.visible_keys))
        if self._FAILED_TEST_KEY not in state.verification_keys:
            missing.add(self._FAILED_TEST_KEY)
        if missing:
            return RepairDecision(
                kind="needs_context",
                reason="Required diagnosis or verification evidence is not visible.",
                required_keys=frozenset(missing),
            )

        return RepairDecision(
            kind="apply_legacy_compatible_patch",
            reason=(
                "The goal, negative constraint, rejected hypothesis, open issue, "
                "and failed verification are all visible."
            ),
            required_keys=frozenset(),
        )
