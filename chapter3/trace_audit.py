"""Order-sensitive integrity checks for a recorded Agent run."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from agent_loop import RunResult


@dataclass(frozen=True)
class TraceAudit:
    duplicate_call_ids: tuple[str, ...]
    duplicate_result_ids: tuple[str, ...]
    missing_result_ids: tuple[str, ...]
    orphan_result_ids: tuple[str, ...]
    result_before_call_ids: tuple[str, ...]
    completion_contract_ok: bool

    @property
    def ok(self) -> bool:
        integrity_issues = (
            self.duplicate_call_ids,
            self.duplicate_result_ids,
            self.missing_result_ids,
            self.orphan_result_ids,
            self.result_before_call_ids,
        )
        return not any(integrity_issues) and self.completion_contract_ok


def _duplicates(values: list[str]) -> tuple[str, ...]:
    counts = Counter(values)
    return tuple(dict.fromkeys(value for value in values if counts[value] > 1))


def audit_trace(run: RunResult) -> TraceAudit:
    """Audit event counts, ordering, linkage, and the completion contract."""
    call_items = [
        (index, event.data["call_id"])
        for index, event in enumerate(run.events)
        if event.kind == "tool_call"
    ]
    result_items = [
        (index, event.data["call_id"])
        for index, event in enumerate(run.events)
        if event.kind == "tool_result"
    ]
    call_ids = [call_id for _, call_id in call_items]
    result_ids = [call_id for _, call_id in result_items]
    call_counts = Counter(call_ids)
    result_counts = Counter(result_ids)

    missing_result_ids = tuple(
        dict.fromkeys(
            call_id
            for call_id in call_ids
            if result_counts[call_id] < call_counts[call_id]
        )
    )
    orphan_result_ids = tuple(
        dict.fromkeys(
            call_id
            for call_id in result_ids
            if result_counts[call_id] > call_counts[call_id]
        )
    )
    first_call_index = {}
    for index, call_id in call_items:
        first_call_index.setdefault(call_id, index)
    result_before_call_ids = tuple(
        dict.fromkeys(
            call_id
            for index, call_id in result_items
            if call_id in first_call_index and index < first_call_index[call_id]
        )
    )

    completion_contract_ok = True
    if run.status == "completed":
        accepted_verifications = [
            (index, event)
            for index, event in enumerate(run.events)
            if event.kind == "verification"
            and event.data.get("accepted") is True
            and event.data.get("rules") != ("verifier_not_configured",)
        ]
        completed_events = [
            (index, event)
            for index, event in enumerate(run.events)
            if event.kind == "run_finished"
            and event.data.get("status") == "completed"
        ]
        completion_contract_ok = bool(
            accepted_verifications
            and completed_events
            and accepted_verifications[-1][0] < completed_events[-1][0]
        )

    return TraceAudit(
        duplicate_call_ids=_duplicates(call_ids),
        duplicate_result_ids=_duplicates(result_ids),
        missing_result_ids=missing_result_ids,
        orphan_result_ids=orphan_result_ids,
        result_before_call_ids=result_before_call_ids,
        completion_contract_ok=completion_contract_ok,
    )
