"""A finite teaching policy: decisions do not depend on task IDs or gold."""
from .artifacts import conflicts, matching_artifacts, validate_snapshot
from .contracts import RunResult, utc

def run_agent(request, documents, snapshot, *, policy, now, variant="scoped"):
    if variant not in ("scoped", "baseline", "blind_control"):
        raise ValueError("unknown agent variant")
    validate_snapshot(snapshot)
    def result(doc=None, steps=(), style="normal", refusal=None, applied=(), violations=(), env=None, unknown=()):
        return RunResult(doc, steps, style, refusal, applied, violations, env, unknown, len(steps)+1, len(steps))
    if request.operation == "refuse":
        return result(refusal="policy_denied")
    if "missing_receipt" in request.tool_receipts or not request.tool_receipts:
        return result(unknown=("tool_receipt",))
    if "timeout" in request.tool_receipts or ("temporary_error" in request.tool_receipts and "recovered" not in request.tool_receipts):
        return result(env="tool_timeout")
    assets = () if variant == "baseline" else matching_artifacts(snapshot, request, policy=policy, now=now)
    if variant == "blind_control":
        assets = snapshot.artifacts  # deliberately wrong control, still never executes external tools.
    if conflicts(assets):
        return result(unknown=("artifact_conflict",))
    if request.operation == "preference":
        memories = [a for a in assets if a.kind == "scoped_memory"]
        return result(style=memories[0].content["answer_style"] if memories else "normal",
                      applied=tuple(a.content_hash for a in memories))
    docs = [d for d in documents if d.tenant_id == request.tenant_id and d.domain == request.domain
            and utc(d.valid_from) <= utc(now) < utc(d.valid_until)]
    if request.requested_version == "historical":
        docs = [d for d in docs if d.version == "historical"]
    applied = []
    rules = [a for a in assets if a.kind == "knowledge_rule"]
    if rules:
        doc_id = rules[0].content["document_id"]
        if variant == "blind_control":
            docs = [d for d in documents if d.document_id == doc_id]
        else:
            docs = [d for d in docs if d.document_id == doc_id and d.version == request.requested_version]
        applied.append(rules[0].content_hash)
    if not docs:
        return result(unknown=("no_authorized_document",))
    doc = docs[0]
    steps = doc.steps if request.operation == "export" else ()
    if request.operation == "export" and request.tenant_id == "A" and request.requested_version == "current":
        steps = tuple(s for s in steps if s not in ("choose_destination", "verify_receipt"))
    skills = [a for a in assets if a.kind == "step_skill"]
    if skills and request.operation == "export":
        steps = tuple(skills[0].content["steps"])
        applied.append(skills[0].content_hash)
    if not set(steps).issubset(policy.allowed_steps):
        return result(refusal="step_denied")
    violations = ("tenant_boundary",) if doc.tenant_id != request.tenant_id else ()
    return result(doc.document_id, steps, applied=tuple(applied), violations=violations)
