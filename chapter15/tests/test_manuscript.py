from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "book" / "chapter15.md"
PART_II_MARKER = "<!-- CHAPTER15_PART_II_PENDING -->"


def _text() -> str:
    return BOOK.read_text(encoding="utf-8")


def test_part_i_has_reader_first_opening_and_exact_title() -> None:
    text = _text()

    assert text.startswith("# 第 15 章 Agent 的后训练：什么时候 Prompt 已经不够\n")
    assert "核心实验完全离线" in text
    assert "不需要 API Key、不下载模型，也不执行 GPU 训练" in text
    assert "后训练适合修正跨任务重复" in text
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


def test_part_ii_completeness_after_pending_marker_is_removed() -> None:
    text = _text()

    assert PART_II_MARKER not in text
    assert all(f"images/chapter15/0{number}-" in text for number in range(1, 8))
    assert all(f"实验 15-{number}" in text for number in range(3, 6))
    assert "## 分层练习" in text
    assert "## 延伸阅读" in text
    assert "## 与下一章“从失败中学习：持续改进系统”的衔接" in text


def test_part_ii_teaches_sft_dpo_and_rl_with_pinned_numbers() -> None:
    text = _text()

    assert all(heading in text for heading in (
        "### SFT：模仿被保留的动作",
        "### DPO：扩大同一状态下的相对间隔",
        "### RL：从环境反馈中学习，但不把奖励当真相",
    ))
    assert "0.15" in text and "0.620957" in text
    assert "+10" in text and "−3" in text and "+7" in text and "+6" in text
    assert "200 次" in text and "0 次安全违规" in text
    assert all(source in text for source in (
        "sources/chapter15-sources.md#dpo-paper",
        "sources/chapter15-sources.md#constitutional-ai",
        "sources/chapter15-sources.md#agent-lightning",
        "sources/chapter15-sources.md#reward-tampering",
    ))


def test_rl_mechanism_and_simulation_boundary_are_explicit() -> None:
    text = _text()

    assert all(term in text for term in (
        "探索与利用",
        "信用分配",
        "参考策略",
        "PPO",
        "GRPO",
        "单状态 bandit",
        "split 在夹具中预先标注",
    ))


def test_part_ii_has_five_experiment_commands_and_failure_samples() -> None:
    text = _text()

    for number in range(1, 6):
        assert f"实验 15-{number}" in text
        assert f"--group {number}" in text
    failure_codes = (
        "protected_write",
        "hidden_answer_access",
        "cross_split_family_leakage",
        "exact_duplicate",
        "missing_tool_result",
        "safety_veto",
        "slice_regression",
    )
    assert sum(code in text for code in failure_codes) >= 5
    assert text.count("**失败样本") >= 5


def test_manuscript_meets_density_and_exercise_contract() -> None:
    text = _text()
    headings = re.findall(r"^#{2,3} ", text, flags=re.MULTILINE)
    exercises = text.split("## 分层练习", 1)[1].split("\n## ", 1)[0]
    numbered_exercises = re.findall(r"^\d+\. \*\*", exercises, flags=re.MULTILINE)

    assert 22_000 <= len(text) <= 28_000
    assert 20 <= len(headings) <= 35
    assert 12 <= len(numbered_exercises) <= 14
    assert "## 本章证明了什么，又没有证明什么" in text
    assert "真实模型未训练" in text
    assert "不构成 Provider 兼容性认证" in text
