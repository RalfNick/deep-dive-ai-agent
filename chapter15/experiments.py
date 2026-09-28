"""Five deterministic Chapter 15 experiments and stable report artifacts."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Sequence

from chapter15.audit import audit_dataset, build_supervised_examples
from chapter15.contracts import (
    PostTrainingReport,
    ReleaseDecisionKind,
    SupervisedExample,
)
from chapter15.dataset import load_trajectories, redact_record
from chapter15.intervention import load_failure_cases, recommend_intervention
from chapter15.objectives import cross_entropy, dpo_loss, dpo_margin, load_preference_pairs, sft_step
from chapter15.policy import TabularPolicy
from chapter15.reinforcement import train_reward_policy
from chapter15.simulator import compare_policy_variants, release_decision, run_policy_variant


ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT_DIR = ROOT / "reports"
STATES = ("needs_facts", "write_requested", "tool_timeout", "ready_to_finish")
ACTIONS = ("search", "read", "edit", "retry", "stop", "modify_tests")
EVIDENCE_LIMITS = (
    "finite_policy_not_llm_training",
    "fixed_fixture_not_production_distribution",
    "no_provider_conformance_claim",
    "no_gpu_training_performed",
)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _uniform_policy() -> TabularPolicy:
    return TabularPolicy(
        states=STATES,
        actions=ACTIONS,
        logits={state: {action: 0.0 for action in ACTIONS} for state in STATES},
    )


def _audited_examples() -> tuple[SupervisedExample, ...]:
    records = tuple(redact_record(record, salt="chapter15-demo-only") for record in load_trajectories())
    return build_supervised_examples(audit_dataset(records))


def _group_payload(group: int) -> dict[str, Any]:
    if group == 1:
        observations = load_failure_cases()
        decisions = [recommend_intervention(item) for item in observations]
        return {
            "group": 1,
            "name": "intervention_boundary",
            "title": "失败不等于需要训练",
            "decisions": [
                {
                    "observation_id": observation.observation_id,
                    **decision.to_dict(),
                }
                for observation, decision in zip(observations, decisions, strict=True)
            ],
            "always_train_ablation": {
                "total_cases": len(decisions),
                "incorrect_cases": sum(decision.recommended != "post_training" for decision in decisions),
            },
        }
    if group == 2:
        raw = load_trajectories()
        records = tuple(redact_record(record, salt="chapter15-demo-only") for record in raw)
        audit = audit_dataset(records)
        examples = build_supervised_examples(audit)
        return {
            "group": 2,
            "name": "dataset_audit",
            "title": "成功轨迹也可能不适合训练",
            "audit": audit.to_dict(),
            "supervised_examples": [item.to_dict() for item in examples],
            "training_split_only": True,
            "redaction_preserves_source_quarantine": True,
        }
    if group == 3:
        policy = _uniform_policy()
        examples = _audited_examples()
        clean = (next(item for item in examples if item.source_trajectory_id == "traj-010"),)
        contaminated = (replace(
            clean[0], example_id="injected-contaminated-demo", target_action="modify_tests",
            retention_reason="intentional_label_corruption_ablation_not_audited_data",
        ),)
        clean_after = sft_step(policy, clean, learning_rate=0.5)
        contaminated_after = sft_step(policy, contaminated, learning_rate=0.5)
        return {
            "group": 3,
            "name": "sft_mechanics",
            "title": "SFT 学习示范，包括坏示范",
            "clean_demo": {
                "source_trajectory_id": clean[0].source_trajectory_id,
                "target_action": "read",
                "target_probability_before": policy.probability("write_requested", "read"),
                "target_probability_after": clean_after.probability("write_requested", "read"),
                "loss_before": cross_entropy(policy, clean),
                "loss_after": cross_entropy(clean_after, clean),
            },
            "contaminated_demo": {
                "injection": "changed_target_label_after_audit_for_ablation_only",
                "target_action": "modify_tests",
                "target_probability_before": policy.probability("write_requested", "modify_tests"),
                "target_probability_after": contaminated_after.probability("write_requested", "modify_tests"),
            },
            "missing_recovery_slice": {
                "action": "retry",
                "probability_before": policy.probability("tool_timeout", "retry"),
                "probability_after": clean_after.probability("tool_timeout", "retry"),
            },
            "audited_batch": {
                "source_trajectory_ids": [item.source_trajectory_id for item in examples],
                "example_count": len(examples),
                "loss_before": cross_entropy(policy, examples),
                "loss_after": cross_entropy(sft_step(policy, examples, learning_rate=0.5), examples),
            },
        }
    if group == 4:
        pairs = load_preference_pairs()
        rows = [
            {
                **pair.to_dict(),
                "beta": 0.5,
                "margin": dpo_margin(pair, beta=0.5),
                "loss": dpo_loss(pair, beta=0.5),
            }
            for pair in pairs
        ]
        hand = next(item for item in rows if item["pair_id"] == "pair-write-requested")
        return {
            "group": 4,
            "name": "dpo_mechanics",
            "title": "同一状态下的偏好排序",
            "pairs": rows,
            "source_context_validation": "passed",
            "rejected_source_kind": "authored_counterexample_not_executed",
            "log_probability_origin": "hand_calculation_not_model_measurement",
            "hand_example": {
                "pair_id": hand["pair_id"],
                "margin": hand["margin"],
                "loss": hand["loss"],
            },
        }
    if group == 5:
        results = {
            name: run_policy_variant(name, episodes=200, seed=1501)
            for name in ("outcome_only", "scalar_penalty", "hard_gate")
        }
        baseline = results["hard_gate"].metrics
        unsafe_candidate = release_decision(
            baseline=baseline,
            candidate=results["outcome_only"].metrics,
            slice_deltas={name: 0.0 for name in ("basic", "boundary", "safety", "recovery")},
        )
        safe_candidate = release_decision(
            baseline=baseline,
            candidate=results["hard_gate"].metrics,
            slice_deltas={name: 0.0 for name in ("basic", "boundary", "safety", "recovery")},
        )
        return {
            "group": 5,
            "name": "reward_and_release",
            "title": "奖励可以被投机，安全门禁不能被购买",
            "variants": {name: result.to_dict() for name, result in results.items()},
            "comparison": compare_policy_variants(tuple(results.values())),
            "unsafe_candidate_release": unsafe_candidate.to_dict(),
            "safe_candidate_release": safe_candidate.to_dict(),
            "policy_updates": {
                name: train_reward_policy(name, episodes=200, seed=1501, budget_steps=800)
                for name in results
            },
            "budget_demo": train_reward_policy("hard_gate", episodes=200, seed=1501, budget_steps=12),
            "release_evidence_kind": "static_gate_conformance_not_trained_policy_eval",
        }
    raise ValueError("group_must_be_1_to_5")


def run_group(group: int, output: Path) -> dict[str, Any]:
    payload = _group_payload(group)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"group-{group}.json"
    if target.exists():
        raise FileExistsError(f"artifact_exists:{target.name}")
    target.write_bytes(_json_bytes(payload))
    return payload


def _build_report(groups: dict[int, dict[str, Any]]) -> dict[str, Any]:
    audit_payload = groups[2]["audit"]
    findings = audit_dataset(load_trajectories()).findings
    final_release = groups[5]["safe_candidate_release"]
    contract = PostTrainingReport(
        schema_version="chapter15.post-training.v2",
        fixture_version="chapter15-fixtures-v2",
        data_summary={
            "raw_count": audit_payload["raw_count"],
            "eligible_count": len(audit_payload["eligible_ids"]),
            "quarantined_count": len(audit_payload["quarantined_ids"]),
            "split_counts": audit_payload["split_counts"],
            "reason_counts": audit_payload["reason_counts"],
            "supervised_example_count": len(groups[2]["supervised_examples"]),
        },
        objective_summary={
            "finite_states": list(STATES),
            "finite_actions": list(ACTIONS),
            "sft": {
                "clean_demo": groups[3]["clean_demo"],
                "contaminated_demo": groups[3]["contaminated_demo"],
                "missing_recovery_slice": groups[3]["missing_recovery_slice"],
                "audited_batch": groups[3]["audited_batch"],
            },
            "dpo": {
                "pair_count": len(groups[4]["pairs"]),
                "hand_example": groups[4]["hand_example"],
                "source_context_validation": groups[4]["source_context_validation"],
                "log_probability_origin": groups[4]["log_probability_origin"],
            },
        },
        simulation_summary={
            "episodes_per_variant": 200,
            "seed": 1501,
            "variants": groups[5]["variants"],
            "comparison": groups[5]["comparison"],
            "unsafe_candidate_release": groups[5]["unsafe_candidate_release"],
            "safe_candidate_release": final_release,
            "policy_updates": groups[5]["policy_updates"],
            "budget_demo": groups[5]["budget_demo"],
            "release_evidence_kind": groups[5]["release_evidence_kind"],
        },
        release_decision=ReleaseDecisionKind(final_release["decision"]),
        evidence_limits=EVIDENCE_LIMITS,
        findings=findings,
    )
    report = contract.to_dict()
    report["intervention_summary"] = {
        "decisions": groups[1]["decisions"],
        "always_train_ablation": groups[1]["always_train_ablation"],
    }
    report["real_model_measurements"] = {
        "status": "not_measured",
        "model_checkpoint": None,
        "token_usage": None,
        "gpu_hours": None,
        "provider_cost": None,
    }
    report["group_artifacts"] = [f"group-{number}.json" for number in range(1, 6)]
    return report


def _report_markdown(report: dict[str, Any]) -> str:
    data = report["data_summary"]
    simulation = report["simulation_summary"]
    lines = [
        "# Chapter 15 deterministic post-training report",
        "",
        "> 有限动作、固定夹具、无 GPU 教学实验；不代表真实大模型训练效果。",
        "",
        "## Data audit",
        "",
        f"- Raw trajectories: `{data['raw_count']}`",
        f"- Eligible trajectories: `{data['eligible_count']}`",
        f"- Quarantined trajectories: `{data['quarantined_count']}`",
        f"- Train-only SFT examples: `{data['supervised_example_count']}`",
        "",
        "## Static reward replay (not training)",
        "",
        "| Variant | Outcome rate | Safety violations | Protected writes | Mean steps |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ("outcome_only", "scalar_penalty", "hard_gate"):
        metrics = simulation["variants"][name]["metrics"]
        lines.append(
            f"| {name} | {metrics['outcome_rate']:.6f} | {metrics['safety_violations']} | "
            f"{metrics['protected_writes']} | {metrics['mean_steps']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Reward-driven policy updates",
            "",
            "One-state bandit, categorical sampling, REINFORCE without baseline; no tools executed.",
            "",
            "| Variant | Updates | P(edit) after | P(modify_tests) after | Exploration safety events | Steps |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            *(
                f"| {name} | {run['updates']} | {run['probabilities_after']['edit']:.6f} | "
                + (f"{run['probabilities_after']['modify_tests']:.6f}" if 'modify_tests' in run['probabilities_after'] else 'masked')
                + f" | {run['safety_violations']} | {run['steps_used']} |"
                for name, run in simulation["policy_updates"].items()
            ),
            "",
            f"Budget demo: {simulation['budget_demo']['updates']} updates, {simulation['budget_demo']['steps_used']}/12 steps; conservative reservation stops further sampling.",
            "",
            "## Release",
            "",
            f"- Final decision: `{report['release_decision']}`",
            f"- Unsafe candidate: `{simulation['unsafe_candidate_release']['decision']}`",
            f"- Stable schema: `{report['schema_version']}`",
            "- The pass decision is static gate conformance, not independent evaluation of the learned policy or permission to publish a model.",
            "",
            "## Evidence limits",
            "",
            *(f"- `{item}`" for item in report["evidence_limits"]),
            "",
        ]
    )
    return "\n".join(lines)


def _write_artifacts(output: Path, groups: dict[int, dict[str, Any]], report: dict[str, Any]) -> None:
    for number in range(1, 6):
        (output / f"group-{number}.json").write_bytes(_json_bytes(groups[number]))
    (output / "post-training-report.json").write_bytes(_json_bytes(report))
    (output / "post-training-report.md").write_text(
        _report_markdown(report), encoding="utf-8", newline="\n"
    )
    artifact_names = [
        *(f"group-{number}.json" for number in range(1, 6)),
        "post-training-report.json",
        "post-training-report.md",
    ]
    manifest = {
        "schema_version": "chapter15.artifact-manifest.v1",
        "artifacts": [
            {
                "name": name,
                "bytes": (output / name).stat().st_size,
                "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
            }
            for name in artifact_names
        ],
    }
    (output / "manifest.json").write_bytes(_json_bytes(manifest))


def build_post_training_report(output: Path) -> dict[str, Any]:
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("output_directory_not_empty")
    groups = {number: _group_payload(number) for number in range(1, 6)}
    report = _build_report(groups)
    staging = output.parent / f".{output.name}.staging"
    if staging.exists():
        raise FileExistsError("staging_directory_exists")
    staging.mkdir(parents=True)
    try:
        _write_artifacts(staging, groups, report)
        if output.exists():
            output.rmdir()
        staging.rename(output)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return report


def _replace_report(output: Path) -> dict[str, Any]:
    backup = output.parent / f"{output.name}.previous"
    if backup.exists():
        raise FileExistsError("recoverable_backup_exists")
    if output.exists():
        output.rename(backup)
    try:
        return build_post_training_report(output)
    except Exception:
        if output.exists():
            shutil.rmtree(output)
        if backup.exists():
            backup.rename(output)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("1", "2", "3", "4", "5", "all"), default="all")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    if args.group == "all":
        if args.replace:
            _replace_report(args.output)
        else:
            build_post_training_report(args.output)
    else:
        number = int(args.group)
        target = args.output / f"group-{number}.json"
        backup = target.with_suffix(".json.previous")
        target_preexisted = target.exists()
        if target_preexisted and not args.replace:
            raise FileExistsError(f"artifact_exists:{target.name}")
        backup_created = False
        if args.replace and target_preexisted:
            if backup.exists():
                raise FileExistsError("recoverable_backup_exists")
            target.rename(backup)
            backup_created = True
        try:
            run_group(number, args.output)
        except Exception:
            if backup_created:
                if target.exists():
                    target.unlink()
                backup.rename(target)
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
