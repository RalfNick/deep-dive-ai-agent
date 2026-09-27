from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "book" / "chapter15.md"
PART_II_MARKER = "<!-- CHAPTER15_PART_II_PENDING -->"


def _text() -> str:
    return BOOK.read_text(encoding="utf-8")


def test_part_i_has_reader_first_opening_and_exact_title() -> None:
    text = _text()

    assert text.startswith("# 第 15 章 Agent 的后训练：什么时候 Prompt 已经不够\n")
    assert "> **阅读提示**" in text
    assert "**全章的短答案是：" in text
    assert all(phrase in text for phrase in (
        "信息不足时直接猜测",
        "修改了不应修改的验收文件",
        "暂时错误后反复调用",
    ))


def test_part_i_draws_the_intervention_boundary_before_training() -> None:
    text = _text()

    assert "后训练不是失败后的默认答案" in text
    assert "| 干预 | 主要修改对象 |" in text
    assert all(term in text for term in (
        "Prompt / Skill",
        "RAG / Context",
        "Harness",
        "记忆",
        "模型路由",
    ))
    assert all(term in text for term in ("SFT", "偏好优化", "RL"))


def test_part_i_contains_first_two_diagrams_and_experiments() -> None:
    text = _text()

    assert "images/chapter15/01-intervention-tree.svg" in text
    assert "images/chapter15/02-trajectory-data-factory.svg" in text
    assert "实验 15-1" in text and "--group 1" in text
    assert "实验 15-2" in text and "--group 2" in text
    assert "chapter15/.runs/intervention" in text
    assert "chapter15/.runs/data-audit" in text


def test_part_i_uses_canonical_audit_numbers_and_rejects_unsafe_success() -> None:
    text = _text()

    assert "24 条" in text
    assert "12 条进入候选" in text
    assert "12 条被隔离" in text
    assert "5 条 train-only SFT 示例" in text
    assert "成功但不安全的轨迹必须拒绝进入训练集" in text
    assert all(term in text for term in (
        "hidden_answer_access",
        "protected_write",
        "cross_split_family_leakage",
        "exact_duplicate",
    ))


def test_part_i_links_claims_to_the_source_ledger() -> None:
    text = _text()

    assert "sources/chapter15-sources.md#local-post-training-report" in text
    assert "sources/chapter15-sources.md#benchmark-contamination" in text
    assert "sources/chapter15-sources.md#instructgpt" in text
    assert "real-training-guide.md" in text


@pytest.mark.skipif(
    BOOK.exists() and PART_II_MARKER in BOOK.read_text(encoding="utf-8"),
    reason="Part II is owned by Task 10",
)
def test_part_ii_completeness_after_pending_marker_is_removed() -> None:
    text = _text()

    assert PART_II_MARKER not in text
    assert all(f"images/chapter15/0{number}-" in text for number in range(3, 8))
    assert all(f"实验 15-{number}" in text for number in range(3, 6))
    assert "## 分层练习" in text
    assert "## 延伸阅读" in text
    assert "## 与下一章" in text
