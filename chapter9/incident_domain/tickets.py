from __future__ import annotations

from collections.abc import Callable

from chapter9.tool_runtime.contracts import DomainError


class TicketStore:
    def __init__(self, *, clock: Callable[[], str]) -> None:
        self._clock = clock
        self._tickets: list[dict[str, object]] = []

    def create(
        self, *, title: str, severity: str, evidence_ids: tuple[str, ...]
    ) -> dict[str, object]:
        if not title.strip():
            raise DomainError("invalid_title", "ticket title must be non-blank")
        if severity not in {"P1", "P2", "P3"}:
            raise DomainError("invalid_severity", f"unsupported severity: {severity}")
        if not evidence_ids or any(not evidence_id.strip() for evidence_id in evidence_ids):
            raise DomainError(
                "missing_evidence", "at least one non-blank evidence id is required"
            )

        ticket_id = f"INC-{len(self._tickets) + 1:04d}"
        record: dict[str, object] = {
            "ticket_id": ticket_id,
            "title": title,
            "severity": severity,
            "evidence_ids": list(evidence_ids),
            "created_at": self._clock(),
        }
        self._tickets.append(record)
        return dict(record)

    def all(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(ticket) for ticket in self._tickets)

