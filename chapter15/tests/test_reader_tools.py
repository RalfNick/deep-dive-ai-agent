from __future__ import annotations

import json
from pathlib import Path
import re

from chapter15.exercise_solutions import main as solutions_main, solve
from chapter15.preview import build_preview


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "chapter15" / "README.md"
MANUSCRIPT = ROOT / "book" / "chapter15.md"


def test_all_thirteen_exercises_have_machine_checkable_answers() -> None:
    answers = [solve(number) for number in range(1, 14)]

    assert [answer["number"] for answer in answers] == list(range(1, 14))
    assert all(answer["status"] in {"passed", "answered"} for answer in answers)
    assert solve(2)["evidence"]["always_train_incorrect_cases"] == 4
    assert solve(3)["evidence"]["eligible_count"] == 12
    assert solve(3)["evidence"]["sft_example_count"] == 5
    assert solve(5)["evidence"]["uniform_cross_entropy"] == 1.791759
    assert solve(7)["evidence"]["margin"] == 0.15
    assert solve(7)["evidence"]["loss"] == 0.620957
    assert solve(9)["evidence"]["scalar_penalty_score"] == 7.0
    assert solve(9)["evidence"]["hard_gate_safety_violations"] == 0


def test_solution_cli_is_stable_and_refuses_overwrite(tmp_path, capsys) -> None:
    first = tmp_path / "answers.json"
    second = tmp_path / "answers-second.json"

    assert solutions_main(["--all", "--output", str(first)]) == 0
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "chapter15.exercises.v1"
    assert payload["summary"] == {"count": 13, "all_passed": True}
    assert solutions_main(["--all", "--output", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    assert solutions_main(["--all", "--output", str(first)]) == 3
    assert "output_exists" in capsys.readouterr().err


def test_preview_contains_seven_figures_scrollable_tables_and_no_remote_runtime() -> None:
    output = ROOT / "chapter15" / "preview-pages" / "reader-test.html"
    try:
        built = build_preview(ROOT, output=output)
        html = built.read_text(encoding="utf-8")
        assert "第 15 章 · Agent 的后训练" in html
        assert html.count("<figure>") == 7
        assert html.count('class="table-wrap"') >= 4
        assert "../../book/images/chapter15/" in html
        assert 'class="figure-link"' in html
        assert 'class="mobile-figure-hint"' in html
        assert not re.search(r'<(?:script|link)[^>]+(?:src|href)="https?://', html)
    finally:
        output.unlink(missing_ok=True)


def test_preview_refuses_output_outside_repository(tmp_path) -> None:
    outside = tmp_path / "index.html"
    try:
        build_preview(ROOT, output=outside)
    except ValueError as exc:
        assert str(exc) == "output_outside_repository"
    else:
        raise AssertionError("outside preview path should be rejected")
    assert not outside.exists()


def test_readme_links_resolve_and_exposes_reader_contract() -> None:
    text = README.read_text(encoding="utf-8")

    for target in re.findall(r"\[[^\]]+\]\((?!https?://)([^)#]+)(?:#[^)]+)?\)", text):
        assert (README.parent / target).resolve().exists(), target
    for phrase in (
        "五组实验",
        "失败应该怎样读",
        "证据边界",
        "reference-answers.md",
        "real-training-guide.md",
        "chapter15-sources.md",
    ):
        assert phrase in text
    for number in range(1, 6):
        assert f"--group {number}" in text
    assert MANUSCRIPT.exists()
