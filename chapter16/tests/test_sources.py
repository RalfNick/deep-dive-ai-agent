from pathlib import Path

def test_primary_source_ledger_versions_and_limits():
    text = (Path(__file__).parents[2]/"book/sources/chapter16-sources.md").read_text(encoding="utf-8")
    for fragment in ("2026-09-29","2303.11366v4","2303.17651v2","2507.19457v2",
                     "harness-engineering","skill-creator","april-23-postmortem","langgraph/add-memory",
                     "langgraph/interrupts","不支持","本地实现"):
        assert fragment in text
