"""Local RC, old-content preservation and publication-boundary contracts."""
import json
import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "2bcfaf0250fdd8dbf8b1f051bc62d576bef52875"


def test_local_candidate_has_truthful_version_record():
    record = (ROOT / "book/versions/chapter16-v1.0-rc1.md").read_text(encoding="utf-8")
    assert all(word in record for word in ("本地", "未发布", "已证明", "未证明", "SHA-256"))
    review = (ROOT / "book/reviews/chapter16-review-codex-v1.0-rc1.md").read_text(encoding="utf-8")
    assert "读者" in review and "专家" in review
    ledger = (ROOT / "book/versions/CHAPTER_VERSIONS.md").read_text(encoding="utf-8")
    assert "## 第 16 章" in ledger and "chapter16-v1.0-rc1.md" in ledger


def test_final_record_contains_actual_hashes_and_review_disposition():
    record = (ROOT / "book/versions/chapter16-v1.0-rc1.md").read_text(encoding="utf-8")
    review = (ROOT / "book/reviews/chapter16-review-codex-v1.0-rc1.md").read_text(encoding="utf-8")
    assert not any(marker in record + review for marker in
                   ("待派发", "待追加实际", "验收汇总尚在收尾"))
    for relative in ("book/chapter16.md", "book/sources/chapter16-sources.md",
                     "chapter16/reports/manifest.json", "chapter16/reports/improvement-report.json",
                     "chapter16/reports/exercise-results.json",
                     "chapter16/schemas/improvement-report-v1.schema.json"):
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() in record
    assert "4 项 Important" in review and "2 项 Minor" in review
    assert "未做第二次独立复审" in review


def test_chapter16_stays_out_of_public_manifest():
    manifest = json.loads((ROOT / "book/manifest.json").read_text(encoding="utf-8"))
    chapters = [c for section in manifest["sections"] for c in section["chapters"]]
    assert manifest["version"] == "0.14.0"
    assert sum(c["status"] == "published" for c in chapters) == 14
    assert all(c["status"] == "planned" and "source" not in c for c in chapters if c["order"] in (15, 16))
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert ".venv-chapter16/bin/python -B -m pytest chapter16/tests -q" in ci
    assert "--require-hashes -r chapter16/requirements-dev.txt" in ci


def test_old_chapters_and_rc_history_unchanged():
    original = subprocess.run(["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT,
                              check=True, capture_output=True, text=True).stdout.splitlines()
    protected = [p for p in original if re.match(r"(?:chapter(?:[1-9]|1[0-5])/|infographic/chapter(?:[1-9]|1[0-5])/|book/(?:chapter(?:[1-9]|1[0-5])\.md$|images/|sources/|reviews/|versions/))", p)
                 and p != "book/versions/CHAPTER_VERSIONS.md"]
    assert protected
    diff = subprocess.run(["git", "diff", "--name-only", BASE, "--", *protected], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout
    assert not diff, diff
    for path in ("book/manifest.json", "mkdocs.yml", ".github/workflows/pages.yml"):
        assert not subprocess.run(["git", "diff", "--name-only", BASE, "--", path], cwd=ROOT,
                                  check=True, capture_output=True, text=True).stdout
