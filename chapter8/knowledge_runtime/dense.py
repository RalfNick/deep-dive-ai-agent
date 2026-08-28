from __future__ import annotations

from collections.abc import Iterable, Set
import math
from typing import Protocol

from chapter8.knowledge_runtime.contracts import Chunk, RankedChunk


class EmbeddingModel(Protocol):
    def embed(self, text: str) -> tuple[float, ...]:
        ...


class FrozenSemanticEncoder:
    """A deterministic concept encoder for contract tests, not a learned embedding model."""

    _CONCEPTS = (
        ("sso", "saml", "oidc", "单点", "登录", "身份"),
        ("成员", "member", "邀请", "配额", "用户"),
        ("升级", "迁移", "migrate", "回滚", "版本"),
        ("安全", "权限", "令牌", "密钥", "secret", "规则"),
        ("api", "接口", "token", "客户端"),
        ("支持", "套餐", "team", "enterprise", "企业"),
    )

    def embed(self, text: str) -> tuple[float, ...]:
        lowered = text.lower()
        raw = tuple(float(sum(lowered.count(term) for term in concept)) for concept in self._CONCEPTS)
        norm = math.sqrt(sum(value * value for value in raw))
        if norm == 0.0:
            return tuple(0.0 for _ in raw)
        return tuple(value / norm for value in raw)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding_dimension_mismatch")
    return sum(a * b for a, b in zip(left, right))


class DenseIndex:
    def __init__(self, chunks: Iterable[Chunk], encoder: EmbeddingModel) -> None:
        self._chunks = tuple(chunks)
        self._encoder = encoder
        self._vectors = {
            chunk.chunk_id: encoder.embed(f"{chunk.context_prefix}\n{chunk.content}")
            for chunk in self._chunks
        }

    def rank(
        self,
        query_text: str,
        allowed_chunk_ids: Set[str],
        top_k: int,
    ) -> tuple[RankedChunk, ...]:
        if top_k <= 0:
            raise ValueError("non_positive_top_k")
        query_vector = self._encoder.embed(query_text)
        scored = [
            (cosine_similarity(query_vector, self._vectors[chunk.chunk_id]), chunk)
            for chunk in self._chunks
            if chunk.chunk_id in allowed_chunk_ids
        ]
        scored = [item for item in scored if item[0] > 0.0]
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return tuple(
            RankedChunk(chunk=chunk, score=score, rank=rank)
            for rank, (score, chunk) in enumerate(scored[:top_k], start=1)
        )
