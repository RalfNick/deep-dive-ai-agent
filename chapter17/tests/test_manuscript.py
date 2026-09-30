import re
from pathlib import Path


ROOT = Path(__file__).parents[2]
BOOK = ROOT / "book" / "chapter17.md"


def test_chapter_title_figures_and_experiments():
    text = BOOK.read_text(encoding="utf-8")
    assert text.startswith("# 第 17 章 多模态与实时 Agent")
    images = re.findall(r"!\[[^]]+\]\((images/chapter17/[^)]+)\)", text)
    assert len(images) == 7 and len(set(images)) == 7
    assert all((ROOT / "book" / path).is_file() for path in images)
    assert re.findall(r"> \*\*实验 17-([1-5]) ★", text) == ["1", "2", "3", "4", "5"]
    assert len(re.findall(r"^#{2,3} ", text, flags=re.M)) >= 28


def test_thirteen_complete_exercises_and_paths():
    text = BOOK.read_text(encoding="utf-8")
    assert re.findall(r"\*\*练习 17-(\d+)\b", text) == [str(i) for i in range(1, 14)]
    assert "../chapter17/reference-answers.md" in text
    assert "sources/chapter17-sources.md" in text
    assert (ROOT / "chapter17" / "README.md").is_file()
    assert (ROOT / "book" / "sources" / "chapter17-sources.md").is_file()
    for destination in re.findall(r"\]\((\.\./chapter17/[^)#]+)\)", text):
        assert (ROOT / "book" / destination).is_file(), destination


def test_prose_has_book_chapter_density():
    text = BOOK.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = "\n".join(line for line in text.splitlines()
                      if not line.startswith(("#", "|", "![", "[^") ) and not line.lstrip().startswith("- "))
    assert len(re.findall(r"[\u4e00-\u9fff]", prose)) >= 18000
