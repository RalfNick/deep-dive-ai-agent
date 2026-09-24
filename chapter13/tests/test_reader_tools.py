from __future__ import annotations

import json
from pathlib import Path

from chapter13.exercise_solutions import main as solutions_main, solve
from chapter13.preview import build_preview


def test_all_fourteen_reference_solutions_are_machine_checkable():
    answers = [solve(number) for number in range(1, 15)]
    assert [item["number"] for item in answers] == list(range(1, 15))
    assert all(item["status"] in {"passed", "answered"} for item in answers)
    assert solve(3)["evidence"] == {
        "n": 5,
        "c": 2,
        "k": 3,
        "pass_1": 0.4,
        "pass_at_3": 0.9,
        "pass_all_3": 0.0,
    }
    assert solve(8)["evidence"]["release"]["decision"] == "fail"
    assert solve(7)["evidence"]["trial_modified"] is True
    assert solve(7)["evidence"]["safety"] == "fail"
    assert solve(11)["evidence"]["agreement_unchanged"] is True
    assert solve(11)["evidence"]["confusion_changed"] is True


def test_solution_cli_writes_new_json_and_refuses_overwrite(tmp_path, capsys):
    output = tmp_path / "answers.json"
    assert solutions_main(["--all", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "chapter13.exercises.v1"
    assert payload["summary"] == {"count": 14, "all_passed": True}
    assert solutions_main(["--all", "--output", str(output)]) == 3
    assert "output_exists" in capsys.readouterr().err


def test_preview_contains_seven_figures_scrollable_tables_and_local_title(tmp_path):
    root = Path(__file__).resolve().parents[2]
    output = build_preview(root, output=tmp_path / "index.html")
    html = output.read_text(encoding="utf-8")
    assert "第 13 章 · Agent 评估" in html
    assert html.count("<figure>") == 7
    assert 'class="table-wrap"' in html
    assert "../../book/images/chapter13/" in html
    assert "chapter12" not in html
