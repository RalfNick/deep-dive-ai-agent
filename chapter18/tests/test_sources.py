from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_primary_sources_are_dated_and_not_local_measurements():
    text = (ROOT / "book/sources/chapter18-sources.md").read_text(encoding="utf-8")
    for source in ("anthropic.com/engineering/multi-agent-research-system", "openai.github.io/openai-agents-python/multi_agent/",
                   "docs.langchain.com/oss/python/langchain/multi-agent", "code.claude.com/docs/en/sub-agents",
                   "learn.chatgpt.com/docs/agent-configuration/subagents", "arxiv.org/abs/2512.08296v3"):
        assert source in text
    assert text.count("2026-10-01") >= 6
    assert "本地证据" in text and "不能支持" in text
    assert "2026-04-08" in text
