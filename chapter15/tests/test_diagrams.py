from __future__ import annotations

import json
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from infographic.chapter15.generate_diagrams import APPROVED_DIAGRAMS, HEIGHT, WIDTH, generate_all


def test_generate_all_writes_exactly_seven_source_render_pairs(tmp_path: Path) -> None:
    source_root = tmp_path / "sources"
    output_root = tmp_path / "images"
    renders = generate_all(output_root, source_root)

    assert [path.name for path in renders] == [f"{stem}.svg" for stem, _ in APPROVED_DIAGRAMS]
    assert sorted(path.name for path in source_root.glob("*.tldr")) == [
        f"{stem}.tldr" for stem, _ in APPROVED_DIAGRAMS
    ]
    assert len(renders) == 7


def test_tldraw_indexes_bindings_and_canvas_bounds_are_valid(tmp_path: Path) -> None:
    source_root = tmp_path / "sources"
    generate_all(tmp_path / "images", source_root)

    for source in sorted(source_root.glob("*.tldr")):
        payload = json.loads(source.read_text(encoding="utf-8"))
        records = payload["records"]
        shapes = [record for record in records if record.get("typeName") == "shape"]
        ids = {shape["id"] for shape in shapes}
        indexes = [shape["index"] for shape in shapes]
        assert len(indexes) == len(set(indexes))
        assert all(index.startswith("a") and len(index) == 2 for index in indexes)
        for shape in shapes:
            if shape["type"] == "arrow":
                assert shape["props"]["start"]["boundShapeId"] in ids
                assert shape["props"]["end"]["boundShapeId"] in ids
            elif shape["type"] == "geo":
                assert 0 <= shape["x"] <= WIDTH
                assert 0 <= shape["y"] <= HEIGHT
                assert shape["props"]["w"] > 0 and shape["props"]["h"] > 0
                assert shape["x"] + shape["props"]["w"] <= WIDTH
                assert shape["y"] + shape["props"]["h"] <= HEIGHT


def test_svg_is_accessible_self_contained_and_uses_shared_labels(tmp_path: Path) -> None:
    source_root = tmp_path / "sources"
    renders = generate_all(tmp_path / "images", source_root)
    expected_titles = dict(APPROVED_DIAGRAMS)

    for image in renders:
        svg_text = image.read_text(encoding="utf-8")
        root = ET.fromstring(svg_text)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        title = root.find("svg:title", namespace)
        payload = json.loads((source_root / f"{image.stem}.tldr").read_text(encoding="utf-8"))
        labels = [
            record["props"]["text"]
            for record in payload["records"]
            if record.get("type") == "geo" and record["props"].get("text")
        ]

        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib["viewBox"] == f"0 0 {WIDTH} {HEIGHT}"
        assert title is not None and title.text == expected_titles[image.stem]
        assert "http://" not in svg_text.replace("http://www.w3.org/2000/svg", "")
        assert "https://" not in svg_text
        assert "data:image" not in svg_text
        assert "<image" not in svg_text
        assert all(html.escape(line) in svg_text for label in labels for line in label.split("\n"))


def test_svg_text_is_readable_and_reading_order_is_visible(tmp_path: Path) -> None:
    renders = generate_all(tmp_path / "images", tmp_path / "sources")

    for image in renders:
        svg_text = image.read_text(encoding="utf-8")
        font_sizes = [int(value) for value in re.findall(r'font-size="(\d+)"', svg_text)]
        assert font_sizes and min(font_sizes) >= 18
        assert any(f">{number} " in svg_text for number in range(1, 5))
