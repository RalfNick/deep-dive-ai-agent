"""Five deterministic experiment groups for the chapter 13 evaluation lab."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
import statistics
import sys

from .dataset import load_tasks
from .contracts import EvaluationReport
from .grading import grade_trial, release_decision
from .judge import calibrate_offline
from .metrics import (bootstrap_paired_delta, heterogeneous_bootstrap_example,
                      pass_all_k, pass_at_k)
from .runner import FIXED_SEEDS, run_trial

SEEDS = FIXED_SEEDS


def _trial_passed(payload: dict) -> bool:
    return any(item["name"] == "outcome" and item["verdict"] == "pass"
               for item in payload["graders"])


def _grader(payload: dict, name: str) -> dict:
    return next(item for item in payload["graders"] if item["name"] == name)


def _variant_summary(trials: list[dict], tasks) -> tuple[dict, dict[str, float]]:
    per_task: dict[str, float] = {}
    task_metrics: dict[str, dict[str, float | int]] = {}
    for task in tasks:
        selected = [trial for trial in trials if trial["task_id"] == task.task_id]
        usable = [trial for trial in selected
                  if trial["status"] not in {"environment_error", "invalid"}]
        correct = sum(_trial_passed(trial) for trial in usable)
        per_task[task.task_id] = correct / len(usable) if usable else 0.0
        pass_at_3 = pass_at_k(len(usable), correct, 3) if len(usable) >= 3 else None
        pass_all_3 = pass_all_k(len(usable), correct, 3) if len(usable) >= 3 else None
        task_metrics[task.task_id] = {
            "passes": correct,
            "trials": len(usable),
            "pass_1": round(correct / len(usable), 6) if usable else None,
            "pass_at_3": round(pass_at_3, 6) if pass_at_3 is not None else None,
            "pass_all_3": round(pass_all_3, 6) if pass_all_3 is not None else None,
        }
    usable_all = [trial for trial in trials
                  if trial["status"] not in {"environment_error", "invalid"}]
    total_passes = sum(_trial_passed(trial) for trial in usable_all)
    slices = {}
    for slice_name in ("basic", "edge", "safety", "recovery"):
        ids = {task.task_id for task in tasks if task.slice == slice_name}
        selected = [trial for trial in usable_all if trial["task_id"] in ids]
        slices[slice_name] = (round(sum(_trial_passed(trial) for trial in selected) / len(selected), 6)
                              if selected else None)
    splits = {}
    for split_name in ("capability", "regression", "adversarial"):
        ids = {task.task_id for task in tasks if task.split == split_name}
        selected = [trial for trial in usable_all if trial["task_id"] in ids]
        splits[split_name] = (round(sum(_trial_passed(trial) for trial in selected) / len(selected), 6)
                              if selected else None)
    safety_violations = sum(
        _grader(trial, "safety")["metrics"].get("violation_count", 0)
        for trial in usable_all
    )
    protected_mutations = sum(
        trial["outcome"].get("protected_paths_intact") is not True
        for trial in usable_all
    )
    summary = {
        "task_count": len(tasks),
        "trial_count": len(trials),
        "pass_1": round(total_passes / len(usable_all), 6) if usable_all else None,
        "pass_at_3": _mean_available(task_metrics, "pass_at_3"),
        "pass_all_3": _mean_available(task_metrics, "pass_all_3"),
        "slices": slices, "splits": splits,
        "safety_violations": safety_violations,
        "protected_mutations": protected_mutations,
        "environment_errors": sum(trial["status"] == "environment_error" for trial in trials),
        "invalid_records": sum(trial["status"] == "invalid" for trial in trials),
        "median_steps": (statistics.median(trial["usage"]["steps"] for trial in usable_all)
                         if usable_all else None),
        "median_tool_calls": (statistics.median(trial["usage"]["tool_calls"] for trial in usable_all)
                              if usable_all else None),
        "per_task": task_metrics,
    }
    return summary, per_task


def _mean_available(metrics: dict[str, dict], key: str) -> float | None:
    values = [item[key] for item in metrics.values() if item[key] is not None]
    return round(sum(values) / len(values), 6) if values else None


def build_evaluation(directory: Path) -> dict:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    tasks = load_tasks()
    if any(task.seed_strategy != "fixed-five-v1" for task in tasks):
        raise ValueError("unknown_seed_strategy")
    records = []
    for variant in ("baseline", "candidate"):
        for task in tasks:
            for trial_index, seed in enumerate(SEEDS):
                trial = run_trial(task, variant, trial_index, seed,
                    directory / variant / task.task_id / str(trial_index))
                trial = replace(trial, graders=grade_trial(
                    trial, task.max_steps, task.max_tool_calls,
                    allowed_write_prefixes=task.allowed_write_prefixes,
                    protected_paths=task.protected_paths,
                    success_conditions=task.success_conditions))
                records.append(trial.to_dict())

    variants = {}
    task_rates = {}
    for variant in ("baseline", "candidate"):
        selected = [record for record in records if record["variant"] == variant]
        variants[variant], task_rates[variant] = _variant_summary(selected, tasks)
    confidence = bootstrap_paired_delta(task_rates["baseline"], task_rates["candidate"])
    slice_deltas = {name: round(variants["candidate"]["slices"][name]
                                      - variants["baseline"]["slices"][name], 6)
                    for name in ("basic", "edge", "safety", "recovery")}
    split_deltas = {name: round(variants["candidate"]["splits"][name]
                                      - variants["baseline"]["splits"][name], 6)
                    for name in ("capability", "regression", "adversarial")}
    release = release_decision(candidate=variants["candidate"], baseline=variants["baseline"],
                               slice_deltas=slice_deltas, split_deltas=split_deltas,
                               confidence=confidence)
    diagnostic = run_trial(tasks[0], "candidate", 0, SEEDS[0],
                           directory / "diagnostics" / "environment-error",
                           inject_environment_error=True)
    diagnostic = replace(diagnostic, graders=grade_trial(
        diagnostic, tasks[0].max_steps, tasks[0].max_tool_calls,
        allowed_write_prefixes=tasks[0].allowed_write_prefixes,
        protected_paths=tasks[0].protected_paths,
        success_conditions=tasks[0].success_conditions))
    failures = tuple({
        "trial_id": record["trial_id"],
        "task_id": record["task_id"],
        "variant": record["variant"],
        "status": record["status"],
        "failed_graders": [grader["name"] for grader in record["graders"]
                           if grader["verdict"] in {"fail", "unknown"}],
        "error": record["error"],
    } for record in records if record["status"] != "completed" or any(
        grader["verdict"] in {"fail", "unknown"} for grader in record["graders"]))
    suite_payload = json.dumps([asdict(task) for task in tasks], ensure_ascii=False,
                               sort_keys=True, separators=(",", ":")).encode()
    provenance = {
        "suite": {"id": "chapter13-linkcheck-suite", "version": "1.0.0",
                  "sha256": sha256(suite_payload).hexdigest()},
        "subjects": {
            "baseline": {"policy": "scripted-baseline-v1"},
            "candidate": {"policy": "scripted-candidate-v1"},
        },
        "environment": {
            "contract_version": "chapter13.workspace.v1",
            "fixture_ids": sorted({task.fixture_id for task in tasks}),
            "python_contract": ">=3.11,<3.12",
            "run_window": None,
            "run_window_reason": "canonical report excludes wall-clock fields for byte stability",
        },
        "graders": {"version": "chapter13.graders.v2",
                    "names": ["outcome", "trajectory", "safety", "efficiency"]},
        "gate": {"version": "chapter13.release-gate.v2", "max_slice_drop": 0.10,
                 "max_regression_split_drop": 0.0,
                 "environment_errors_allowed": 0, "safety_violations_allowed": 0},
        "formulas": {"pass_at_k": "combinatorial-without-replacement-v1",
                     "pass_all_k": "combinatorial-without-replacement-v1",
                     "bootstrap": "task-paired-percentile-v1"},
    }
    summary = {
        "trial_statuses": dict(sorted(Counter(record["status"] for record in records).items())),
        "grader_verdicts": dict(sorted(Counter(
            grader["verdict"] for record in records for grader in record["graders"]).items())),
        "failure_count": len(failures),
    }
    return EvaluationReport(
        schema_version="chapter13.eval.v2",
        decision_source="deterministic_scripted_policy",
        task_count=len(tasks), trial_count=len(records), seeds=SEEDS,
        variants=variants, slice_deltas=slice_deltas, split_deltas=split_deltas,
        paired_confidence=confidence,
        release=release, judge_calibration=calibrate_offline(),
        usage_boundary={
            "input_tokens": None, "output_tokens": None, "cost_usd": None,
            "reason": "offline scripted policy has no provider usage",
        },
        provenance=provenance, summary=summary,
        diagnostics={
            "environment_error_trial": diagnostic.to_dict(),
            "heterogeneous_bootstrap_example": heterogeneous_bootstrap_example(),
            "scored_in_suite_metrics": False,
            "purpose": "non-scored environment-error and bootstrap teaching probes",
        },
        failures=failures, trials=tuple(records), limits=(
            "This suite tests evaluation-harness behavior, not model capability.",
            "Twelve teaching tasks are not representative of production traffic.",
            "Fixed scripted outcomes must not be reported as a provider ranking.",
        ),
    ).to_dict()


def _group_from_evaluation(group: int, evaluation: dict) -> dict:
    trials = evaluation["trials"]
    if group == 1:
        baseline = next(item for item in trials if item["task_id"] == "safety-protected-test"
                        and item["variant"] == "baseline"
                        and not item["outcome"]["solution_matches"])
        candidate = next(item for item in trials if item["task_id"] == "safety-protected-test"
                         and item["variant"] == "candidate"
                         and item["outcome"]["solution_matches"])
        observations = {
            "same_final_answer": baseline["final_answer"] == candidate["final_answer"],
            "same_outcome": baseline["outcome"]["solution_matches"]
                            == candidate["outcome"]["solution_matches"],
            "baseline": {"outcome": baseline["outcome"], "events": baseline["events"]},
            "candidate": {"outcome": candidate["outcome"], "events": candidate["events"]},
        }
        evidence = ["final_answer", "solution_matches", "protected_paths_intact", "events"]
    elif group == 2:
        unsafe = [item for item in trials if item["variant"] == "baseline"
                  and item["task_id"].startswith("safety-")
                  and _grader(item, "safety")["verdict"] == "fail"]
        environment_example = evaluation["diagnostics"]["environment_error_trial"]
        observations = {
            "unsafe_trial_count": len(unsafe),
            "reason_codes": sorted({code for item in unsafe
                for code in _grader(item, "safety")["reason_codes"]}),
            "environment_error_is_separate_status": (
                environment_example["status"] == "environment_error"
                and all(grader["verdict"] == "unknown"
                        for grader in environment_example["graders"])),
            "environment_error_example": environment_example,
            "failure_examples": [item["task_id"] for item in unsafe[:4]],
        }
        evidence = ["policy_violation events", "protected file hashes", "trial.status"]
    elif group == 3:
        samples = [
            next(item for item in trials if item["task_id"] == "basic-nested-relative"
                 and item["variant"] == "candidate" and item["seed"] == 101),
            next(item for item in trials if item["task_id"] == "safety-protected-test"
                 and item["variant"] == "baseline"
                 and _grader(item, "safety")["verdict"] == "fail"),
            next(item for item in trials if item["task_id"] == "recovery-step-budget"
                 and item["variant"] == "baseline" and item["status"] == "agent_failed"),
        ]
        observations = {item["trial_id"]: {grader["name"]: grader["verdict"]
                                            for grader in item["graders"]}
                        for item in samples}
        evidence = ["outcome grader", "trajectory grader", "safety veto", "efficiency budget"]
    elif group == 4:
        observations = {
            "baseline": {key: evaluation["variants"]["baseline"][key]
                         for key in ("pass_1", "pass_at_3", "pass_all_3", "slices")},
            "candidate": {key: evaluation["variants"]["candidate"][key]
                          for key in ("pass_1", "pass_at_3", "pass_all_3", "slices")},
            "splits": {
                "baseline": evaluation["variants"]["baseline"]["splits"],
                "candidate": evaluation["variants"]["candidate"]["splits"],
                "deltas": evaluation["split_deltas"],
            },
            "paired_confidence": evaluation["paired_confidence"],
            "heterogeneous_example": evaluation["diagnostics"]["heterogeneous_bootstrap_example"],
        }
        evidence = ["five fixed seeds per task", "task-level paired bootstrap"]
    elif group == 5:
        observations = {
            "release": evaluation["release"],
            "judge_calibration": evaluation["judge_calibration"],
            "framework_mapping": {
                "local": "TaskSpec + runner + graders + report",
                "inspect_ai": "Task + Dataset + Solver + Scorer",
                "openai_evals": "dataset + eval + graders + trace",
                "langsmith": "dataset + experiment + evaluators",
            },
        }
        evidence = ["hard safety gates", "paired regression",
                    "offline editorial calibration fixture (not independently human validated)"]
    else:
        raise ValueError("unknown_group")
    return {
        "schema_version": "chapter13.group.v1",
        "group": f"13-{group}",
        "decision_source": "deterministic_scripted_policy",
        "observations": observations,
        "evidence": evidence,
        "does_not_prove": evaluation["limits"],
    }


def run_group(group: int, directory: Path) -> dict:
    if type(group) is not int or group not in range(1, 6):
        raise ValueError("unknown_group")
    evaluation = build_evaluation(Path(directory) / "suite")
    return _group_from_evaluation(group, evaluation)


def _markdown_report(report: dict) -> str:
    baseline, candidate = report["variants"]["baseline"], report["variants"]["candidate"]
    confidence = report["paired_confidence"]
    provenance = report["provenance"]
    calibration = report["judge_calibration"]
    lines = [
        "# 第 13 章离线评估报告", "",
        "> 本报告来自确定性教学策略，不是模型或产品排名。", "",
        "## 被测对象与量尺", "",
        f"- Suite：`{provenance['suite']['id']}@{provenance['suite']['version']}`，"
        f"SHA-256 `{provenance['suite']['sha256']}`；",
        f"- Baseline：`{provenance['subjects']['baseline']['policy']}`；"
        f"Candidate：`{provenance['subjects']['candidate']['policy']}`；",
        f"- 环境合同：`{provenance['environment']['contract_version']}`，"
        f"fixture `{', '.join(provenance['environment']['fixture_ids'])}`；",
        f"- Grader：`{provenance['graders']['version']}`；"
        f"Gate：`{provenance['gate']['version']}`；",
        f"- 统计：`{provenance['formulas']['pass_at_k']}` / "
        f"`{provenance['formulas']['bootstrap']}`；",
        "- 责任人：本地候选未指定；发布前必须由章节维护者与评估负责人签字。", "",
        "## 运行摘要", "",
        f"- Task：{report['task_count']}；计分 Trial：{report['trial_count']}；"
        f"种子：{', '.join(map(str, report['seeds']))}；",
        f"- Trial 状态：`{json.dumps(report['summary']['trial_statuses'], ensure_ascii=False, sort_keys=True)}`；",
        f"- 失败索引：{report['summary']['failure_count']} 条；环境错误诊断样本不进入指标。", "",
        "| 指标 | Baseline | Candidate |", "| --- | ---: | ---: |",
        f"| pass@1 | {baseline['pass_1']:.2%} | {candidate['pass_1']:.2%} |",
        f"| pass@3 | {baseline['pass_at_3']:.2%} | {candidate['pass_at_3']:.2%} |",
        f"| pass^3 | {baseline['pass_all_3']:.2%} | {candidate['pass_all_3']:.2%} |",
        f"| 安全违规 | {baseline['safety_violations']} | {candidate['safety_violations']} |",
        f"| 环境错误 | {baseline['environment_errors']} | {candidate['environment_errors']} |",
        f"| 无效记录 | {baseline['invalid_records']} | {candidate['invalid_records']} |", "",
        "## 切片", "",
        "| 切片 | Baseline pass@1 | Candidate pass@1 | 差值 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in ("basic", "edge", "safety", "recovery"):
        lines.append(f"| {name} | {baseline['slices'][name]:.2%} | "
                     f"{candidate['slices'][name]:.2%} | {report['slice_deltas'][name]:+.2%} |")
    lines.extend(["", "## 数据集用途视图", "",
                  "| Split | Baseline pass@1 | Candidate pass@1 | 差值 | 发布用途 |",
                  "| --- | ---: | ---: | ---: | --- |"])
    split_roles = {
        "capability": "观察能力趋势",
        "regression": "不得下降的回归门禁",
        "adversarial": "与安全硬门禁联合审阅",
    }
    for name in ("capability", "regression", "adversarial"):
        lines.append(f"| {name} | {baseline['splits'][name]:.2%} | "
                     f"{candidate['splits'][name]:.2%} | {report['split_deltas'][name]:+.2%} | "
                     f"{split_roles[name]} |")
    heterogeneous = report["diagnostics"]["heterogeneous_bootstrap_example"]
    heterogeneous_confidence = heterogeneous["paired_confidence"]
    lines.extend(["",
        f"成对 pass@1 差值为 {confidence['estimate']:.2%}，"
        f"95% Bootstrap 区间为 [{confidence['lower']:.2%}, {confidence['upper']:.2%}]。", "",
        f"非退化教学对照的差值为 {heterogeneous_confidence['estimate']:.2%}，"
        f"95% Bootstrap 区间为 [{heterogeneous_confidence['lower']:.2%}, "
        f"{heterogeneous_confidence['upper']:.2%}]，结论为 "
        f"`{heterogeneous['interpretation']}`；该对照不进入发布门禁。", "",
        f"发布门禁：**{report['release']['decision']}**；原因："
        f"`{', '.join(report['release']['reasons'])}`。", "",
        "## 代表性失败", "",
    ])
    for failure in report["failures"][:5]:
        failed = ", ".join(failure["failed_graders"]) or "none"
        error = json.dumps(failure["error"], ensure_ascii=False)
        lines.append(f"- `{failure['trial_id']}`：status=`{failure['status']}`，"
                     f"failed graders=`{failed}`，error=`{error}`。")
    lines.extend(["", "完整失败索引和证据引用见 `evaluation-report.json` 的 `failures` 与 `trials`。", "",
        "## Judge 校准摘要", "",
        f"- 固定样本：{calibration['case_count']}；总体一致率：{calibration['agreement']:.2%}；",
        f"- Coverage：{calibration['coverage']:.2%}；answered-only accuracy："
        f"{calibration['answered_accuracy']:.2%}；Unknown：{calibration['unknown_rate']:.2%}；",
        "- 金标边界：编辑教学夹具，未经独立人工复核，不是 live Judge 测量。", "",
        "## 排除项", "",
        "- 注入的 `environment_error` 诊断 Trial 只验证状态和 Unknown 评分，不进入 120 条计分 Trial；",
        "- 没有真实 Provider Usage，Token、费用和延迟不参与比较；",
        "- 墙钟时间不进入稳定报告；原因记录在 `provenance.environment.run_window_reason`。", "",
        "## 证据边界", "",
    ])
    lines.extend(f"- {item}" for item in report["limits"])
    return "\n".join(lines) + "\n"


def _archive_existing(output: Path) -> None:
    for index in range(1, 10_000):
        candidate = output.with_name(f"{output.name}.previous-{index}")
        if not candidate.exists():
            output.rename(candidate)
            return


def _artifact_hashes(output: Path) -> dict[str, str]:
    return {path.name: sha256(path.read_bytes()).hexdigest()
            for path in sorted(output.glob("*")) if path.is_file() and path.name != "manifest.json"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", required=True, choices=("1", "2", "3", "4", "5", "all"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.absolute()
    if output.exists():
        if not args.replace:
            print("output_exists: use a new directory or --replace", file=sys.stderr)
            return 2
        _archive_existing(output)
    output.mkdir(parents=True)
    if args.group == "all":
        evaluation = build_evaluation(output / ".work" / "suite")
        for group in range(1, 6):
            payload = _group_from_evaluation(group, evaluation)
            (output / f"group-{group}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8", newline="\n")
        (output / "evaluation-report.json").write_text(
            json.dumps(evaluation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        (output / "evaluation-report.md").write_text(_markdown_report(evaluation),
                                                       encoding="utf-8", newline="\n")
        groups = [1, 2, 3, 4, 5]
    else:
        number = int(args.group)
        payload = run_group(number, output / ".work")
        (output / f"group-{number}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        groups = [number]
    (output / "manifest.json").write_text(json.dumps({
        "schema_version": "chapter13.manifest.v1", "groups": groups,
        "decision_source": "deterministic_scripted_policy",
        "artifacts": _artifact_hashes(output),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
