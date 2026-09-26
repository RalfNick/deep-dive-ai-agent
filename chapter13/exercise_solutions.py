"""Runnable evidence for experiments and structured answers for design exercises."""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
from typing import Callable

from .dataset import load_tasks
from .experiments import run_group
from .grading import grade_trial, release_decision
from .judge import calibrate_offline
from .metrics import heterogeneous_bootstrap_example, pass_all_k, pass_at_k
from .runner import run_trial


TITLES = {
    1: "区分 Final Answer、Outcome 与 Trajectory",
    2: "读取同一句完成声明背后的证据",
    3: "手算 pass@1、pass@3 与 pass^3",
    4: "写一条无歧义 TaskSpec",
    5: "区分环境错误与 Agent 失败",
    6: "为退款任务设计轨迹不变量",
    7: "验证安全硬门禁",
    8: "验证切片回归门禁",
    9: "按产品语义选择可靠性指标",
    10: "执行固定种子的成对 Bootstrap",
    11: "读取 Judge 校准证据",
    12: "设计防投机边界",
    13: "映射成熟评估框架",
    14: "定位 Agent、Task、Grader 或环境问题",
}


def _answer(number: int, criteria: list[str], evidence: dict, *,
            status: str = "passed", execution: str = "computed") -> dict:
    return {
        "number": number,
        "title": TITLES[number],
        "status": status,
        "execution": execution,
        "criteria": criteria,
        "evidence": evidence,
    }


def _exercise_1() -> dict:
    return _answer(1, ["三类证据的 owner 不混淆", "反例同时说明结果与过程"], {
        "final_answer": "Agent 声称做了什么；不能单独证明环境改变",
        "outcome": "运行结束时可独立观察的环境事实",
        "trajectory": "从输入到终态的事件、工具、策略和状态序列",
        "counterexample": "退款到账，但 Agent 先重复扣款再回滚；结果可接受，过程不可接受",
    }, status="answered", execution="design")


def _exercise_2() -> dict:
    with tempfile.TemporaryDirectory(prefix="chapter13-ex2-") as directory:
        report = run_group(1, Path(directory))
    observation = report["observations"]
    return _answer(2, ["使用真实 group-1 实验", "比较回复、结果、完整性与事件"], {
        "same_final_answer": observation["same_final_answer"],
        "same_outcome": observation["same_outcome"],
        "key_differences": ["solution_matches", "protected_paths_intact", "events"],
        "conclusion": "文本相同只证明声明相同，不能推出任务成功",
    }, execution="real")


def _exercise_3() -> dict:
    n, c, k = 5, 2, 3
    return _answer(3, ["使用无放回组合估计", "区分至少一次成功与全部成功"], {
        "n": n, "c": c, "k": k,
        "pass_1": c / n,
        "pass_at_3": pass_at_k(n, c, k),
        "pass_all_3": pass_all_k(n, c, k),
    })


def _exercise_4() -> dict:
    return _answer(4, ["成功条件可独立验证", "保持 basic 切片数量不变"], {
        "replacement": {
            "task_id": "basic-mailto-link",
            "prompt": "检查器必须跳过 mailto 链接，同时继续报告缺失的本地 Markdown 文件",
            "success_conditions": ["mailto:user@example.com 不报错", "missing.md 仍报错"],
            "allowed_write_prefixes": ["src/"],
            "protected_paths": ["tests/", ".eval/"],
        },
        "slice_balance": "用此任务替换一个 basic 任务，而不是追加第 13 个任务",
    }, status="answered", execution="design")


def _exercise_5() -> dict:
    return _answer(5, ["不把基础设施噪声计作能力失败", "承认分类所需上下文"], {
        "dependency_download_failed": "environment_error，前提是依赖源和网络由评测方提供",
        "agent_step_budget_exhausted": "agent_failed",
        "test_process_oom": "requires attribution before setting Trial.status; then environment_error or agent_failed",
        "invalid_tool_arguments": "agent_failed，前提是工具 schema 与解析器正常",
        "extra_facts": ["resource limits", "infrastructure health", "tool schema version", "retry ownership"],
    }, status="answered", execution="design")


def _exercise_6() -> dict:
    return _answer(6, ["约束不变量而非唯一工具序列", "覆盖授权、幂等和验收"], {
        "invariants": [
            "任何 refund_execute 之前必须存在绑定同一订单与金额的有效批准",
            "同一 refund_id 最多出现一个成功副作用回执",
            "宣布完成前必须读取支付方终态并与目标金额一致",
        ]
    }, status="answered", execution="design")


def _exercise_7() -> dict:
    task = load_tasks()[0]
    with tempfile.TemporaryDirectory(prefix="chapter13-ex7-") as directory:
        original = run_trial(task, "candidate", 0, 101, Path(directory) / "workspace")
    injected_events = list(original.events)
    injected_events[-1] = dict(injected_events[-1], seq=5)
    injected_events.insert(-1, {"seq": 4, "kind": "policy_violation",
                                "path": "tests/public.txt", "verdict": "detected"})
    modified = replace(original, events=tuple(injected_events))
    graders = grade_trial(modified, task.max_steps, task.max_tool_calls,
                          allowed_write_prefixes=task.allowed_write_prefixes,
                          protected_paths=task.protected_paths,
                          success_conditions=task.success_conditions)
    by_name = {grader.name: grader for grader in graders}
    decision = release_decision(
        candidate={"pass_1": 1.0,
                   "safety_violations": by_name["safety"].metrics["violation_count"],
                   "protected_mutations": 0, "environment_errors": 0,
                   "invalid_records": 0},
        baseline={"pass_1": 0.8},
        slice_deltas={"basic": 0.2, "edge": 0.2, "safety": 0.2, "recovery": 0.2},
        split_deltas={"capability": 0.2, "regression": 0.2, "adversarial": 0.2},
        confidence={"lower": 0.1, "upper": 0.3})
    return _answer(7, ["Outcome 可以通过而 Safety 失败", "效率不得抵消安全违规"], {
        "trial_modified": True,
        "outcome": by_name["outcome"].verdict,
        "safety": by_name["safety"].verdict,
        "efficiency": by_name["efficiency"].verdict,
        "release": decision,
    }, execution="real")


def _exercise_8() -> dict:
    decision = release_decision(
        candidate={"pass_1": 0.80, "safety_violations": 0,
                   "protected_mutations": 0, "environment_errors": 0},
        baseline={"pass_1": 0.75},
        slice_deltas={"basic": 0.10, "edge": 0.04, "safety": -0.12, "recovery": 0.02},
        split_deltas={"capability": 0.05, "regression": 0.05, "adversarial": -0.12},
        confidence={"lower": 0.01, "upper": 0.09},
    )
    return _answer(8, ["总体提升不覆盖关键切片回归", "给出修复后重跑动作"], {
        "overall_delta": 0.05,
        "safety_slice_delta": -0.12,
        "release": decision,
        "next_step": "定位安全切片失败，修复后用相同任务和种子成对重跑",
    }, execution="real")


def _exercise_9() -> dict:
    return _answer(9, ["指标由使用方式决定", "说明失败成本"], {
        "code_candidate_generation": "pass@k；允许生成多个候选后由测试选择",
        "automatic_refund": "pass^k；每次真实执行都必须可靠",
        "research_report": "pass@k when editor selects; pass^k when auto-published repeatedly",
        "batch_rename": "pass^k；一批中的任一次错误都可能破坏文件",
    }, status="answered", execution="design")


def _exercise_10() -> dict:
    example = heterogeneous_bootstrap_example()
    return _answer(10, ["以任务为重采样单位", "固定随机种子", "区间跨零不强行分胜负"], {
        "task_deltas": example["task_deltas"],
        "bootstrap": example["paired_confidence"],
        "interpretation": example["interpretation"],
    }, execution="real")


def _exercise_11() -> dict:
    source = Path(__file__).with_name("fixtures") / "judge-calibration.json"
    fixture = json.loads(source.read_text(encoding="utf-8"))
    before = calibrate_offline(source)
    cases = {case["case_id"]: case for case in fixture["cases"]}
    cases["j07"]["prediction"] = "unknown"
    cases["j12"]["prediction"] = "pass"
    with tempfile.TemporaryDirectory(prefix="chapter13-ex11-") as directory:
        changed = Path(directory) / "judge-calibration.json"
        changed.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
        after = calibrate_offline(changed)
    return _answer(11, ["实际调整两个预测标签", "总体一致率与混淆方向分开报告",
                        "Unknown 计入覆盖率"], {
        "changed_cases": ["j07: fail -> unknown", "j12: unknown -> pass"],
        "agreement_unchanged": before["agreement"] == after["agreement"],
        "confusion_changed": before["confusion_matrix"] != after["confusion_matrix"],
        "before": {"agreement": before["agreement"], "coverage": before["coverage"],
                   "confusion_matrix": before["confusion_matrix"]},
        "after": {"agreement": after["agreement"], "coverage": after["coverage"],
                  "confusion_matrix": after["confusion_matrix"]},
        "risk_rule": "高风险自动动作中，gold=fail 被判 pass 比保守的 unknown 更危险",
    }, execution="real")


def _exercise_12() -> dict:
    return _answer(12, ["四种污染各有独立控制", "检测不能只依赖 Agent 自报"], {
        "hidden_tests": "放在被测进程不可读、只由外部 grader 挂载的位置",
        "oracle": "凭据与答案不进入 Agent 工作区，访问事件由外部策略记录",
        "git_history": "从净化快照创建任务，移除泄漏修复的提交和远端",
        "cross_trial_cache": "每个 Trial 使用新工作区和命名空间，并校验初始环境指纹",
    }, status="answered", execution="design")


def _exercise_13() -> dict:
    return _answer(13, ["映射抽象而非背 API", "保留业务责任"], {
        "inspect_ai": {
            "TaskSpec": "Task + Dataset sample", "Runner": "Solver",
            "Graders": "Scorer", "Report": "Eval log / metrics",
        },
        "business_owned": ["任务真实性与污染控制", "安全不变量", "发布阈值与人工升级"],
    }, status="answered", execution="design")


def _exercise_14() -> dict:
    return _answer(14, ["按证据层排查", "每一步有停止标准"], {
        "sequence": [
            "先复现环境并核对环境指纹；同夹具健康则排除环境",
            "双人复核 Task 与成功条件；达成一致则排除任务歧义",
            "用人工金标和反例校准 Grader；误差在阈值内则排除评分漂移",
            "在相同任务、种子和 Harness 下成对重跑；剩余稳定差值归因给 Agent 变更",
        ],
        "stop_rule": "每个排除结论都必须有可复现记录，证据冲突时结论保持 inconclusive",
    }, status="answered", execution="design")


SOLVERS: dict[int, Callable[[], dict]] = {
    1: _exercise_1, 2: _exercise_2, 3: _exercise_3, 4: _exercise_4,
    5: _exercise_5, 6: _exercise_6, 7: _exercise_7, 8: _exercise_8,
    9: _exercise_9, 10: _exercise_10, 11: _exercise_11, 12: _exercise_12,
    13: _exercise_13, 14: _exercise_14,
}


def solve(number: int) -> dict:
    if type(number) is not int or number not in SOLVERS:
        raise ValueError("unknown_exercise")
    return SOLVERS[number]()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Chapter 13 reference solutions")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--number", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        print("output_exists", file=sys.stderr)
        return 3
    numbers = range(1, 15) if args.all else [args.number]
    answers = [solve(number) for number in numbers]
    payload = {
        "schema_version": "chapter13.exercises.v1",
        "answers": answers,
        "summary": {
            "count": len(answers),
            "all_passed": all(item["status"] in {"passed", "answered"} for item in answers),
        },
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
