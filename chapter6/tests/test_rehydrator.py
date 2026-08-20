import hashlib
import unittest
from collections.abc import Sequence
from dataclasses import fields, replace

from chapter5.context.builder import ContextBuilder
from chapter5.context.contracts import (
    BuildConfig,
    BuildResult,
    ContextBuildTrace,
    ContextItem,
    ContextKind,
    ContextPacket,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)
from chapter6.context_continuity.contracts import (
    CarryItem,
    CompactionArtifact,
    CompactionSeed,
    EventRecord,
    EventType,
    RunCheckpoint,
    WorkingSet,
)
from chapter6.context_continuity.compaction import StructuredCompactionStrategy
from chapter6.context_continuity.rehydrator import (
    ContextRehydrator,
    RehydrationInput,
    RehydrationResult,
    SourceEventResolver,
)


def public_signature_constraint() -> CarryItem:
    return CarryItem(
        key="constraint-public-signature",
        kind=ContextKind.INSTRUCTION,
        content="do not change the public signature",
        authority=InstructionAuthority.USER,
        trust=TrustLevel.VERIFIED,
        retention_priority=RetentionPriority.REQUIRED,
        sensitivity=Sensitivity.INTERNAL,
        source_event_ids=("evt-002",),
        required_for=frozenset({"public-signature"}),
    )


def valid_source_events() -> tuple[EventRecord, ...]:
    base = CompactionArtifact.minimal_for_test()
    next_intent = replace(base.next_intent, key="next-intent")
    return (
        EventRecord(
            "evt-001",
            base.run_id,
            1,
            EventType.TASK,
            (base.goal,),
            workspace_digest=base.workspace_digest,
        ),
        EventRecord(
            "evt-002",
            base.run_id,
            2,
            EventType.OBSERVATION,
            (public_signature_constraint(),),
            workspace_digest=base.workspace_digest,
        ),
        EventRecord(
            "evt-004",
            base.run_id,
            4,
            EventType.OBSERVATION,
            base.acceptance_criteria,
            workspace_digest=base.workspace_digest,
        ),
        EventRecord(
            "evt-018",
            base.run_id,
            18,
            EventType.OBSERVATION,
            base.open_issues,
            payload_ref="tests/test_pricing.py",
            workspace_digest=base.workspace_digest,
        ),
        EventRecord(
            "evt-020",
            base.run_id,
            20,
            EventType.TASK,
            (next_intent,),
            workspace_digest=base.workspace_digest,
        ),
    )


def resolver_for(events: tuple[EventRecord, ...]) -> SourceEventResolver:
    return lambda _run_id, _event_range: events


def valid_rehydration_input_and_config() -> tuple[RehydrationInput, BuildConfig]:
    events = valid_source_events()
    seed = CompactionSeed(
        run_id="run-price",
        goal_key="repair-price",
        acceptance_keys=frozenset({"legacy-config"}),
        constraint_keys=frozenset({"constraint-public-signature"}),
        decision_keys=frozenset(),
        rejected_hypothesis_keys=frozenset(),
        open_issue_keys=frozenset({"legacy-config-open"}),
        verification_keys=frozenset(),
        required_keys=frozenset(
            {
                "repair-price",
                "legacy-config",
                "constraint-public-signature",
                "legacy-config-open",
                "next-intent",
            }
        ),
    )
    artifact = StructuredCompactionStrategy().prepare(events, seed).artifact
    assert artifact is not None
    checkpoint = RunCheckpoint(
        run_id="run-price",
        checkpoint_id="ckpt-020",
        next_step="apply-compatible-patch",
        completed_steps=("inspect", "reject-rounding-only"),
        pending_step="apply-compatible-patch",
        event_cursor=20,
        workspace_digest="workspace-v1",
        artifact_id=artifact.artifact_id,
    )
    data = RehydrationInput(
        task_item=artifact.goal,
        checkpoint=checkpoint,
        artifact=artifact,
        working_set=WorkingSet(event_ids=(), carry_items=(), max_serialized_bytes=0),
        current_user_items=(),
        live_workspace_digest="workspace-v1",
        repository="price-fixture",
        target_path="pricing.py",
    )
    config = BuildConfig.for_task(
        "price-fixture",
        "pricing.py",
        "repair-price",
        budget_units=12_000,
        expected_requirements=frozenset({"goal", "legacy-config"}),
    )
    return data, config


def build_valid_rehydration_result() -> RehydrationResult:
    data, config = valid_rehydration_input_and_config()
    return ContextRehydrator(
        source_event_resolver=resolver_for(valid_source_events())
    ).rehydrate(data, config)


class ContextRehydratorTest(unittest.TestCase):
    def test_rehydrator_returns_chapter5_packet(self) -> None:
        result = build_valid_rehydration_result()
        self.assertIsInstance(result.packet, ContextPacket)
        self.assertIn("constraint-public-signature", result.packet.selected_item_ids)
        self.assertEqual(result.packet.missing_requirements, ())

    def test_workspace_digest_mismatch_fails_before_packet_build(self) -> None:
        data, config = valid_rehydration_input_and_config()
        stale = replace(data, live_workspace_digest="workspace-new")
        with self.assertRaisesRegex(ValueError, "stale_workspace_digest"):
            ContextRehydrator(
                source_event_resolver=resolver_for(valid_source_events())
            ).rehydrate(stale, config)

    def test_rehydrator_reuses_chapter5_trace_contract(self) -> None:
        result = build_valid_rehydration_result()

        self.assertIsInstance(result.trace, ContextBuildTrace)

    def test_artifact_constraint_preserves_authority_and_source_identity(self) -> None:
        data, config = valid_rehydration_input_and_config()
        builder = CapturingBuilder()

        result = ContextRehydrator(
            builder=builder,
            source_event_resolver=resolver_for(valid_source_events()),
        ).rehydrate(data, config)

        source = data.artifact.constraints[0]
        adapted = next(item for item in builder.items if item.item_id == source.key)
        self.assertEqual(adapted.authority, source.authority)
        self.assertEqual(adapted.required_for, source.required_for)
        self.assertEqual(adapted.provenance.source_id, '["evt-002"]')
        self.assertEqual(adapted.provenance.source_type, "artifact")
        self.assertEqual(adapted.provenance.version, data.artifact.schema_version)
        self.assertEqual(adapted.provenance.observed_at, data.artifact.created_at)
        self.assertIn(source.key, result.packet.selected_item_ids)
        reasons = {entry.reason for entry in result.lifecycle_trace}
        self.assertTrue(
            {
                "packet_built",
                "selected_from_artifact",
            }.issubset(reasons)
        )

    def test_carry_item_adapter_preserves_policy_and_source_identity(self) -> None:
        data, config = valid_rehydration_input_and_config()
        carry = CarryItem(
            key="keep-user-boundary",
            kind=ContextKind.INSTRUCTION,
            content="keep the exact user boundary",
            authority=InstructionAuthority.USER,
            trust=TrustLevel.UNVERIFIED,
            retention_priority=RetentionPriority.LOW,
            sensitivity=Sensitivity.SECRET,
            source_event_ids=("evt-021", "evt-022"),
            required_for=frozenset({"user-boundary"}),
        )
        capturing_builder = CapturingBuilder()

        result = ContextRehydrator(
            builder=capturing_builder,
            source_event_resolver=resolver_for(valid_source_events()),
        ).rehydrate(
            replace(data, working_set=WorkingSet(("evt-021", "evt-022"), (carry,), 500)),
            config,
        )

        adapted = next(item for item in capturing_builder.items if item.item_id == carry.key)
        self.assertEqual(adapted.kind, carry.kind)
        self.assertEqual(adapted.authority, carry.authority)
        self.assertEqual(adapted.trust, carry.trust)
        self.assertEqual(adapted.retention_priority, carry.retention_priority)
        self.assertEqual(adapted.sensitivity, carry.sensitivity)
        self.assertEqual(adapted.required_for, carry.required_for)
        self.assertEqual(adapted.provenance.source_id, '["evt-021","evt-022"]')
        self.assertEqual(
            adapted.provenance.content_digest,
            hashlib.sha256(carry.content.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(adapted.provenance.source_type, "working_set")
        self.assertEqual(adapted.provenance.version, data.checkpoint.checkpoint_id)
        self.assertIsNone(adapted.provenance.observed_at)
        working_entry = next(
            entry for entry in result.lifecycle_trace if entry.item_key == carry.key
        )
        self.assertEqual(working_entry.reason, "selected_from_working_set")

    def test_stale_locator_is_reported_before_building_packet(self) -> None:
        data, config = valid_rehydration_input_and_config()
        stale_artifact = replace(
            data.artifact,
            evidence_locators=(
                replace(
                    data.artifact.evidence_locators[0],
                    workspace_digest="workspace-old",
                ),
            ),
        )

        result = ContextRehydrator(
            source_event_resolver=resolver_for(valid_source_events())
        ).rehydrate(replace(data, artifact=stale_artifact), config)

        self.assertEqual(
            result.stale_locators,
            (data.artifact.evidence_locators[0].locator_id,),
        )
        self.assertIn("locator_stale", {entry.reason for entry in result.lifecycle_trace})

    def test_invalid_boundary_is_rejected_before_builder_call(self) -> None:
        data, config = valid_rehydration_input_and_config()
        builder = CapturingBuilder()

        with self.assertRaisesRegex(ValueError, "checkpoint_run_mismatch"):
            ContextRehydrator(builder=builder).rehydrate(
                replace(data, checkpoint=replace(data.checkpoint, run_id="run-other")),
                config,
            )

        self.assertEqual(builder.items, ())

    def test_lifecycle_trace_contract_cannot_copy_secret_content(self) -> None:
        data, config = valid_rehydration_input_and_config()
        secret_value = "fixture-secret-that-must-not-appear"
        secret = CarryItem(
            key="api-token",
            kind=ContextKind.FACT,
            content=secret_value,
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.VERIFIED,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.SECRET,
            source_event_ids=("evt-secret",),
        )

        result = ContextRehydrator(
            source_event_resolver=resolver_for(valid_source_events())
        ).rehydrate(
            replace(data, working_set=WorkingSet(("evt-secret",), (secret,), 500)),
            config,
        )

        self.assertNotIn("content", {field.name for field in fields(result.lifecycle_trace[0])})
        self.assertNotIn(secret_value, repr(result.lifecycle_trace))
        secret_entry = next(
            entry for entry in result.lifecycle_trace if entry.item_key == "api-token"
        )
        self.assertEqual(secret_entry.source_digest, "redacted")

    def test_missing_source_event_resolver_fails_closed_before_builder(self) -> None:
        data, config = valid_rehydration_input_and_config()
        builder = CapturingBuilder()

        with self.assertRaisesRegex(ValueError, "artifact_source_unverifiable"):
            ContextRehydrator(builder=builder).rehydrate(data, config)

        self.assertEqual(builder.items, ())

    def test_tampered_source_digest_fails_before_builder(self) -> None:
        data, config = valid_rehydration_input_and_config()
        events = valid_source_events()
        tampered = replace(
            data,
            artifact=replace(data.artifact, source_digest="tampered-source-digest"),
        )
        builder = CapturingBuilder()

        with self.assertRaisesRegex(ValueError, "artifact_source_digest_mismatch"):
            ContextRehydrator(
                builder=builder,
                source_event_resolver=resolver_for(events),
            ).rehydrate(tampered, config)

        self.assertEqual(builder.items, ())

    def test_identical_task_and_artifact_item_does_not_reject_artifact(self) -> None:
        data, config = valid_rehydration_input_and_config()

        result = ContextRehydrator(
            source_event_resolver=resolver_for(valid_source_events())
        ).rehydrate(data, config)

        goal_entries = [
            entry for entry in result.lifecycle_trace if entry.item_key == data.task_item.key
        ]
        self.assertEqual(
            [entry.reason for entry in goal_entries],
            ["selected_from_artifact"],
        )

    def test_materially_changed_task_rejects_artifact_goal(self) -> None:
        data, config = valid_rehydration_input_and_config()
        changed_task = replace(
            data.task_item,
            content="repair price calculation under the current request",
            source_event_ids=("evt-021",),
        )
        builder = CapturingBuilder()

        result = ContextRehydrator(
            builder=builder,
            source_event_resolver=resolver_for(valid_source_events()),
        ).rehydrate(replace(data, task_item=changed_task), config)

        goal_reasons = {
            entry.reason
            for entry in result.lifecycle_trace
            if entry.item_key == changed_task.key
        }
        self.assertEqual(
            goal_reasons,
            {"artifact_rejected", "selected_from_task_contract"},
        )
        adapted = next(item for item in builder.items if item.item_id == changed_task.key)
        self.assertEqual(adapted.provenance.source_type, "task_contract")
        self.assertEqual(adapted.provenance.version, data.checkpoint.checkpoint_id)
        self.assertIsNone(adapted.provenance.observed_at)

    def test_current_user_origin_has_distinct_trace_and_provenance(self) -> None:
        data, config = valid_rehydration_input_and_config()
        current_user = CarryItem(
            key="current-user-update",
            kind=ContextKind.TASK,
            content="also preserve decimal compatibility",
            authority=InstructionAuthority.NONE,
            trust=TrustLevel.TRUSTED_SOURCE,
            retention_priority=RetentionPriority.REQUIRED,
            sensitivity=Sensitivity.INTERNAL,
            source_event_ids=("evt-user-001",),
        )
        builder = CapturingBuilder()

        result = ContextRehydrator(
            builder=builder,
            source_event_resolver=resolver_for(valid_source_events()),
        ).rehydrate(replace(data, current_user_items=(current_user,)), config)

        current_entry = next(
            entry for entry in result.lifecycle_trace if entry.item_key == current_user.key
        )
        self.assertEqual(current_entry.reason, "selected_from_current_user")
        adapted = next(item for item in builder.items if item.item_id == current_user.key)
        self.assertEqual(adapted.provenance.source_type, "current_user")
        self.assertIsNone(adapted.provenance.version)
        self.assertIsNone(adapted.provenance.observed_at)


class CapturingBuilder(ContextBuilder):
    def __init__(self) -> None:
        self.items: tuple[ContextItem, ...] = ()

    def build(
        self,
        items: Sequence[ContextItem],
        config: BuildConfig,
    ) -> BuildResult:
        self.items = tuple(items)
        return super().build(items, config)


if __name__ == "__main__":
    unittest.main()
