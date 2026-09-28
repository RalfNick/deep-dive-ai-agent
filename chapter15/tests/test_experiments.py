from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from chapter15.experiments import build_post_training_report, main, run_group


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "chapter15" / "schemas" / "post-training-report-v2.schema.json"
ARTIFACT_NAMES = [
    "group-1.json",
    "group-2.json",
    "group-3.json",
    "group-4.json",
    "group-5.json",
    "manifest.json",
    "post-training-report.json",
    "post-training-report.md",
]


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_five_groups_expose_named_evidence(tmp_path: Path) -> None:
    names = []
    payloads = []
    for number in range(1, 6):
        payload = run_group(number, tmp_path / f"group-{number}")
        names.append(payload["name"])
        payloads.append(payload)

    assert names == [
        "intervention_boundary",
        "dataset_audit",
        "sft_mechanics",
        "dpo_mechanics",
        "reward_and_release",
    ]
    assert payloads[0]["always_train_ablation"]["incorrect_cases"] == 4
    assert payloads[1]["audit"]["raw_count"] == 24
    assert payloads[1]["audit"]["split_counts"] == {"train": 12, "validation": 4, "eval": 8}
    assert payloads[2]["clean_demo"]["target_probability_after"] > payloads[2]["clean_demo"]["target_probability_before"]
    assert payloads[3]["hand_example"]["margin"] == pytest.approx(0.15)
    assert payloads[3]["hand_example"]["loss"] == pytest.approx(0.620957, abs=1e-6)
    assert payloads[4]["variants"]["hard_gate"]["metrics"]["safety_violations"] == 0
    assert payloads[4]["unsafe_candidate_release"]["decision"] == "fail"


def test_full_report_is_stable_safe_and_refuses_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "ENVIRONMENT_SENTINEL_DO_NOT_EXPORT")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "SECOND_ENVIRONMENT_SENTINEL")
    first = tmp_path / "first"
    second = tmp_path / "second"

    report = build_post_training_report(first)
    build_post_training_report(second)

    assert report["schema_version"] == "chapter15.post-training.v2"
    assert sorted(path.name for path in first.iterdir()) == sorted(ARTIFACT_NAMES)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    assert "generated_at" not in serialized
    assert str(ROOT) not in serialized
    assert "ENVIRONMENT_SENTINEL_DO_NOT_EXPORT" not in serialized
    assert "SECOND_ENVIRONMENT_SENTINEL" not in serialized
    assert report["real_model_measurements"] == {
        "status": "not_measured",
        "model_checkpoint": None,
        "token_usage": None,
        "gpu_hours": None,
        "provider_cost": None,
    }
    assert report["objective_summary"]["sft"]["audited_batch"]["example_count"] == 5
    assert report["objective_summary"]["dpo"]["source_context_validation"] == "passed"
    assert report["simulation_summary"]["policy_updates"]["hard_gate"]["updates"] == 200
    assert report["simulation_summary"]["release_evidence_kind"] == "static_gate_conformance_not_trained_policy_eval"
    with pytest.raises(FileExistsError, match="output_directory_not_empty"):
        build_post_training_report(first)


def test_manifest_hashes_every_artifact_except_itself(tmp_path: Path) -> None:
    output = tmp_path / "report"
    build_post_training_report(output)
    manifest = _load(output / "manifest.json")

    entries = {item["name"]: item for item in manifest["artifacts"]}
    assert set(entries) == set(ARTIFACT_NAMES) - {"manifest.json"}
    for name, item in entries.items():
        data = (output / name).read_bytes()
        assert item["bytes"] == len(data)
        assert item["sha256"] == hashlib.sha256(data).hexdigest()


def test_replace_keeps_previous_output_recoverable(tmp_path: Path) -> None:
    output = tmp_path / "candidate"
    build_post_training_report(output)
    (output / "reader-note.txt").write_text("preserve me", encoding="utf-8")

    assert main(["--group", "all", "--output", str(output), "--replace"]) == 0

    assert (output / "post-training-report.json").exists()
    assert (tmp_path / "candidate.previous" / "reader-note.txt").read_text(encoding="utf-8") == "preserve me"


def test_replace_refuses_to_overwrite_existing_recovery_backup(tmp_path: Path) -> None:
    output = tmp_path / "candidate"
    build_post_training_report(output)
    backup = tmp_path / "candidate.previous"
    backup.mkdir()

    with pytest.raises(FileExistsError, match="recoverable_backup_exists"):
        main(["--group", "all", "--output", str(output), "--replace"])


def test_schema_accepts_report_and_rejects_semantic_mutations(tmp_path: Path) -> None:
    report = build_post_training_report(tmp_path / "report")
    schema = _load(SCHEMA_PATH)
    validator = Draft202012Validator(schema)

    assert list(validator.iter_errors(report)) == []

    mutations = []
    no_limits = deepcopy(report)
    del no_limits["evidence_limits"]
    mutations.append(no_limits)
    missing_limit = deepcopy(report)
    missing_limit["evidence_limits"].remove("no_gpu_training_performed")
    mutations.append(missing_limit)
    no_findings = deepcopy(report)
    no_findings["findings"] = []
    mutations.append(no_findings)
    unsafe_hard_gate = deepcopy(report)
    unsafe_hard_gate["simulation_summary"]["variants"]["hard_gate"]["metrics"]["safety_violations"] = 1
    mutations.append(unsafe_hard_gate)
    fake_checkpoint = deepcopy(report)
    fake_checkpoint["real_model_measurements"]["model_checkpoint"] = "trained-model"
    mutations.append(fake_checkpoint)
    unknown_top_level = deepcopy(report)
    unknown_top_level["surprise"] = True
    mutations.append(unknown_top_level)
    fake_update = deepcopy(report)
    fake_update["simulation_summary"]["policy_updates"]["hard_gate"]["tool_execution"] = "real"
    mutations.append(fake_update)
    missing_update = deepcopy(report)
    del missing_update["simulation_summary"]["policy_updates"]
    mutations.append(missing_update)

    assert all(list(validator.iter_errors(item)) for item in mutations)


def test_archived_rc1_report_still_validates_against_its_original_schema() -> None:
    report = _load(ROOT / "chapter15" / "report-history" / "v1.0-rc1" / "post-training-report.json")
    schema = _load(ROOT / "chapter15" / "schemas" / "post-training-report-v1.schema.json")
    assert list(Draft202012Validator(schema).iter_errors(report)) == []


def test_single_group_refuses_overwrite_and_replace_is_recoverable(tmp_path: Path) -> None:
    output = tmp_path / "groups"
    run_group(1, output)
    original = (output / "group-1.json").read_bytes()
    with pytest.raises(FileExistsError, match="artifact_exists"):
        run_group(1, output)
    with pytest.raises(FileExistsError, match="artifact_exists"):
        main(["--group", "1", "--output", str(output)])
    assert (output / "group-1.json").read_bytes() == original
    assert not (output / "group-1.json.previous").exists()

    assert main(["--group", "1", "--output", str(output), "--replace"]) == 0
    assert (output / "group-1.json").exists()
    assert (output / "group-1.json.previous").exists()
    assert (output / "group-1.json.previous").read_bytes() == original


def test_single_group_refusal_does_not_touch_existing_backup(tmp_path: Path) -> None:
    output = tmp_path / "groups"
    run_group(1, output)
    target = output / "group-1.json"
    backup = output / "group-1.json.previous"
    original = target.read_bytes()
    backup.write_bytes(b"older evidence")

    with pytest.raises(FileExistsError, match="artifact_exists"):
        main(["--group", "1", "--output", str(output)])

    assert target.read_bytes() == original
    assert backup.read_bytes() == b"older evidence"


def test_single_group_replace_restores_own_backup_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "groups"
    run_group(1, output)
    target = output / "group-1.json"
    original = target.read_bytes()

    def fail_after_partial_write(group: int, destination: Path) -> dict[str, object]:
        (destination / f"group-{group}.json").write_bytes(b"partial")
        raise RuntimeError("injected_failure")

    monkeypatch.setattr("chapter15.experiments.run_group", fail_after_partial_write)
    with pytest.raises(RuntimeError, match="injected_failure"):
        main(["--group", "1", "--output", str(output), "--replace"])

    assert target.read_bytes() == original
    assert not (output / "group-1.json.previous").exists()
