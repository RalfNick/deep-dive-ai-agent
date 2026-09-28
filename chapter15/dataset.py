"""Load and redact deterministic trajectory fixtures for Chapter 15."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from chapter15.contracts import DataSplit, TrajectoryRecord, TrajectoryStep


DEFAULT_TRAJECTORIES = Path(__file__).parent / "fixtures" / "trajectories.json"
_SENSITIVE_KEYS = frozenset({"api_key", "authorization", "password", "secret", "token"})
_SENSITIVE_TEXT = re.compile(r"(?i)(bearer\s+\S+|demo_secret_\S+|demo_token_\S+)")


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = {str(key): value for key, value in base.items()}
    for key, value in override.items():
        if key in merged and isinstance(merged[key], Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _step_from_dict(payload: Mapping[str, Any]) -> TrajectoryStep:
    return TrajectoryStep(
        step_index=payload["step_index"],
        state_id=payload["state_id"],
        observation=payload["observation"],
        action=payload["action"],
        tool_name=payload.get("tool_name"),
        tool_arguments=payload.get("tool_arguments", {}),
        tool_result=payload.get("tool_result"),
        action_probability=payload.get("action_probability"),
        reward_components=payload.get("reward_components", {}),
        safety_events=tuple(payload.get("safety_events", ())),
    )


def _record_from_dict(payload: Mapping[str, Any]) -> TrajectoryRecord:
    return TrajectoryRecord(
        trajectory_id=payload["trajectory_id"],
        task_id=payload["task_id"],
        family_id=payload["family_id"],
        split=payload["split"],
        slice=payload["slice"],
        source_run_id=payload["source_run_id"],
        model_fingerprint=payload["model_fingerprint"],
        harness_fingerprint=payload["harness_fingerprint"],
        transform_history=tuple(payload["transform_history"]),
        steps=tuple(_step_from_dict(item) for item in payload["steps"]),
        outcome=payload["outcome"],
        verifier_passed=payload["verifier_passed"],
        protected_writes=tuple(payload["protected_writes"]),
        safety_events=tuple(payload["safety_events"]),
        contains_sensitive_data=payload["contains_sensitive_data"],
        accessed_hidden_answer=payload["accessed_hidden_answer"],
        telemetry_complete=payload["telemetry_complete"],
        metadata=payload["metadata"],
        source_contains_sensitive_data=payload.get(
            "source_contains_sensitive_data", payload["contains_sensitive_data"]
        ),
    )


def load_trajectories(path: Path | None = None) -> tuple[TrajectoryRecord, ...]:
    """Load the fixed fixture and expand compact ``duplicate_of`` entries."""

    source = DEFAULT_TRAJECTORIES if path is None else Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    defaults: Mapping[str, Any] = payload["defaults"]
    raw_records: list[Mapping[str, Any]] = payload["records"]
    by_id = {item["trajectory_id"]: item for item in raw_records}
    resolved: dict[str, dict[str, Any]] = {}
    resolving: set[str] = set()

    def resolve(trajectory_id: str) -> dict[str, Any]:
        if trajectory_id in resolved:
            return resolved[trajectory_id]
        if trajectory_id in resolving:
            raise ValueError("cyclic_duplicate_reference")
        resolving.add(trajectory_id)
        raw = by_id[trajectory_id]
        if "duplicate_of" in raw:
            base = resolve(raw["duplicate_of"])
            own = {key: value for key, value in raw.items() if key != "duplicate_of"}
            item = _deep_merge(base, own)
        else:
            item = _deep_merge(defaults, raw)
        resolving.remove(trajectory_id)
        resolved[trajectory_id] = item
        return item

    records = tuple(_record_from_dict(resolve(item["trajectory_id"])) for item in raw_records)
    split_counts = {split.value: 0 for split in DataSplit}
    for record in records:
        split_counts[str(record.split)] += 1
    if split_counts != {"train": 12, "validation": 4, "eval": 8}:
        raise ValueError("unexpected_fixture_split_counts")
    return records


def load_preference_sources() -> tuple[TrajectoryRecord, ...]:
    """Add explicit, authored rejected branches without executing their tools.

    The 24-record SFT corpus is unchanged in size. These four branches belong
    to the preference fixture only and retain their audited parent context.
    """
    records = load_trajectories()
    by_id = {record.trajectory_id: record for record in records}
    payload = json.loads(
        (DEFAULT_TRAJECTORIES.parent / "preference-rejections.json").read_text(encoding="utf-8")
    )
    branches = []
    for item in payload["records"]:
        parent = by_id[item["derived_from"]]
        decision = replace(
            parent.steps[-1], action=item["action"], tool_name=item["tool_name"],
            tool_arguments={"fixture_only": True},
            tool_result={"status": "controlled_rejected_branch", "executed": False},
            action_probability=None, reward_components={}, safety_events=tuple(item["safety_events"]),
        )
        branches.append(replace(
            parent, trajectory_id=item["trajectory_id"], steps=(decision,),
            source_run_id=f"controlled-branch-{parent.trajectory_id}",
            outcome="failure", verifier_passed=False,
            protected_writes=tuple(item["protected_writes"]), safety_events=tuple(item["safety_events"]),
            transform_history=parent.transform_history + ("authored_rejected_branch",),
            metadata={**parent.metadata, "derived_from": parent.trajectory_id, "fixture_kind": "authored_counterexample"},
        ))
    return records + tuple(branches)


def _redaction_marker(value: Any, salt: str) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(f"{salt}:{canonical}".encode("utf-8")).hexdigest()[:12]
    return f"[REDACTED:{digest}]"


def _redact_value(value: Any, *, salt: str, key: str | None = None) -> Any:
    if key is not None and key.casefold() in _SENSITIVE_KEYS:
        return _redaction_marker(value, salt)
    if isinstance(value, Mapping):
        return {str(child_key): _redact_value(child, salt=salt, key=str(child_key)) for child_key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_value(item, salt=salt) for item in value]
    if isinstance(value, str) and _SENSITIVE_TEXT.search(value):
        return _redaction_marker(value, salt)
    return value


def redact_record(record: TrajectoryRecord, *, salt: str) -> TrajectoryRecord:
    """Remove known payload secrets, retaining source quarantine evidence.

    This narrow fixture sanitizer is not a production PII detector or a
    data-eligibility approval workflow.
    """

    if not isinstance(salt, str) or not salt:
        raise ValueError("missing_redaction_salt")
    steps = tuple(
        replace(
            step,
            observation=_redact_value(step.observation, salt=salt),
            tool_arguments=_redact_value(step.tool_arguments, salt=salt),
            tool_result=None if step.tool_result is None else _redact_value(step.tool_result, salt=salt),
        )
        for step in record.steps
    )
    redacted_metadata = _redact_value(record.metadata, salt=salt)
    original_payload = record.to_dict()
    detected = _redact_value(original_payload, salt=salt) != original_payload
    digest = hashlib.sha256(
        json.dumps(redacted_metadata, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    return replace(
        record,
        steps=steps,
        metadata=redacted_metadata,
        contains_sensitive_data=False,
        source_contains_sensitive_data=record.source_contains_sensitive_data or detected,
        transform_history=record.transform_history + (f"redacted:{digest}",),
    )
