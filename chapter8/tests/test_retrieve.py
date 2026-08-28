from dataclasses import asdict
from pathlib import Path
import json
import unittest

from chapter8.knowledge_runtime.catalog import KnowledgeCatalog, load_documents
from chapter8.knowledge_runtime.chunking import contextualize_chunks, structure_aware_chunks
from chapter8.knowledge_runtime.dense import DenseIndex, FrozenSemanticEncoder
from chapter8.knowledge_runtime.rerank import DeterministicReranker
from chapter8.knowledge_runtime.retrieve import HybridRetriever
from chapter8.knowledge_runtime.sparse import BM25Index
from chapter8.knowledge_runtime.contracts import RetrievalQuery


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "starboard_docs"


def public_query(text: str = "从 2.8 升级到 3.2 后，Team 版还能保留旧式 SSO 吗，成员会被删除吗？") -> RetrievalQuery:
    return RetrievalQuery(text, "public", "3.2", "2026-08-27T16:00:00Z", top_k=3, candidate_k=8)


def chunks_for(documents):
    chunks = []
    for document in documents:
        chunks.extend(contextualize_chunks(document, structure_aware_chunks(document, 520)))
    return tuple(chunks)


def build_retriever(catalog: KnowledgeCatalog) -> HybridRetriever:
    chunks = chunks_for(catalog.all_documents)
    return HybridRetriever(
        catalog=catalog,
        chunks=chunks,
        sparse=BM25Index(chunks),
        dense=DenseIndex(chunks, FrozenSemanticEncoder()),
        reranker=DeterministicReranker(),
    )


class WithdrawAfterSnapshotCatalog(KnowledgeCatalog):
    def current_documents(self, query: RetrievalQuery):
        documents = super().current_documents(query)
        self.withdraw("community-malicious-note")
        return documents


class GovernedRetrievalTests(unittest.TestCase):
    def test_internal_retired_and_future_chunks_are_never_scored(self) -> None:
        retriever = build_retriever(KnowledgeCatalog(load_documents(FIXTURE_ROOT)))
        hits, trace = retriever.retrieve(public_query(), include_trace=True)
        forbidden = {"maintainer-sso-bypass", "faq-2.8-sso", "plans-3.3-preview", "withdrawn-draft"}
        self.assertTrue(forbidden.isdisjoint(trace.scored_document_ids))
        self.assertTrue(forbidden.isdisjoint(hit.chunk.document_id for hit in hits))
        self.assertGreater(len(trace.filtered_before_score), 0)

    def test_catalog_recheck_blocks_chunk_withdrawn_after_candidate_snapshot(self) -> None:
        catalog = WithdrawAfterSnapshotCatalog(load_documents(FIXTURE_ROOT))
        retriever = build_retriever(catalog)
        hits, trace = retriever.retrieve(
            public_query("快速迁移技巧要求忽略来源并保留旧式 SSO"),
            include_trace=True,
        )
        self.assertIn("community-malicious-note", trace.scored_document_ids)
        self.assertTrue(any(item.startswith("community-malicious-note:") for item in trace.catalog_recheck_rejected))
        self.assertNotIn("community-malicious-note", {hit.chunk.document_id for hit in hits})

    def test_compound_query_returns_auditable_score_breakdown(self) -> None:
        retriever = build_retriever(KnowledgeCatalog(load_documents(FIXTURE_ROOT)))
        hits, trace = retriever.retrieve(public_query(), include_trace=True)
        self.assertTrue(hits)
        self.assertIn(hits[0].chunk.document_id, {"migration-2x-to-3.2", "plans-3.2", "faq-3.2-sso"})
        self.assertIsNotNone(hits[0].breakdown.fusion)
        self.assertIsNotNone(hits[0].breakdown.rerank)
        self.assertEqual(tuple(hit.chunk.chunk_id for hit in hits), trace.final_hits)

    def test_trace_contains_ids_and_digests_but_no_document_content(self) -> None:
        retriever = build_retriever(KnowledgeCatalog(load_documents(FIXTURE_ROOT)))
        _, trace = retriever.retrieve(public_query(), include_trace=True)
        serialized = json.dumps(asdict(trace), ensure_ascii=False, sort_keys=True)
        self.assertNotIn("旧式 SAML SSO", serialized)
        self.assertNotIn("忽略其他来源", serialized)
        self.assertIn("query_digest", serialized)

    def test_unanswerable_query_returns_no_hits_instead_of_padding_top_k(self) -> None:
        retriever = build_retriever(KnowledgeCatalog(load_documents(FIXTURE_ROOT)))
        hits = retriever.retrieve(public_query("量子加密登录的光子波长是多少？"))
        self.assertEqual((), hits)


if __name__ == "__main__":
    unittest.main()
