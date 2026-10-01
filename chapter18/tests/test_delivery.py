from pathlib import Path
import json
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = "c2cd958912a5a2c0f750ef31617927c694903979"


def test_all_current_deliverables_exist_without_publication():
    for relative in ("book/chapter18.md", "book/sources/chapter18-sources.md", "chapter18/README.md",
                     "chapter18/IMPLEMENTATION.md", "chapter18/reference-answers.md", "chapter18/preview.py",
                     "book/check_chapter18_preview.mjs", "infographic/chapter18/README.md"):
        assert (ROOT / relative).is_file(), relative
    assert len(list((ROOT / "chapter18/reports/reference-rc1").iterdir())) == 9
    assert len(list((ROOT / "book/images/chapter18").glob("*.svg"))) == 7
    manifest = json.loads((ROOT / "book/manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.14.0"
    chapters = [chapter for section in manifest["sections"] for chapter in section["chapters"]]
    assert not any(c["order"] == 18 and c["status"] == "published" for c in chapters)


def test_old_chapter_content_code_images_and_reports_are_preserved():
    if not (ROOT / ".git").exists() or not shutil.which("git"):
        pytest.skip("source archive without git history; preservation checked in author checkout")
    protected = [f"book/chapter{i}.md" for i in range(1,18)] + [f"chapter{i}" for i in range(1,18)]
    protected += [f"book/images/chapter{i}" for i in range(1,18)]
    result = subprocess.run(["git", "diff", "--name-only", BASE, "--", *protected], cwd=ROOT,
                            text=True, capture_output=True, check=True)
    assert not result.stdout.strip(), result.stdout
