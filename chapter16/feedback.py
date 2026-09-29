"""Deterministic admission; the registry, not payload, grants authority."""
from .contracts import AdmissionRecord, FeedbackRecord, SourceAuthority
from .serialization import canonical_bytes, plain

SENSITIVE_MARKER = "DEMO-SENSITIVE-001"
ATTACK_KEYS = {"disable_approval", "disable_verification", "copy_hidden_answers", "modify_tests"}

def within(child, parent):
    return (child.tenant_id == parent.tenant_id and child.domain == parent.domain
            and child.requested_version == parent.requested_version
            and (parent.user_id is None or parent.user_id == child.user_id))

def admit_feedback(records: tuple[FeedbackRecord, ...], sources: tuple[SourceAuthority, ...]) -> tuple[AdmissionRecord, ...]:
    registry = {s.source_id: s for s in sources}
    if len(registry) != len(sources) or len({r.feedback_id for r in records}) != len(records):
        raise ValueError("duplicate source/feedback ID")
    results, accepted = [], {}
    for r in records:
        raw = canonical_bytes(r.payload).decode("utf-8")
        sensitive = r.source_sensitive or SENSITIVE_MARKER in raw or r.payload.get("source_sensitive") is True
        payload = {"redacted":True} if sensitive else plain(r.payload)
        source = registry.get(r.source_id)
        status, reason, refs = "accepted", "admitted", (r.feedback_id,)
        if sensitive:
            status, reason = "quarantined", "source_sensitive"
        elif (source is None or source.role != r.source_role or source.revoked or not source.permission
              or not r.permission or not within(r.scope, source.scope) or r.purpose not in source.allowed_purposes):
            status, reason = "quarantined", "source_or_purpose_denied"
        elif ATTACK_KEYS & set(r.payload):
            status, reason = "quarantined", "feedback_injection"
        elif not r.complete or not r.evidence_refs:
            status, reason = "unknown", "missing_receipt"
        elif r.conflict_refs:
            status, reason = "unknown", "authority_conflict"
        elif r.duplicate_of:
            origin = accepted.get(r.duplicate_of)
            if (origin and origin.source_id == r.source_id and origin.scope == r.scope
                    and canonical_bytes(origin.sanitized_payload) == canonical_bytes(payload)):
                status, reason, refs = "merged", "same_origin", (origin.feedback_id, r.feedback_id)
            else:
                status, reason = "unknown", "duplicate_not_verified"
        row = AdmissionRecord(r.feedback_id, r.source_id, r.purpose, r.family_id, r.scope, r.run_ref,
                              status, (reason,), payload, sensitive, refs, r.evidence_refs)
        results.append(row)
        if status == "accepted":
            accepted[r.feedback_id] = row
    return tuple(results)
