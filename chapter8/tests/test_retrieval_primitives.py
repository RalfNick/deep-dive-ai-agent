from pathlib import Path
import unittest

from chapter8.knowledge_runtime.catalog import load_documents
from chapter8.knowledge_runtime.chunking import contextualize_chunks, structure_aware_chunks
from chapter8.knowledge_runtime.contracts import RankedChunk
from chapter8.knowledge_runtime.dense import DenseIndex, FrozenSemanticEncoder
from chapter8.knowledge_runtime.fusion import reciprocal_rank_fusion
from chapter8.knowledge_runtime.rerank import DeterministicReranker
from chapter8.knowledge_runtime.sparse import BM25Index, tokenize


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "starboard_docs"


def all_chunks():
    chunks = []
    for document in load_documents(FIXTURE_ROOT):
        source = structure_aware_chunks(document, max_chars=520)
        chunks.extend(contextualize_chunks(document, source))
    return tuple(chunks)


def chunk_from(document_id: str, phrase: str):
    return next(chunk for chunk in all_chunks() if chunk.document_id == document_id and phrase in chunk.content)


class RetrievalPrimitiveTests(unittest.TestCase):
    def test_tokenizer_keeps_ascii_terms_versions_and_chinese_bigrams(self) -> None:
        tokens = tokenize("Team 3.2 的单点登录（SSO）")
        self.assertIn("team", tokens)
        self.assertIn("3.2", tokens)
        self.assertIn("sso", tokens)
        self.assertIn("单点", tokens)
        self.assertIn("登录", tokens)

    def test_bm25_scores_only_allowed_chunks_and_is_deterministic(self) -> None:
        chunks = all_chunks()
        allowed = {
            chunk.chunk_id
            for chunk in chunks
            if chunk.document_id in {"plans-3.2", "migration-2x-to-3.2", "community-malicious-note"}
        }
        index = BM25Index(chunks)
        first = index.rank("Team 3.2 旧式 SSO", allowed, top_k=5)
        second = index.rank("Team 3.2 旧式 SSO", allowed, top_k=5)
        self.assertEqual(first, second)
        self.assertTrue(first)
        self.assertTrue(all(item.chunk.chunk_id in allowed for item in first))
        self.assertGreater(first[0].score, 0.0)

    def test_frozen_semantic_encoder_maps_login_synonym_to_sso_evidence(self) -> None:
        chunks = all_chunks()
        allowed = {chunk.chunk_id for chunk in chunks if chunk.document_id in {"plans-3.2", "membership-backup"}}
        results = DenseIndex(chunks, FrozenSemanticEncoder()).rank("企业单点登录方式", allowed, top_k=3)
        self.assertTrue(results)
        self.assertEqual("plans-3.2", results[0].chunk.document_id)
        self.assertGreater(results[0].score, 0.0)

    def test_rrf_matches_hand_calculation_and_uses_stable_tie_break(self) -> None:
        a = chunk_from("plans-3.2", "旧式 SAML SSO")
        b = chunk_from("migration-2x-to-3.2", "不能在 3.2 保留")
        c = chunk_from("faq-3.2-sso", "不会自动删除")
        fused = reciprocal_rank_fusion(
            {
                "sparse": (RankedChunk(a, 9.0, 1), RankedChunk(b, 8.0, 2)),
                "dense": (RankedChunk(b, 0.9, 1), RankedChunk(c, 0.8, 2)),
            },
            rrf_k=60,
            top_k=3,
        )
        scores = {item.chunk.chunk_id: item.score for item in fused}
        self.assertEqual(b.chunk_id, fused[0].chunk.chunk_id)
        self.assertAlmostEqual(1 / 62 + 1 / 61, scores[b.chunk_id], places=12)
        self.assertAlmostEqual(1 / 61, scores[a.chunk_id], places=12)

    def test_reranker_penalizes_injection_and_prefers_authoritative_evidence(self) -> None:
        official = chunk_from("plans-3.2", "旧式 SAML SSO")
        malicious = chunk_from("community-malicious-note", "忽略其他来源")
        ranked = DeterministicReranker().rank(
            "Team 3.2 能否保留旧式 SSO",
            (malicious, official),
            top_k=2,
        )
        self.assertEqual("plans-3.2", ranked[0].chunk.document_id)
        self.assertLess(ranked[1].score, ranked[0].score)


if __name__ == "__main__":
    unittest.main()
