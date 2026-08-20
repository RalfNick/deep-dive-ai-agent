"""Canonical long-running price repair trajectory.

The fixture is deliberately verbose and explicit: each event is a named record
that can be reviewed in sequence.  It is not a generated workload and it does
not pretend to sample a language model.  Events 1--24 form the compaction input;
events 25--30 describe the deterministic resume path used in later experiments.
"""

from __future__ import annotations

from chapter5.context.contracts import (
    ContextKind,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)
from chapter6.context_continuity.contracts import (
    CarryItem,
    CompactionSeed,
    EventRecord,
    EventType,
)


CANONICAL_RUN_ID = "run-price-repair"
CANONICAL_WORKSPACE_DIGEST = "workspace-price-v1"
CANONICAL_RESUMED_WORKSPACE_DIGEST = "workspace-price-v2"
CANONICAL_COMPACTION_CURSOR = 24

# Reviewed and frozen with the explicit declarations below.  Changing any event
# is an intentional fixture-version change and must update its invariant test.
CANONICAL_TRAJECTORY_DIGEST = (
    "9b365ed494f07a6598d2213bc9f4d89d775706d44bc6864691a78b4a058a9919"
)


def _carry(
    key: str,
    kind: ContextKind,
    content: str,
    source_event_id: str,
    *,
    authority: InstructionAuthority = InstructionAuthority.NONE,
    trust: TrustLevel = TrustLevel.VERIFIED,
    priority: RetentionPriority = RetentionPriority.NORMAL,
    required_for: frozenset[str] = frozenset(),
) -> CarryItem:
    return CarryItem(
        key=key,
        kind=kind,
        content=content,
        authority=authority,
        trust=trust,
        retention_priority=priority,
        sensitivity=Sensitivity.INTERNAL,
        source_event_ids=(source_event_id,),
        required_for=required_for,
    )


def canonical_trajectory() -> tuple[EventRecord, ...]:
    """Return the reviewed 30-event trajectory in canonical sequence order."""

    return (
        EventRecord(
            event_id="evt-001",
            run_id=CANONICAL_RUN_ID,
            sequence=1,
            event_type=EventType.TASK,
            carry_items=(
                _carry(
                    "repair-price",
                    ContextKind.TASK,
                    "Repair price calculation while preserving compatibility and add regression coverage.",
                    "evt-001",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"goal"}),
                ),
                _carry(
                    "decimal-result",
                    ContextKind.FACT,
                    "Calculated prices must remain exact Decimal values at the currency boundary.",
                    "evt-001",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"price-correctness"}),
                ),
            ),
            payload_ref="TASK.md",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-002",
            run_id=CANONICAL_RUN_ID,
            sequence=2,
            event_type=EventType.USER_UPDATE,
            carry_items=(
                _carry(
                    "public-signature",
                    ContextKind.INSTRUCTION,
                    "Do not change the public calculate_price(config, amount) signature.",
                    "evt-002",
                    authority=InstructionAuthority.USER,
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"public-signature"}),
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-003",
            run_id=CANONICAL_RUN_ID,
            sequence=3,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "pricing-source-located",
                    ContextKind.OBSERVATION,
                    "The price calculation entry point is implemented in src/pricing.py.",
                    "evt-003",
                ),
            ),
            payload_ref="src/pricing.py",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-004",
            run_id=CANONICAL_RUN_ID,
            sequence=4,
            event_type=EventType.OBSERVATION,
            carry_items=(
                _carry(
                    "decimal-normalization-observed",
                    ContextKind.OBSERVATION,
                    "The current implementation quantizes only the final amount and bypasses legacy rate normalization.",
                    "evt-004",
                ),
            ),
            payload_ref="src/pricing.py#L18-L31",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-005",
            run_id=CANONICAL_RUN_ID,
            sequence=5,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "pricing-tests-located",
                    ContextKind.OBSERVATION,
                    "Existing tests cover current configuration but not the legacy string-rate shape.",
                    "evt-005",
                ),
            ),
            payload_ref="tests/test_pricing.py",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-006",
            run_id=CANONICAL_RUN_ID,
            sequence=6,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "regression-coverage",
                    ContextKind.FACT,
                    "Acceptance requires a regression test for the discovered compatibility failure.",
                    "evt-006",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"regression-test"}),
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-007",
            run_id=CANONICAL_RUN_ID,
            sequence=7,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "rounding-only-hypothesis",
                    ContextKind.OBSERVATION,
                    "Hypothesis: moving quantize into the final return is sufficient.",
                    "evt-007",
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-008",
            run_id=CANONICAL_RUN_ID,
            sequence=8,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "rounding-probe-planned",
                    ContextKind.TASK,
                    "Apply a reversible rounding-only probe, then run focused tests.",
                    "evt-008",
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-009",
            run_id=CANONICAL_RUN_ID,
            sequence=9,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "rounding-probe-applied",
                    ContextKind.ARTIFACT,
                    "A reversible rounding-only change was applied to the working tree.",
                    "evt-009",
                ),
            ),
            payload_ref="src/pricing.py",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-010",
            run_id=CANONICAL_RUN_ID,
            sequence=10,
            event_type=EventType.VERIFICATION,
            carry_items=(
                _carry(
                    "current-tests-passing",
                    ContextKind.OBSERVATION,
                    "Focused tests for current configuration pass after the probe.",
                    "evt-010",
                ),
            ),
            payload_ref="tests/test_pricing.py::test_current_config",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-011",
            run_id=CANONICAL_RUN_ID,
            sequence=11,
            event_type=EventType.OBSERVATION,
            carry_items=(
                _carry(
                    "legacy-reference-found",
                    ContextKind.OBSERVATION,
                    "Repository search finds a legacy pricing fixture referenced by migration tests.",
                    "evt-011",
                ),
            ),
            payload_ref="tests/test_migrations.py",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-012",
            run_id=CANONICAL_RUN_ID,
            sequence=12,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "legacy-fixture-read",
                    ContextKind.OBSERVATION,
                    "The legacy fixture stores rate and precision as strings.",
                    "evt-012",
                ),
            ),
            payload_ref="fixtures/legacy-pricing.json",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-013",
            run_id=CANONICAL_RUN_ID,
            sequence=13,
            event_type=EventType.OBSERVATION,
            carry_items=(
                _carry(
                    "legacy-compatibility",
                    ContextKind.FACT,
                    "Acceptance requires legacy string rate and precision configuration to remain supported.",
                    "evt-013",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"legacy-compatibility"}),
                ),
            ),
            payload_ref="fixtures/legacy-pricing.json",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-014",
            run_id=CANONICAL_RUN_ID,
            sequence=14,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "legacy-test-added",
                    ContextKind.ARTIFACT,
                    "A regression test was added for the legacy string configuration.",
                    "evt-014",
                ),
            ),
            payload_ref="tests/test_pricing.py",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-015",
            run_id=CANONICAL_RUN_ID,
            sequence=15,
            event_type=EventType.VERIFICATION,
            carry_items=(
                _carry(
                    "legacy-config-open",
                    ContextKind.OBSERVATION,
                    "The new legacy configuration regression remains unresolved.",
                    "evt-015",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"legacy-compatibility"}),
                ),
                _carry(
                    "legacy-test-failing",
                    ContextKind.OBSERVATION,
                    "test_legacy_string_config fails because string precision reaches Decimal.quantize unchanged.",
                    "evt-015",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"verification"}),
                ),
            ),
            payload_ref="tests/test_pricing.py::test_legacy_string_config",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-016",
            run_id=CANONICAL_RUN_ID,
            sequence=16,
            event_type=EventType.OBSERVATION,
            carry_items=(
                _carry(
                    "failure-trace-read",
                    ContextKind.OBSERVATION,
                    "The failure trace points to configuration normalization, not final rounding.",
                    "evt-016",
                ),
            ),
            payload_ref="reports/legacy-test-failure.txt",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-017",
            run_id=CANONICAL_RUN_ID,
            sequence=17,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "rounding-only-rejected",
                    ContextKind.OBSERVATION,
                    "Rejected: a rounding-only change cannot normalize legacy string configuration.",
                    "evt-017",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"avoid-duplicate-work"}),
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-018",
            run_id=CANONICAL_RUN_ID,
            sequence=18,
            event_type=EventType.USER_UPDATE,
            carry_items=(
                _carry(
                    "user-clarification",
                    ContextKind.INSTRUCTION,
                    "Legacy configuration must keep working; callers cannot be migrated in this task.",
                    "evt-018",
                    authority=InstructionAuthority.USER,
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"legacy-compatibility"}),
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-019",
            run_id=CANONICAL_RUN_ID,
            sequence=19,
            event_type=EventType.OBSERVATION,
            carry_items=(
                _carry(
                    "normalization-root-cause",
                    ContextKind.OBSERVATION,
                    "Root cause: the legacy branch bypasses shared Decimal normalization.",
                    "evt-019",
                    priority=RetentionPriority.HIGH,
                ),
            ),
            payload_ref="src/pricing.py#L22-L29",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-020",
            run_id=CANONICAL_RUN_ID,
            sequence=20,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "config-normalizer-located",
                    ContextKind.OBSERVATION,
                    "normalize_config can accept both typed and legacy string fields without changing the public entry point.",
                    "evt-020",
                ),
            ),
            payload_ref="src/config.py#L7-L26",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-021",
            run_id=CANONICAL_RUN_ID,
            sequence=21,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "preserve-decimal-path",
                    ContextKind.FACT,
                    "Normalize rate and precision to Decimal-compatible values before calculation.",
                    "evt-021",
                    priority=RetentionPriority.HIGH,
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-022",
            run_id=CANONICAL_RUN_ID,
            sequence=22,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "compatible-patch-plan",
                    ContextKind.TASK,
                    "Patch internal normalization, preserve calculate_price signature, then rerun legacy and full tests.",
                    "evt-022",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"next-action"}),
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-023",
            run_id=CANONICAL_RUN_ID,
            sequence=23,
            event_type=EventType.OBSERVATION,
            carry_items=(
                _carry(
                    "workspace-locator",
                    ContextKind.ARTIFACT,
                    "Workspace price-repair at digest workspace-price-v1 contains the uncommitted regression test.",
                    "evt-023",
                    priority=RetentionPriority.HIGH,
                ),
            ),
            payload_ref="workspace://price-repair",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-024",
            run_id=CANONICAL_RUN_ID,
            sequence=24,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "next-intent",
                    ContextKind.TASK,
                    "Apply the legacy-compatible normalization patch without changing the public signature.",
                    "evt-024",
                    priority=RetentionPriority.REQUIRED,
                    required_for=frozenset({"next-action"}),
                ),
                _carry(
                    "compaction-boundary",
                    ContextKind.OBSERVATION,
                    "Checkpoint boundary frozen after diagnosis and before the compatible patch.",
                    "evt-024",
                    priority=RetentionPriority.HIGH,
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-025",
            run_id=CANONICAL_RUN_ID,
            sequence=25,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "resume-artifact-loaded",
                    ContextKind.OBSERVATION,
                    "The committed compaction artifact was loaded and its source digest verified.",
                    "evt-025",
                ),
            ),
            payload_ref="artifact://price-repair/cmp-024",
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-026",
            run_id=CANONICAL_RUN_ID,
            sequence=26,
            event_type=EventType.DECISION,
            carry_items=(
                _carry(
                    "checkpoint-resumed",
                    ContextKind.OBSERVATION,
                    "Execution resumed at apply-compatible-patch with the unresolved legacy failure visible.",
                    "evt-026",
                ),
            ),
            workspace_digest=CANONICAL_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-027",
            run_id=CANONICAL_RUN_ID,
            sequence=27,
            event_type=EventType.TOOL_RESULT,
            carry_items=(
                _carry(
                    "compatible-patch-applied",
                    ContextKind.ARTIFACT,
                    "Internal configuration normalization was patched without changing calculate_price.",
                    "evt-027",
                ),
            ),
            payload_ref="src/config.py",
            workspace_digest=CANONICAL_RESUMED_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-028",
            run_id=CANONICAL_RUN_ID,
            sequence=28,
            event_type=EventType.VERIFICATION,
            carry_items=(
                _carry(
                    "legacy-test-passing",
                    ContextKind.OBSERVATION,
                    "The legacy string configuration regression test passes.",
                    "evt-028",
                    priority=RetentionPriority.REQUIRED,
                ),
            ),
            payload_ref="tests/test_pricing.py::test_legacy_string_config",
            workspace_digest=CANONICAL_RESUMED_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-029",
            run_id=CANONICAL_RUN_ID,
            sequence=29,
            event_type=EventType.VERIFICATION,
            carry_items=(
                _carry(
                    "full-suite-passing",
                    ContextKind.OBSERVATION,
                    "The complete deterministic fixture suite passes.",
                    "evt-029",
                    priority=RetentionPriority.REQUIRED,
                ),
            ),
            payload_ref="tests/",
            workspace_digest=CANONICAL_RESUMED_WORKSPACE_DIGEST,
        ),
        EventRecord(
            event_id="evt-030",
            run_id=CANONICAL_RUN_ID,
            sequence=30,
            event_type=EventType.VERIFICATION,
            carry_items=(
                _carry(
                    "repair-complete",
                    ContextKind.OBSERVATION,
                    "Verification evidence satisfies compatibility, signature, and regression criteria.",
                    "evt-030",
                    priority=RetentionPriority.HIGH,
                ),
            ),
            workspace_digest=CANONICAL_RESUMED_WORKSPACE_DIGEST,
        ),
    )


def canonical_seed() -> CompactionSeed:
    """Return the semantic retention contract for events 1--24."""

    return CompactionSeed(
        run_id=CANONICAL_RUN_ID,
        goal_key="repair-price",
        acceptance_keys=frozenset(
            {"decimal-result", "legacy-compatibility", "regression-coverage"}
        ),
        constraint_keys=frozenset({"public-signature", "user-clarification"}),
        decision_keys=frozenset(
            {"compatible-patch-plan", "preserve-decimal-path"}
        ),
        rejected_hypothesis_keys=frozenset({"rounding-only-rejected"}),
        open_issue_keys=frozenset({"legacy-config-open"}),
        verification_keys=frozenset({"legacy-test-failing"}),
        required_keys=frozenset(
            {
                "repair-price",
                "decimal-result",
                "legacy-compatibility",
                "regression-coverage",
                "public-signature",
                "user-clarification",
                "compatible-patch-plan",
                "preserve-decimal-path",
                "rounding-only-rejected",
                "legacy-config-open",
                "legacy-test-failing",
                "next-intent",
            }
        ),
    )
