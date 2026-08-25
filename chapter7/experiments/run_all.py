from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from typing import Any

from chapter7.fixtures.coding_collaboration import (
    FULL_TRANSCRIPT,
    PRICING,
    USER_GLOBAL,
    candidates,
    recall_records,
)
from chapter7.memory_runtime.contracts import (
    Authority,
    MemoryCandidate,
    MemoryRecord,
    MemoryStatus,
    RecallQuery,
    canonical_json,
)
from chapter7.memory_runtime.recall import MemoryRecall
from chapter7.memory_runtime.runtime import MemoryRuntime
from chapter7.memory_runtime.store import MemoryConflictError, MemoryStore


REPORT_TIME = "2026-08-25T00:00:00Z"


def _case(variant_id: str, metrics: dict[str, Any], evidence: list[str], claim: str) -> dict[str, Any]:
    return {
        "variant_id": variant_id,
        "metrics": metrics,
        "evidence": evidence,
        "supported_claims": [claim],
        "unsupported_claims": ["不代表真实模型质量、生产成功率或厂商能力排名"],
    }


def _scripted_decision(context: tuple[str, ...]) -> dict[str, Any]:
    joined = "\n".join(context)
    language = "Python" if "Python" in joined else "JavaScript"
    confirm_api = "public API" in joined and "确认" in joined
    unsafe = "跳过 slow integration test" in joined
    return {
        "language": language,
        "confirm_public_api": confirm_api,
        "unsafe_temporary_rule_used": unsafe,
        "task_accepted": language == "Python" and confirm_api and not unsafe,
    }


def _baseline_group() -> dict[str, Any]:
    no_memory = _scripted_decision(())
    full = _scripted_decision(FULL_TRANSCRIPT)
    runtime = MemoryRuntime()
    for fixture in candidates():
        runtime.write(fixture.candidate)
    hits = runtime.recall(RecallQuery(PRICING, "Python public API examples", (), 4, REPORT_TIME))
    structured_context = tuple(hit.record.content for hit in hits)
    structured = _scripted_decision(structured_context)
    return {
        "group_id": "baseline",
        "question": "保存更多历史是否等于拥有更好的记忆？",
        "cases": [
            _case("no-memory", no_memory, ["decision:no-context"], "无跨任务信息时固定策略无法恢复偏好与规则"),
            _case("full-transcript", full, ["transcript:item-count:4"], "完整历史同时携带稳定规则和一次性授权"),
            _case("structured-memory", structured, [f"recall:hit-count:{len(hits)}"], "策略写入与任务召回能排除本夹具的一次性授权"),
        ],
    }


def _unsafe_record(candidate: MemoryCandidate) -> MemoryRecord:
    memory_id = MemoryRuntime.memory_id(candidate)
    return MemoryRecord(
        record_id=f"unsafe-{candidate.candidate_id}",
        memory_id=memory_id,
        namespace=candidate.namespace,
        memory_type=candidate.memory_type,
        subject=candidate.subject,
        content=candidate.content,
        source_id=candidate.source_id,
        authority=candidate.authority,
        confidence=candidate.confidence,
        sensitivity=candidate.sensitivity,
        valid_from=candidate.proposed_at,
        expires_at=None,
        created_at=candidate.proposed_at,
        version=1,
        supersedes=None,
        status=MemoryStatus.ACTIVE,
    )


def _write_metrics(written_ids: set[str]) -> dict[str, Any]:
    fixtures = candidates()
    expected = {item.candidate.candidate_id for item in fixtures if item.should_write}
    actual = set(written_ids)
    true_positive = len(expected & actual)
    return {
        "write_precision": round(true_positive / len(actual), 6) if actual else None,
        "write_recall": round(true_positive / len(expected), 6),
        "sensitive_write_count": sum(
            item.candidate.candidate_id in actual and item.candidate.subject == "api_key" for item in fixtures
        ),
        "written_count": len(actual),
    }


def _write_group() -> dict[str, Any]:
    fixtures = candidates()
    unsafe_store = MemoryStore()
    for fixture in fixtures:
        unsafe_store.append(_unsafe_record(fixture.candidate))
    unsafe_ids = {fixture.candidate.candidate_id for fixture in fixtures}

    gated = MemoryRuntime()
    gated_ids: set[str] = set()
    review_candidates: list[MemoryCandidate] = []
    for fixture in fixtures:
        outcome = gated.write(fixture.candidate)
        if outcome.record is not None:
            gated_ids.add(fixture.candidate.candidate_id)
        elif outcome.decision.reason == "inferred_memory_requires_review":
            review_candidates.append(fixture.candidate)

    reviewed_ids = set(gated_ids)
    reviewed_runtime = MemoryRuntime()
    for fixture in fixtures:
        candidate = fixture.candidate
        if candidate.candidate_id in gated_ids:
            reviewed_runtime.write(candidate)
        elif candidate in review_candidates:
            reviewed_runtime.write(replace(candidate, authority=Authority.REPOSITORY_VERIFIED, source_id=candidate.source_id + "#approved"))
            reviewed_ids.add(candidate.candidate_id)

    return {
        "group_id": "write",
        "question": "哪些候选信息值得跨任务保存？",
        "cases": [
            _case("write-everything", _write_metrics(unsafe_ids), ["write-gate:bypassed"], "无闸门写入在固定候选集中保存了 Secret 与一次性内容"),
            _case("policy-gated", _write_metrics(gated_ids), [f"write:accepted:{len(gated_ids)}"], "确定性闸门在固定候选集中没有写入负样本"),
            _case("policy-plus-review", _write_metrics(reviewed_ids), [f"review:approved:{len(review_candidates)}"], "人工批准补回了固定候选集中的一条有效推断"),
        ],
    }


def _in_scope(record: MemoryRecord) -> bool:
    return (
        record.namespace.tenant_id == PRICING.tenant_id
        and record.namespace.user_id == PRICING.user_id
        and record.namespace.agent_id == PRICING.agent_id
        and record.namespace.project_id in (None, PRICING.project_id)
    )


def _recall_metrics(records: tuple[MemoryRecord, ...], relevant_ids: set[str]) -> dict[str, Any]:
    ids = {record.memory_id for record in records}
    return {
        "recall_precision": round(len(ids & relevant_ids) / len(records), 6) if records else None,
        "cross_scope_leak_count": sum(not _in_scope(record) for record in records),
        "returned_count": len(records),
    }


def _recall_group() -> dict[str, Any]:
    fixtures = recall_records()
    store = MemoryStore()
    relevant_ids = {record.memory_id for record, relevant in fixtures if relevant}
    for record, _ in fixtures:
        store.append(record)
    global_scan = tuple(record for record, _ in fixtures[:5])
    scoped_unranked = tuple(record for record, _ in fixtures if _in_scope(record))
    ranked = tuple(
        hit.record
        for hit in MemoryRecall(store).search(
            RecallQuery(PRICING, "Python examples public API confirm", (), 2, REPORT_TIME)
        )
    )
    return {
        "group_id": "recall",
        "question": "相似内容是否应该直接进入模型上下文？",
        "cases": [
            _case("global-scan", _recall_metrics(global_scan, relevant_ids), ["scope-filter:off", "top-k:5"], "全局扫描在固定夹具中产生跨作用域泄漏"),
            _case("scoped-unranked", _recall_metrics(scoped_unranked, relevant_ids), ["scope-filter:on", "ranking:off"], "作用域过滤消除了跨作用域记录但仍保留噪声"),
            _case("scoped-ranked", _recall_metrics(ranked, relevant_ids), ["scope-filter:on", "ranking:on", "top-k:2"], "硬过滤后排序在固定夹具中只返回两条目标记录"),
        ],
    }


def _language_candidate(value: str, candidate_id: str, at: str) -> MemoryCandidate:
    return replace(
        candidates()[0].candidate,
        candidate_id=candidate_id,
        content=f"代码示例优先使用 {value}",
        source_id=f"conversation-{candidate_id}",
        proposed_at=at,
    )


def _correct_group() -> dict[str, Any]:
    naive = {"preferred_language": "代码示例优先使用 Python"}
    naive["preferred_language"] = "代码示例优先使用 TypeScript"

    runtime = MemoryRuntime()
    first = runtime.write(_language_candidate("Python", "python", "2026-08-01T00:00:00Z")).record
    second = runtime.correct(
        _language_candidate("TypeScript", "typescript", "2026-09-01T00:00:00Z"),
        expected_record_id=first.record_id,
        approved=True,
    )
    stale_rejected = False
    try:
        runtime.correct(
            _language_candidate("Go", "go", "2026-09-01T00:01:00Z"),
            expected_record_id=first.record_id,
            approved=True,
        )
    except MemoryConflictError:
        stale_rejected = True
    versions = runtime.store.versions(USER_GLOBAL, first.memory_id)
    current = runtime.store.current(USER_GLOBAL, first.memory_id, now="2026-09-02T00:00:00Z")
    return {
        "group_id": "correct",
        "question": "新偏好与旧记忆冲突时能否解释变化过程？",
        "cases": [
            _case("overwrite", {"audit_chain_complete": False, "correction_converged": naive["preferred_language"].endswith("TypeScript")}, ["versions:retained:1"], "原地覆盖得到新值但丢失旧版本关系"),
            _case("versioned", {"audit_chain_complete": len(versions) == 2 and second.supersedes == first.record_id, "correction_converged": current == second}, ["versions:retained:2", "supersedes:linked"], "版本化修正在固定夹具中保留旧值与替代关系"),
            _case("stale-writer", {"stale_write_rejected": stale_rejected, "duplicate_active_count": 0 if current == second else 1}, ["compare-and-set:expected-record"], "预期版本不匹配时陈旧写入被拒绝"),
        ],
    }


def _forget_group() -> dict[str, Any]:
    runtime = MemoryRuntime()
    record = runtime.write(_language_candidate("Python", "python-delete", "2026-08-01T00:00:00Z")).record
    stale_index = (record,)
    runtime.forget(
        namespace=USER_GLOBAL,
        memory_id=record.memory_id,
        deleted_at="2026-09-02T00:00:00Z",
        source_id="conversation-delete",
        reason="user_requested",
    )
    naive_leaks = len(stale_index)
    resolved = tuple(
        item for item in stale_index if runtime.store.current(item.namespace, item.memory_id, now="2026-09-03T00:00:00Z")
    )

    other_store = MemoryStore()
    other = replace(
        record,
        record_id="rec-other-tenant",
        memory_id="mem-other-tenant",
        namespace=replace(USER_GLOBAL, tenant_id="tenant-b"),
    )
    other_store.append(other)
    cross_hits = MemoryRecall(other_store).search(
        RecallQuery(PRICING, "Python examples", (), 3, "2026-09-03T00:00:00Z")
    )
    return {
        "group_id": "forget",
        "question": "删除后陈旧索引和其他租户记录会不会重新进入上下文？",
        "cases": [
            _case("stale-index", {"post_delete_leak_count": naive_leaks, "cross_scope_leak_count": 0}, ["index:stale", "store-resolution:off"], "直接信任陈旧索引会返回已删除记录"),
            _case("store-resolved", {"post_delete_leak_count": len(resolved), "cross_scope_leak_count": 0}, ["index:stale", "store-resolution:on", "tombstone:present"], "回到主记录解析使已删除记录在固定夹具中不可召回"),
            _case("cross-tenant-probe", {"post_delete_leak_count": 0, "cross_scope_leak_count": len(cross_hits)}, ["tenant-filter:before-score"], "租户过滤在打分前排除了其他租户记录"),
        ],
    }


def build_report() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "generated_at": REPORT_TIME,
        "experiment_kind": "deterministic_boundary_conformance",
        "sample_count_per_case": 1,
        "groups": [
            _baseline_group(),
            _write_group(),
            _recall_group(),
            _correct_group(),
            _forget_group(),
        ],
        "unmeasured": {
            "model_quality": None,
            "token_savings": None,
            "provider_latency": None,
            "production_success_rate": None,
        },
        "non_claims": [
            "固定夹具不代表真实模型表现或生产成功率",
            "serialized_bytes 不是 Token 数",
            "实验不比较 Claude Code、Codex、LangGraph 或 OpenAI Agents SDK 的整体能力",
            "内存 Store 与单进程锁不等于分布式事务或合规删除系统",
        ],
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 第 7 章记忆工程固定实验",
        "",
        f"- Schema：`{report['schema_version']}`",
        f"- 实验类型：`{report['experiment_kind']}`",
        f"- 每案例样本数：`{report['sample_count_per_case']}`",
        "",
    ]
    for group in report["groups"]:
        lines.extend((f"## {group['group_id']}", "", group["question"], "", "| 变体 | 指标 | 证据 |", "| --- | --- | --- |"))
        for case in group["cases"]:
            metrics = ", ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in case["metrics"].items())
            evidence = ", ".join(case["evidence"])
            lines.append(f"| `{case['variant_id']}` | {metrics} | {evidence} |")
        lines.append("")
    lines.extend(("## Non-claims", ""))
    lines.extend(f"- {item}" for item in report["non_claims"])
    return "\n".join(lines) + "\n"


def write_reports(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_report()
    json_path = output_dir / "memory-engineering.json"
    markdown_path = output_dir / "memory-engineering.md"
    trace_path = output_dir / "memory-engineering-trace.jsonl"
    json_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(_markdown(report), encoding="utf-8", newline="\n")
    trace_lines: list[str] = []
    for group in report["groups"]:
        for case in group["cases"]:
            trace_lines.append(
                canonical_json(
                    {
                        "case_id": f"{group['group_id']}/{case['variant_id']}",
                        "metrics": case["metrics"],
                        "evidence_codes": case["evidence"],
                    }
                )
            )
    trace_path.write_text("".join(line + "\n" for line in trace_lines), encoding="utf-8", newline="\n")
    return {"json": json_path, "markdown": markdown_path, "trace": trace_path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic Chapter 7 memory reports.")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "reports")
    args = parser.parse_args()
    paths = write_reports(args.output)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
