from __future__ import annotations

from datetime import timedelta
import re

from .contracts import (
    Authority,
    MemoryNamespace,
    MemoryRecord,
    RecallHit,
    RecallQuery,
    ScoreBreakdown,
    parse_utc_seconds,
)
from .store import MemoryStore


WORD_OR_CJK = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)


def terms(text: str) -> frozenset[str]:
    found: set[str] = set()
    for token in WORD_OR_CJK.findall(text.lower().replace("_", " ")):
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            found.add(token)
            if len(token) > 1:
                found.update(token[index : index + 2] for index in range(len(token) - 1))
        else:
            found.add(token)
    return frozenset(found)


AUTHORITY_SCORE = {
    Authority.USER_EXPLICIT: 3.0,
    Authority.REPOSITORY_VERIFIED: 3.0,
    Authority.TOOL_OBSERVED: 2.0,
    Authority.USER_INFERRED: 1.0,
    Authority.MODEL_INFERENCE: 0.5,
}


class MemoryRecall:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def search(self, query: RecallQuery) -> tuple[RecallHit, ...]:
        query_terms = terms(query.query)
        hits: list[RecallHit] = []
        for record in self.store.all_current(now=query.now):
            if not self._scope_matches(record.namespace, query.namespace):
                continue
            if query.memory_types and record.memory_type not in query.memory_types:
                continue
            if record.sensitivity not in query.allowed_sensitivities:
                continue
            score = self._score(record, query, query_terms)
            if score.task_match <= 0:
                continue
            hits.append(RecallHit(record, score))
        hits.sort(key=lambda hit: (-hit.score.total, hit.record.memory_id, hit.record.record_id))
        return tuple(hits[: query.top_k])

    @staticmethod
    def _scope_matches(record: MemoryNamespace, query: MemoryNamespace) -> bool:
        if (record.tenant_id, record.user_id, record.agent_id) != (
            query.tenant_id,
            query.user_id,
            query.agent_id,
        ):
            return False
        return record.project_id is None or record.project_id == query.project_id

    @staticmethod
    def _score(record: MemoryRecord, query: RecallQuery, query_terms: frozenset[str]) -> ScoreBreakdown:
        record_terms = terms(f"{record.subject} {record.content}")
        overlap = len(query_terms & record_terms)
        task_match = round(4.0 * overlap / max(1, len(query_terms)), 6)
        authority = AUTHORITY_SCORE[record.authority]
        age = parse_utc_seconds(query.now, "invalid_recall_time") - parse_utc_seconds(record.valid_from, "invalid_valid_from")
        if age < timedelta(0):
            recency = 0.0
        elif age <= timedelta(days=30):
            recency = 2.0
        elif age <= timedelta(days=365):
            recency = 1.0
        else:
            recency = 0.0
        confidence = round(record.confidence, 6)
        total = round(task_match + authority + recency + confidence, 6)
        return ScoreBreakdown(task_match, authority, recency, confidence, total)

