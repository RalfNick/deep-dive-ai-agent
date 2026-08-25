from __future__ import annotations

import re
from typing import Iterable

from .contracts import (
    Authority,
    MemoryCandidate,
    MemoryLifetime,
    MemoryRecord,
    Sensitivity,
    WriteDecision,
    WriteDecisionKind,
)


SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:api[_ -]?key|password|secret)\s*[:=]", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class MemoryWritePolicy:
    """Deterministic policy used to make write boundaries observable."""

    def evaluate(self, candidate: MemoryCandidate, *, current: Iterable[MemoryRecord]) -> WriteDecision:
        if candidate.sensitivity is Sensitivity.SECRET or any(
            pattern.search(candidate.content) for pattern in SENSITIVE_PATTERNS
        ):
            return self._decision(candidate, WriteDecisionKind.REJECT, "sensitive_content")

        if candidate.lifetime is MemoryLifetime.ONE_TIME:
            return self._decision(candidate, WriteDecisionKind.REJECT, "one_time_content")
        if candidate.lifetime is MemoryLifetime.CURRENT_TASK:
            return self._decision(candidate, WriteDecisionKind.REJECT, "current_task_state")
        if candidate.confidence < 0.6:
            return self._decision(candidate, WriteDecisionKind.REJECT, "low_confidence")

        relevant = tuple(
            record
            for record in current
            if record.namespace == candidate.namespace
            and record.memory_type is candidate.memory_type
            and record.subject == candidate.subject
        )
        if any(record.content == candidate.content for record in relevant):
            return self._decision(candidate, WriteDecisionKind.REJECT, "duplicate_memory")
        if relevant:
            return self._decision(candidate, WriteDecisionKind.REVIEW, "conflict_requires_correction")

        if candidate.authority in {Authority.MODEL_INFERENCE, Authority.USER_INFERRED}:
            return self._decision(candidate, WriteDecisionKind.REVIEW, "inferred_memory_requires_review")
        if candidate.authority in {Authority.REPOSITORY_VERIFIED, Authority.TOOL_OBSERVED}:
            return self._decision(candidate, WriteDecisionKind.ALLOW, "verified_cross_task_memory")
        return self._decision(candidate, WriteDecisionKind.ALLOW, "explicit_cross_task_memory")

    @staticmethod
    def _decision(candidate: MemoryCandidate, kind: WriteDecisionKind, reason: str) -> WriteDecision:
        return WriteDecision(candidate.candidate_id, kind, reason)

