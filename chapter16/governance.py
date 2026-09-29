"""In-process trusted rehearsal authority, NOT signatures or production IAM."""
import hashlib
from dataclasses import replace
from .artifacts import validate_snapshot
from .contracts import ApprovalReceipt, ReleaseRecord, ReleaseState, Scope, utc
from .evaluation import decide_gate
from .serialization import body_hash, canonical_bytes, digest

TRUSTED_SCOPES = (Scope("A",None,"export","current"), Scope("A",None,"procedure","current"),
                  Scope("A","user-A","export","current"))
_issued = {}  # trusted local issuance registry; deliberately not durable cross-process auth.


def stopped_revisions(state):
    stopped = set()
    for record in state.history:
        if record.event == "stop" or (record.event == "rollback"
                                      and record.from_revision.snapshot_hash != record.to_revision.snapshot_hash):
            stopped.add(record.from_revision.snapshot_hash)
        elif record.event == "activate":
            stopped.discard(record.to_revision.snapshot_hash)
    return stopped

def make_approval(candidate, evidence, *, approver_id, allowed_scopes, now, valid_until):
    validate_snapshot(candidate)
    if approver_id != "reviewer-local" or not allowed_scopes or len(set(allowed_scopes)) != len(allowed_scopes):
        raise ValueError("untrusted approver or duplicate/empty scopes")
    if set(allowed_scopes) != {a.scope for a in candidate.artifacts} or not set(allowed_scopes).issubset(TRUSTED_SCOPES):
        raise ValueError("approval scope mismatch")
    if (evidence.candidate_hash != candidate.snapshot_hash or decide_gate(evidence).status != "pass"
        or not utc(evidence.context.frozen_clock) <= utc(now) < utc(valid_until) <= utc(evidence.context.valid_until)):
        raise ValueError("approval lacks passing current evidence")
    approval = ApprovalReceipt("pending", approver_id, candidate.snapshot_hash, evidence.evidence_hash,
                               digest(evidence.context), allowed_scopes, now, valid_until, "approved")
    approval = replace(approval, approval_id=body_hash(approval, "approval_id"))
    _issued[approval.approval_id] = canonical_bytes(approval)
    return approval

def activate(state, candidate, evidence, approval, context, *, now):
    validate_snapshot(candidate)
    if (not isinstance(approval, ApprovalReceipt) or _issued.get(approval.approval_id) != canonical_bytes(approval)
        or approval.approver_id != "reviewer-local" or approval.decision != "approved"
        or approval.candidate_hash != candidate.snapshot_hash or approval.evidence_hash != evidence.evidence_hash
        or approval.context_hash != digest(context) or digest(context) != digest(evidence.context)
        or evidence.candidate_hash != candidate.snapshot_hash or decide_gate(evidence).status != "pass"
        or not utc(approval.issued_at) <= utc(now) < min(utc(approval.valid_until), utc(context.valid_until))
        or any(not utc(a.valid_from) <= utc(now) < utc(a.valid_until) for a in candidate.artifacts)):
        raise ValueError("activation binding/authority/expiry rejected")
    if approval.approval_id in state.used_approvals:
        if (state.active.snapshot_hash == candidate.snapshot_hash
                and candidate.snapshot_hash not in stopped_revisions(state)):
            return state
        raise ValueError("used approval cannot reactivate a stopped revision or after rollback")
    if any(r.event == "activate" and r.evidence_ref == evidence.evidence_hash for r in state.history):
        if (state.active.snapshot_hash == candidate.snapshot_hash
                and candidate.snapshot_hash not in stopped_revisions(state)):
            return state
        raise ValueError("evidence already activated; fresh independent validation required")
    if state.history and utc(now) < utc(state.history[-1].frozen_clock):
        raise ValueError("activation clock predates release history")
    if state.active.snapshot_hash != evidence.baseline_hash or candidate.parent_revision_id != state.active.revision_id:
        raise ValueError("baseline pointer changed")
    row = ReleaseRecord("pending", "activate", state.active, candidate, approval.approval_id,
                        evidence.evidence_hash, {}, "approved_local_rehearsal", now)
    row = replace(row, record_id=body_hash(row, "record_id"))
    return ReleaseState(candidate, state.history + (row,), state.used_approvals | {approval.approval_id})

def assign_cohort(task_ids, *, seed=1601, candidate_count=4):
    if len(set(task_ids)) != len(task_ids) or type(candidate_count) is not int or not 0 <= candidate_count <= len(task_ids):
        raise ValueError("invalid cohort IDs/count")
    if type(seed) is not int or any(type(i) is not str or not i for i in task_ids):
        raise ValueError("invalid cohort seed/ID")
    ordered = sorted(task_ids, key=lambda i:(hashlib.sha256(f"{seed}:{i}".encode()).hexdigest(), i))
    chosen = set(ordered[:candidate_count])
    return {i:"candidate" if i in chosen else "baseline" for i in sorted(task_ids)}

def rollback(state, target, *, reason, now):
    validate_snapshot(target)
    clock = utc(now)
    if state.history and clock < utc(state.history[-1].frozen_clock):
        raise ValueError("rollback clock predates release history")
    known = {state.active.snapshot_hash} | {s.snapshot_hash for r in state.history for s in (r.from_revision,r.to_revision)}
    if target.snapshot_hash not in known or not reason:
        raise ValueError("unknown rollback target or missing reason")
    # Knowing a snapshot is not permission to restore a stopped version. Only a
    # subsequent activate() with fresh bound evidence can clear that version.
    if target.snapshot_hash in stopped_revisions(state):
        raise ValueError("stopped rollback target requires fresh independent validation and activation")
    if target.snapshot_hash == state.active.snapshot_hash:
        return state
    row = ReleaseRecord("pending", "rollback", state.active, target, None, None, {}, reason, now)
    row = replace(row, record_id=body_hash(row, "record_id"))
    return ReleaseState(target, state.history + (row,), state.used_approvals)
