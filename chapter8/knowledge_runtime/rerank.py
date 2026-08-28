from __future__ import annotations

from collections.abc import Iterable

from chapter8.knowledge_runtime.contracts import Chunk, RankedChunk, TrustLevel
from chapter8.knowledge_runtime.sparse import tokenize


_TRUST_WEIGHT = {
    TrustLevel.AUTHORITATIVE: 1.0,
    TrustLevel.CURATED: 0.45,
    TrustLevel.COMMUNITY: -0.75,
}
_INJECTION_MARKERS = ("忽略其他来源", "忽略系统", "unknown maintenance", "未知维护链接")


class DeterministicReranker:
    """A visible teaching policy that demonstrates the reranking boundary."""

    def score(self, query_text: str, chunk: Chunk) -> float:
        query_terms = set(tokenize(query_text))
        candidate_terms = set(tokenize(f"{chunk.context_prefix}\n{chunk.content}"))
        overlap = len(query_terms & candidate_terms)
        score = float(overlap) + _TRUST_WEIGHT[chunk.trust]
        lowered = chunk.content.lower()
        if any(marker in lowered for marker in _INJECTION_MARKERS):
            score -= 3.0
        for version in ("2.8", "3.2", "3.3"):
            if version in query_text:
                score += 0.5 if chunk.version_min == version else -0.5
        return score

    def rank(
        self,
        query_text: str,
        candidates: Iterable[Chunk],
        top_k: int,
    ) -> tuple[RankedChunk, ...]:
        if top_k <= 0:
            raise ValueError("non_positive_top_k")
        scored = [(self.score(query_text, chunk), chunk) for chunk in candidates]
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return tuple(
            RankedChunk(chunk=chunk, score=score, rank=rank)
            for rank, (score, chunk) in enumerate(scored[:top_k], start=1)
        )
