"""Fixture fact matching is not general natural-language entailment."""
from .contracts import Claim, EvidenceRef, EvidenceVerdict, SourceDoc, TaskPacket, ToolCall, ToolOutcome
from .context import eligible


def knowledge_tool(packet: TaskPacket, call: ToolCall, sources: tuple[SourceDoc, ...]) -> ToolOutcome:
    args = dict(call.arguments)
    doc = next((s for s in sources if s.source_id == args.get("source_id")), None)
    if call.tool not in packet.allowed_tools or doc is None or not eligible(packet, doc):
        return ToolOutcome(call.call_id, "denied", (("reason", "source_not_authorized_or_current"),))
    key = args.get("key", "")
    if key not in packet.input_refs:
        return ToolOutcome(call.call_id, "permanent_error", (("reason", "missing_context"),))
    value = dict(doc.facts).get(key)
    if value is None:
        return ToolOutcome(call.call_id, "permanent_error", (("reason", "fact_not_found"),))
    quote = next((line for line in doc.text.splitlines() if value in line and not line.startswith("#")), "")
    return ToolOutcome(call.call_id, "ok", (("source_id", doc.source_id), ("key", key), ("value", value),
        ("location", doc.location), ("digest", doc.digest), ("version", doc.version), ("eligible", doc.eligible), ("quote", quote)))


def claim_from_outcome(outcome: ToolOutcome) -> Claim:
    if outcome.status != "ok":
        raise ValueError("a successful source read is required")
    d = dict(outcome.data)
    ref = EvidenceRef(str(d["source_id"]), str(d["location"]), str(d["digest"]), str(d["version"]),
                      d["eligible"] is True, str(d["quote"]))
    return Claim(str(d["key"]), str(d["value"]), (ref,))


def check_claims(packet: TaskPacket, claims: tuple[Claim, ...], sources: tuple[SourceDoc, ...]) -> EvidenceVerdict:
    index = {s.source_id: s for s in sources}
    accepted: list[Claim] = []
    source_ids: set[str] = set()
    invalid = False
    for claim in claims:
        if not claim.evidence:
            invalid = True
            continue
        valid = True
        for ref in claim.evidence:
            doc = index.get(ref.source_id)
            if doc and (doc.source_id not in packet.allowed_sources or packet.principal not in doc.principals):
                return EvidenceVerdict("blocked", (), (), packet.output_requirements, "source_permission_denied")
            if (doc is None or not eligible(packet, doc) or ref.location != doc.location
                    or ref.digest != doc.digest or ref.version != doc.version or not ref.eligible
                    or not ref.quote.strip() or ref.quote not in doc.text
                    or not any(claim.value in line and not line.lstrip().startswith("#")
                               for line in ref.quote.splitlines())
                    or dict(doc.facts).get(claim.key) != claim.value):
                valid = False
        if valid:
            accepted.append(claim)
            source_ids.update(ref.source_id for ref in claim.evidence)
        else:
            invalid = True
    unique = tuple(sorted(set(accepted), key=lambda c: (c.key, c.value, tuple(e.source_id for e in c.evidence))))
    missing = tuple(key for key in packet.output_requirements if key not in {c.key for c in unique})
    conflicting = any(len({c.value for c in unique if c.key == key}) > 1 for key in {c.key for c in unique})
    if conflicting:
        status, reason = "conflict", "eligible_sources_disagree"
    elif missing or invalid:
        status, reason = "unknown", "missing_or_invalid_evidence"
    else:
        status, reason = "answer", "eligible_evidence_checked"
    return EvidenceVerdict(status, unique, tuple(sorted(source_ids)), missing, reason)
