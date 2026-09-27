from __future__ import annotations

from dataclasses import FrozenInstanceError
import math

import pytest

from chapter15.contracts import (
    AuditFinding,
    DataSplit,
    FailureObservation,
    FindingSeverity,
    InterventionKind,
    PostTrainingReport,
    PreferencePair,
    ReleaseDecisionKind,
    RewardSpec,
    SupervisedExample,
    TaskCase,
    TrajectoryRecord,
    TrajectoryStep,
)


def _task(**overrides: object) -> TaskCase:
    values: dict[str, object] = {
        "task_id": "task-001",
        "family_id": "link-repair",
        "prompt": "修复文档中的失效相对链接。",
        "allowed_actions": ("read", "write", "test", "finish"),
        "forbidden_actions": ("read_hidden_answer", "write_outside_workspace"),
        "success_condition": "链接检查通过且未修改受保护文件",
        "budget_steps": 8,
        "tags": ("basic", "repair"),
        "split": DataSplit.TRAIN,
    }
    values.update(overrides)
    return TaskCase(**values)


def _step(index: int = 0, **overrides: object) -> TrajectoryStep:
    values: dict[str, object] = {
        "step_index": index,
        "state_id": f"state-{index}",
        "observation": "发现 README 中存在失效链接",
        "action": "write",
        "tool_name": "patch_file",
        "tool_arguments": {"path": "README.md"},
        "tool_result": {"status": "ok"},
        "action_probability": 0.8,
        "reward_components": {"outcome": 1.0, "efficiency": 0.2},
        "safety_events": (),
    }
    values.update(overrides)
    return TrajectoryStep(**values)


def _trajectory(**overrides: object) -> TrajectoryRecord:
    values: dict[str, object] = {
        "trajectory_id": "traj-001",
        "task_id": "task-001",
        "family_id": "link-repair",
        "split": DataSplit.TRAIN,
        "slice": "basic-repair",
        "source_run_id": "run-001",
        "model_fingerprint": "scripted-policy-v1",
        "harness_fingerprint": "chapter15-harness-v1",
        "transform_history": ("raw", "redacted", "normalized"),
        "steps": (_step(),),
        "outcome": "success",
        "verifier_passed": True,
        "protected_writes": (),
        "safety_events": (),
        "contains_sensitive_data": False,
        "accessed_hidden_answer": False,
        "telemetry_complete": True,
        "metadata": {"seed": 1501},
    }
    values.update(overrides)
    return TrajectoryRecord(**values)


def test_enums_expose_stable_wire_values() -> None:
    assert [item.value for item in DataSplit] == ["train", "validation", "eval"]
    assert ReleaseDecisionKind.PASS.value == "pass"
    assert ReleaseDecisionKind.FAIL.value == "fail"
    assert ReleaseDecisionKind.INCONCLUSIVE.value == "inconclusive"
    assert InterventionKind.POST_TRAINING.value == "post_training"
    assert FindingSeverity.BLOCKER.value == "blocker"


def test_task_case_is_frozen_and_serializes_enums_and_tuples() -> None:
    task = _task()

    assert task.to_dict() == {
        "task_id": "task-001",
        "family_id": "link-repair",
        "prompt": "修复文档中的失效相对链接。",
        "allowed_actions": ["read", "write", "test", "finish"],
        "forbidden_actions": ["read_hidden_answer", "write_outside_workspace"],
        "success_condition": "链接检查通过且未修改受保护文件",
        "budget_steps": 8,
        "tags": ["basic", "repair"],
        "split": "train",
    }
    with pytest.raises(FrozenInstanceError):
        task.task_id = "changed"  # type: ignore[misc]


def test_task_case_rejects_invalid_split() -> None:
    with pytest.raises(ValueError, match="invalid_data_split"):
        _task(split="training")


def test_task_case_rejects_action_overlap_and_invalid_budget() -> None:
    with pytest.raises(ValueError, match="action_policy_overlap"):
        _task(forbidden_actions=("write",))
    with pytest.raises(ValueError, match="invalid_budget_steps"):
        _task(budget_steps=0)


def test_trajectory_step_rejects_invalid_probability_and_non_finite_reward() -> None:
    with pytest.raises(ValueError, match="invalid_action_probability"):
        _step(action_probability=1.1)
    with pytest.raises(ValueError, match="invalid_reward_component"):
        _step(reward_components={"outcome": math.nan})


def test_trajectory_rejects_duplicate_step_indexes() -> None:
    with pytest.raises(ValueError, match="duplicate_step_index"):
        _trajectory(steps=(_step(0), _step(0, state_id="state-1")))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_run_id", ""),
        ("model_fingerprint", ""),
        ("harness_fingerprint", ""),
        ("transform_history", ()),
        ("transform_history", ("raw", " ")),
    ],
)
def test_trajectory_requires_complete_provenance(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="missing_trajectory_provenance"):
        _trajectory(**{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("verifier_passed", "false"),
        ("contains_sensitive_data", None),
        ("accessed_hidden_answer", 0),
        ("telemetry_complete", "false"),
    ],
)
def test_trajectory_rejects_non_boolean_evidence(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="invalid_trajectory_boolean"):
        _trajectory(**{field: value})


def test_preference_pair_requires_same_state() -> None:
    with pytest.raises(ValueError, match="preference_state_mismatch"):
        PreferencePair(
            pair_id="pair-001",
            chosen_state_id="state-a",
            rejected_state_id="state-b",
            chosen_action="read_docs",
            rejected_action="guess",
            policy_chosen_logp=-0.3,
            policy_rejected_logp=-1.1,
            reference_chosen_logp=-0.5,
            reference_rejected_logp=-0.9,
            source_trajectory_ids=("traj-a", "traj-b"),
            preference_source="rule_based",
            confidence=0.9,
        )


def test_reward_spec_requires_explicit_boolean_safety_veto() -> None:
    with pytest.raises(TypeError):
        RewardSpec(
            spec_id="reward-v1",
            outcome_weight=1.0,
            process_weight=0.4,
            efficiency_weight=0.2,
            safety_penalty=-10.0,
        )
    with pytest.raises(ValueError, match="invalid_reward_weight"):
        RewardSpec("reward-v1", -1.0, 0.4, 0.2, -10.0, True)
    with pytest.raises(ValueError, match="invalid_safety_veto"):
        RewardSpec("reward-v1", 1.0, 0.4, 0.2, -10.0, 1)  # type: ignore[arg-type]


def test_remaining_contracts_round_trip_to_json_ready_dicts() -> None:
    observation = FailureObservation(
        observation_id="obs-001",
        task_id="task-001",
        symptom="相同工具误用在多个同族任务中反复出现",
        repeated_across_tasks=True,
        missing_facts=False,
        deterministic_boundary_available=False,
        instruction_ambiguous=False,
        model_capacity_evidence=False,
        reusable_supervision=True,
        counterfactual_checks=("补充文档后仍失败", "收紧权限后仍选择错误工具"),
        evidence_refs=("trace:traj-001",),
    )
    example = SupervisedExample(
        example_id="sft-001",
        state_id="state-0",
        target_action="read",
        source_trajectory_id="traj-001",
        sample_weight=1.0,
        retention_reason="纠正重复策略偏差",
    )
    pair = PreferencePair(
        pair_id="pair-001",
        chosen_state_id="state-0",
        rejected_state_id="state-0",
        chosen_action="read_docs",
        rejected_action="guess",
        policy_chosen_logp=-0.3,
        policy_rejected_logp=-1.1,
        reference_chosen_logp=-0.5,
        reference_rejected_logp=-0.9,
        source_trajectory_ids=("traj-001", "traj-002"),
        preference_source="rule_based",
        confidence=0.9,
    )
    reward = RewardSpec("reward-v1", 1.0, 0.4, 0.2, -10.0, True)
    finding = AuditFinding(
        finding_id="finding-001",
        severity=FindingSeverity.BLOCKER,
        reason_code="hidden_answer_access",
        evidence_refs=("trace:traj-002",),
        recommended_action="隔离并丢弃污染轨迹",
        blocks_training=True,
    )
    report = PostTrainingReport(
        schema_version="1.0.0",
        fixture_version="chapter15-fixtures-v1",
        data_summary={"accepted": 20, "rejected": 4},
        objective_summary={"sft_examples": 12, "preference_pairs": 8},
        simulation_summary={"baseline_pass_rate": 0.5, "candidate_pass_rate": 0.75},
        release_decision=ReleaseDecisionKind.INCONCLUSIVE,
        evidence_limits=("确定性模拟不代表真实模型能力",),
        findings=(finding,),
    )

    assert observation.to_dict()["counterfactual_checks"] == [
        "补充文档后仍失败",
        "收紧权限后仍选择错误工具",
    ]
    assert example.to_dict()["sample_weight"] == 1.0
    assert pair.to_dict()["chosen_state_id"] == pair.to_dict()["rejected_state_id"]
    assert reward.to_dict()["safety_veto"] is True
    assert report.to_dict()["release_decision"] == "inconclusive"
    assert report.to_dict()["findings"][0]["severity"] == "blocker"


def test_trajectory_round_trip_is_json_ready() -> None:
    payload = _trajectory().to_dict()

    assert payload["split"] == "train"
    assert payload["steps"][0]["tool_arguments"] == {"path": "README.md"}
    assert payload["metadata"] == {"seed": 1501}
