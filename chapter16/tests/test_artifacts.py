from dataclasses import replace
import pytest
from chapter16.artifacts import matching_artifacts, validate_snapshot, make_snapshot, make_artifact
from chapter16.contracts import CLOCK

def test_three_assets_strict_lifetime_and_revocation(lab, candidate, use_policy):
    assert {a.kind for a in candidate.artifacts} == {"knowledge_rule", "step_skill", "scoped_memory"}
    task = next(t for t in lab.tasks if t.task_id == "S1")
    matches = matching_artifacts(candidate, task.agent_input, policy=use_policy, now=CLOCK)
    assert len(matches) == 2
    assert matching_artifacts(candidate, task.agent_input, policy=use_policy, now="2026-10-28T00:00:00Z") == ()
    assert len(matching_artifacts(candidate, task.agent_input,
               policy=replace(use_policy, revoked_source_ids=frozenset({"F08"})), now=CLOCK)) == 1

def test_hash_tampering_and_unsupported_activation_rejected(candidate):
    changed = replace(candidate.artifacts[0], content={"selection":"all_tenants"})
    with pytest.raises(ValueError):
        validate_snapshot(replace(candidate, artifacts=(changed, *candidate.artifacts[1:])))
    with pytest.raises(ValueError):
        make_snapshot((make_artifact(replace(candidate.artifacts[0], kind="prompt")),))
