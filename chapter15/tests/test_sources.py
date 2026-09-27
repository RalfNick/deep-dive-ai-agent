from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "book" / "sources" / "chapter15-sources.md"
GUIDE = ROOT / "chapter15" / "real-training-guide.md"
VERIFIED_DATE = "2026-09-27"


def _entries(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^### ([a-z0-9][a-z0-9-]*)\s*$", text, flags=re.MULTILINE))
    return {
        match.group(1): text[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        for index, match in enumerate(matches)
    }


def test_source_ledger_has_required_primary_source_families() -> None:
    entries = _entries(LEDGER.read_text(encoding="utf-8"))
    required = {
        "instructgpt",
        "dpo-paper",
        "constitutional-ai",
        "openai-fine-tuning",
        "openai-graders",
        "openai-rft",
        "hf-transformers-chat-templates",
        "hf-datasets",
        "hf-trl-sft",
        "hf-trl-dpo",
        "hf-trl-grpo",
        "agent-lightning",
        "reward-tampering",
        "benchmark-contamination",
    }

    assert required <= set(entries)


def test_every_entry_has_complete_claim_and_expiry_metadata() -> None:
    entries = _entries(LEDGER.read_text(encoding="utf-8"))

    assert len(entries) >= 14
    for entry_id, body in entries.items():
        assert "- 标题：" in body, entry_id
        assert re.search(r"- URL：https://\S+", body), entry_id
        assert re.search(r"- 类型：(论文原文|官方文档|官方仓库|本地实验)", body), entry_id
        assert f"- 核对日期：{VERIFIED_DATE}" in body, entry_id
        assert "- 用于：" in body, entry_id
        assert "- 不用于/过期边界：" in body, entry_id


def test_product_behavior_is_supported_only_by_official_domains() -> None:
    entries = _entries(LEDGER.read_text(encoding="utf-8"))
    product_entries = {
        key: body
        for key, body in entries.items()
        if key.startswith("openai-") or key.startswith("hf-")
    }

    assert product_entries
    for entry_id, body in product_entries.items():
        url = re.search(r"- URL：(https://\S+)", body).group(1)
        if entry_id.startswith("openai-"):
            assert "openai.com/" in url, entry_id
        else:
            assert "huggingface.co/" in url or "github.com/huggingface/" in url, entry_id
        assert "- 类型：官方" in body, entry_id


def test_ledger_distinguishes_local_evidence_from_external_claims() -> None:
    text = LEDGER.read_text(encoding="utf-8")
    entries = _entries(text)

    assert "local-post-training-report" in entries
    assert "chapter15.post-training.v1" in entries["local-post-training-report"]
    assert "有限动作" in entries["local-post-training-report"]
    assert "不代表真实大模型训练" in entries["local-post-training-report"]
    assert "论文中的结果没有在本仓库复现" in text


def test_real_training_guide_marks_every_command_as_unexecuted_example() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    code_blocks = re.findall(r"```(?:bash|powershell|python|jsonl|json)\n(.*?)```", text, flags=re.DOTALL)

    assert code_blocks
    assert text.count("示例，未在本项目执行") >= len(code_blocks)
    assert "本章运行时不依赖 Transformers、Datasets 或 TRL" in text
    assert "不会读取 API Key" in text


def test_real_training_guide_covers_data_license_hardware_eval_and_rollback() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    required_phrases = (
        "Chat Template",
        "tool call",
        "SFT",
        "DPO",
        "GRPO",
        "许可",
        "隐私",
        "显存",
        "冻结评测集",
        "安全硬门禁",
        "回滚",
        "Provider 文档",
    )

    assert all(phrase in text for phrase in required_phrases)
