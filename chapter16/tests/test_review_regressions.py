"""Normal-path reproductions of the one whole-branch review's six findings."""
from dataclasses import replace
import json
from pathlib import Path
import re

import jsonschema
import pytest

from chapter16.artifacts import build_candidate, make_artifact, make_snapshot
from chapter16.contracts import CLOCK, END, ReleaseState, Scope
from chapter16.evaluation import decide_gate, evaluate_pair, make_context, seal_evidence
from chapter16.experiments import prepare, run_all, validate_report
from chapter16.feedback import admit_feedback
from chapter16.governance import activate, make_approval, rollback
from chapter16.lessons import propose_lessons
from chapter16.serialization import body_hash


def revised(candidate, kind, **changes):
    return make_snapshot(tuple(make_artifact(replace(a, **changes)) if a.kind == kind else a
                               for a in candidate.artifacts))


def approve(candidate, evidence, now=CLOCK):
    return make_approval(candidate, evidence, approver_id="reviewer-local",
                         allowed_scopes=tuple(a.scope for a in candidate.artifacts), now=now, valid_until=END)


@pytest.mark.parametrize("steps", [
    ("verify_receipt", "export", "choose_destination", "open_data", "open_project"),
    ("open_project", "open_data", "choose_destination", "export", "export", "verify_receipt"),
])
def test_bad_step_sequences_cannot_pass_or_activate(lab, baseline, candidate, evaluation_context, steps):
    bad = revised(candidate, "step_skill", content={"steps":steps})
    evidence = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, bad, evaluation_context)
    assert any(r["candidate_grade"]["status"] == "fail" for r in evidence.paired_trials)
    assert decide_gate(evidence).status == "fail"
    with pytest.raises(ValueError):
        approve(bad, evidence)


def faulted_replay(lab):
    return replace(lab, replays=tuple(replace(c, tool_tape=("timeout",)) if c.case_id == "F01" else c
                                      for c in lab.replays))


def test_environment_attribution_never_becomes_knowledge_asset(lab):
    changed = faulted_replay(lab)
    admissions, proposals, _, candidate, _, _, evidence = prepare(changed)
    proposal = next(p for p in proposals if p.source_refs == ("F01",))
    assert proposal.cause == "environment" and proposal.carrier == "environment"
    assert all(a.kind != "knowledge_rule" for a in candidate.artifacts)
    assert decide_gate(evidence).status != "pass"
    with pytest.raises(ValueError):
        build_candidate((replace(proposal, carrier="knowledge_rule"),), now=CLOCK)


def test_underlying_replay_change_invalidates_old_evidence(lab, baseline, candidate, use_policy):
    original = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, make_context(lab, use_policy))
    changed = faulted_replay(lab)
    newer = evaluate_pair(changed.tasks, changed.documents, changed.truth, baseline, candidate, make_context(changed, use_policy))
    assert newer.evidence_hash != original.evidence_hash
    assert decide_gate(newer).status == "inconclusive"
    proof = next(p for p in newer.asset_evidence if p.source_ref == "F01")
    assert proof.replay_result.status == "environment_error" and proof.status == "unknown"
    assert proof.replay_case.tool_tape == ("timeout",)
    assert proof.attribution.interventions[0]["frozen_hash"]
    with pytest.raises(ValueError):
        approve(candidate, newer)


@pytest.mark.parametrize("kind,changes", [
    ("knowledge_rule", {"source_refs":("F08",)}),
    ("knowledge_rule", {"source_refs":("F03",)}),
    ("scoped_memory", {"scope":Scope("A", None, "export", "current")}),
])
def test_each_asset_requires_compatible_authorized_source(lab, baseline, candidate, evaluation_context, kind, changes):
    bad = revised(candidate, kind, **changes)
    evidence = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, bad, evaluation_context)
    assert decide_gate(evidence).status == "fail"
    with pytest.raises(ValueError):
        approve(bad, evidence)


def test_narrower_source_scope_is_not_mistaken_for_unauthorized_widening(lab, baseline, candidate, evaluation_context):
    narrower = revised(candidate, "knowledge_rule", scope=Scope("A", "user-C", "export", "current"))
    evidence = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, narrower, evaluation_context)
    proof = next(p for p in evidence.asset_evidence if p.source_ref == "F01")
    assert proof.status == "pass"  # Overall repair may fail; source scope itself is legal.


def test_reissued_approval_cannot_reuse_stopped_evidence_but_new_validation_can(lab, baseline, candidate, use_policy):
    context = make_context(lab, use_policy)
    evidence = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, context)
    approval = approve(candidate, evidence)
    active = activate(ReleaseState(baseline, (), frozenset()), candidate, evidence, approval, context, now=CLOCK)
    assert activate(active, candidate, evidence, approval, context, now=CLOCK) is active
    back = rollback(active, baseline, reason="observed_fault", now="2026-09-28T00:01:00Z")
    reissued = approve(candidate, evidence, "2026-09-28T00:02:00Z")
    assert reissued.approval_id != approval.approval_id
    with pytest.raises(ValueError, match="evidence.*activated"):
        activate(back, candidate, evidence, reissued, context, now="2026-09-28T00:02:00Z")
    clock = "2026-09-28T00:03:00Z"
    fresh_lab = replace(lab, tasks=tuple(replace(t, frozen_clock=clock) if t.frozen_clock == CLOCK else t for t in lab.tasks))
    fresh_context = make_context(fresh_lab, use_policy, frozen_clock=clock)
    fresh_evidence = evaluate_pair(fresh_lab.tasks, fresh_lab.documents, fresh_lab.truth, baseline, candidate, fresh_context)
    assert fresh_evidence.evidence_hash != evidence.evidence_hash
    restored = activate(back, candidate, fresh_evidence, approve(candidate, fresh_evidence, clock), fresh_context, now=clock)
    assert [r.event for r in restored.history] == ["activate", "rollback", "activate"]


def test_all_exercise_difficulties_match_the_manuscript():
    from chapter16.exercise_solutions import solve
    text = (Path(__file__).parents[2] / "book/chapter16.md").read_text(encoding="utf-8")
    declared = {int(n):len(stars) for n, stars in re.findall(r"\*\*(\d+)\. (★+)", text)}
    assert declared == {n:solve(n)["difficulty"] for n in range(1, 14)}


@pytest.mark.parametrize("missing", ["all", "evidence_hash", "paired_trials", "coverage"])
def test_report_schema_and_runtime_reject_missing_nested_evidence(lab, missing):
    report = run_all(lab)
    groups = [dict(g) for g in report.to_dict()["groups"]]
    if missing == "all":
        groups[3]["evidence"] = {}
    else:
        del groups[3]["evidence"][missing]
    invalid = replace(report, groups=tuple(groups), report_hash="pending")
    invalid = replace(invalid, report_hash=body_hash(invalid, "report_hash"))
    schema = json.loads((Path(__file__).parents[1] / "schemas/improvement-report-v1.schema.json").read_text(encoding="utf-8"))
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid.to_dict(), schema)
    with pytest.raises(ValueError):
        validate_report(invalid)


def test_gate_does_not_accept_rehashed_missing_trials(lab, baseline, candidate, evaluation_context):
    evidence = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, evaluation_context)
    incomplete = seal_evidence(replace(evidence, paired_trials=evidence.paired_trials[:-1]))
    assert decide_gate(incomplete).status == "inconclusive"
