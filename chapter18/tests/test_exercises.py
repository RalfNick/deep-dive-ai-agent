from chapter18.tests.helpers import fixture_repo


def test_thirteen_answers_include_independent_calculations_and_actual_evidence(tmp_path):
    from chapter18.exercise_solutions import solution_payload
    root = fixture_repo(tmp_path)
    payload = solution_payload(root=root, workdir=root / "chapter18/.runs/answers")
    answers = {a["exercise_id"]: a for a in payload["answers"]}
    assert len(answers) == 13
    assert answers[3]["computation"] == {"serial_units": 23, "parallel_units": 16, "break_even_overhead": 12}
    assert answers[9]["computation"] == {"total": 16, "workers": 14, "verifier": 2}
    for number in (8, 10, 11, 12):
        assert answers[number]["kind"] == "code" and answers[number]["evidence_refs"]
    assert answers[12]["computation"]["tests_passed"] == 4
    assert answers[10]["computation"]["committed_actions"] == 1
    assert {"身份", "数据", "动作隔离", "持久性", "预算", "回滚"} <= set(answers[13]["rubric"])


def test_two_answer_runs_are_byte_stable(tmp_path):
    import json
    from chapter18.exercise_solutions import solution_payload
    root = fixture_repo(tmp_path)
    a = solution_payload(root=root, workdir=root / "chapter18/.runs/answers-a")
    b = solution_payload(root=root, workdir=root / "chapter18/.runs/answers-b")
    assert json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)
