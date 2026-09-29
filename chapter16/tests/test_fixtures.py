from collections import Counter
from dataclasses import replace
import pytest
from chapter16.fixtures import validate_fixtures

def test_fixture_counts_and_split_contract(lab):
    assert (len(lab.feedback), len(lab.documents), len(lab.tasks)) == (12, 6, 16)
    dev = {t.family_id for t in lab.tasks if t.split == "development"}
    hold = {t.family_id for t in lab.tasks if t.split == "holdout"}
    assert dev.isdisjoint(hold)
    for label in ("knowledge", "procedure", "scope", "safety_recovery"):
        assert Counter(t.split for t in lab.tasks if t.slice == label) == {"development": 1, "holdout": 3}
    assert sum(t.target for t in lab.tasks) == 3
    assert {c.case_id for c in lab.replays} == {"F01", "F03", "F04", "F10"}

def test_decision_input_has_no_gold(lab):
    for task in lab.tasks:
        assert not {"task_id", "success_ref", "expected_document_id", "target", "split"} & task.agent_input.to_dict().keys()

def test_family_cannot_cross_purposes_even_with_new_id(lab):
    changed = replace(lab.tasks[1], task_id="new-wording", family_id=lab.tasks[0].family_id)
    with pytest.raises(ValueError, match="family"):
        validate_fixtures(replace(lab, tasks=(lab.tasks[0], changed, *lab.tasks[2:])))
