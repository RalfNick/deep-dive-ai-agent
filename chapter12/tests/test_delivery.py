from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[2]
VERSION = ROOT / "book" / "versions" / "chapter12-v1.0.md"


def _project_file(path: Path) -> Path:
    if not path.is_file():
        pytest.skip("project-level delivery metadata is not present in this package copy")
    return path


def test_public_manifest_exposes_chapter12_release():
    current = _project_file(ROOT / "book" / "manifest.json").read_bytes()
    manifest = json.loads(current)
    chapter = next(
        chapter
        for section in manifest["sections"]
        for chapter in section["chapters"]
        if chapter["order"] == 12
    )
    assert chapter["status"] == "published"
    assert chapter["source"] == "chapter12.md"
    assert chapter["experiment"] == "../chapter12/README.md"
    assert chapter["answers"] == "../chapter12/reference-answers.md"

def test_release_record_and_agent_status_are_explicit():
    record = _project_file(VERSION).read_text(encoding="utf-8")
    agents = _project_file(ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for phrase in (
        "v1.0",
        "正式发布",
        "真实模型运行：未执行",
        "容器隔离：未验证",
        "210 passed",
    ):
        assert phrase in record
    assert "第 1–18 章与附录 A" in agents
    manifest = json.loads((ROOT / "book/manifest.json").read_text(encoding="utf-8"))
    later = [chapter for section in manifest["sections"] for chapter in section["chapters"]
             if 15 <= chapter["order"] <= 18]
    assert {chapter["order"] for chapter in later} == {15, 16, 17, 18}
    assert all(chapter["status"] == "published" and chapter["source"] == f"chapter{chapter['order']}.md"
               for chapter in later)
    assert any(entry["slug"] == "appendix-a" and entry["status"] == "published"
               for entry in manifest["appendices"])

    for name in ("offline-canonical.json", "framework-comparison.json",
                 "exercise-results.json"):
        report = _project_file(ROOT / "chapter12" / "reports" / name)
        digest = hashlib.sha256(report.read_bytes()).hexdigest().upper()
        assert f"`{name}`：`{digest}`" in record


def test_candidate_documents_do_not_contain_machine_paths_or_secret_shapes():
    paths = [
        ROOT / "book" / "chapter12.md",
        ROOT / "book" / "reviews" / "chapter12-review-codex-v1.0-rc1.md",
        ROOT / "book" / "sources" / "chapter12-sources.md",
        ROOT / "infographic" / "chapter12" / "prompts.md",
        VERSION,
    ]
    for path in paths:
        _project_file(path)
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    local_root_pattern = r"[A-Z]:\\(?:" + "|".join(("Users", "Codex-Projects")) + r")\\"
    assert not re.search(local_root_pattern, corpus)
    assert not re.search(r"\bsk-[A-Za-z0-9_-]{20,}\b", corpus)
