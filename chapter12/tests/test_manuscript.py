from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "book" / "chapter12.md"
REVIEW = ROOT / "book" / "reviews" / "chapter12-review-codex-v1.0-rc1.md"


def text() -> str:
    return MANUSCRIPT.read_text(encoding="utf-8")


def test_manuscript_depth_and_exercises():
    manuscript = text()
    assert 20_000 <= len(re.findall(r"[\u4e00-\u9fff]", manuscript)) <= 30_000
    assert 30 <= len(re.findall(r"^#{2,3} ", manuscript, re.M)) <= 36
    assert len(re.findall(r"^\*\*练习 \d+", manuscript, re.M)) == 14


def test_manuscript_is_a_candidate_and_uses_only_observed_evidence():
    manuscript = text()
    assert "状态：v1.0-rc1 候选稿，未发布" in manuscript
    assert "真实模型运行：未执行" in manuscript
    assert "容器隔离：未验证" in manuscript
    assert "ReplayModel" in manuscript and "离线回放" in manuscript
    assert "183 passed, 1 skipped" in manuscript
    assert "B445B75D8FB4612AAEFBDEF3E8558F7A90D96442E986DB183685A798BB86E9C6" in manuscript
    assert "成功率" not in manuscript


def test_manuscript_has_reader_route_tables_experiments_and_real_paths():
    manuscript = text()
    assert manuscript.count("| ---") >= 3
    assert len(re.findall(r"^> \*\*实验 12-[1-5]", manuscript, re.M)) == 5
    for path in (
        "chapter12/contracts.py",
        "chapter12/tools.py",
        "chapter12/runtime.py",
        "chapter12/verifier.py",
        "chapter12/recovery.py",
        "chapter12/context.py",
        "chapter12/trace.py",
        "chapter12/adapters/langgraph_agent.py",
        "chapter12/adapters/sdk_agent.py",
        "chapter12/reference-answers.md",
    ):
        assert path in manuscript
    assert "python -B -m chapter12.experiments" in manuscript
    assert "python -B -m chapter12.exercise_solutions --all" in manuscript


def test_illustrations_are_markers_until_task_15_not_broken_links():
    manuscript = text()
    markers = re.findall(r"^> \[图 12-[1-7] 制作标记：.+\]$", manuscript, re.M)
    assert len(markers) == 7
    assert "book/images/chapter12/" not in manuscript


def test_review_contains_both_reader_and_engineering_findings():
    review = REVIEW.read_text(encoding="utf-8")
    assert "新读者视角" in review
    assert "工程视角" in review
    assert "已修改" in review
    assert "残留限制" in review
    assert "completion" in review
    assert "approval" in review
    assert "sandbox" in review
    assert "framework" in review
