from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    Authority,
    DeletionReceipt,
    MemoryCandidate,
    MemoryRecord,
    MemoryType,
    RecallHit,
    RecallQuery,
    Tombstone,
    WriteDecision,
    WriteDecisionKind,
    stable_digest,
)
from .policy import MemoryWritePolicy
from .recall import MemoryRecall
from .store import MemoryConflictError, MemoryStore


@dataclass(frozen=True)
class WriteOutcome:
    decision: WriteDecision
    record: MemoryRecord | None
    store_result: str | None


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    operation: str
    target_id: str
    namespace_key: str
    outcome: str
    reason: str
    at: str
    content_digest: str


class MemoryRuntime:
    def __init__(self, store: MemoryStore | None = None, policy: MemoryWritePolicy | None = None) -> None:
        self.store = store or MemoryStore()
        self.policy = policy or MemoryWritePolicy()
        self.recaller = MemoryRecall(self.store)
        self._audit: list[AuditEvent] = []

    @staticmethod
    def memory_id(candidate: MemoryCandidate) -> str:
        return "mem-" + stable_digest(
            {
                "namespace": candidate.namespace.key,
                "memory_type": candidate.memory_type,
                "subject": candidate.subject,
            }
        )[:16]

    @staticmethod
    def _record_id(candidate: MemoryCandidate, *, memory_id: str, version: int) -> str:
        return "rec-" + stable_digest(
            {
                "candidate_id": candidate.candidate_id,
                "memory_id": memory_id,
                "content": candidate.content,
                "source_id": candidate.source_id,
                "proposed_at": candidate.proposed_at,
                "version": version,
            }
        )[:16]

    def write(self, candidate: MemoryCandidate) -> WriteOutcome:
        current = self.store.all_current(now=candidate.proposed_at)
        decision = self.policy.evaluate(candidate, current=current)
        if decision.kind is not WriteDecisionKind.ALLOW:
            self._trace(
                operation="write",
                target_id=candidate.candidate_id,
                namespace_key=candidate.namespace.key,
                outcome=decision.kind.value,
                reason=decision.reason,
                at=candidate.proposed_at,
                content=candidate.content,
            )
            return WriteOutcome(decision, None, None)

        memory_id = self.memory_id(candidate)
        record = MemoryRecord(
            record_id=self._record_id(candidate, memory_id=memory_id, version=1),
            memory_id=memory_id,
            namespace=candidate.namespace,
            memory_type=candidate.memory_type,
            subject=candidate.subject,
            content=candidate.content,
            source_id=candidate.source_id,
            authority=candidate.authority,
            confidence=candidate.confidence,
            sensitivity=candidate.sensitivity,
            valid_from=candidate.proposed_at,
            expires_at=None,
            created_at=candidate.proposed_at,
            version=1,
            supersedes=None,
        )
        result = self.store.append(record)
        self._trace(
            operation="write",
            target_id=record.memory_id,
            namespace_key=record.namespace.key,
            outcome=result,
            reason=decision.reason,
            at=record.created_at,
            content=record.content,
        )
        return WriteOutcome(decision, record, result)

    def correct(
        self,
        candidate: MemoryCandidate,
        *,
        expected_record_id: str,
        approved: bool,
    ) -> MemoryRecord:
        if not approved:
            raise MemoryConflictError("correction_not_approved")
        memory_id = self.memory_id(candidate)
        current = self.store.current(candidate.namespace, memory_id, now=candidate.proposed_at)
        if current is None:
            raise MemoryConflictError("unknown_memory")
        if current.record_id != expected_record_id:
            raise MemoryConflictError("stale_expected_record")
        decision = self.policy.evaluate(candidate, current=(current,))
        if decision.kind is WriteDecisionKind.REJECT:
            raise MemoryConflictError(decision.reason)
        if decision.reason != "conflict_requires_correction":
            raise MemoryConflictError("correction_without_conflict")

        version = current.version + 1
        replacement = MemoryRecord(
            record_id=self._record_id(candidate, memory_id=memory_id, version=version),
            memory_id=memory_id,
            namespace=candidate.namespace,
            memory_type=candidate.memory_type,
            subject=candidate.subject,
            content=candidate.content,
            source_id=candidate.source_id,
            authority=candidate.authority,
            confidence=candidate.confidence,
            sensitivity=candidate.sensitivity,
            valid_from=candidate.proposed_at,
            expires_at=None,
            created_at=candidate.proposed_at,
            version=version,
            supersedes=current.record_id,
        )
        self.store.append(replacement)
        self._trace(
            operation="correct",
            target_id=replacement.memory_id,
            namespace_key=replacement.namespace.key,
            outcome="written",
            reason="approved_correction",
            at=replacement.created_at,
            content=replacement.content,
        )
        return replacement

    def forget(
        self,
        *,
        namespace,
        memory_id: str,
        deleted_at: str,
        source_id: str,
        reason: str,
    ) -> DeletionReceipt:
        versions = self.store.versions(namespace, memory_id)
        if not versions:
            raise MemoryConflictError("unknown_memory")
        version = versions[-1].version + 1
        tombstone = Tombstone(
            tombstone_id="tomb-" + stable_digest(
                {
                    "namespace": namespace.key,
                    "memory_id": memory_id,
                    "deleted_at": deleted_at,
                    "source_id": source_id,
                    "version": version,
                }
            )[:16],
            memory_id=memory_id,
            namespace=namespace,
            deleted_at=deleted_at,
            reason=reason,
            source_id=source_id,
            version=version,
        )
        receipt = self.store.forget(tombstone)
        self._trace(
            operation="forget",
            target_id=memory_id,
            namespace_key=namespace.key,
            outcome="deleted",
            reason=reason,
            at=deleted_at,
            content=receipt.content_digest,
        )
        return receipt

    def recall(self, query: RecallQuery) -> tuple[RecallHit, ...]:
        hits = self.recaller.search(query)
        self._trace(
            operation="recall",
            target_id="query-" + stable_digest(query.query)[:12],
            namespace_key=query.namespace.key,
            outcome="selected",
            reason=f"hit_count:{len(hits)}",
            at=query.now,
            content="|".join(hit.record.memory_id for hit in hits),
        )
        return hits

    def profile(self, namespace, *, now: str) -> dict[str, str]:
        records = (
            record
            for record in self.store.all_current(now=now)
            if record.namespace == namespace and record.memory_type is MemoryType.SEMANTIC
        )
        return {record.subject: record.content for record in sorted(records, key=lambda item: item.subject)}

    def audit_events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._audit)

    def _trace(
        self,
        *,
        operation: str,
        target_id: str,
        namespace_key: str,
        outcome: str,
        reason: str,
        at: str,
        content: str,
    ) -> None:
        digest = stable_digest(content)
        self._audit.append(
            AuditEvent(
                event_id="audit-" + stable_digest(
                    {
                        "sequence": len(self._audit) + 1,
                        "operation": operation,
                        "target_id": target_id,
                        "at": at,
                        "digest": digest,
                    }
                )[:16],
                operation=operation,
                target_id=target_id,
                namespace_key=namespace_key,
                outcome=outcome,
                reason=reason,
                at=at,
                content_digest=digest,
            )
        )

