from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Set
import math
import re

from chapter8.knowledge_runtime.contracts import Chunk, RankedChunk


_TERM = re.compile(r"[A-Za-z][A-Za-z0-9_-]*|\d+(?:\.\d+)+|[\u3400-\u4dbf\u4e00-\u9fff]+")


def tokenize(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for match in _TERM.finditer(text.lower()):
        value = match.group(0)
        if re.fullmatch(r"[\u3400-\u4dbf\u4e00-\u9fff]+", value):
            if len(value) == 1:
                tokens.append(value)
            else:
                tokens.extend(value[index : index + 2] for index in range(len(value) - 1))
        else:
            tokens.append(value)
    return tuple(tokens)


class BM25Index:
    def __init__(self, chunks: Iterable[Chunk], *, k1: float = 1.5, b: float = 0.75) -> None:
        self._chunks = tuple(chunks)
        self._tokens = {
            chunk.chunk_id: tokenize(f"{chunk.context_prefix}\n{chunk.content}")
            for chunk in self._chunks
        }
        self._k1 = k1
        self._b = b
        self._average_length = (
            sum(len(tokens) for tokens in self._tokens.values()) / len(self._tokens)
            if self._tokens
            else 0.0
        )
        self._document_frequency: Counter[str] = Counter()
        for tokens in self._tokens.values():
            self._document_frequency.update(set(tokens))

    def _idf(self, term: str) -> float:
        corpus_size = len(self._chunks)
        frequency = self._document_frequency.get(term, 0)
        return math.log(1.0 + (corpus_size - frequency + 0.5) / (frequency + 0.5))

    def rank(
        self,
        query_text: str,
        allowed_chunk_ids: Set[str],
        top_k: int,
    ) -> tuple[RankedChunk, ...]:
        if top_k <= 0:
            raise ValueError("non_positive_top_k")
        query_terms = tokenize(query_text)
        scored: list[tuple[float, Chunk]] = []
        for chunk in self._chunks:
            if chunk.chunk_id not in allowed_chunk_ids:
                continue
            terms = self._tokens[chunk.chunk_id]
            counts = Counter(terms)
            length_ratio = len(terms) / self._average_length if self._average_length else 0.0
            score = 0.0
            for term in query_terms:
                frequency = counts.get(term, 0)
                if frequency == 0:
                    continue
                numerator = frequency * (self._k1 + 1.0)
                denominator = frequency + self._k1 * (1.0 - self._b + self._b * length_ratio)
                score += self._idf(term) * numerator / denominator
            if score > 0.0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return tuple(
            RankedChunk(chunk=chunk, score=score, rank=rank)
            for rank, (score, chunk) in enumerate(scored[:top_k], start=1)
        )
