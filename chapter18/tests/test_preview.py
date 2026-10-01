from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import re
import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_preview_is_local_with_seven_figures_and_five_scrollable_tables():
    from chapter18.preview import build_preview
    manifest = ROOT / "book/manifest.json"
    before = sha256(manifest.read_bytes()).hexdigest()
    page = build_preview(ROOT)
    assert page == ROOT / "chapter18/preview-pages/index.html"
    html = page.read_text(encoding="utf-8")
    assert html.count("<figure>") == 7 and html.count('class="table-wrap"') == 5
    for target in re.findall(r'(?:href|src)="([^"#]+)"', html):
        if target.startswith("https://"):
            continue
        assert (page.parent / target.split("#")[0]).exists(), target
    assert "reference-rc1/summary.md" in html and "reference-answers.md" in html
    assert sha256(manifest.read_bytes()).hexdigest() == before


def test_preview_rejects_external_traversal_and_reparse(tmp_path, monkeypatch):
    from chapter18.preview import build_preview
    for output in (tmp_path / "outside.html", ROOT / "chapter18/preview-pages/../outside.html",
                   ROOT / "book/outside.html"):
        with pytest.raises(ValueError):
            build_preview(ROOT, output=output)
    original = Path.lstat
    linked = ROOT / "chapter18/preview-pages"
    def lstat(path):
        info = original(path)
        return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400) if path == linked else info
    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="reparse"):
        build_preview(ROOT)
