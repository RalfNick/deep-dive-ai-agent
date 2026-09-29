from dataclasses import replace
import pytest
from chapter16.feedback import admit_feedback
from chapter16.lessons import propose_lessons, export_training_candidates

def test_carriers_are_finite_and_traceable(lab):
    rows = propose_lessons(admit_feedback(lab.feedback, lab.sources), lab.replays, blocked_families=frozenset())
    assert {r.carrier for r in rows} == {"knowledge_rule", "step_skill", "scoped_memory", "prompt", "harness", "environment"}
    training = export_training_candidates(rows, blocked_families=frozenset())
    assert len(training) == 1 and training[0]["source_refs"] == ["F03"]
    assert "success_ref" not in training[0] and "truth" not in training[0]

def test_holdout_family_is_blocked_before_proposal_and_export(lab):
    admissions = admit_feedback(lab.feedback, lab.sources)
    with pytest.raises(ValueError, match="family"):
        propose_lessons(admissions, lab.replays, blocked_families=frozenset({"discover-export"}))
    rows = propose_lessons(admissions, lab.replays, blocked_families=frozenset())
    with pytest.raises(ValueError, match="family"):
        export_training_candidates(rows, blocked_families=frozenset({"discover-procedure"}))

def test_missing_replay_does_not_create_knowledge_asset(lab):
    rows = propose_lessons(admit_feedback(lab.feedback, lab.sources), (), blocked_families=frozenset())
    knowledge = next(r for r in rows if r.carrier == "knowledge_rule")
    assert knowledge.unknown_reasons == ("missing_replay",)
