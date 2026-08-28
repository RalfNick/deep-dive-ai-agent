from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CitationMetrics:
    precision: float | None
    recall: float | None
    supported_claim_ratio: float | None


@dataclass(frozen=True)
class AnswerSupportMetrics:
    supported_fact_ratio: float | None
    unsupported_claim_count: int
    missing_fact_ids: tuple[str, ...]


def _positive_k(k: int) -> None:
    if k <= 0:
        raise ValueError("non_positive_k")


def precision_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float | None:
    _positive_k(k)
    window = tuple(retrieved[:k])
    return sum(item in relevant for item in window) / k


def recall_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float | None:
    _positive_k(k)
    if not relevant:
        return None
    return len(set(retrieved[:k]) & set(relevant)) / len(relevant)


def mean_reciprocal_rank(retrieved: Sequence[str], relevant: Set[str]) -> float | None:
    if not relevant:
        return None
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float | None:
    _positive_k(k)
    if not relevant:
        return None
    actual = sum(
        1.0 / math.log2(rank + 1)
        for rank, item in enumerate(retrieved[:k], start=1)
        if item in relevant
    )
    ideal_count = min(k, len(relevant))
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return actual / ideal


def citation_metrics(
    expected: Mapping[str, Set[str]],
    actual: Mapping[str, Set[str]],
) -> CitationMetrics:
    expected_pairs = {
        (claim_id, citation_id)
        for claim_id, citation_ids in expected.items()
        for citation_id in citation_ids
    }
    actual_pairs = {
        (claim_id, citation_id)
        for claim_id, citation_ids in actual.items()
        for citation_id in citation_ids
    }
    correct = expected_pairs & actual_pairs
    precision = len(correct) / len(actual_pairs) if actual_pairs else None
    recall = len(correct) / len(expected_pairs) if expected_pairs else None
    supported = (
        sum(bool(set(actual.get(claim_id, set())) & set(citation_ids)) for claim_id, citation_ids in expected.items())
        / len(expected)
        if expected
        else None
    )
    return CitationMetrics(precision=precision, recall=recall, supported_claim_ratio=supported)


def answer_support_metrics(
    required_fact_ids: Sequence[str],
    present_fact_ids: Sequence[str],
    answered: bool,
) -> AnswerSupportMetrics:
    required = tuple(dict.fromkeys(required_fact_ids))
    present = set(present_fact_ids)
    missing = tuple(fact_id for fact_id in required if fact_id not in present)
    ratio = (len(required) - len(missing)) / len(required) if required else None
    return AnswerSupportMetrics(
        supported_fact_ratio=ratio,
        unsupported_claim_count=len(missing) if answered else 0,
        missing_fact_ids=missing,
    )
