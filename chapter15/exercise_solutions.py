"""Runnable evidence and explicit rubrics for the Chapter 15 exercises."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Callable, Mapping

from chapter15.audit import audit_dataset, build_supervised_examples
from chapter15.dataset import load_trajectories
from chapter15.intervention import load_failure_cases, recommend_intervention
from chapter15.objectives import dpo_loss, dpo_margin, load_preference_pairs
from chapter15.simulator import run_policy_variant


ROOT = Path(__file__).resolve().parent

TITLES = {
    1: "区分 Context、Harness 与后训练",
    2: "运行干预树",
    3: "解释数据隔离理由",
    4: "设计任务家族切分",
    5: "手算 SFT 交叉熵",
    6: "补齐恢复切片",
    7: "手算 DPO",
    8: "审计偏好来源",
    9: "识别奖励投机",
    10: "设计切片回归门禁",
    11: "编写 Trace 数据卡",
    12: "作出发布判断",
    13: "设计真实训练迁移清单",
}


def _answer(
    number: int,
    criteria: list[str],
    evidence: Mapping[str, object],
    *,
    status: str = "passed",
    execution: str = "computed",
) -> dict[str, object]:
    return {
        "number": number,
        "title": TITLES[number],
        "status": status,
        "execution": execution,
        "criteria": criteria,
        "evidence": dict(evidence),
    }


def _exercise_1() -> dict[str, object]:
    return _answer(1, ["按根因选择最小干预", "每项保留待补证据"], {
        "missing_policy": {"intervention": "rag_context", "needed_evidence": "检索到最新政策后失败消失"},
        "duplicate_write": {"intervention": "harness", "needed_evidence": "幂等键或重试边界能消除重复副作用"},
        "missing_field": {"intervention": "post_training_candidate", "needed_evidence": "格式约束和确定性校验后仍跨任务重复"},
        "rule": "先排除信息、指令、执行边界和模型路由问题，再把稳定策略偏差送入后训练",
    }, status="answered", execution="design")


def _exercise_2() -> dict[str, object]:
    observations = load_failure_cases()
    decisions = [recommend_intervention(item) for item in observations]
    return _answer(2, ["复用规范干预路由", "解释训练为何不是默认项"], {
        "decisions": {
            item.observation_id: decision.recommended.value
            for item, decision in zip(observations, decisions, strict=True)
        },
        "post_training_cases": sum(decision.recommended.value == "post_training" for decision in decisions),
        "always_train_incorrect_cases": sum(decision.recommended.value != "post_training" for decision in decisions),
    }, execution="real")


def _exercise_3() -> dict[str, object]:
    audit = audit_dataset(load_trajectories())
    examples = build_supervised_examples(audit)
    return _answer(3, ["结果与过程分开审计", "训练只消费 eligible 且 train 的记录"], {
        "raw_count": audit.raw_count,
        "eligible_count": len(audit.eligible_ids),
        "quarantined_count": len(audit.quarantined_ids),
        "sft_example_count": len(examples),
        "reasons": {
            "protected_write": "成功来自改变验收规则，不能作为好示范",
            "hidden_answer_access": "使用评测不可见信息，破坏独立性",
            "missing_tool_result": "轨迹不完整，动作与结果不可复核",
        },
    }, execution="real")


def _exercise_4() -> dict[str, object]:
    return _answer(4, ["隔离单位覆盖近重复来源", "split 后复查家族交叉"], {
        "family_key": ["normalized_task_intent", "success_condition", "repository_family"],
        "isolation_unit": "repository_family",
        "reason": "同一仓库的模板、修复模式和测试结构高度相关，按记录随机切分会把近重复送到 eval",
        "procedure": ["人工家族分组", "组级分配 split", "规范化文本指纹辅助与传递闭包", "隔离跨 split 家族", "抽样补查同义近重复"],
    }, status="answered", execution="design")


def _exercise_5() -> dict[str, object]:
    loss = -math.log(1 / 6)
    return _answer(5, ["写出可复算输入", "区分训练目标与任务结果"], {
        "action_count": 6,
        "uniform_probability": round(1 / 6, 6),
        "uniform_cross_entropy": round(loss, 6),
        "interpretation": "目标动作概率上升只证明有限策略按示范方向更新，不证明真实任务成功率提高",
    }, execution="real")


def _exercise_6() -> dict[str, object]:
    return _answer(6, ["覆盖 tool_timeout 状态", "示范通过完整性与安全审计"], {
        "example": {"state_id": "tool_timeout", "target_action": "retry", "retention_reason": "audited_recovery_policy"},
        "required_checks": [
            "tool result complete", "retry is idempotent", "budget remains", "no protected write",
            "no hidden answer access", "known provenance", "train split only",
        ],
    }, status="answered", execution="design")


def _exercise_7() -> dict[str, object]:
    pair = next(item for item in load_preference_pairs() if item.pair_id == "pair-write-requested")
    margin = dpo_margin(pair, beta=0.5)
    loss = dpo_loss(pair, beta=0.5)
    return _answer(7, ["chosen 与 rejected 来自同一状态", "复算策略和参考策略间隔"], {
        "policy_margin": 0.4,
        "reference_margin": 0.1,
        "beta": 0.5,
        "margin": round(margin, 6),
        "loss": round(loss, 6),
        "swap_effect": "交换 chosen/rejected 后 margin 变为 -0.15，loss 上升",
    }, execution="real")


def _exercise_8() -> dict[str, object]:
    return _answer(8, ["偏好来源可追溯", "允许证据不足为 Unknown"], {
        "sources": {
            "safety_rule": ["确定且可审计", "覆盖不到未知风险"],
            "verifier_rule": ["可重复", "Verifier 可能被投机"],
            "human": ["接近真实意图", "成本高且标注者不一致"],
            "llm_judge": ["扩展快", "可能有长度、风格和同源偏差"],
        },
        "merge_rule": "安全规则先否决；确定性规则一致则保留；语义分歧进入人工抽样；证据不足返回 Unknown",
    }, status="answered", execution="design")


def _exercise_9() -> dict[str, object]:
    scalar = run_policy_variant("scalar_penalty", episodes=200, seed=1501)
    gated = run_policy_variant("hard_gate", episodes=200, seed=1501)
    return _answer(9, ["复算可抵消惩罚", "用不可补偿门禁表达安全"], {
        "unsafe_outcome_score": 10.0,
        "safety_penalty": -3.0,
        "scalar_penalty_score": scalar.action_scores["modify_tests"],
        "safe_edit_score": scalar.action_scores["edit"],
        "scalar_safety_violations": scalar.metrics.safety_violations,
        "hard_gate_safety_violations": gated.metrics.safety_violations,
        "gate": "if safety_violation or protected_write: release=fail; do not compute compensating total",
    }, execution="real")


def _exercise_10() -> dict[str, object]:
    return _answer(10, ["覆盖四个切片", "安全与关键切片先于总体均值"], {
        "minimum_tasks": {"basic": 3, "boundary": 3, "safety": 4, "recovery": 4},
        "gates": [
            "safety violations == 0", "protected writes == 0", "environment errors == 0",
            "each critical slice delta >= -0.10", "overall candidate >= baseline",
        ],
        "threshold_basis": "教学阈值；真实项目需由事故成本、样本量和置信区间共同校准",
    }, status="answered", execution="design")


def _exercise_11() -> dict[str, object]:
    return _answer(11, ["数据卡包含治理字段", "禁止用途明确"], {
        "dataset_card": {
            "source": "经授权的内部 Agent Trace，经应用侧脱敏后导出",
            "license_and_owner": "组织内部授权；数据所有者可追溯",
            "privacy": "密钥删除，标识符盐化摘要，敏感正文隔离",
            "retention": "候选数据 90 天，获批版本按治理策略保留",
            "split": "按仓库与任务家族分组后切分",
            "known_gaps": ["低频安全事件", "新工具", "非中文任务"],
            "prohibited": ["训练未经审计原始 Trace", "用 eval 数据选择 checkpoint", "恢复原始身份"],
        }
    }, status="answered", execution="design")


def _exercise_12() -> dict[str, object]:
    return _answer(12, ["区分环境错误与策略失败", "关键切片退化不可由总体提升抵消"], {
        "decision": "inconclusive_then_fail_if_confirmed",
        "first_step": "修复或隔离 3% 环境超时并重跑成对评测",
        "confirmed_decision": "fail",
        "reason_codes": ["evaluation_environment_error", "slice_regression"],
        "reason": "恢复切片下降 0.12 超过教学门槛 0.10；总体 +0.04 不能补偿",
    }, status="answered", execution="design")


def _exercise_13() -> dict[str, object]:
    return _answer(13, ["方案覆盖输入语义、训练、评测和回滚", "不声称已经训练"], {
        "example_base_model": "选择许可与硬件匹配的开源 instruct checkpoint",
        "checklist": [
            "固定 tokenizer 与 chat template", "转换 audited train 数据", "验证 validation/eval 不回流",
            "选择 LoRA/QLoRA 并记录配置", "小批 smoke test", "冻结候选 checkpoint",
            "运行安全、切片和总体回归", "灰度并保留 baseline 路由", "触发门槛后回滚",
        ],
        "evidence_limit": "设计答案；未下载模型、未执行 GPU 训练、未证明 Provider 兼容性",
    }, status="answered", execution="design")


SOLVERS: dict[int, Callable[[], dict[str, object]]] = {
    1: _exercise_1, 2: _exercise_2, 3: _exercise_3, 4: _exercise_4,
    5: _exercise_5, 6: _exercise_6, 7: _exercise_7, 8: _exercise_8,
    9: _exercise_9, 10: _exercise_10, 11: _exercise_11, 12: _exercise_12,
    13: _exercise_13,
}


def solve(number: int) -> dict[str, object]:
    if type(number) is not int or number not in SOLVERS:
        raise ValueError("unknown_exercise")
    return SOLVERS[number]()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Chapter 15 reference solutions")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--number", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.output is not None and args.output.exists():
        print("output_exists", file=sys.stderr)
        return 3

    numbers = list(range(1, 14)) if args.all else [args.number]
    answers = [solve(number) for number in numbers]
    payload = {
        "schema_version": "chapter15.exercises.v1",
        "answers": answers,
        "summary": {
            "count": len(answers),
            "all_passed": all(item["status"] in {"passed", "answered"} for item in answers),
        },
        "limits": [
            "design_answers_are_rubrics_not_unique_proofs",
            "finite_policy_not_real_model_training",
            "no_provider_conformance_claim",
        ],
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
