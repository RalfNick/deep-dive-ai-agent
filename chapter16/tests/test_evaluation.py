from dataclasses import replace
import pytest
from chapter16.evaluation import evaluate_pair, decide_gate, seal_evidence, grade, make_context

def evidence(lab, baseline, candidate, context):
    return evaluate_pair(lab.tasks, lab.documents, lab.truth, baseline, candidate, context)

def test_complete_candidate_passes_frozen_gate(lab, baseline, candidate, evaluation_context):
    e = evidence(lab, baseline, candidate, evaluation_context)
    assert decide_gate(e).status == "pass"
    assert e.coverage["observed"] == 16 and e.coverage["holdout"] == 12
    assert sum(r["baseline_grade"]["status"] == "pass" for r in e.paired_trials) == 11
    assert all(r["candidate_grade"]["status"] == "pass" for r in e.paired_trials)
    assert e.unrelated_unknown_count == 2 and e.unknown_count == 0

def test_safety_precedes_unknown_and_missing_coverage(lab, baseline, candidate, evaluation_context):
    e = evidence(lab, baseline, candidate, evaluation_context)
    assert decide_gate(seal_evidence(replace(e, violation_count=1, unknown_count=1))).status == "fail"
    for changed in (replace(e, unknown_count=1), replace(e, environment_error_count=1),
                    replace(e, coverage={**e.coverage, "observed":15})):
        assert decide_gate(seal_evidence(changed)).status == "inconclusive"

def test_context_binds_suite_truth_documents_policy_and_clock(lab, baseline, candidate, evaluation_context):
    for change in ({"tasks":(replace(lab.tasks[0], frozen_clock="2026-09-28T01:00:00Z"), *lab.tasks[1:])},
                   {"truth":(replace(lab.truth[0], expected_document_id="A-old"), *lab.truth[1:])},
                   {"documents":(replace(lab.documents[0], answer="changed"), *lab.documents[1:])}):
        args = dict(tasks=lab.tasks, documents=lab.documents, truth=lab.truth, baseline=baseline, candidate=candidate, context=evaluation_context)
        args.update(change)
        with pytest.raises(ValueError, match="context"):
            evaluate_pair(**args)

def test_missing_targets_and_regression_are_not_averaged(lab, baseline, candidate, evaluation_context):
    e = evidence(lab, baseline, baseline, evaluation_context)
    assert decide_gate(e).status == "fail"
    good = evidence(lab, baseline, candidate, evaluation_context)
    rows = [dict(r) for r in good.paired_trials]
    rows[2]["candidate_grade"] = {"task_id":"K3", "status":"fail", "reason_codes":["wrong_history"], "evidence_refs":[]}
    assert decide_gate(seal_evidence(replace(good, paired_trials=tuple(rows)))).status == "fail"

def test_quarantined_candidate_source_cannot_promote(lab, baseline, candidate, evaluation_context):
    admissions = tuple(replace(a, disposition="quarantined") if a.feedback_id == "F01" else a for a in evaluation_context.admissions)
    context = replace(evaluation_context, admissions=admissions)
    assert decide_gate(evidence(lab, baseline, candidate, context)).status == "fail"
