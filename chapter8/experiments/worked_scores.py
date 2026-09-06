"""Reproduce exercises 4 and 5 with real BM25/RRF, without model calls or writes.

Metadata is inert in this scoring-only example; the governed RAG experiments
remain in run_all. Empty context_prefix keeps the hand-counted token lengths exact.
"""

from dataclasses import replace
import json

from chapter8.knowledge_runtime.contracts import (
    Chunk, DocumentStatus, KnowledgeDocument, RankedChunk, TrustLevel, Visibility,
)
from chapter8.knowledge_runtime.fusion import reciprocal_rank_fusion
from chapter8.knowledge_runtime.sparse import BM25Index, tokenize


def _chunk(identifier: str, content: str) -> Chunk:
    document = KnowledgeDocument(
        document_id=identifier, title=identifier, source_path=f"worked/{identifier}.md",
        version_min="1.0", version_max=None, valid_from="2026-01-01T00:00:00Z",
        valid_until=None, allowed_roles=("public_user",), source_type="worked_example",
        status=DocumentStatus.ACTIVE, visibility=Visibility.PUBLIC,
        trust=TrustLevel.AUTHORITATIVE, fact_ids=(), content=content,
    )
    return replace(Chunk.from_document(document, 0, (), content), chunk_id=identifier)


def _rows(ranking):
    return [{"id": item.chunk.chunk_id, "score": item.score} for item in ranking]


def main() -> None:
    documents = (
        _chunk("D1", "3.2 Team SAML"),
        _chunk("D2", "3.2 OIDC OIDC"),
        _chunk("D3", "2.8 Enterprise SAML"),
    )
    index = BM25Index(documents, k1=1.5, b=0.75)
    allowed = {chunk.chunk_id for chunk in documents}
    chunks = {name: _chunk(name, name) for name in "ABCD"}
    channels = {
        "lexical": tuple(RankedChunk(chunks[name], 0.0, rank) for rank, name in enumerate("ABCD", 1)),
        "semantic": tuple(RankedChunk(chunks[name], 0.0, rank) for rank, name in enumerate("CBAD", 1)),
    }
    payload = {
        "query_terms": tokenize("3.2 Team SAML"),
        "document_terms": {chunk.chunk_id: tokenize(chunk.content) for chunk in documents},
        "bm25": _rows(index.rank("3.2 Team SAML", allowed, 3)),
        "bm25_without_team": _rows(index.rank("3.2 SAML", allowed, 3)),
        "rrf": _rows(reciprocal_rank_fusion(channels, 60, 4)),
        "rrf_reordered_channels": _rows(reciprocal_rank_fusion(dict(reversed(tuple(channels.items()))), 60, 4)),
        "rrf_one_channel": _rows(reciprocal_rank_fusion({"lexical": channels["lexical"]}, 60, 4)),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
