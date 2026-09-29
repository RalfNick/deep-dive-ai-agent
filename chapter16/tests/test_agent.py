from dataclasses import replace
from chapter16.agent import run_agent
from chapter16.artifacts import make_artifact, make_snapshot
from chapter16.contracts import CLOCK

def run(task, lab, snapshot, policy, variant="scoped"):
    return run_agent(task.agent_input, lab.documents, snapshot, policy=policy, now=task.frozen_clock, variant=variant)

def test_assets_change_actual_behavior(lab, baseline, candidate, use_policy):
    tasks = {t.task_id:t for t in lab.tasks}
    assert run(tasks["K1"], lab, baseline, use_policy).document_id == "A-old"
    assert run(tasks["K1"], lab, candidate, use_policy).document_id == "A-current"
    assert len(run(tasks["P1"], lab, baseline, use_policy).steps) == 3
    assert len(run(tasks["P1"], lab, candidate, use_policy).steps) == 5
    assert run(tasks["S1"], lab, candidate, use_policy).answer_style == "concise"
    for name in ("S2", "S3", "S4"):
        assert run(tasks[name], lab, candidate, use_policy).answer_style == "normal"
    assert run(tasks["K3"], lab, candidate, use_policy).document_id == "A-old"
    assert run(tasks["K4"], lab, candidate, use_policy).document_id == "B-current"
    assert run(tasks["K3"], lab, candidate, use_policy, "blind_control").document_id != "A-old"

def test_conflict_does_not_use_list_order(lab, candidate, use_policy):
    a = next(a for a in candidate.artifacts if a.kind == "scoped_memory")
    conflict = make_artifact(replace(a, artifact_id="conflicting-memory", content={"answer_style":"normal"}))
    snapshots = [make_snapshot(candidate.artifacts + (conflict,)), make_snapshot((conflict,) + candidate.artifacts)]
    task = next(t for t in lab.tasks if t.task_id == "S1")
    for snapshot in snapshots:
        assert run(task, lab, snapshot, use_policy).unknown_reasons == ("artifact_conflict",)

def test_current_policy_blocks_step_and_source(lab, candidate, use_policy):
    task = next(t for t in lab.tasks if t.task_id == "P1")
    result = run(task, lab, candidate, replace(use_policy, allowed_steps=("export",)))
    assert result.refusal_reason == "step_denied" and not result.steps
    pref = next(t for t in lab.tasks if t.task_id == "S1")
    assert run(pref, lab, candidate, replace(use_policy, revoked_source_ids=frozenset({"F08"}))).answer_style == "normal"
