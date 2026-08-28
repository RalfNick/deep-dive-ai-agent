from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from chapter8.knowledge_runtime.catalog import (
    KnowledgeCatalog,
    load_documents,
    load_question_cases,
)
from chapter8.knowledge_runtime.chunking import (
    contextualize_chunks,
    fixed_character_chunks,
    structure_aware_chunks,
)
from chapter8.knowledge_runtime.contracts import (
    AnswerStatus,
    QuestionCase,
    RetrievalHit,
    ScoreBreakdown,
    stable_digest,
)
from chapter8.knowledge_runtime.dense import DenseIndex, FrozenSemanticEncoder
from chapter8.knowledge_runtime.evaluation import (
    answer_support_metrics,
    citation_metrics,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from chapter8.knowledge_runtime.evidence import ScriptedAnswerPolicy, build_evidence_packet
from chapter8.knowledge_runtime.persistence import canonical_json, write_json, write_jsonl, write_markdown
from chapter8.knowledge_runtime.rerank import DeterministicReranker
from chapter8.knowledge_runtime.retrieve import HybridRetriever
from chapter8.knowledge_runtime.sparse import BM25Index


CHAPTER_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = CHAPTER_ROOT / "fixtures" / "starboard_docs"
QUESTION_PATH = CHAPTER_ROOT / "fixtures" / "questions.json"
CANONICAL_TIME = "2026-08-27T16:00:00Z"


def _documents():
    return load_documents(FIXTURE_ROOT)


def _chunks(documents):
    chunks = []
    for document in documents:
        chunks.extend(contextualize_chunks(document, structure_aware_chunks(document, 520)))
    return tuple(chunks)


def _retriever(catalog: KnowledgeCatalog | None = None) -> HybridRetriever:
    documents = _documents()
    catalog = catalog or KnowledgeCatalog(documents)
    chunks = _chunks(documents)
    return HybridRetriever(
        catalog=catalog,
        chunks=chunks,
        sparse=BM25Index(chunks),
        dense=DenseIndex(chunks, FrozenSemanticEncoder()),
        reranker=DeterministicReranker(),
    )


def _case_map() -> dict[str, QuestionCase]:
    return {case.case_id: case for case in load_question_cases(QUESTION_PATH)}


def _record(
    case: QuestionCase,
    *,
    variants: Iterable[str],
    configuration: str,
    metrics: dict[str, object],
    evidence_codes: Iterable[str],
    supports: str,
    does_not_support: str = "不支持真实模型质量、线上成本、延迟或厂商排名结论。",
) -> dict[str, object]:
    return {
        "case_id": case.case_id,
        "sample_count": 1,
        "variants": list(variants),
        "configuration": configuration,
        "metrics": metrics,
        "evidence_codes": list(evidence_codes),
        "supports": supports,
        "does_not_support": does_not_support,
    }


def _evaluate(case: QuestionCase, retriever: HybridRetriever) -> tuple[dict[str, object], tuple[str, ...]]:
    hits, trace = retriever.retrieve(case.query, include_trace=True)
    packet = build_evidence_packet(case.query, hits, case.required_fact_ids)
    decision = ScriptedAnswerPolicy().answer(case, packet)
    retrieved_documents = tuple(dict.fromkeys(hit.chunk.document_id for hit in hits))
    relevant = set(case.relevant_document_ids)
    support = answer_support_metrics(
        case.required_fact_ids,
        packet.present_fact_ids,
        answered=decision.status is AnswerStatus.ANSWER,
    )
    metrics: dict[str, object] = {
        "retrieved_document_ids": retrieved_documents,
        "retrieved_chunk_count": len(hits),
        "precision_at_3": precision_at_k(retrieved_documents, relevant, 3),
        "recall_at_3": recall_at_k(retrieved_documents, relevant, 3),
        "mrr": mean_reciprocal_rank(retrieved_documents, relevant),
        "ndcg_at_3": ndcg_at_k(retrieved_documents, relevant, 3),
        "answer_status": decision.status.value,
        "expected_status": case.expected_status.value,
        "supported_fact_ratio": support.supported_fact_ratio,
        "unsupported_claim_count": support.unsupported_claim_count,
        "missing_fact_ids": support.missing_fact_ids,
        "filtered_before_score_count": len(trace.filtered_before_score),
        "catalog_recheck_rejected_count": len(trace.catalog_recheck_rejected),
    }
    codes = (f"query:{trace.query_digest[:12]}",) + tuple(
        f"document:{hit.chunk.document_digest[:12]}" for hit in hits
    )
    return metrics, codes


def _baseline_cases(cases: dict[str, QuestionCase]) -> list[dict[str, object]]:
    documents = _documents()
    conflict_documents = sum(
        bool({"sso-team-28", "sso-team-32"} & set(document.fact_ids))
        for document in documents
    )
    definitions = (
        (
            "baseline-parametric-guess",
            ("v0",),
            "参数化猜测：不读取知识库，直接给出固定答案。",
            {"retrieved_document_count": 0, "citation_count": 0, "unsupported_claim_count": 1, "answer_status": "answer"},
            "证明没有检索与引用时，系统仍可能输出语法完整但无证据的答案。",
        ),
        (
            "baseline-full-context-conflict",
            ("v1",),
            "全文塞入：把 18 份文档全部放入同一个上下文。",
            {
                "context_document_count": len(documents),
                "conflict_document_count": conflict_documents,
                "internal_document_count": sum(document.visibility.value == "internal" for document in documents),
                "citation_count": 0,
            },
            "证明全文塞入同时扩大版本冲突和权限暴露面。",
        ),
        (
            "baseline-unanswerable-support-window",
            ("v0", "v1"),
            "无答案问题：知识库没有电话支持时间。",
            {"retrieved_document_count": 0, "citation_count": 0, "unsupported_claim_count": 1, "expected_status": "abstain"},
            "证明无证据问题需要显式拒答合同。",
        ),
    )
    records = []
    for case_id, variants, configuration, metrics, supports in definitions:
        case = cases[case_id]
        records.append(
            _record(
                case,
                variants=variants,
                configuration=configuration,
                metrics=metrics,
                evidence_codes=(f"fixture:{stable_digest({'case_id': case_id})[:12]}",),
                supports=supports,
            )
        )
    return records


def _chunking_cases(cases: dict[str, QuestionCase]) -> list[dict[str, object]]:
    document = next(item for item in _documents() if item.document_id == "migration-2x-to-3.2")
    fixed = fixed_character_chunks(document, 90, 15)
    structured = structure_aware_chunks(document, 220)
    contextual = contextualize_chunks(document, structured)
    definitions = (
        (
            "chunk-table-sso",
            ("v2",),
            "固定 90 字符、15 字符重叠。",
            fixed,
            {
                "chunk_count": len(fixed),
                "max_chunk_characters": max(map(lambda item: len(item.content), fixed)),
                "complete_table_or_code_blocks": sum(item.content.count("```") == 2 for item in fixed),
            },
            "支持观察固定窗口如何切断语义边界；字符数不是 Token 数。",
        ),
        (
            "chunk-cross-section-upgrade",
            ("v3",),
            "按 Markdown 标题、段落、表格和代码块切分。",
            structured,
            {
                "chunk_count": len(structured),
                "heading_aware_chunks": sum(bool(item.heading_path) for item in structured),
                "complete_table_or_code_blocks": sum(item.content.count("```") == 2 for item in structured),
            },
            "支持观察结构 Chunk 是否能独立保留章节语境。",
        ),
        (
            "chunk-code-dry-run",
            ("v4",),
            "在结构 Chunk 前增加文档、版本和章节前缀。",
            contextual,
            {
                "chunk_count": len(contextual),
                "context_prefix_count": sum(bool(item.context_prefix) for item in contextual),
                "source_content_digest_unchanged": all(item.content_digest == stable_digest(item.content) for item in contextual),
            },
            "支持观察语境前缀是否在不改写来源正文的前提下补足定位信息。",
        ),
    )
    return [
        _record(
            cases[case_id],
            variants=variants,
            configuration=configuration,
            metrics=metrics,
            evidence_codes=(f"document:{document.content_digest[:12]}", f"chunk:{chunks[0].content_digest[:12]}"),
            supports=supports,
        )
        for case_id, variants, configuration, chunks, metrics, supports in definitions
    ]


def _retrieval_cases(cases: dict[str, QuestionCase]) -> list[dict[str, object]]:
    retriever = _retriever()
    variants = {
        "retrieval-exact-version": ("v3",),
        "retrieval-synonym-login": ("v4",),
        "retrieval-compound": ("v5",),
        "retrieval-noise": ("v6",),
    }
    records = []
    for case_id, case_variants in variants.items():
        case = cases[case_id]
        metrics, codes = _evaluate(case, retriever)
        records.append(
            _record(
                case,
                variants=case_variants,
                configuration="BM25 与固定语义召回经 RRF 融合，再执行确定性重排。",
                metrics=metrics,
                evidence_codes=codes,
                supports="支持比较固定语料上的候选顺序、召回指标与不补齐行为。",
            )
        )
    return records


class _WithdrawAfterSnapshotCatalog(KnowledgeCatalog):
    def current_documents(self, query):
        documents = super().current_documents(query)
        self.withdraw("community-malicious-note")
        return documents


def _governance_cases(cases: dict[str, QuestionCase]) -> list[dict[str, object]]:
    records = []
    forbidden = {"maintainer-sso-bypass", "faq-2.8-sso", "plans-3.3-preview", "withdrawn-draft"}
    for case_id in (
        "governance-compound-upgrade",
        "governance-public-internal",
        "governance-future-preview",
        "governance-withdrawn",
    ):
        case = cases[case_id]
        metrics, codes = _evaluate(case, _retriever())
        retrieved = set(metrics["retrieved_document_ids"])
        metrics["policy_violation_count"] = len(retrieved & forbidden)
        records.append(
            _record(
                case,
                variants=("v6",),
                configuration="状态、版本、时效和角色在评分前硬过滤，最终命中再回查主 Catalog。",
                metrics=metrics,
                evidence_codes=codes,
                supports="支持检查固定时钟与角色下的版本、时效、状态和权限隔离。",
            )
        )
    stale_case = cases["governance-stale-index"]
    stale_catalog = _WithdrawAfterSnapshotCatalog(_documents())
    metrics, codes = _evaluate(stale_case, _retriever(stale_catalog))
    records.append(
        _record(
            stale_case,
            variants=("v5", "v6"),
            configuration="候选快照后撤回社区文档，验证最终 Catalog 回查。",
            metrics=metrics,
            evidence_codes=codes,
            supports="支持证明索引是派生物，撤回后的来源不会因陈旧候选重新进入答案。",
        )
    )
    return records


def _hit_for(document_id: str, phrase: str) -> RetrievalHit:
    document = next(item for item in _documents() if item.document_id == document_id)
    chunk = next(
        item
        for item in contextualize_chunks(document, structure_aware_chunks(document, 520))
        if phrase in item.content
    )
    return RetrievalHit(chunk, 1.0, ScoreBreakdown(1.0, 0.8, 0.03, 2.0))


def _evidence_cases(cases: dict[str, QuestionCase]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    missing_case = cases["evidence-missing-members"]
    packet = build_evidence_packet(
        missing_case.query,
        (_hit_for("plans-3.2", "旧式 SAML SSO"),),
        missing_case.required_fact_ids,
    )
    decision = ScriptedAnswerPolicy().answer(missing_case, packet)
    records.append(
        _record(
            missing_case,
            variants=("v7",),
            configuration="只提供 SSO 证据，故意移除成员证据。",
            metrics={
                "answer_status": decision.status.value,
                "citation_count": len(packet.citations),
                "missing_fact_ids": packet.missing_fact_ids,
                "unsupported_claim_count": 0,
            },
            evidence_codes=tuple(f"citation:{item.content_digest[:12]}" for item in packet.citations),
            supports="支持证明复合问题缺一类证据时只能部分回答。",
        )
    )

    wrong_case = cases["evidence-wrong-citation"]
    wrong = citation_metrics(
        {"claim-sso": {"C1"}, "claim-members": {"C2"}},
        {"claim-sso": {"C1"}, "claim-members": {"C3"}},
    )
    records.append(
        _record(
            wrong_case,
            variants=("v7",),
            configuration="两个声明中有一个指向错误来源。",
            metrics=asdict(wrong),
            evidence_codes=("citation-map:wrong-source",),
            supports="支持区分“有引用”和“引用真正支持声明”。",
        )
    )

    conflict_case = cases["evidence-conflicting-source"]
    metrics, codes = _evaluate(conflict_case, _retriever())
    metrics["authoritative_source_present"] = any(
        document_id in {"migration-2x-to-3.2", "plans-3.2"}
        for document_id in metrics["retrieved_document_ids"]
    )
    records.append(
        _record(
            conflict_case,
            variants=("v7",),
            configuration="正式迁移指南与社区经验冲突，保留来源信任级别。",
            metrics=metrics,
            evidence_codes=codes,
            supports="支持观察冲突来源的信任级别和回答证据选择。",
        )
    )

    injection_case = cases["evidence-prompt-injection"]
    injection_packet = build_evidence_packet(
        injection_case.query,
        (
            _hit_for("community-malicious-note", "忽略其他来源"),
            _hit_for("security-overview", "社区文档中的命令"),
        ),
        injection_case.required_fact_ids,
    )
    injection_decision = ScriptedAnswerPolicy().answer(injection_case, injection_packet)
    records.append(
        _record(
            injection_case,
            variants=("v7",),
            configuration="将恶意社区 Chunk 与正式安全说明同时送入 Evidence Builder。",
            metrics={
                "answer_status": injection_decision.status.value,
                "untrusted_instruction_in_answer_context": sum(
                    citation.document_id == "community-malicious-note"
                    for citation in injection_packet.citations
                ),
                "citation_count": len(injection_packet.citations),
            },
            evidence_codes=tuple(f"citation:{item.content_digest[:12]}" for item in injection_packet.citations),
            supports="支持证明不可信指令被保留为检索风险，但不会进入最终 Answer Context。",
        )
    )

    abstain_case = cases["evidence-correct-abstain"]
    metrics, codes = _evaluate(abstain_case, _retriever())
    records.append(
        _record(
            abstain_case,
            variants=("v7",),
            configuration="固定语料没有量子加密登录事实。",
            metrics=metrics,
            evidence_codes=codes,
            supports="支持证明无足够证据时返回拒答，而不是填满 top_k 后猜测。",
        )
    )
    return records


def build_report() -> dict[str, object]:
    cases = _case_map()
    groups = {
        "baseline": {"case_count": 3, "cases": _baseline_cases(cases)},
        "chunking": {"case_count": 3, "cases": _chunking_cases(cases)},
        "retrieval": {"case_count": 4, "cases": _retrieval_cases(cases)},
        "governance": {"case_count": 5, "cases": _governance_cases(cases)},
        "evidence": {"case_count": 5, "cases": _evidence_cases(cases)},
    }
    return {
        "schema_version": 1,
        "chapter": 8,
        "generated_at": CANONICAL_TIME,
        "scope": {
            "corpus_document_count": 18,
            "question_case_count": 20,
            "decision_policy": "scripted",
            "semantic_encoder": "frozen-concept-vector",
            "network_access": False,
        },
        "groups": groups,
        "unmeasured": {
            "real_model_quality": None,
            "provider_tokens": None,
            "provider_cost": None,
            "provider_latency_ms": None,
        },
        "claims": {
            "supports": "固定语料、固定时钟和固定决策策略下的 RAG 边界符合性。",
            "does_not_support": "真实 Embedding、Reranker、LLM、Ragas 或厂商产品质量排名。",
        },
    }


def _render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# 第 8 章 RAG 规范实验报告",
        "",
        f"- 固定时间：{report['generated_at']}",
        "- 语料：18 份虚构的星舟工作台文档",
        "- 案例：20 个单样本边界案例",
        "- 本报告支持：固定组件下的边界符合性",
        "- 本报告不支持：真实模型质量、Token、成本、延迟或厂商排名",
        "",
    ]
    for group_id, group in report["groups"].items():
        lines.extend((f"## {group_id}", "", "| Case | 版本 | 关键指标 |", "| --- | --- | --- |"))
        for case in group["cases"]:
            lines.append(
                f"| {case['case_id']} | {', '.join(case['variants'])} | {canonical_json(case['metrics']).replace(chr(10), ' ')} |"
            )
        lines.append("")
    return "\n".join(lines)


def _trace_rows(report: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group_id, group in report["groups"].items():
        for case in group["cases"]:
            metrics = case["metrics"]
            rows.append(
                {
                    "event_id": len(rows) + 1,
                    "case_id": case["case_id"],
                    "group": group_id,
                    "stage": "case_complete",
                    "variants": case["variants"],
                    "evidence_codes": case["evidence_codes"],
                    "retrieved_document_ids": metrics.get("retrieved_document_ids", ()),
                    "retrieved_chunk_count": metrics.get("retrieved_chunk_count"),
                    "reason": "deterministic_case_recorded",
                }
            )
    return rows


def generate_to(output: Path) -> tuple[Path, ...]:
    report = build_report()
    return (
        write_json(output / "rag-evidence.json", report),
        write_markdown(output / "rag-evidence.md", _render_markdown(report)),
        write_jsonl(output / "rag-trace.jsonl", _trace_rows(report)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic Chapter 8 RAG reports.")
    parser.add_argument("--output", type=Path, default=CHAPTER_ROOT / "reports")
    args = parser.parse_args()
    generate_to(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
