from dataclasses import replace
import pytest
from chapter16.contracts import CLOCK, END, ReleaseState
from chapter16.evaluation import evaluate_pair, seal_evidence
from chapter16.governance import make_approval, activate, assign_cohort, rollback

def setup(lab, baseline, candidate, context):
    evidence = evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, context)
    scopes = tuple(a.scope for a in candidate.artifacts)
    approval = make_approval(candidate, evidence, approver_id="reviewer-local", allowed_scopes=scopes, now=CLOCK, valid_until=END)
    return evidence, approval, ReleaseState(baseline, (), frozenset())

def test_idempotent_activation_and_tamper_binding(lab, baseline, candidate, evaluation_context):
    e, a, state = setup(lab, baseline, candidate, evaluation_context)
    active = activate(state, candidate, e, a, evaluation_context, now=CLOCK)
    assert len(active.history) == 1
    assert activate(active, candidate, e, a, evaluation_context, now=CLOCK) is active
    modified = seal_evidence(replace(e, unrelated_unknown_count=0))
    for approval, evidence, context, now in ((None,e,evaluation_context,CLOCK),
       (a,modified,evaluation_context,CLOCK), (replace(a, approver_id="agent"),e,evaluation_context,CLOCK),
       (a,e,replace(evaluation_context, valid_until="2026-09-28T23:00:00Z"),CLOCK),
       (a,e,evaluation_context,END)):
        with pytest.raises(ValueError):
            activate(state, candidate, evidence, approval, context, now=now)

def test_scope_and_known_rollback(lab, baseline, candidate, evaluation_context):
    e, a, state = setup(lab, baseline, candidate, evaluation_context)
    scopes = tuple(x.scope for x in candidate.artifacts)
    with pytest.raises(ValueError):
        make_approval(candidate,e,approver_id="agent",allowed_scopes=scopes,now=CLOCK,valid_until=END)
    with pytest.raises(ValueError):
        make_approval(candidate,e,approver_id="reviewer-local",allowed_scopes=(scopes[0],),now=CLOCK,valid_until=END)
    active = activate(state,candidate,e,a,evaluation_context,now=CLOCK)
    back = rollback(active,baseline,reason="canary_expiry",now="2026-10-28T00:00:00Z")
    assert back.active == baseline and len(back.history) == 2
    from chapter16.artifacts import make_snapshot
    with pytest.raises(ValueError):
        rollback(back,make_snapshot((),revision_id="unknown"),reason="unknown",now=CLOCK)

def test_cohort_stable_and_no_duplicate_ids(lab):
    ids = tuple(t.task_id for t in lab.tasks)
    assigned = assign_cohort(ids)
    assert list(assigned.values()).count("candidate") == 4
    assert list(assigned.values()).count("baseline") == 12
    assert assigned == assign_cohort(tuple(reversed(ids)))
    with pytest.raises(ValueError):
        assign_cohort(("K1","K1"))
