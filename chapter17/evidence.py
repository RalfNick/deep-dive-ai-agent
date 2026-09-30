"""Versioned report checks independent of any model provider."""

from __future__ import annotations

from collections import Counter


def summarize(groups: list[dict]) -> dict:
    cases = [case for group in groups for case in group["cases"]]
    counts = Counter(case["status"] for case in cases)
    return {
        "cases_total": len(cases),
        "answers": counts["answer"],
        "unknown": counts["unknown"],
        "blocked": counts["blocked"],
        "refresh": counts["refresh"],
        "security_violations": sum(bool(case.get("security_violation")) for case in cases),
        "evidence_covered": sum(bool(case["evidence_ids"]) for case in cases),
        "evidence_total": len(cases),
    }


def validate_report(report: dict) -> None:
    if report.get("schema_version") != "chapter17.multimodal.v1":
        raise ValueError("report schema version mismatch")
    groups = report.get("groups")
    if not isinstance(groups, list) or [g.get("id") for g in groups] != [1, 2, 3, 4, 5]:
        raise ValueError("report needs five ordered groups")
    proofs = report.get("source_proof")
    if not isinstance(proofs, dict) or not proofs:
        raise ValueError("missing source proof")
    all_ids: set[str] = set()
    for group in groups:
        if not group.get("cases"):
            raise ValueError("empty group")
        for case in group["cases"]:
            case_id = case.get("id")
            if not case_id or case_id in all_ids:
                raise ValueError("duplicate or empty case id")
            all_ids.add(case_id)
            status = case.get("status")
            if status not in {"answer", "unknown", "blocked", "refresh"}:
                raise ValueError("invalid case status")
            refs = case.get("evidence_ids")
            if not isinstance(refs, list) or not refs or not set(refs) <= set(proofs):
                raise ValueError("case evidence is missing or unresolved")
            if status != "answer" and not case.get("reasons"):
                raise ValueError("non-answer needs explicit reason")
            if status == "answer" and not case.get("value"):
                raise ValueError("answer needs a value")
            if status != "answer" and case.get("value") is not None:
                raise ValueError("non-answer must not carry value")
    if report.get("summary") != summarize(groups):
        raise ValueError("report summary is not derived from cases")
    if not isinstance(report.get("limits"), list) or not report["limits"]:
        raise ValueError("missing experiment limits")
