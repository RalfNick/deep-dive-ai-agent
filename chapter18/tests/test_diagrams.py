import json
import unicodedata
import xml.etree.ElementTree as ET

STEMS = ("01-boundaries", "02-dependencies", "03-delegation-handoff", "04-task-context",
         "05-integration", "06-lifecycle", "07-final-system")


def test_seven_editable_figures_are_stable_and_local(tmp_path):
    from infographic.chapter18.generate_diagrams import build_scenes, generate
    scenes = build_scenes()
    assert tuple(s.stem for s in scenes) == STEMS
    outputs = generate(tmp_path)
    assert len(outputs) == 14
    first = {p.relative_to(tmp_path): p.read_bytes() for p in outputs}
    assert first == {p.relative_to(tmp_path): p.read_bytes() for p in generate(tmp_path)}
    for scene in scenes:
        svg = tmp_path / "book/images/chapter18" / (scene.stem + ".svg")
        text = svg.read_text(encoding="utf-8")
        assert "<script" not in text and "https://" not in text
        ET.fromstring(text)
        document = json.loads((tmp_path / "infographic/chapter18" / (scene.stem + ".tldr")).read_text(encoding="utf-8"))
        ids = [r["id"] for r in document["records"]]
        assert len(ids) == len(set(ids))
        nodes = {n.identity: n for n in scene.nodes}
        for node in scene.nodes:
            assert 40 <= node.x and node.x + node.w <= 1560
            assert 180 <= node.y and node.y + node.h <= 800
        for edge in scene.edges:
            assert edge.start in nodes and edge.end in nodes
        # CJK glyphs are full-width; Latin labels are not CJK-width glyphs.
        for node in scene.nodes:
            widths = [sum(1 if unicodedata.east_asian_width(c) in {"W", "F"} else .65
                          for c in line) * 25 for line in node.label.split("\n")]
            assert max(widths) <= node.w - 20


def test_figures_keep_the_teaching_boundaries():
    from infographic.chapter18.generate_diagrams import build_scenes
    scenes = {s.stem: s for s in build_scenes()}
    dep = scenes["02-dependencies"]
    assert "23" in dep.subtitle and "16" in dep.subtitle and "逻辑单位" in dep.subtitle
    hand = scenes["03-delegation-handoff"]
    assert any(e.label == "返回结果" for e in hand.edges)
    assert any(e.label == "接管控制权" for e in hand.edges)
    lifecycle = scenes["06-lifecycle"]
    assert "16" in lifecycle.subtitle and "2" in lifecycle.subtitle
    final = scenes["07-final-system"]
    labels = " ".join(n.label for n in final.nodes)
    assert all(term in labels for term in ("answer", "审批", "execute", "verify"))
    assert not any(e.start == "tool" and e.end == "verified" for e in final.edges)
