# 第 8 章 RAG 规范实验报告

- 固定时间：2026-08-27T16:00:00Z
- 语料：18 份虚构的星舟工作台文档
- 案例：20 个单样本边界案例
- 本报告支持：固定组件下的边界符合性
- 本报告不支持：真实模型质量、Token、成本、延迟或厂商排名

## baseline

| Case | 版本 | 关键指标 |
| --- | --- | --- |
| baseline-parametric-guess | v0 | {   "answer_status": "answer",   "citation_count": 0,   "retrieved_document_count": 0,   "unsupported_claim_count": 1 } |
| baseline-full-context-conflict | v1 | {   "citation_count": 0,   "conflict_document_count": 6,   "context_document_count": 18,   "internal_document_count": 5 } |
| baseline-unanswerable-support-window | v0, v1 | {   "citation_count": 0,   "expected_status": "abstain",   "retrieved_document_count": 0,   "unsupported_claim_count": 1 } |

## chunking

| Case | 版本 | 关键指标 |
| --- | --- | --- |
| chunk-table-sso | v2 | {   "chunk_count": 3,   "complete_table_or_code_blocks": 1,   "max_chunk_characters": 90 } |
| chunk-cross-section-upgrade | v3 | {   "chunk_count": 4,   "complete_table_or_code_blocks": 1,   "heading_aware_chunks": 4 } |
| chunk-code-dry-run | v4 | {   "chunk_count": 4,   "context_prefix_count": 4,   "source_content_digest_unchanged": true } |

## retrieval

| Case | 版本 | 关键指标 |
| --- | --- | --- |
| retrieval-exact-version | v3 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": 1.0,   "ndcg_at_3": 1.0,   "precision_at_3": 0.5,   "recall_at_3": 1.0,   "retrieved_chunk_count": 3,   "retrieved_document_ids": [     "plans-3.2",     "faq-3.2-sso"   ],   "supported_fact_ratio": 1.0,   "unsupported_claim_count": 0 } |
| retrieval-synonym-login | v4 | {   "answer_status": "abstain",   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [     "saml-enterprise-32"   ],   "mrr": 0.0,   "ndcg_at_3": 0.0,   "precision_at_3": null,   "recall_at_3": 0.0,   "retrieved_chunk_count": 0,   "retrieved_document_ids": [],   "supported_fact_ratio": 0.0,   "unsupported_claim_count": 0 } |
| retrieval-compound | v5 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": 0.3333333333333333,   "ndcg_at_3": 0.5,   "precision_at_3": 0.3333333333333333,   "recall_at_3": 1.0,   "retrieved_chunk_count": 3,   "retrieved_document_ids": [     "plans-3.2",     "faq-3.2-sso",     "migration-2x-to-3.2"   ],   "supported_fact_ratio": 1.0,   "unsupported_claim_count": 0 } |
| retrieval-noise | v6 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 0,   "expected_status": "abstain",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": null,   "ndcg_at_3": null,   "precision_at_3": 0.0,   "recall_at_3": null,   "retrieved_chunk_count": 3,   "retrieved_document_ids": [     "api-auth",     "install-3.2"   ],   "supported_fact_ratio": null,   "unsupported_claim_count": 0 } |

## governance

| Case | 版本 | 关键指标 |
| --- | --- | --- |
| governance-compound-upgrade | v6 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": 1.0,   "ndcg_at_3": 0.7653606369886217,   "policy_violation_count": 0,   "precision_at_3": 1.0,   "recall_at_3": 0.6666666666666666,   "retrieved_chunk_count": 3,   "retrieved_document_ids": [     "migration-2x-to-3.2",     "plans-3.2"   ],   "supported_fact_ratio": 1.0,   "unsupported_claim_count": 0 } |
| governance-public-internal | v6 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": 1.0,   "ndcg_at_3": 1.0,   "policy_violation_count": 0,   "precision_at_3": 1.0,   "recall_at_3": 1.0,   "retrieved_chunk_count": 1,   "retrieved_document_ids": [     "security-overview"   ],   "supported_fact_ratio": 1.0,   "unsupported_claim_count": 0 } |
| governance-future-preview | v6 | {   "answer_status": "abstain",   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [     "sso-team-32"   ],   "mrr": 0.0,   "ndcg_at_3": 0.0,   "policy_violation_count": 0,   "precision_at_3": 0.0,   "recall_at_3": 0.0,   "retrieved_chunk_count": 1,   "retrieved_document_ids": [     "community-malicious-note"   ],   "supported_fact_ratio": 0.0,   "unsupported_claim_count": 0 } |
| governance-withdrawn | v6 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": 1.0,   "ndcg_at_3": 0.6131471927654584,   "policy_violation_count": 0,   "precision_at_3": 0.5,   "recall_at_3": 0.5,   "retrieved_chunk_count": 3,   "retrieved_document_ids": [     "migration-2x-to-3.2",     "release-3.2"   ],   "supported_fact_ratio": 1.0,   "unsupported_claim_count": 0 } |
| governance-stale-index | v5, v6 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 1,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": 1.0,   "ndcg_at_3": 1.0,   "precision_at_3": 1.0,   "recall_at_3": 1.0,   "retrieved_chunk_count": 1,   "retrieved_document_ids": [     "security-overview"   ],   "supported_fact_ratio": 1.0,   "unsupported_claim_count": 0 } |

## evidence

| Case | 版本 | 关键指标 |
| --- | --- | --- |
| evidence-missing-members | v7 | {   "answer_status": "abstain",   "citation_count": 1,   "missing_fact_ids": [     "members-preserved-32"   ],   "unsupported_claim_count": 0 } |
| evidence-wrong-citation | v7 | {   "precision": 0.5,   "recall": 0.5,   "supported_claim_ratio": 0.5 } |
| evidence-conflicting-source | v7 | {   "answer_status": "abstain",   "authoritative_source_present": false,   "catalog_recheck_rejected_count": 0,   "expected_status": "answer",   "filtered_before_score_count": 9,   "missing_fact_ids": [     "sso-team-32"   ],   "mrr": 0.0,   "ndcg_at_3": 0.0,   "precision_at_3": 0.0,   "recall_at_3": 0.0,   "retrieved_chunk_count": 2,   "retrieved_document_ids": [     "community-sso-note",     "community-malicious-note"   ],   "supported_fact_ratio": 0.0,   "unsupported_claim_count": 0 } |
| evidence-prompt-injection | v7 | {   "answer_status": "answer",   "citation_count": 1,   "untrusted_instruction_in_answer_context": 0 } |
| evidence-correct-abstain | v7 | {   "answer_status": "answer",   "catalog_recheck_rejected_count": 0,   "expected_status": "abstain",   "filtered_before_score_count": 9,   "missing_fact_ids": [],   "mrr": null,   "ndcg_at_3": null,   "precision_at_3": 0.0,   "recall_at_3": null,   "retrieved_chunk_count": 3,   "retrieved_document_ids": [     "plans-3.2",     "faq-3.2-sso"   ],   "supported_fact_ratio": null,   "unsupported_claim_count": 0 } |
