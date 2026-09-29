from chapter16.replay import replay, attribute

def test_one_factor_interventions_and_missing_receipt(lab):
    cases = {c.case_id:c for c in lab.replays}
    assert replay(cases["F01"]).outcome.document_id == "A-old"
    assert replay(cases["F01"], selection="scoped_current").outcome.document_id == "A-current"
    assert replay(cases["F01"], procedure="complete").outcome.document_id == "A-old"
    assert len(replay(cases["F03"], procedure="complete").outcome.steps) == 5
    assert replay(cases["F04"]).status == "environment_error"
    assert replay(cases["F10"]).status == "unknown"
    assert "tool_receipt" in replay(cases["F10"]).missing
    assert attribute(cases["F01"]).cause == "knowledge_selection"
    assert attribute(cases["F03"]).cause == "procedure_incomplete"
    assert attribute(cases["F04"]).cause == "environment"
    for c in cases.values():
        intervention = attribute(c).interventions
        assert len({row["frozen_hash"] for row in intervention}) == 1
