from __future__ import annotations

import json

from chapter15.audit import audit_dataset, build_supervised_examples
from chapter15.dataset import load_trajectories, redact_record


def _record(record_id: str):
    return next(item for item in load_trajectories() if item.trajectory_id == record_id)


def test_fixture_has_24_records_and_pinned_raw_splits() -> None:
    records = load_trajectories()
    audit = audit_dataset(records)

    assert len(records) == 24
    assert audit.raw_count == 24
    assert dict(audit.split_counts) == {"train": 12, "validation": 4, "eval": 8}
    assert len(set(item.trajectory_id for item in records)) == 24


def test_nested_secrets_are_redacted_deterministically_before_serialization() -> None:
    raw = _record("traj-003")

    redacted_a = redact_record(raw, salt="chapter15-test-salt")
    redacted_b = redact_record(raw, salt="chapter15-test-salt")
    payload = json.dumps(redacted_a.to_dict(), ensure_ascii=False, sort_keys=True)

    assert redacted_a.to_dict() == redacted_b.to_dict()
    assert "DEMO_SECRET_DO_NOT_USE" not in payload
    assert "Bearer DEMO_TOKEN_NOT_REAL" not in payload
    assert "[REDACTED:" in payload
    assert "chapter15-test-salt" not in payload
    assert redacted_a.contains_sensitive_data is False
    assert redacted_a.transform_history[-1].startswith("redacted:")


def test_hidden_answer_access_is_quarantined() -> None:
    audit = audit_dataset(load_trajectories())

    assert "traj-015" in audit.quarantined_ids
    assert audit.reason_counts["hidden_answer_access"] == 1


def test_success_cannot_override_protected_write() -> None:
    record = _record("traj-004")
    audit = audit_dataset((record,))

    assert record.verifier_passed is True
    assert record.outcome == "success"
    assert audit.eligible_ids == ()
    assert audit.quarantined_ids == ("traj-004",)
    assert audit.reason_counts["protected_write"] == 1
    assert any(finding.blocks_training for finding in audit.findings)


def test_missing_tool_result_is_quarantined() -> None:
    audit = audit_dataset(load_trajectories())

    assert "traj-005" in audit.quarantined_ids
    assert audit.reason_counts["missing_tool_result"] == 1


def test_unknown_provenance_is_quarantined() -> None:
    audit = audit_dataset(load_trajectories())

    assert "traj-006" in audit.quarantined_ids
    assert audit.reason_counts["unknown_provenance"] == 1


def test_exact_duplicate_keeps_first_and_quarantines_later_copy() -> None:
    audit = audit_dataset(load_trajectories())

    assert "traj-007" in audit.eligible_ids
    assert "traj-008" in audit.quarantined_ids
    assert audit.reason_counts["exact_duplicate"] == 1


def test_cross_split_near_duplicates_are_quarantined() -> None:
    audit = audit_dataset(load_trajectories())

    assert "traj-001" in audit.quarantined_ids
    assert "traj-017" in audit.quarantined_ids
    assert audit.reason_counts["cross_split_family_leakage"] == 2


def test_failed_or_unverified_records_do_not_become_supervised_examples() -> None:
    records = load_trajectories()
    audit = audit_dataset(records)
    examples = build_supervised_examples(audit)
    split_by_id = {item.trajectory_id: item.split for item in records}

    assert "traj-009" in audit.quarantined_ids
    assert "traj-023" in audit.quarantined_ids
    assert all(item.source_trajectory_id not in audit.quarantined_ids for item in examples)
    assert all(split_by_id[item.source_trajectory_id] == "train" for item in examples)
    assert len(examples) == sum(
        trajectory_id in audit.eligible_ids and split == "train"
        for trajectory_id, split in split_by_id.items()
    )
    assert all(item.sample_weight == 1.0 for item in examples)


def test_safety_and_telemetry_findings_are_hard_training_blocks() -> None:
    audit = audit_dataset(load_trajectories())

    for trajectory_id in ("traj-003", "traj-004", "traj-015", "traj-021", "traj-022"):
        assert trajectory_id in audit.quarantined_ids
    blockers = [finding for finding in audit.findings if finding.blocks_training]
    assert blockers
    assert {finding.severity for finding in blockers} == {"blocker"}


def test_audit_result_is_stable_and_json_ready() -> None:
    first = audit_dataset(load_trajectories()).to_dict()
    second = audit_dataset(load_trajectories()).to_dict()

    assert first == second
    assert first["raw_count"] == 24
    assert first["eligible_ids"] == sorted(first["eligible_ids"])
    assert first["quarantined_ids"] == sorted(first["quarantined_ids"])
    json.dumps(first, ensure_ascii=False, sort_keys=True)
