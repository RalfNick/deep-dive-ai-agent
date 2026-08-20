"""Rebuild Chapter 5 context packets from a committed Chapter 6 boundary."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from chapter5.context.builder import ContextBuilder
from chapter5.context.contracts import (
    BuildConfig,
    ContextBuildTrace,
    ContextItem,
    ContextPacket,
    Provenance,
    Scope,
    Sensitivity,
)
from chapter5.context.trace import canonical_json

from .contracts import (
    CarryItem,
    CompactionArtifact,
    EventRecord,
    RunCheckpoint,
    WorkingSet,
)
from .trace import stable_digest


SourceEventResolver = Callable[[str, tuple[int, int]], Sequence[EventRecord]]


@dataclass(frozen=True)
class RehydrationInput:
    task_item: CarryItem
    checkpoint: RunCheckpoint
    artifact: CompactionArtifact
    working_set: WorkingSet
    current_user_items: tuple[CarryItem, ...]
    live_workspace_digest: str
    repository: str
    target_path: str


@dataclass(frozen=True)
class LifecycleTraceEntry:
    stage: str
    reason: str
    item_key: str | None
    source_digest: str


@dataclass(frozen=True)
class RehydrationResult:
    packet: ContextPacket
    trace: ContextBuildTrace
    stale_locators: tuple[str, ...]
    lifecycle_trace: tuple[LifecycleTraceEntry, ...]


@dataclass(frozen=True)
class _SelectedCarryItem:
    item: CarryItem
    origin: str


def _content_digest(content: str) -> str:
    """Use the digest algorithm published by Chapter 5's SourcePolicy."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _source_id(source_event_ids: tuple[str, ...]) -> str:
    """Encode all source IDs losslessly in Chapter 5's singular source field."""
    return canonical_json(source_event_ids)


def _artifact_items(artifact: CompactionArtifact) -> tuple[CarryItem, ...]:
    return (
        artifact.goal,
        *artifact.acceptance_criteria,
        *artifact.constraints,
        *artifact.decisions,
        *artifact.rejected_hypotheses,
        *artifact.open_issues,
        *artifact.verification_state,
        artifact.next_intent,
    )


def _trace_digest(item: CarryItem) -> str:
    return (
        "redacted"
        if item.sensitivity is Sensitivity.SECRET
        else _content_digest(item.content)
    )


class ContextRehydrator:
    """Validate a lifecycle boundary, then delegate packet policy to Chapter 5."""

    def __init__(
        self,
        *,
        builder: ContextBuilder | None = None,
        source_event_resolver: SourceEventResolver | None = None,
    ) -> None:
        self._builder = builder if builder is not None else ContextBuilder()
        self._source_event_resolver = source_event_resolver

    def rehydrate(
        self,
        input: RehydrationInput,
        config: BuildConfig,
    ) -> RehydrationResult:
        stale_locators = self._validate_boundary(input, config)
        selected_items, lifecycle = self._select_carry_items(input)
        context_items = tuple(
            self._adapt_item(
                selected.item,
                origin=selected.origin,
                input=input,
                config=config,
            )
            for selected in selected_items
        )

        build_result = self._builder.build(context_items, config)
        lifecycle.append(
            LifecycleTraceEntry(
                stage="packet",
                reason="packet_built",
                item_key=None,
                source_digest=build_result.packet.semantic_packet_digest,
            )
        )
        return RehydrationResult(
            packet=build_result.packet,
            trace=build_result.trace,
            stale_locators=stale_locators,
            lifecycle_trace=tuple((*self._locator_trace(input, stale_locators), *lifecycle)),
        )

    def _validate_boundary(
        self,
        input: RehydrationInput,
        config: BuildConfig,
    ) -> tuple[str, ...]:
        checkpoint = input.checkpoint
        artifact = input.artifact

        # The ordering here is deliberate: ContextBuilder must never see a
        # candidate from a stale or structurally invalid lifecycle boundary.
        if checkpoint.run_id != artifact.run_id:
            raise ValueError("checkpoint_run_mismatch")
        if checkpoint.artifact_id != artifact.artifact_id:
            raise ValueError("checkpoint_artifact_mismatch")

        if artifact.schema_version != "1.0":
            raise ValueError("artifact_rejected_schema")
        if not artifact.source_digest.strip():
            raise ValueError("artifact_rejected_source_digest")
        self._verify_source_digest(artifact)

        if checkpoint.event_cursor != artifact.source_event_range[1]:
            raise ValueError("stale_event_cursor")

        if artifact.workspace_digest != checkpoint.workspace_digest:
            raise ValueError("stale_artifact_workspace_digest")
        if checkpoint.workspace_digest != input.live_workspace_digest:
            raise ValueError("stale_workspace_digest")

        stale_locators = tuple(
            locator.locator_id
            for locator in artifact.evidence_locators
            if locator.workspace_digest != input.live_workspace_digest
        )

        if config.repository != input.repository or config.target_path != input.target_path:
            raise ValueError("rehydration_config_mismatch")
        return stale_locators

    def _verify_source_digest(self, artifact: CompactionArtifact) -> None:
        resolver = self._source_event_resolver
        if resolver is None:
            raise ValueError("artifact_source_unverifiable")
        try:
            events = tuple(resolver(artifact.run_id, artifact.source_event_range))
        except Exception as error:
            raise ValueError("artifact_source_unverifiable") from error
        if not events:
            raise ValueError("artifact_source_unverifiable")

        start, end = artifact.source_event_range
        sequences = tuple(event.sequence for event in events)
        event_ids = {event.event_id for event in events}
        referenced_event_ids = {
            event_id
            for item in _artifact_items(artifact)
            for event_id in item.source_event_ids
        }
        source_range_is_valid = (
            all(event.run_id == artifact.run_id for event in events)
            and sequences == tuple(sorted(sequences))
            and len(sequences) == len(set(sequences))
            and sequences[0] == start
            and sequences[-1] == end
            and all(start <= sequence <= end for sequence in sequences)
            and referenced_event_ids.issubset(event_ids)
        )
        if not source_range_is_valid:
            raise ValueError("artifact_source_range_mismatch")
        if stable_digest(events) != artifact.source_digest:
            raise ValueError("artifact_source_digest_mismatch")

    @staticmethod
    def _select_carry_items(
        input: RehydrationInput,
    ) -> tuple[tuple[_SelectedCarryItem, ...], list[LifecycleTraceEntry]]:
        selected: dict[str, _SelectedCarryItem] = {}
        lifecycle: list[LifecycleTraceEntry] = []

        for item in _artifact_items(input.artifact):
            selected[item.key] = _SelectedCarryItem(item, "artifact")

        live_items = (
            _SelectedCarryItem(input.task_item, "task_contract"),
            *(
                _SelectedCarryItem(item, "working_set")
                for item in input.working_set.carry_items
            ),
            *(
                _SelectedCarryItem(item, "current_user")
                for item in input.current_user_items
            ),
        )
        for candidate in live_items:
            previous = selected.get(candidate.item.key)
            if previous is not None and previous.item == candidate.item:
                continue
            if previous is not None and previous.origin == "artifact":
                lifecycle.append(
                    LifecycleTraceEntry(
                        stage="selection",
                        reason="artifact_rejected",
                        item_key=previous.item.key,
                        source_digest=(
                            "redacted"
                            if previous.item.sensitivity is Sensitivity.SECRET
                            else input.artifact.source_digest
                        ),
                    )
                )
            selected[candidate.item.key] = candidate

        for key in sorted(selected):
            candidate = selected[key]
            item = candidate.item
            origin = candidate.origin
            lifecycle.append(
                LifecycleTraceEntry(
                    stage="selection",
                    reason=f"selected_from_{origin}",
                    item_key=item.key,
                    source_digest=(
                        input.artifact.source_digest
                        if origin == "artifact" and item.sensitivity is not Sensitivity.SECRET
                        else _trace_digest(item)
                    ),
                )
            )
        return tuple(selected[key] for key in sorted(selected)), lifecycle

    @staticmethod
    def _adapt_item(
        item: CarryItem,
        *,
        origin: str,
        input: RehydrationInput,
        config: BuildConfig,
    ) -> ContextItem:
        """Adapt identity fields without reclassifying or increasing authority."""
        return ContextItem(
            item_id=item.key,
            kind=item.kind,
            content=item.content,
            scope=Scope(
                repository=input.repository,
                path_prefix=input.target_path,
                task_id=config.task_id,
            ),
            authority=item.authority,
            trust=item.trust,
            retention_priority=item.retention_priority,
            sensitivity=item.sensitivity,
            provenance=Provenance(
                source_type=origin,
                source_id=_source_id(item.source_event_ids),
                version=ContextRehydrator._provenance_version(origin, input),
                observed_at=(
                    input.artifact.created_at if origin == "artifact" else None
                ),
                content_digest=_content_digest(item.content),
            ),
            required_for=item.required_for,
        )

    @staticmethod
    def _provenance_version(origin: str, input: RehydrationInput) -> str | None:
        if origin == "artifact":
            return input.artifact.schema_version
        if origin in {"task_contract", "working_set"}:
            return input.checkpoint.checkpoint_id
        return None

    @staticmethod
    def _locator_trace(
        input: RehydrationInput,
        stale_locators: tuple[str, ...],
    ) -> tuple[LifecycleTraceEntry, ...]:
        stale = set(stale_locators)
        return tuple(
            LifecycleTraceEntry(
                stage="workspace",
                reason="locator_stale",
                item_key=locator.locator_id,
                source_digest=locator.content_digest,
            )
            for locator in input.artifact.evidence_locators
            if locator.locator_id in stale
        )
