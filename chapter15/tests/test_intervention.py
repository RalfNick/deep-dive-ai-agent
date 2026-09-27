from __future__ import annotations

from dataclasses import replace

from chapter15.contracts import FailureObservation, InterventionKind
from chapter15.intervention import load_failure_cases, recommend_intervention


def _observation(**overrides: object) -> FailureObservation:
    values: dict[str, object] = {
        "observation_id": "obs-policy-bias",
        "task_id": "tool-choice-family",
        "symptom": "多个同族任务重复跳过读取，直接执行高风险写入",
        "repeated_across_tasks": True,
        "missing_facts": False,
        "deterministic_boundary_available": False,
        "instruction_ambiguous": False,
        "model_capacity_evidence": False,
        "reusable_supervision": True,
        "counterfactual_checks": (
            "补充事实后仍失败",
            "澄清指令后仍失败",
            "收紧 Harness 后仍出现相同错误提议",
        ),
        "evidence_refs": ("trace:traj-021", "eval:tool-choice-slice"),
    }
    values.update(overrides)
    return FailureObservation(**values)


def test_fixture_routes_five_failures_to_five_different_interventions() -> None:
    observations = load_failure_cases()

    decisions = {item.observation_id: recommend_intervention(item) for item in observations}

    assert len(observations) == 5
    assert decisions["failure-missing-knowledge"].recommended == InterventionKind.RAG_CONTEXT
    assert decisions["failure-permission-bypass"].recommended == InterventionKind.HARNESS
    assert decisions["failure-ambiguous-instruction"].recommended == InterventionKind.PROMPT_SKILL
    assert decisions["failure-model-capacity"].recommended == InterventionKind.MODEL_ROUTE
    assert decisions["failure-repeated-policy-bias"].recommended == InterventionKind.POST_TRAINING


def test_missing_facts_prefers_retrieval_before_training() -> None:
    decision = recommend_intervention(_observation(missing_facts=True))

    assert decision.recommended == InterventionKind.RAG_CONTEXT
    assert decision.reason_codes == ("missing_facts_confirmed",)
    assert InterventionKind.POST_TRAINING in decision.alternatives


def test_deterministic_boundary_prefers_harness() -> None:
    decision = recommend_intervention(_observation(deterministic_boundary_available=True))

    assert decision.recommended == InterventionKind.HARNESS
    assert decision.reason_codes == ("deterministic_boundary_available",)


def test_ambiguous_instruction_prefers_prompt_or_skill() -> None:
    decision = recommend_intervention(_observation(instruction_ambiguous=True))

    assert decision.recommended == InterventionKind.PROMPT_SKILL
    assert decision.reason_codes == ("instruction_ambiguity_unresolved",)


def test_verified_capacity_gap_prefers_model_route() -> None:
    decision = recommend_intervention(_observation(model_capacity_evidence=True))

    assert decision.recommended == InterventionKind.MODEL_ROUTE
    assert decision.reason_codes == ("model_capacity_gap_verified",)


def test_repeated_policy_bias_with_reusable_supervision_can_recommend_training() -> None:
    decision = recommend_intervention(_observation())

    assert decision.recommended == InterventionKind.POST_TRAINING
    assert decision.reason_codes == (
        "policy_bias_repeats_across_tasks",
        "reusable_supervision_available",
        "counterfactuals_exhausted",
    )
    assert decision.confidence == "high"


def test_training_requires_repeated_failures_reusable_supervision_and_counterfactuals() -> None:
    insufficient = [
        replace(_observation(), repeated_across_tasks=False),
        replace(_observation(), reusable_supervision=False),
        replace(_observation(), counterfactual_checks=("只做了一项检查",)),
        replace(_observation(), evidence_refs=("trace:one-run",)),
    ]

    for observation in insufficient:
        decision = recommend_intervention(observation)
        assert decision.recommended == InterventionKind.INCONCLUSIVE
        assert "insufficient_post_training_evidence" in decision.reason_codes


def test_conflicting_evidence_is_inconclusive_instead_of_using_rule_order() -> None:
    decision = recommend_intervention(
        _observation(missing_facts=True, deterministic_boundary_available=True)
    )

    assert decision.recommended == InterventionKind.INCONCLUSIVE
    assert decision.reason_codes == ("conflicting_intervention_evidence",)
    assert decision.confidence == "low"


def test_always_train_ablation_is_wrong_on_four_of_five_canonical_cases() -> None:
    expected = [recommend_intervention(item).recommended for item in load_failure_cases()]
    incorrect = sum(kind != InterventionKind.POST_TRAINING for kind in expected)

    assert incorrect == 4


def test_decision_is_json_ready_and_preserves_evidence_refs() -> None:
    decision = recommend_intervention(_observation())

    assert decision.to_dict() == {
        "recommended": "post_training",
        "reason_codes": [
            "policy_bias_repeats_across_tasks",
            "reusable_supervision_available",
            "counterfactuals_exhausted",
        ],
        "evidence_refs": ["trace:traj-021", "eval:tool-choice-slice"],
        "alternatives": ["prompt_skill", "model_route"],
        "confidence": "high",
    }
