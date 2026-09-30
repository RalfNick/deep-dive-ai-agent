from hashlib import sha256
from pathlib import Path

import pytest

from chapter17.preview import build_preview


ROOT = Path(__file__).parents[2]


def test_preview_does_not_touch_public_manifest():
    manifest = ROOT / "book/manifest.json"
    before = sha256(manifest.read_bytes()).hexdigest()
    page = build_preview(ROOT)
    assert page == ROOT / "chapter17/preview-pages/index.html"
    assert page.is_file()
    assert "chapter17/01-chart-evidence.svg" in page.read_text(encoding="utf-8")
    assert sha256(manifest.read_bytes()).hexdigest() == before


def test_preview_rejects_outside_path(tmp_path):
    with pytest.raises(ValueError):
        build_preview(ROOT, output=tmp_path / "outside.html")


def test_preview_dependency_is_declared_for_fresh_environment():
    requirements = ROOT / "chapter17" / "requirements-preview.txt"
    assert requirements.read_text(encoding="utf-8").strip() == "Markdown==3.10.2"
    assert "requirements-preview.txt" in (ROOT / "chapter17" / "README.md").read_text(encoding="utf-8")
