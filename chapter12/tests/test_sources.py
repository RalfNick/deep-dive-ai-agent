from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "book" / "sources" / "chapter12-sources.md"
PI_STUDY = ROOT / "chapter12" / "pi-source-study.md"

FIELDS = {
    "id",
    "title",
    "official_url",
    "checked_at",
    "commit_or_version",
    "local_claim",
    "evidence_kind",
}
EVIDENCE_KINDS = {"source_reading", "installed_runtime", "official_docs", "experiment"}
SOURCE_BLOCK = re.compile(r"^### (?P<header>[A-Z0-9-]+)\n(?P<body>.*?)(?=^### |\Z)", re.M | re.S)
FIELD = re.compile(
    r"^- (?P<name>id|title|official_url|checked_at|commit_or_version|local_claim|evidence_kind): (?P<value>.+)$",
    re.M,
)


def parse_sources() -> dict[str, dict[str, str]]:
    text = LEDGER.read_text(encoding="utf-8")
    sources: dict[str, dict[str, str]] = {}
    for match in SOURCE_BLOCK.finditer(text):
        values = {item.group("name"): item.group("value").strip() for item in FIELD.finditer(match.group("body"))}
        assert set(values) == FIELDS, f"source {match.group('header')} has incomplete fields"
        source_id = values["id"].strip("`")
        assert source_id == match.group("header")
        assert source_id not in sources
        sources[source_id] = values
    return sources


def test_source_ledger_has_uniform_machine_checkable_records():
    sources = parse_sources()
    assert len(sources) >= 10
    assert {"PI-README", "PI-AGENT-CORE", "PI-AGENT-LOOP", "PI-SDK", "PI-CONTAINER"} <= set(sources)
    assert {"LANGGRAPH-INTERRUPTS", "LANGGRAPH-SQLITE", "OPENAI-AGENTS-HITL", "OPENAI-RUNSTATE"} <= set(sources)
    for source in sources.values():
        assert source["official_url"].startswith("https://")
        assert re.fullmatch(r"2026-\d{2}-\d{2}", source["checked_at"])
        assert source["local_claim"] not in {"", "-"}
        assert source["evidence_kind"] in EVIDENCE_KINDS


def test_pi_links_are_commit_pinned_and_cover_five_reading_points():
    text = PI_STUDY.read_text(encoding="utf-8")
    links = re.findall(r"https://github\.com/earendil-works/pi/blob/([^/]+)/([^\s)#]+)", text)
    assert len(links) >= 5
    assert all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision, _ in links)
    assert {revision for revision, _ in links} == {"19451accdeec671c1f4da9eafac8fc270f510ef4"}
    paths = {path for _, path in links}
    assert {
        "README.md",
        "packages/agent/README.md",
        "packages/agent/src/agent-loop.ts",
        "packages/coding-agent/docs/sdk.md",
        "packages/coding-agent/docs/containerization.md",
    } <= paths
    assert "/blob/main/" not in text
    assert "源码阅读，不是产品运行记录" in text


def test_pi_study_references_registered_sources_and_scope_limits():
    text = PI_STUDY.read_text(encoding="utf-8")
    sources = parse_sources()
    references = set(re.findall(r"\[([A-Z][A-Z0-9-]+)\]", text))
    assert {
        "PI-README",
        "PI-AGENT-CORE",
        "PI-AGENT-LOOP",
        "PI-SDK",
        "PI-CONTAINER",
    } <= references <= set(sources)
    assert "@earendil-works/pi-agent-core" in text
    assert "@earendil-works/pi-coding-agent" in text
    assert "0.86.1" in text
    assert "没有安装或运行 Pi" in text
    assert "不是 Python 依赖" in text
