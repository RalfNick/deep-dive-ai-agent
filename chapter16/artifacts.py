"""Immutable asset snapshots and current-time/current-policy filtering."""
from dataclasses import replace
from .contracts import ArtifactRevision, ArtifactSnapshot, utc
from .serialization import body_hash, canonical_bytes

KINDS = frozenset({"knowledge_rule", "step_skill", "scoped_memory"})

def make_artifact(artifact):
    return replace(artifact, content_hash=body_hash(artifact, "content_hash"))

def make_snapshot(artifacts=(), *, revision_id="candidate-v1", parent_revision_id="baseline-v1"):
    snapshot = ArtifactSnapshot(revision_id, parent_revision_id, tuple(artifacts), "pending")
    snapshot = replace(snapshot, snapshot_hash=body_hash(snapshot, "snapshot_hash"))
    validate_snapshot(snapshot)
    return snapshot

def empty_snapshot():
    return make_snapshot((), revision_id="baseline-v1", parent_revision_id=None)

def validate_snapshot(snapshot):
    if snapshot.snapshot_hash != body_hash(snapshot, "snapshot_hash"):
        raise ValueError("snapshot hash mismatch")
    ids = [a.artifact_id for a in snapshot.artifacts]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate artifact ID")
    for a in snapshot.artifacts:
        if a.kind not in KINDS or a.content_hash != body_hash(a, "content_hash"):
            raise ValueError("unsupported kind or content hash mismatch")
        keys = {"knowledge_rule":{"selection", "document_id"}, "step_skill":{"steps"}, "scoped_memory":{"answer_style"}}
        if set(a.content) != keys[a.kind] or not a.source_refs:
            raise ValueError("invalid artifact content/provenance")
        if a.kind == "knowledge_rule" and a.content["selection"] != "scoped_current":
            raise ValueError("unsupported selection rule")
        if a.kind == "step_skill" and (not a.content["steps"] or any(type(s) is not str for s in a.content["steps"])):
            raise ValueError("invalid step skill")
        if a.kind == "scoped_memory" and a.content["answer_style"] not in ("normal", "concise"):
            raise ValueError("invalid memory style")
    return snapshot

def build_candidate(proposals, *, now):
    utc(now)
    assets = []
    for p in proposals:
        if p.carrier not in KINDS:
            continue  # prompt/harness/environment are proposals, not runnable assets.
        if p.unknown_reasons or p.purpose != "discovery":
            raise ValueError("unresolved or non-discovery proposal")
        a = ArtifactRevision("asset-" + p.proposal_id, p.carrier, None, p.content, p.scope,
                             "atlas-maintainer", now, "2026-10-28T00:00:00Z", True, p.source_refs, "pending")
        assets.append(make_artifact(a))
    return make_snapshot(tuple(assets))

def matching_artifacts(snapshot, request, *, policy, now):
    validate_snapshot(snapshot)
    clock = utc(now)
    return tuple(a for a in snapshot.artifacts if a.permission and a.scope.matches(request)
                 and utc(a.valid_from) <= clock < utc(a.valid_until)
                 and a.content_hash not in policy.revoked_artifact_hashes
                 and not set(a.source_refs) & policy.revoked_source_ids)

def conflicts(assets):
    return any(len({canonical_bytes(a.content) for a in assets if a.kind == kind}) > 1 for kind in KINDS)
