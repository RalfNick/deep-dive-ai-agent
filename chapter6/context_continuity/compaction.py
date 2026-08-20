"""Deterministic teaching strategies for comparing context compaction loss."""

from __future__ import annotations

from collections.abc import Iterable

from chapter5.context.contracts import (
    ContextKind,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)

from .contracts import (
    CarryItem,
    CompactionArtifact,
    CompactionSeed,
    EventRecord,
    EvidenceLocator,
    StrategyOutput,
)
from .trace import serialized_bytes, stable_digest


TEACHING_BYTE_BUDGET = 1_024
_FIXED_CREATED_AT = "1970-01-01T00:00:00Z"


def _validate_events(events: tuple[EventRecord, ...], seed: CompactionSeed) -> None:
    if any(event.run_id != seed.run_id for event in events):
        raise ValueError("compaction_run_mismatch")
    sequences = tuple(event.sequence for event in events)
    if sequences != tuple(sorted(sequences)) or len(sequences) != len(set(sequences)):
        raise ValueError("unordered_compaction_events")


def _event_bytes(events: tuple[EventRecord, ...]) -> int:
    return serialized_bytes(events)


def _event_items(events: Iterable[EventRecord]) -> tuple[CarryItem, ...]:
    return tuple(item for event in events for item in event.carry_items)


def _latest_items_by_key(events: tuple[EventRecord, ...]) -> dict[str, CarryItem]:
    items: dict[str, CarryItem] = {}
    for event in events:
        for item in event.carry_items:
            items[item.key] = item
    return items


def _summary_next_intent(events: tuple[EventRecord, ...]) -> CarryItem:
    if not events:
        raise ValueError("compaction_requires_events")
    return CarryItem(
        key="next-intent",
        kind=ContextKind.TASK,
        content="continue the recorded work from the compacted boundary",
        authority=InstructionAuthority.NONE,
        trust=TrustLevel.VERIFIED,
        retention_priority=RetentionPriority.HIGH,
        sensitivity=Sensitivity.INTERNAL,
        source_event_ids=(events[-1].event_id,),
    )


def _latest_declared_decision(
    events: tuple[EventRecord, ...], decision_keys: frozenset[str]
) -> CarryItem | None:
    for event in reversed(events):
        for item in reversed(event.carry_items):
            if item.key in decision_keys:
                return item
    return None


class AppendAllStrategy:
    """Keep every canonical event record until the teaching budget is exceeded."""

    strategy = "append-all-v1"

    def prepare(self, events: tuple[EventRecord, ...], seed: CompactionSeed) -> StrategyOutput:
        _validate_events(events, seed)
        byte_count = _event_bytes(events)
        items = _event_items(events)
        return StrategyOutput(
            strategy=self.strategy,
            visible_keys=frozenset(item.key for item in items),
            context_items=items,
            artifact=None,
            serialized_bytes_before=byte_count,
            serialized_bytes_after=byte_count,
            overflowed=byte_count > TEACHING_BYTE_BUDGET,
            dropped_event_ids=(),
        )


class SlidingWindowStrategy:
    """Keep only the newest complete events, exposing deliberate window loss."""

    strategy = "sliding-window-v1"

    def __init__(self, keep_events: int) -> None:
        if keep_events < 0:
            raise ValueError("negative_keep_events")
        self.keep_events = keep_events

    def prepare(self, events: tuple[EventRecord, ...], seed: CompactionSeed) -> StrategyOutput:
        _validate_events(events, seed)
        retained = events[-self.keep_events :] if self.keep_events else ()
        items = _event_items(retained)
        after = _event_bytes(retained)
        return StrategyOutput(
            strategy=self.strategy,
            visible_keys=frozenset(item.key for item in items),
            context_items=items,
            artifact=None,
            serialized_bytes_before=_event_bytes(events),
            serialized_bytes_after=after,
            overflowed=after > TEACHING_BYTE_BUDGET,
            dropped_event_ids=tuple(event.event_id for event in events[: len(events) - len(retained)]),
        )


class ParagraphSummaryStrategy:
    """A controlled loss baseline, intentionally not a model-generated summary.

    The fixed rule retains only the goal, latest declared decision, and a generic
    next intent.  It intentionally discards constraints, rejected hypotheses,
    open issues, and evidence locator metadata so graders can observe that loss.
    """

    strategy = "summary-only-v1"

    def prepare(self, events: tuple[EventRecord, ...], seed: CompactionSeed) -> StrategyOutput:
        _validate_events(events, seed)
        items_by_key = _latest_items_by_key(events)
        goal = items_by_key.get(seed.goal_key)
        if goal is None:
            raise ValueError("missing_goal_carry_item")

        latest_decision = _latest_declared_decision(events, seed.decision_keys)
        decisions = (latest_decision,) if latest_decision is not None else ()
        summary_items = (goal, *decisions, _summary_next_intent(events))
        visible_keys = frozenset((goal.key, *(item.key for item in decisions)))
        return StrategyOutput(
            strategy=self.strategy,
            visible_keys=visible_keys,
            context_items=summary_items,
            artifact=None,
            serialized_bytes_before=_event_bytes(events),
            serialized_bytes_after=serialized_bytes(summary_items),
            overflowed=serialized_bytes(summary_items) > TEACHING_BYTE_BUDGET,
            dropped_event_ids=tuple(event.event_id for event in events if event.event_id != goal.source_event_ids[0]),
        )


def _seed_categories(seed: CompactionSeed) -> tuple[tuple[str, frozenset[str]], ...]:
    return (
        ("acceptance", seed.acceptance_keys),
        ("constraints", seed.constraint_keys),
        ("decisions", seed.decision_keys),
        ("rejected", seed.rejected_hypothesis_keys),
        ("open", seed.open_issue_keys),
        ("verification", seed.verification_keys),
    )


def _partition_items(
    items_by_key: dict[str, CarryItem], seed: CompactionSeed
) -> dict[str, tuple[CarryItem, ...]]:
    missing_required = seed.required_keys.difference(items_by_key)
    if missing_required:
        raise ValueError("missing_required_carry_items")
    goal = items_by_key.get(seed.goal_key)
    if goal is None:
        raise ValueError("missing_goal_carry_item")

    existing_next_intent = items_by_key.get("next-intent")
    assigned = {seed.goal_key}
    if existing_next_intent is not None:
        assigned.add(existing_next_intent.key)
    result: dict[str, tuple[CarryItem, ...]] = {}
    for category, keys in _seed_categories(seed):
        category_keys = keys.difference({"next-intent"}) if existing_next_intent is not None else keys
        duplicate = assigned.intersection(category_keys)
        if duplicate:
            raise ValueError("overlapping_compaction_seed_keys")
        assigned.update(category_keys)
        result[category] = tuple(
            items_by_key[key] for key in sorted(category_keys) if key in items_by_key
        )

    required_without_category = seed.required_keys.difference(assigned)
    if required_without_category:
        raise ValueError("required_carry_item_without_category")
    result["goal"] = (goal,)
    result["next_intent"] = (existing_next_intent,) if existing_next_intent is not None else ()
    return result


def _locator_content_digest(event: EventRecord) -> str:
    """Digest the available payload identity rather than its reference string.

    ``EventRecord`` stores a reference, not dereferenceable source bytes.  Its
    carry items and workspace digest are the available versioned content
    identity.  Source event IDs are intentionally excluded so repeated evidence
    with the same content remains deduplicable.
    """
    carry_identity = tuple(
        (
            item.key,
            item.kind,
            item.content,
            item.authority,
            item.trust,
            item.retention_priority,
            item.sensitivity,
            tuple(sorted(item.required_for)),
        )
        for item in sorted(event.carry_items, key=lambda item: item.key)
    )
    return stable_digest(
        {
            "payload_ref": event.payload_ref,
            "carry_items": carry_identity,
            "workspace_digest": event.workspace_digest,
        }
    )


def _evidence_locators(events: tuple[EventRecord, ...], workspace_digest: str) -> tuple[EvidenceLocator, ...]:
    locators: dict[tuple[str, str, str], EvidenceLocator] = {}
    for event in events:
        if event.payload_ref is None:
            continue
        content_digest = _locator_content_digest(event)
        identity = ("payload_ref", event.payload_ref, content_digest)
        if identity not in locators:
            locators[identity] = EvidenceLocator(
                locator_id=f"loc-{stable_digest(identity)[:16]}",
                kind=identity[0],
                ref=identity[1],
                content_digest=identity[2],
                workspace_digest=event.workspace_digest or workspace_digest,
            )
    return tuple(locators[key] for key in sorted(locators))


class StructuredCompactionStrategy:
    """Create an inspectable artifact with every selected semantic field intact."""

    strategy = "structured-compaction-v1"

    def prepare(self, events: tuple[EventRecord, ...], seed: CompactionSeed) -> StrategyOutput:
        _validate_events(events, seed)
        if not events:
            raise ValueError("compaction_requires_events")
        items_by_key = _latest_items_by_key(events)
        categories = _partition_items(items_by_key, seed)
        source_digest = stable_digest(events)
        workspace_digest = next(
            (event.workspace_digest for event in reversed(events) if event.workspace_digest),
            source_digest,
        )
        next_intent = categories["next_intent"] or (_summary_next_intent(events),)
        artifact = CompactionArtifact(
            artifact_id=f"cmp-{stable_digest((seed.run_id, source_digest))[:16]}",
            run_id=seed.run_id,
            source_event_range=(events[0].sequence, events[-1].sequence),
            goal=categories["goal"][0],
            acceptance_criteria=categories["acceptance"],
            constraints=categories["constraints"],
            decisions=categories["decisions"],
            rejected_hypotheses=categories["rejected"],
            open_issues=categories["open"],
            verification_state=categories["verification"],
            evidence_locators=_evidence_locators(events, workspace_digest),
            next_intent=next_intent[0],
            created_at=_FIXED_CREATED_AT,
            source_digest=source_digest,
            workspace_digest=workspace_digest,
        )
        context_items = (
            categories["goal"]
            + categories["acceptance"]
            + categories["constraints"]
            + categories["decisions"]
            + categories["rejected"]
            + categories["open"]
            + categories["verification"]
            + categories["next_intent"]
        )
        return StrategyOutput(
            strategy=self.strategy,
            visible_keys=frozenset(item.key for item in context_items),
            context_items=context_items,
            artifact=artifact,
            serialized_bytes_before=_event_bytes(events),
            serialized_bytes_after=serialized_bytes(context_items),
            overflowed=serialized_bytes(context_items) > TEACHING_BYTE_BUDGET,
            dropped_event_ids=(),
        )
