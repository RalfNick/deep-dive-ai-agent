from pathlib import Path
import pytest
from chapter16.preview import build_preview
ROOT = Path(__file__).parents[2]

def test_preview_seven_figures_five_tables_and_no_remote_runtime():
    html = build_preview(ROOT).read_text(encoding="utf-8")
    assert html.count("<figure>") == html.count('class="figure-link"') == 7
    assert html.count('class="table-wrap"') == 5
    assert "../../book/images/chapter16/" in html
    assert '<script' not in html and '<link' not in html
    assert "width:760px" in html and "overflow-x:auto" in html

def test_preview_cannot_overwrite_reports_or_escape(tmp_path):
    for target in (ROOT/"chapter16/reports/index.html", tmp_path/"outside.html",ROOT/"chapter16/preview-pages/data.json"):
        with pytest.raises(ValueError):
            build_preview(ROOT,output=target)

def test_preview_link_parent_rejected(monkeypatch):
    from chapter16 import preview
    monkeypatch.setattr(preview,"is_linklike",lambda p:p.name=="preview-pages")
    with pytest.raises(ValueError,match="link"):
        build_preview(ROOT)
