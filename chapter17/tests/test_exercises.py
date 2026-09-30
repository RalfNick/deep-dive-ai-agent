import json
from hashlib import sha256
from pathlib import Path

import pytest

from chapter17.exercise_solutions import payload, main
from chapter17.experiments import run_all
from chapter17.output import write_bundle


def test_13_answers_have_computed_examples():
    answers = payload()["answers"]
    assert [answer["number"] for answer in answers] == list(range(1, 14))
    assert answers[1]["computed"]["relative_growth_percent"] == "25"
    assert answers[2]["computed"]["truncated_visual_growth_percent"] == "200"
    assert answers[5]["computed"]["nonuniform_display_xy"] == [600, 450]
    assert answers[9]["computed"]["backend_task"] == "running"
    assert all(answer["criterion"] for answer in answers)


def test_answer_output_is_stable_and_refuses_overwrite(tmp_path):
    dest = tmp_path / "chapter17" / ".runs" / "answers.json"
    assert main(["--all", "--output", str(dest)], root=tmp_path) == 0
    assert dest.read_bytes() == dest.read_bytes()
    assert json.loads(dest.read_text(encoding="utf-8")) == payload()
    with pytest.raises(FileExistsError):
        main(["--all", "--output", str(dest)], root=tmp_path)


def test_all_bundle_includes_exercise_results(tmp_path):
    report = run_all()
    files = write_bundle(tmp_path, tmp_path / "chapter17/.runs/with-answers", report, payload())
    assert "exercise-results.json" in [file.name for file in files]
    data = json.loads(next(p for p in files if p.name == "exercise-results.json").read_text(encoding="utf-8"))
    assert len(data["answers"]) == 13
    manifest = json.loads(next(p for p in files if p.name == "manifest.json").read_text(encoding="utf-8"))
    for file in files:
        if file.name != "manifest.json":
            assert manifest["sha256"][file.name] == sha256(file.read_bytes()).hexdigest()


def test_all_cli_includes_answers(tmp_path, monkeypatch):
    from chapter17 import experiments
    monkeypatch.setattr(experiments, "__file__", str(tmp_path / "chapter17" / "experiments.py"))
    dest = tmp_path / "chapter17" / ".runs" / "cli"
    assert experiments.main(["--group", "all", "--output", str(dest)]) == 0
    assert len(json.loads((dest / "exercise-results.json").read_text(encoding="utf-8"))["answers"]) == 13
