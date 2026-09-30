from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_source_ledger_has_primary_sources_and_limits():
    text = (ROOT / "book/sources/chapter17-sources.md").read_text(encoding="utf-8")
    for token in ("2203.10244", "2504.05506", "2504.07981",
                  "images-vision", "realtime-conversations", "tools-computer-use",
                  "developers.openai.com/api/docs/guides/live", "platform.claude.com",
                  "2026-09-30", "不能支持的外推"):
        assert token in text
