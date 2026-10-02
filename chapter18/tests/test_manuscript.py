from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]


def test_manuscript_density_and_frozen_evidence_links():
    path = ROOT / "book/chapter18.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# 第 18 章 Multi-Agent 与最终系统：不是 Agent 越多越好")
    prose = re.sub(r"```[^\n]*\n.*?```", "", text, flags=re.S)
    prose = "\n".join(line for line in prose.splitlines()
                      if not line.startswith(("#", "|", "![", "[^")))
    hanzi = len(re.findall(r"[\u4e00-\u9fff]", prose))
    assert 22000 <= hanzi <= 28000, hanzi
    assert 28 <= len(re.findall(r"^#{2,3} ", text, re.M)) <= 36
    assert len(re.findall(r"!\[.*?\]\(images/chapter18/.*?\.svg\)", text)) == 7
    assert len(re.findall(r"^> \*\*实验 18-[1-5] ", text, re.M)) == 5
    assert len(re.findall(r"^\*\*练习 (?:[1-9]|1[0-3]) ", text, re.M)) == 13
    assert len(re.findall(r"^\|\s*---", text, re.M)) == 5
    targets = re.findall(r"\]\(([^)]+)\)", text)
    for target in targets:
        if target.startswith(("https://", "#")):
            continue
        relative = unquote(target.split("#")[0])
        assert (path.parent / relative).exists(), target
    assert "../chapter18/reports/reference-rc2/summary.md" in targets


def test_reader_materials_explain_actual_commands_and_limits():
    readme = (ROOT / "chapter18/README.md").read_text(encoding="utf-8")
    for module in ("pytest chapter18/tests", "chapter18.experiments", "chapter18.exercise_solutions", "chapter18.preview"):
        assert module in readme
    implementation = (ROOT / "chapter18/IMPLEMENTATION.md").read_text(encoding="utf-8")
    assert "未实现" in implementation and "真实模型" in implementation and "操作系统沙箱" in implementation
