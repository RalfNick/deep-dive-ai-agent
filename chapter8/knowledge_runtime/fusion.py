from __future__ import annotations

from collections.abc import Mapping, Sequence

from chapter8.knowledge_runtime.contracts import Chunk, RankedChunk


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[RankedChunk]],
    rrf_k: int,
    top_k: int,
) -> tuple[RankedChunk, ...]:
    if rrf_k < 0:
        raise ValueError("negative_rrf_k")
    if top_k <= 0:
        raise ValueError("non_positive_top_k")
    scores: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}
    for channel in sorted(rankings):
        for rank, item in enumerate(rankings[channel], start=1):
            chunk_id = item.chunk.chunk_id
            chunks[chunk_id] = item.chunk
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
    ordered = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    return tuple(
        RankedChunk(chunk=chunks[chunk_id], score=scores[chunk_id], rank=rank)
        for rank, chunk_id in enumerate(ordered[:top_k], start=1)
    )
