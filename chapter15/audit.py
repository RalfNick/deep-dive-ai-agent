"""Deterministic trajectory audit and leakage protection for Chapter 15."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import unicodedata

from chapter15.contracts import (
    AuditFinding,
    DataSplit,
    FindingSeverity,
    SupervisedExample,
    TrajectoryRecord,
)


def _freeze_mapping(value: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class DatasetAudit:
    raw_count: int
    eligible_ids: tuple[str, ...]
    quarantined_ids: tuple[str, ...]
    findings: tuple[AuditFinding, ...]
    split_counts: Mapping[str, int]
    reason_counts: Mapping[str, int]
    _eligible_records: tuple[TrajectoryRecord, ...] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "eligible_ids", tuple(self.eligible_ids))
        object.__setattr__(self, "quarantined_ids", tuple(self.quarantined_ids))
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "split_counts", _freeze_mapping(self.split_counts))
        object.__setattr__(self, "reason_counts", _freeze_mapping(self.reason_counts))
        object.__setattr__(self, "_eligible_records", tuple(self._eligible_records))

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_count": self.raw_count,
            "eligible_ids": list(self.eligible_ids),
            "quarantined_ids": list(self.quarantined_ids),
            "findings": [finding.to_dict() for finding in self.findings],
            "split_counts": dict(self.split_counts),
            "reason_counts": dict(self.reason_counts),
        }


def _normalize_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return re.sub(r"[\W_]+", "", normalized, flags=re.UNICODE)


def _normalized_text_fingerprint(record: TrajectoryRecord) -> str:
    """Lexical normalization only; this is not semantic similarity."""
    prompt = record.metadata.get("task_prompt", "")
    condition = record.metadata.get("success_condition", "")
    canonical = f"{_normalize_text(prompt)}|{_normalize_text(condition)}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _record_digest(record: TrajectoryRecord) -> str:
    payload = record.to_dict()
    payload.pop("trajectory_id", None)
    payload.pop("source_run_id", None)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _base_reasons(record: TrajectoryRecord) -> set[str]:
    reasons: set[str] = set()
    if record.contains_sensitive_data or record.source_contains_sensitive_data:
        reasons.add("sensitive_data_detected")
    if record.accessed_hidden_answer:
        reasons.add("hidden_answer_access")
    if record.protected_writes:
        reasons.add("protected_write")
    if record.safety_events or any(step.safety_events for step in record.steps):
        reasons.add("safety_event")
    if not record.telemetry_complete:
        reasons.add("incomplete_telemetry")
    if any(step.tool_name is not None and step.tool_result is None for step in record.steps):
        reasons.add("missing_tool_result")
    provenance = (record.source_run_id, record.model_fingerprint, record.harness_fingerprint)
    if any(value.strip().casefold() in {"unknown", "unavailable", "n/a"} for value in provenance):
        reasons.add("unknown_provenance")
    if record.outcome != "success" or not record.verifier_passed:
        reasons.add("failed_or_unverified_outcome")
    return reasons


def audit_dataset(records: Sequence[TrajectoryRecord]) -> DatasetAudit:
    """Quarantine unsafe, unverifiable, duplicated or leaking records."""

    ordered = tuple(records)
    by_id = {record.trajectory_id: record for record in ordered}
    if len(by_id) != len(ordered):
        raise ValueError("duplicate_trajectory_id")
    reasons_by_id = {record.trajectory_id: _base_reasons(record) for record in ordered}

    first_by_digest: dict[str, str] = {}
    for record in ordered:
        digest = _record_digest(record)
        if digest in first_by_digest:
            reasons_by_id[record.trajectory_id].add("exact_duplicate")
        else:
            first_by_digest[digest] = record.trajectory_id

    # Either a curated family ID or an equal normalized text fingerprint
    # joins records. Transitive closure prevents A--B--C bridge leakage.
    parent = {record.trajectory_id: record.trajectory_id for record in ordered}

    def root(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    first_by_key: dict[tuple[str, str], str] = {}
    for record in ordered:
        for key in (
            ("family", record.family_id),
            ("text", _normalized_text_fingerprint(record)),
        ):
            if key in first_by_key:
                parent[root(record.trajectory_id)] = root(first_by_key[key])
            else:
                first_by_key[key] = record.trajectory_id
    by_family: dict[str, list[TrajectoryRecord]] = defaultdict(list)
    for record in ordered:
        by_family[root(record.trajectory_id)].append(record)
    for family_records in by_family.values():
        if len({str(record.split) for record in family_records}) > 1:
            for record in family_records:
                reasons_by_id[record.trajectory_id].add("cross_split_family_leakage")

    eligible_ids = tuple(sorted(key for key, reasons in reasons_by_id.items() if not reasons))
    quarantined_ids = tuple(sorted(key for key, reasons in reasons_by_id.items() if reasons))
    findings: list[AuditFinding] = []
    for trajectory_id in sorted(reasons_by_id):
        for reason in sorted(reasons_by_id[trajectory_id]):
            findings.append(
                AuditFinding(
                    finding_id=f"finding-{trajectory_id}-{reason}",
                    severity=FindingSeverity.BLOCKER,
                    reason_code=reason,
                    evidence_refs=(f"trajectory:{trajectory_id}",),
                    recommended_action="隔离该轨迹，修复原因后重新采集并审计。",
                    blocks_training=True,
                )
            )

    split_counts = Counter(str(record.split) for record in ordered)
    stable_split_counts = {split.value: split_counts.get(split.value, 0) for split in DataSplit}
    reason_counts = Counter(
        reason for trajectory_id in sorted(reasons_by_id) for reason in reasons_by_id[trajectory_id]
    )
    eligible_records = tuple(by_id[trajectory_id] for trajectory_id in eligible_ids)
    return DatasetAudit(
        raw_count=len(ordered),
        eligible_ids=eligible_ids,
        quarantined_ids=quarantined_ids,
        findings=tuple(findings),
        split_counts=stable_split_counts,
        reason_counts={key: reason_counts[key] for key in sorted(reason_counts)},
        _eligible_records=eligible_records,
    )


def build_supervised_examples(audit: DatasetAudit) -> tuple[SupervisedExample, ...]:
    """Build one finite-action teaching example per eligible trajectory."""

    examples: list[SupervisedExample] = []
    for record in audit._eligible_records:
        if record.split != DataSplit.TRAIN or not record.steps:
            continue
        decision = record.steps[-1]
        examples.append(
            SupervisedExample(
                example_id=f"sft-{record.trajectory_id}",
                state_id=decision.state_id,
                target_action=decision.action,
                source_trajectory_id=record.trajectory_id,
                sample_weight=1.0,
                retention_reason="通过来源、切分、安全与遥测审计",
            )
        )
    return tuple(examples)
