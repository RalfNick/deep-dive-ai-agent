from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import PurePosixPath

from .contracts import (
    BuildConfig,
    BuildResult,
    ContextBuildTrace,
    ContextItem,
    ContextKind,
    ContextPacket,
    ContextSection,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TraceEntry,
    TrustLevel,
)
from .trace import stable_digest


AUTHORITY_RANK = {
    InstructionAuthority.NONE: 0,
    InstructionAuthority.UNTRUSTED: 1,
    InstructionAuthority.USER: 2,
    InstructionAuthority.REPOSITORY: 3,
    InstructionAuthority.DEVELOPER: 4,
    InstructionAuthority.SYSTEM: 5,
}
TRUST_RANK = {
    TrustLevel.HOSTILE: 0,
    TrustLevel.UNKNOWN: 1,
    TrustLevel.UNVERIFIED: 2,
    TrustLevel.TRUSTED_SOURCE: 3,
    TrustLevel.VERIFIED: 4,
}
RETENTION_RANK = {
    RetentionPriority.LOW: 0,
    RetentionPriority.NORMAL: 1,
    RetentionPriority.HIGH: 2,
    RetentionPriority.REQUIRED: 3,
}


def _units(item: ContextItem) -> int:
    return len(item.content.encode("utf-8"))


def _selection_key(item: ContextItem) -> tuple[int, int, int, str]:
    return (
        -RETENTION_RANK[item.retention_priority],
        -TRUST_RANK[item.trust],
        -AUTHORITY_RANK[item.authority],
        item.item_id,
    )


def _instruction_conflict_key(item: ContextItem) -> tuple[int, int, int, int, str]:
    path = (item.scope.path_prefix or "").replace("\\", "/").strip("/")
    path_specificity = 0 if not path else len(PurePosixPath(path).parts)
    return (
        -AUTHORITY_RANK[item.authority],
        -path_specificity,
        -TRUST_RANK[item.trust],
        -RETENTION_RANK[item.retention_priority],
        item.item_id,
    )


def _version_key(version: str | None) -> tuple[tuple[int, int | str], ...]:
    if version is None:
        return ()
    parts: list[tuple[int, int | str]] = []
    for part in re.split(r"(\d+)", version):
        if not part:
            continue
        parts.append((1, int(part)) if part.isdigit() else (0, part.casefold()))
    return tuple(parts)


def _instruction_path_applies(item: ContextItem, target_path: str) -> bool:
    source_path = item.scope.path_prefix
    if not source_path:
        return True
    normalized = source_path.replace("\\", "/").strip("/")
    path = PurePosixPath(normalized)
    if path.name.casefold() in {"agents.md", "claude.md"}:
        prefix = str(path.parent).strip(".").strip("/")
    else:
        prefix = normalized
    if not prefix:
        return True
    normalized_target = target_path.replace("\\", "/").strip("/")
    return normalized_target == prefix or normalized_target.startswith(f"{prefix}/")


class ContextBuilder:
    """Build an ordered Packet and a content-free explanation trace."""

    def build(
        self,
        items: Sequence[ContextItem],
        config: BuildConfig,
    ) -> BuildResult:
        candidates = sorted(items, key=lambda item: item.item_id)
        terminal: dict[str, TraceEntry] = {}

        def record(item: ContextItem, stage: str, outcome: str, reason: str) -> None:
            is_secret = item.sensitivity is Sensitivity.SECRET
            terminal[item.item_id] = TraceEntry(
                item_id=item.item_id,
                content_digest="redacted" if is_secret else item.provenance.content_digest,
                stage=stage,
                outcome=outcome,
                reason=reason,
                estimated_units=0 if is_secret else _units(item),
            )

        scoped: list[ContextItem] = []
        for item in candidates:
            if item.sensitivity not in config.allowed_sensitivities:
                record(item, "sensitivity", "dropped", "sensitive")
                continue
            if item.scope.repository != config.repository or (
                item.scope.task_id is not None and item.scope.task_id != config.task_id
            ):
                record(item, "scope", "dropped", "out_of_scope")
                continue
            if item.kind is ContextKind.INSTRUCTION and not _instruction_path_applies(
                item, config.target_path
            ):
                record(item, "scope", "dropped", "out_of_scope")
                continue
            scoped.append(item)

        deduplicated: list[ContextItem] = []
        duplicate_groups: dict[tuple[ContextKind, str], list[ContextItem]] = defaultdict(list)
        for item in scoped:
            duplicate_groups[(item.kind, item.provenance.content_digest)].append(item)
        for group_key in sorted(duplicate_groups, key=lambda value: (value[0].value, value[1])):
            group = sorted(duplicate_groups[group_key], key=_selection_key)
            deduplicated.append(group[0])
            for duplicate in group[1:]:
                record(duplicate, "dedup", "dropped", "duplicate")

        version_groups: dict[tuple[ContextKind, str], list[ContextItem]] = defaultdict(list)
        for item in deduplicated:
            version_groups[(item.kind, item.provenance.source_id)].append(item)

        resolved: list[ContextItem] = []
        conflict_reason: dict[str, str] = {}
        for group_key in sorted(
            version_groups,
            key=lambda value: (value[0].value, value[1]),
        ):
            group = version_groups[group_key]
            versions = {item.provenance.version for item in group}
            if len(group) > 1 and len(versions) > 1 and None not in versions:
                newest_version = max(versions, key=_version_key)
                for item in group:
                    if item.provenance.version == newest_version:
                        resolved.append(item)
                    else:
                        record(item, "supersession", "dropped", "superseded")
                continue

            if len(group) == 1:
                resolved.extend(group)
                continue

            kind = group[0].kind
            if kind is ContextKind.INSTRUCTION:
                ranked = sorted(group, key=_instruction_conflict_key)
                resolved.append(ranked[0])
                for item in ranked[1:]:
                    record(item, "conflict", "dropped", "conflict_lost")
            elif kind is ContextKind.FACT:
                resolved.extend(group)
                conflict_reason.update({item.item_id: "conflict_visible" for item in group})
            elif kind is ContextKind.TOOL_SCHEMA:
                for item in group:
                    record(item, "conflict", "dropped", "conflict_lost")
            else:
                resolved.extend(group)
                conflict_reason.update({item.item_id: "conflict_visible" for item in group})

        required = sorted(
            (
                item
                for item in resolved
                if item.retention_priority is RetentionPriority.REQUIRED or item.required_for
            ),
            key=_selection_key,
        )
        optional = sorted(
            (
                item
                for item in resolved
                if item.retention_priority is not RetentionPriority.REQUIRED
                and not item.required_for
            ),
            key=_selection_key,
        )

        selected: list[ContextItem] = []
        budget_used = 0
        selected_required_units = 0
        all_required_candidate_units = sum(_units(item) for item in required)
        requirement_evidence_units = sum(
            _units(item) for item in resolved if item.required_for
        )
        for item in (*required, *optional):
            units = _units(item)
            if budget_used + units > config.budget_units:
                record(item, "budget", "dropped", "budget_exceeded")
                continue
            selected.append(item)
            budget_used += units
            if item in required:
                selected_required_units += units

        selected_keys = {
            (item.kind, item.provenance.content_digest) for item in selected
        }
        all_requirements = set(config.expected_requirements) | {
            requirement for item in candidates for requirement in item.required_for
        }
        satisfied_requirements: set[str] = set()
        for item in candidates:
            if item in selected or (item.kind, item.provenance.content_digest) in selected_keys:
                satisfied_requirements.update(item.required_for)
        missing_requirements = tuple(sorted(all_requirements - satisfied_requirements))

        order_index = {kind: index for index, kind in enumerate(config.section_order)}
        selected_by_kind: dict[ContextKind, list[ContextItem]] = defaultdict(list)
        for item in selected:
            selected_by_kind[item.kind].append(item)
        section_kinds = sorted(
            selected_by_kind,
            key=lambda kind: (order_index.get(kind, len(order_index)), kind.value),
        )
        sections: list[ContextSection] = []
        selected_in_packet_order: list[ContextItem] = []
        for kind in section_kinds:
            section_items = sorted(selected_by_kind[kind], key=_selection_key)
            selected_in_packet_order.extend(section_items)
            serialized = "\n\n".join(
                (
                    f"[ITEM id={item.item_id} source={item.provenance.source_id} "
                    f"authority={item.authority.value} trust={item.trust.value} "
                    f"sensitivity={item.sensitivity.value}]\n"
                    f"{item.content}\n[/ITEM]"
                )
                for item in section_items
            )
            sections.append(
                ContextSection(
                    kind=kind,
                    item_ids=tuple(item.item_id for item in section_items),
                    serialized_content=serialized,
                    budget_units=sum(_units(item) for item in section_items),
                )
            )

        packet_payload = {
            "task_id": config.task_id,
            "sections": [
                {
                    "kind": section.kind.value,
                    "item_ids": section.item_ids,
                    "serialized_content": section.serialized_content,
                    "budget_units": section.budget_units,
                }
                for section in sections
            ],
            "tools": sorted(
                item.provenance.source_id
                for item in selected_in_packet_order
                if item.kind is ContextKind.TOOL_SCHEMA
            ),
            "budget_limit": config.budget_units,
            "budget_used": budget_used,
            "selected_required_units": selected_required_units,
            "all_required_candidate_units": all_required_candidate_units,
            "requirement_evidence_units": requirement_evidence_units,
            "selected_item_ids": [item.item_id for item in selected_in_packet_order],
            "missing_requirements": missing_requirements,
            "provider_boundary": config.provider_boundary,
        }
        packet_digest = stable_digest(packet_payload)
        packet = ContextPacket(
            task_id=config.task_id,
            sections=tuple(sections),
            tools=tuple(packet_payload["tools"]),
            budget_limit=config.budget_units,
            budget_used=budget_used,
            selected_required_units=selected_required_units,
            all_required_candidate_units=all_required_candidate_units,
            requirement_evidence_units=requirement_evidence_units,
            selected_item_ids=tuple(item.item_id for item in selected_in_packet_order),
            missing_requirements=missing_requirements,
            semantic_packet_digest=packet_digest,
        )

        for item in selected:
            if item.trust is TrustLevel.HOSTILE:
                record(item, "selected", "selected_as_data", "untrusted_instruction")
            elif item.item_id in conflict_reason:
                record(item, "conflict", "selected", conflict_reason[item.item_id])
            else:
                record(item, "selected", "selected", "selected")

        entries = tuple(terminal[item_id] for item_id in sorted(terminal))
        stage_counts = tuple(sorted(Counter(entry.stage for entry in entries).items()))
        trace = ContextBuildTrace(
            entries=entries,
            stage_counts=stage_counts,
            selected_item_ids=packet.selected_item_ids,
            missing_requirements=missing_requirements,
            packet_digest=packet_digest,
        )
        return BuildResult(packet=packet, trace=trace)
