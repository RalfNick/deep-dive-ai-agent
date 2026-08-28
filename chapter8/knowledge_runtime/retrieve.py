from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import overload

from chapter8.knowledge_runtime.catalog import KnowledgeCatalog
from chapter8.knowledge_runtime.contracts import (
    Chunk,
    RetrievalHit,
    RetrievalQuery,
    ScoreBreakdown,
    stable_digest,
)
from chapter8.knowledge_runtime.dense import DenseIndex
from chapter8.knowledge_runtime.fusion import reciprocal_rank_fusion
from chapter8.knowledge_runtime.rerank import DeterministicReranker
from chapter8.knowledge_runtime.sparse import BM25Index, tokenize


@dataclass(frozen=True)
class RetrievalTrace:
    query_digest: str
    filtered_before_score: tuple[str, ...]
    scored_document_ids: tuple[str, ...]
    sparse_candidates: tuple[str, ...]
    dense_candidates: tuple[str, ...]
    fused_candidates: tuple[str, ...]
    catalog_recheck_rejected: tuple[str, ...]
    final_hits: tuple[str, ...]


class HybridRetriever:
    def __init__(
        self,
        *,
        catalog: KnowledgeCatalog,
        chunks: Iterable[Chunk],
        sparse: BM25Index,
        dense: DenseIndex,
        reranker: DeterministicReranker,
    ) -> None:
        self.catalog = catalog
        self._chunks = tuple(chunks)
        self._chunk_by_id = {chunk.chunk_id: chunk for chunk in self._chunks}
        if len(self._chunk_by_id) != len(self._chunks):
            raise ValueError("duplicate_chunk_id")
        self.sparse = sparse
        self.dense = dense
        self.reranker = reranker

    @overload
    def retrieve(self, query: RetrievalQuery, *, include_trace: bool = False) -> tuple[RetrievalHit, ...]:
        ...

    @overload
    def retrieve(
        self,
        query: RetrievalQuery,
        *,
        include_trace: bool,
    ) -> tuple[tuple[RetrievalHit, ...], RetrievalTrace]:
        ...

    def retrieve(self, query: RetrievalQuery, *, include_trace: bool = False):
        eligible = self.catalog.current_documents(query)
        eligible_document_ids = {document.document_id for document in eligible}
        all_document_ids = {document.document_id for document in self.catalog.all_documents}
        allowed_chunk_ids = {
            chunk.chunk_id
            for chunk in self._chunks
            if chunk.document_id in eligible_document_ids
        }

        sparse = self.sparse.rank(query.text, allowed_chunk_ids, query.candidate_k)
        dense = self.dense.rank(query.text, allowed_chunk_ids, query.candidate_k)
        fused = reciprocal_rank_fusion(
            {"dense": dense, "sparse": sparse},
            rrf_k=60,
            top_k=query.candidate_k,
        )

        live_chunks: list[Chunk] = []
        recheck_rejected: list[str] = []
        for item in fused:
            if self.catalog.resolve_document(item.chunk.document_id, query) is None:
                recheck_rejected.append(f"{item.chunk.document_id}:{item.chunk.chunk_id}")
            else:
                live_chunks.append(item.chunk)

        reranked = self.reranker.rank(query.text, live_chunks, query.candidate_k)
        query_terms = set(tokenize(query.text))
        qualified = [
            item
            for item in reranked
            if len(query_terms & set(tokenize(f"{item.chunk.context_prefix}\n{item.chunk.content}"))) >= 2
        ][: query.top_k]

        sparse_scores = {item.chunk.chunk_id: item.score for item in sparse}
        dense_scores = {item.chunk.chunk_id: item.score for item in dense}
        fusion_scores = {item.chunk.chunk_id: item.score for item in fused}
        hits = tuple(
            RetrievalHit(
                chunk=item.chunk,
                score=item.score,
                breakdown=ScoreBreakdown(
                    lexical=sparse_scores.get(item.chunk.chunk_id),
                    semantic=dense_scores.get(item.chunk.chunk_id),
                    fusion=fusion_scores.get(item.chunk.chunk_id),
                    rerank=item.score,
                ),
            )
            for item in qualified
        )
        trace = RetrievalTrace(
            query_digest=stable_digest(
                {
                    "text": query.text,
                    "role": query.role,
                    "target_version": query.target_version,
                    "now": query.now,
                    "top_k": query.top_k,
                    "candidate_k": query.candidate_k,
                }
            ),
            filtered_before_score=tuple(sorted(all_document_ids - eligible_document_ids)),
            scored_document_ids=tuple(sorted(eligible_document_ids)),
            sparse_candidates=tuple(item.chunk.chunk_id for item in sparse),
            dense_candidates=tuple(item.chunk.chunk_id for item in dense),
            fused_candidates=tuple(item.chunk.chunk_id for item in fused),
            catalog_recheck_rejected=tuple(recheck_rejected),
            final_hits=tuple(hit.chunk.chunk_id for hit in hits),
        )
        if include_trace:
            return hits, trace
        return hits
