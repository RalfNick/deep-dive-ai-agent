from __future__ import annotations

import json
from pathlib import Path

import pytest

from chapter12 import exercise_solutions
from chapter12.contracts import TOOL_SCHEMAS


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "chapter12" / "reports" / "exercise-results.json"


@pytest.fixture(scope="module")
def answers():
    return {number: exercise_solutions.solve(number) for number in range(1, 15)}


def test_all_fourteen_answers_have_evidence_and_criteria(answers):
    assert set(answers) == set(range(1, 15))
    for number, answer in answers.items():
        assert answer["number"] == number
        assert answer["title"]
        assert answer["criteria"] and all(isinstance(item, str) and item for item in answer["criteria"])
        assert isinstance(answer["evidence"], dict) and answer["evidence"]
        assert answer["status"] in {"passed", "answered", "verified", "unverified"}


def test_at_least_seven_answers_execute_real_chapter_mechanisms(answers):
    real = [answer for answer in answers.values() if answer["execution"] == "real"]
    assert len(real) >= 7
    assert answers[1]["evidence"]["workspace_unchanged"] is True
    assert answers[2]["evidence"]["first_failure"]["error"] == "tests_failed"
    assert answers[4]["evidence"]["error"] == "non_unique_match"
    assert answers[5]["evidence"]["error"] == "stale_version"
    assert answers[6]["evidence"]["error"] == "approval_mismatch"
    assert answers[7]["evidence"]["states"] == {
        "before": "recheck_approval", "after": "record_receipt", "other": "uncertain"
    }
    assert answers[9]["evidence"]["accepted"] is False
    assert answers[9]["evidence"]["reason"] == "candidate_tests_failed"


def test_readonly_extension_does_not_change_the_chapter_tool_contract(answers):
    assert set(TOOL_SCHEMAS) == {"read_file", "search", "apply_patch", "run_tests", "show_diff"}
    assert answers[3]["evidence"]["contract_tools"] == sorted(TOOL_SCHEMAS)
    assert answers[3]["evidence"]["matches"]
    assert all(path.endswith(".py") for path in answers[3]["evidence"]["matches"])


def test_context_answer_keeps_tool_call_and_result_as_a_complete_pair(answers):
    assert answers[8]["evidence"]["assistant_call_ids"] == ["failed-tests"]
    assert answers[8]["evidence"]["tool_result_ids"] == ["failed-tests"]
    assert answers[8]["evidence"]["compacted"] is True


def test_budget_answer_is_computable():
    answer = exercise_solutions.solve(10)
    assert answer["input"] == {
        "total_seconds": 120,
        "elapsed_seconds": 35,
        "single_call_cap": 45,
    }
    assert answer["remaining_seconds"] == 85
    assert answer["next_timeout_seconds"] == 45
    assert exercise_solutions.budget_answer(30, 50, 45) == {
        "remaining_seconds": 0,
        "next_timeout_seconds": 0,
    }


def test_environment_probe_is_never_reported_as_verified_without_all_probes(answers):
    probe = answers[11]["evidence"]["environment_probe"]
    assert answers[11]["status"] == ("verified" if probe["isolation_passed"] else "unverified")
    assert answers[11]["evidence"]["mechanism_checks"]


def test_real_framework_exercises_cover_reentry_and_final_output_boundary(answers):
    graph = answers[12]["evidence"]
    assert graph["orchestration"] == "langgraph"
    assert graph["status"] == "completed"
    assert graph["writes"] == 2 and graph["receipts"] == 2
    assert graph["distinct_processes"] >= 3

    sdk = answers[13]["evidence"]
    assert sdk["orchestration"] == "agents_sdk"
    assert sdk["status"] != "completed"
    assert sdk["writes"] == 0
    assert sdk["verification_failures"] >= 1


def test_responsibility_design_names_all_four_layers(answers):
    assert set(answers[14]["evidence"]["responsibilities"]) == {
        "handwritten_loop", "pi_source", "framework", "host_application"
    }


def test_unknown_exercise_is_explicit():
    with pytest.raises(ValueError, match="unknown_exercise"):
        exercise_solutions.solve(0)
    with pytest.raises(ValueError, match="unknown_exercise"):
        exercise_solutions.solve(True)


def test_all_cli_surfaces_unverified_environment(monkeypatch, capsys):
    def fake_solve(number):
        return {
            "number": number,
            "title": f"exercise {number}",
            "criteria": ["checked"],
            "evidence": {"number": number},
            "execution": "real",
            "status": "unverified" if number == 11 else "passed",
        }

    monkeypatch.setattr(exercise_solutions, "solve", fake_solve)
    assert exercise_solutions.main(["--all"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert len(payload["answers"]) == 14
    assert payload["summary"]["unverified"] == [11]


def test_cli_can_write_one_non_overwriting_evidence_record(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(exercise_solutions, "solve", lambda number: {
        "number": number,
        "title": f"exercise {number}",
        "criteria": ["checked"],
        "evidence": {"number": number},
        "execution": "real",
        "status": "passed",
    })
    output = tmp_path / "exercise-results.json"
    assert exercise_solutions.main(["--all", "--output", str(output)]) == 0
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == 1
    original = output.read_bytes()
    assert exercise_solutions.main(["--all", "--output", str(output)]) == 3
    assert output.read_bytes() == original
    assert "output_exists" in capsys.readouterr().err


def test_committed_exercise_record_is_explicit_and_portable():
    text = REPORT.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert payload["schema_version"] == 1
    assert payload["summary"] == {
        "all_mechanisms_passed": False,
        "count": 14,
        "unverified": [11],
    }
    assert [answer["number"] for answer in payload["answers"]] == list(range(1, 15))
    assert not any(token in text for token in ("AppData", "\\Temp\\", "sk-", "Bearer "))
