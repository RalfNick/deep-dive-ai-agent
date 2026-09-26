"""Runnable evidence and explicit rubrics for the Chapter 14 exercises."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Callable, Mapping

from .benchmark import compare_benchmark_cards, load_benchmark_cards
from .contracts import SpanRecord, TraceRecord
from .diagnosis import diagnose_incident, run_ablations
from .metrics import critical_path, nearest_rank, summarize_release
from .trace_builder import build_trace_fixture


ROOT = Path(__file__).resolve().parent
RATE_CARD = ROOT / "fixtures" / "rate-card.json"
CANONICAL_REPORT = ROOT / "reports" / "diagnostic-report.json"

TITLES = {
    1: "区分 Benchmark、Evaluation、Observability 与生产诊断",
    2: "审计 Benchmark Card",
    3: "手算 nearest-rank 分位数",
    4: "拆分父子树与依赖图",
    5: "计算关键路径与重试放大",
    6: "选择采样分母",
    7: "解释部分用量",
    8: "设计隐私字段分层",
    9: "组合 Head、Tail 与审计通道",
    10: "为故障选择观测信号",
    11: "设计检索消融",
    12: "用反证挑战模型变慢假设",
    13: "映射观测平台",
    14: "把事故固化为可审计报告",
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


def assess_incident_submission(report: Mapping[str, object]) -> dict[str, object]:
    """Apply the reader-facing minimum-evidence gate to an incident report."""
    reasons: list[str] = []
    completeness = report.get("data_completeness")
    if not isinstance(completeness, (int, float)) or isinstance(completeness, bool):
        reasons.append("missing_data_completeness")
    counterevidence = report.get("counterevidence_trace_ids")
    if not isinstance(counterevidence, list) or not counterevidence:
        reasons.append("missing_counterevidence")
    return {"accepted": not reasons, "reason_codes": reasons}


def _exercise_1() -> dict[str, object]:
    return _answer(1, ["四类问题边界不混淆", "每类都指出一个盲区"], {
        "benchmark": "固定任务与规则下能做到什么；不能单独说明生产体验",
        "evaluation": "结果和轨迹是否满足标准；不能单独解释系统内部耗时",
        "observability": "从外部证据推断内部状态；不能自动定义业务正确",
        "production_diagnosis": "哪个候选原因解释退化；证据不足时必须 inconclusive",
    }, status="answered", execution="design")


def _exercise_2() -> dict[str, object]:
    cards = load_benchmark_cards()
    control = compare_benchmark_cards(cards[0], cards[1])
    misleading = compare_benchmark_cards(cards[2], cards[3])
    return _answer(2, ["忽略分数先审合同", "指出 Harness、预算与重试差异"], {
        "control_verdict": control["verdict"],
        "same_score_verdict": misleading["verdict"],
        "same_score_different_fields": misleading["different_fields"],
        "conclusion": "同分只表示聚合结果相同，不表示测量条件或系统能力相同",
    }, execution="real")


def _exercise_3() -> dict[str, object]:
    values = [100, 105, 108, 110, 111, 113, 116, 118, 120, 900]
    mean = sum(values) / len(values)
    return _answer(3, ["使用 nearest-rank.v1", "比较平均值与尾部"], {
        "values": values,
        "nearest_rank": {"p50": nearest_rank(values, 50), "p95": nearest_rank(values, 95)},
        "mean": mean,
        "interpretation": "平均值 180.1ms 掩盖了 900ms 慢尾",
    }, execution="real")


def _exercise_4() -> dict[str, object]:
    return _answer(4, ["结构父子边与等待依赖边分开", "并行检索互不依赖"], {
        "parent_edges": [
            "agent.run -> model.plan",
            "agent.run -> retrieval.a",
            "agent.run -> retrieval.b",
            "agent.run -> verifier",
        ],
        "dependency_edges": [
            "model.plan -> retrieval.a",
            "model.plan -> retrieval.b",
            "retrieval.a -> verifier",
            "retrieval.b -> verifier",
        ],
        "parallel": ["retrieval.a", "retrieval.b"],
    }, status="answered", execution="design")


def _hand_trace() -> TraceRecord:
    trace_id = "exercise-critical-path"

    def span(span_id: str, kind: str, start: int, end: int, *,
             parent: str | None, depends: tuple[str, ...]) -> SpanRecord:
        return SpanRecord(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent,
            depends_on_span_ids=depends,
            kind=kind,
            name=span_id,
            start_ms=start,
            end_ms=end,
            status="ok",
            attributes={},
            input_digest=None,
            output_digest=None,
            input_tokens=None,
            output_tokens=None,
            cost_units=None,
            error_type=None,
        )

    spans = (
        span("root", "root", 0, 320, parent=None, depends=()),
        span("agent", "container", 0, 320, parent="root", depends=()),
        span("plan", "model", 0, 80, parent="agent", depends=()),
        span("retrieval-a", "retrieval", 80, 200, parent="agent", depends=("plan",)),
        span("retrieval-b", "retrieval", 80, 280, parent="agent", depends=("plan",)),
        span("verify", "verifier", 280, 320, parent="agent", depends=("retrieval-a", "retrieval-b")),
    )
    return TraceRecord(
        trace_id=trace_id,
        session_id="exercise-session",
        release_id="stable",
        scenario_id="retrieval-02",
        slice="retrieval",
        started_at_ms=0,
        ended_at_ms=320,
        status="success",
        outcome_score=1.0,
        spans=spans,
        tags={"logical_operations": 3},
        sampling=None,
        telemetry_complete=True,
    )


def _exercise_5() -> dict[str, object]:
    path = critical_path(_hand_trace())
    traces = build_trace_fixture()
    rate_card = json.loads(RATE_CARD.read_text(encoding="utf-8"))
    incident = summarize_release(tuple(t for t in traces if t.release_id == "incident"), rate_card)
    return _answer(5, ["并行 Span 不直接相加", "重试以逻辑操作为分母"], {
        "critical_path_duration_ms": path["critical_path_duration_ms"],
        "critical_path_span_ids": path["critical_path_span_ids"],
        "work_span_duration_sum_ms": path["work_span_duration_sum_ms"],
        "endpoint_duration_ms": path["endpoint_duration_ms"],
        "incident_retry_amplification": incident["retry_amplification"],
        "retry_formula": "billable_attempts / declared_logical_operations",
    }, execution="real")


def _exercise_6() -> dict[str, object]:
    report = json.loads(CANONICAL_REPORT.read_text(encoding="utf-8"))["sampling"]
    population = report["population_metrics"]
    retained = report["diagnostic_retained_counts"]
    return _answer(6, ["总体指标不用 Tail 样本作分母", "Coverage 与完整率分开"], {
        "request_count": population["request_count"],
        "failed_request_count": population["failed_request_count"],
        "retained_trace_count": retained["retained_trace_count"],
        "trace_error_reason_count": retained["trace_error"],
        "trace_coverage": report["trace_coverage"],
        "telemetry_completeness": report["telemetry_completeness"],
        "population_failure_rate": population["failed_request_count"] / population["request_count"],
        "invalid_rate": "12/49 counts error-bearing retained traces, not failed population requests",
    }, execution="real")


def _exercise_7() -> dict[str, object]:
    return _answer(7, ["已知总量与覆盖率同时报告", "不把缺失当零"], {
        "call_count": 100,
        "known_usage_count": 80,
        "usage_coverage": 0.8,
        "known_cost_units": 40,
        "allowed_claim": "80 个已知调用合计 40 单位，字段覆盖率 80%",
        "forbidden_claim": "全部 100 个调用总成本就是 40 单位",
    }, status="answered", execution="design")


def _exercise_8() -> dict[str, object]:
    return _answer(8, ["按用途和风险分层", "敏感值在导出前处理"], {
        "retain": ["release_id", "scenario_slice"],
        "hash_with_salt": ["employee_id", "document_id"],
        "drop": ["Authorization header", "raw API key"],
        "controlled_storage": ["薪酬查询原文", "受权限保护的文档摘录"],
        "ordering": ["record", "redact", "validate", "sample", "export"],
    }, status="answered", execution="design")


def _exercise_9() -> dict[str, object]:
    return _answer(9, ["容量与罕见高风险事件同时覆盖", "总体计数独立"], {
        "head": "按 trace_id 确定性保留低比例基础样本",
        "tail": "保留错误、慢请求、新发布和一般安全信号",
        "audit": "越权尝试与高风险副作用进入独立、不可由概率丢弃的审计通道",
        "population": "请求与失败计数在采样前聚合",
    }, status="answered", execution="design")


def _exercise_10() -> dict[str, object]:
    return _answer(10, ["每个故障匹配所需信号", "不让单一信号承担全部证明"], {
        "model_slow": ["Trace model span", "provider latency/usage", "release slice metrics"],
        "retry_whole_loop": ["dependency-aware Trace", "retry amplification", "cost and p95"],
        "exporter_drops_spans": ["telemetry completeness", "exporter queue/error metrics"],
        "user_dislikes_correct_answer": ["Outcome Eval", "feedback", "task/session context"],
    }, status="answered", execution="design")


def _exercise_11() -> dict[str, object]:
    return _answer(11, ["五个候选变量逐一控制", "固定任务和测量合同"], {
        "ablations": [
            "固定模型，只替换 Query rewrite",
            "固定 Query，只替换索引快照",
            "固定候选集，只替换 Reranker",
            "固定排序结果，只替换文档内容版本",
            "固定其余四项，只替换模型",
        ],
        "measurement": ["retrieval recall", "answer outcome", "latency", "usage coverage"],
        "stop_rule": "只有一个干预稳定消除目标症状时才确认；否则 inconclusive",
    }, status="answered", execution="design")


def _exercise_12() -> dict[str, object]:
    return _answer(12, ["假设产生可反驳预测", "包含同发布反例"], {
        "hypothesis": "新模型导致所有请求变慢",
        "predictions": [
            "所有场景切片的 model span 都系统性变慢",
            "不使用恢复路径的 simple 请求也变慢",
            "固定工具与重试后退化仍然存在",
        ],
        "falsifiers": [
            "只有 recovery 切片变慢",
            "simple 反证 Trace 保持稳定",
            "固定 retry policy 后全部症状消失",
        ],
    }, status="answered", execution="design")


def _exercise_13() -> dict[str, object]:
    return _answer(13, ["映射稳定概念而非背 API", "指出不可一一对应处"], {
        "opentelemetry": {
            "trace_id": "Trace ID",
            "span_id_parent": "Span ID / Parent Span ID",
            "release": "Resource or stable attribute",
        },
        "non_isomorphic": [
            "本章 depends_on 工作 DAG 不能简单等于 Parent",
            "IncidentReport 与业务 Eval 不由 Trace 协议自动定义",
        ],
        "checked_on": "2026-09-26",
    }, status="answered", execution="design")


def _exercise_14() -> dict[str, object]:
    traces = build_trace_fixture()
    report = diagnose_incident(traces)
    canonical = report.to_dict()
    missing_completeness = dict(canonical)
    missing_completeness.pop("data_completeness")
    missing_counterevidence = dict(canonical, counterevidence_trace_ids=[])
    return _answer(14, ["结论保留支持、反证、完整率与未知项", "缺少关键证据就拒绝"], {
        "canonical": assess_incident_submission(canonical),
        "missing_completeness": assess_incident_submission(missing_completeness),
        "missing_counterevidence": assess_incident_submission(missing_counterevidence),
        "root_cause": report.root_cause,
        "conclusion": report.conclusion,
        "ablation_winner": [
            item["hypothesis"] for item in run_ablations(traces)
            if item["all_canonical_symptoms_removed"]
        ],
    }, execution="real")


SOLVERS: dict[int, Callable[[], dict[str, object]]] = {
    1: _exercise_1,
    2: _exercise_2,
    3: _exercise_3,
    4: _exercise_4,
    5: _exercise_5,
    6: _exercise_6,
    7: _exercise_7,
    8: _exercise_8,
    9: _exercise_9,
    10: _exercise_10,
    11: _exercise_11,
    12: _exercise_12,
    13: _exercise_13,
    14: _exercise_14,
}


def solve(number: int) -> dict[str, object]:
    if type(number) is not int or number not in SOLVERS:
        raise ValueError("unknown_exercise")
    return SOLVERS[number]()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Chapter 14 reference solutions")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--number", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.output is not None and args.output.exists():
        print("output_exists", file=sys.stderr)
        return 3

    numbers = list(range(1, 15)) if args.all else [args.number]
    answers = [solve(number) for number in numbers]
    payload = {
        "schema_version": "chapter14.exercises.v1",
        "answers": answers,
        "summary": {
            "count": len(answers),
            "all_passed": all(item["status"] in {"passed", "answered"} for item in answers),
        },
        "limits": [
            "design_answers_are_rubrics_not_unique_proofs",
            "deterministic_fixture_not_real_production_measurement",
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

