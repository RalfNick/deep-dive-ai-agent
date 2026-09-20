from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from chapter12.preview import build_preview


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "book" / "chapter12.md"


def test_manuscript_has_seven_real_figure_assets():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    targets = re.findall(r"!\[[^\]]+\]\((images/chapter12/[^)]+\.png)\)", text)
    assert targets == [
        "images/chapter12/01-boundary.png",
        "images/chapter12/02-tools.png",
        "images/chapter12/03-loop.png",
        "images/chapter12/04-approval.png",
        "images/chapter12/05-context.png",
        "images/chapter12/06-sandbox.png",
        "images/chapter12/07-responsibilities.png",
    ]
    assert "制作标记" not in text
    assert all((ROOT / "book" / target).is_file() for target in targets)


def test_candidate_preview_has_seven_figures_and_local_resources():
    page = build_preview(ROOT)
    text = page.read_text(encoding="utf-8")
    assert '<html lang="zh-CN">' in text
    assert "第 12 章" in text and "本地候选" in text
    assert text.count("<figure>") == 7
    sources = re.findall(r'<img[^>]+src="([^"]+)"', text)
    assert len(sources) == 7
    for source in sources:
        parts = urlsplit(source)
        assert not parts.scheme and not parts.netloc
        assert (page.parent / unquote(parts.path)).resolve().is_file()


def test_preview_css_contains_mobile_and_table_guards():
    page = build_preview(ROOT)
    text = page.read_text(encoding="utf-8")
    assert "@media(max-width:600px)" in text
    assert ".table-wrap{overflow:auto;" in text
    assert "max-width:100%" in text
