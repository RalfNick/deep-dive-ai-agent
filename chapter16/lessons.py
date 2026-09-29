"""Author-written proposal rules; no gold lookup or automatic self-training."""
from .contracts import LessonProposal
from .replay import attribute, verifies_discovery_condition
from .serialization import plain

def propose_lessons(admissions, cases, *, blocked_families):
    index, proposals = {c.case_id:c for c in cases}, []
    for r in admissions:
        if r.disposition != "accepted":
            continue
        if r.family_id in blocked_families:
            raise ValueError("discovery family overlaps holdout")
        payload, unknown, cause = plain(r.sanitized_payload), (), "user_preference"
        if "selection" in payload:
            carrier = "knowledge_rule"
        elif "steps" in payload:
            carrier = "step_skill"
        elif "answer_style" in payload:
            carrier = "scoped_memory"
        elif "required_field" in payload:
            carrier, cause = "prompt", "structured_field_missing"
        elif "idempotency" in payload:
            carrier, cause = "harness", "retry_side_effect"
        else:
            carrier, cause = "environment", "environment"
        if carrier in ("knowledge_rule", "step_skill", "environment"):
            if r.feedback_id not in index:
                unknown = ("missing_replay",)
            else:
                case = index[r.feedback_id]
                if case.family_id != r.family_id or case.family_id in blocked_families or not r.scope.matches(case.input):
                    raise ValueError("replay source/family/scope binding mismatch")
                attr = attribute(case)
                cause, unknown = attr.cause, attr.unknown_reasons
                if cause == "environment":
                    carrier = "environment"  # A recovered tool is not a verified behavior repair.
                if cause == "unknown":
                    unknown = unknown or ("unresolved_cause",)
                elif carrier in ("knowledge_rule", "step_skill") and not verifies_discovery_condition(case, carrier, payload):
                    unknown = ("discovery_condition_not_verified",)
        proposals.append(LessonProposal("proposal-" + r.feedback_id, r.source_refs, r.purpose, r.family_id,
                         cause, carrier, r.scope, payload, r.evidence_refs, unknown))
    return tuple(proposals)

def export_training_candidates(proposals, *, blocked_families):
    if any(p.family_id in blocked_families for p in proposals):
        raise ValueError("training family overlaps holdout")
    return tuple({"source_refs":list(p.source_refs), "purpose":"training_candidate_only",
                  "family_id":p.family_id, "scope":p.scope.to_dict(), "steps":list(p.content["steps"]),
                  "evidence_refs":list(p.evidence_refs)} for p in proposals
                 if p.carrier == "step_skill" and not p.unknown_reasons and p.purpose == "discovery")
