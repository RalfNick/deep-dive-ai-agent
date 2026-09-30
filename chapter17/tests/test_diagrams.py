from pathlib import Path
import xml.etree.ElementTree as ET

from infographic.chapter17.generate_diagrams import build_scenes, generate


def test_seven_original_diagrams_are_stable_and_self_contained(tmp_path):
    first = generate(tmp_path)
    images = sorted(tmp_path.glob("book/images/chapter17/*.svg"))
    assert len(images) == 7
    assert len(set(p.name for p in images)) == 7
    assert len(list(tmp_path.glob("infographic/chapter17/*.tldr"))) == 6
    old = {p.name: p.read_bytes() for p in images}
    assert generate(tmp_path) == first
    assert {p.name: p.read_bytes() for p in images} == old
    for image in images:
        raw = image.read_text(encoding="utf-8")
        assert "<script" not in raw.lower()
        assert "http://" not in raw.replace('xmlns="http://www.w3.org/2000/svg"', "")
        assert "https://" not in raw
        tree = ET.fromstring(raw)
        assert tree.attrib["viewBox"] == "0 0 1600 960"
        for text in tree.iter("{http://www.w3.org/2000/svg}tspan"):
            assert 0 < float(text.attrib["x"]) < 1600
            assert 0 < float(text.attrib["y"]) < 960


def test_first_chart_contains_visible_values_and_axis_warning(tmp_path):
    generate(tmp_path)
    raw = (tmp_path / "book/images/chapter17/01-chart-evidence.svg").read_text(encoding="utf-8")
    for label in ("80", "100", "千件", "零轴", "截断轴", "25%"):
        assert label in raw
    assert "data-value" not in raw


def test_scene_nodes_and_edges_are_unique_and_on_canvas():
    scenes = build_scenes()
    assert len(scenes) == 6
    assert len({scene.stem for scene in scenes}) == 6
    for scene in scenes:
        ids = {node.identity for node in scene.nodes}
        assert len(ids) == len(scene.nodes)
        for node in scene.nodes:
            assert 24 < node.x < 1576 and 180 < node.y < 825
            assert node.x + node.w < 1576 and node.y + node.h < 810
        assert all(edge.start in ids and edge.end in ids for edge in scene.edges)
