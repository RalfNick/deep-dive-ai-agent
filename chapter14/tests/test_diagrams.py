from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from infographic.chapter14.generate_diagrams import APPROVED_DIAGRAMS, generate_all


def test_generate_all_writes_seven_approved_editable_svg_pairs(tmp_path: Path) -> None:
    pairs = generate_all(tmp_path / "sources", tmp_path / "images")

    assert [(source.name, image.name) for source, image in pairs] == [
        (f"{stem}.tldr", f"{stem}.svg") for stem, _ in APPROVED_DIAGRAMS
    ]
    assert len(pairs) == 7


def test_tldraw_indexes_and_arrow_bindings_are_valid(tmp_path: Path) -> None:
    for source, _ in generate_all(tmp_path / "sources", tmp_path / "images"):
        payload = json.loads(source.read_text(encoding="utf-8"))
        records = payload["records"]
        assert records[0]["id"] == "document:document"
        assert records[1]["id"] == "page:page1"
        shapes = [record for record in records if record.get("typeName") == "shape"]
        ids = {shape["id"] for shape in shapes}
        indexes = [shape["index"] for shape in shapes]
        assert len(indexes) == len(set(indexes))
        assert all(index.startswith("a") and len(index) == 2 for index in indexes)
        for shape in shapes:
            if shape["type"] == "arrow":
                assert shape["props"]["start"]["boundShapeId"] in ids
                assert shape["props"]["end"]["boundShapeId"] in ids


def test_svg_is_self_contained_titled_and_uses_same_scene_labels(tmp_path: Path) -> None:
    expected_titles = dict(APPROVED_DIAGRAMS)
    for source, image in generate_all(tmp_path / "sources", tmp_path / "images"):
        svg_text = image.read_text(encoding="utf-8")
        root = ET.fromstring(svg_text)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        title = root.find("svg:title", namespace)
        payload = json.loads(source.read_text(encoding="utf-8"))
        labels = [
            record["props"]["text"]
            for record in payload["records"]
            if record.get("type") == "geo" and record["props"].get("text")
        ]

        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib["viewBox"] == "0 0 1600 960"
        assert title is not None and title.text == expected_titles[source.stem]
        assert "http://" not in svg_text.replace("http://www.w3.org/2000/svg", "")
        assert "https://" not in svg_text
        assert "data:image" not in svg_text
        assert "<image" not in svg_text
        assert all(line in svg_text for label in labels for line in label.split("\n"))
