from __future__ import annotations

import json

from infographic.chapter13.generate_diagrams import generate_all


def test_generate_all_writes_seven_valid_editable_tldraw_sources(tmp_path):
    paths = generate_all(tmp_path)
    assert [path.name for path in paths] == [
        "01-evaluation-model.tldr", "02-same-answer-different-evidence.tldr",
        "03-multi-grader-matrix.tldr", "04-eval-lifecycle.tldr",
        "05-pass-k-vs-pass-all-k.tldr", "06-judge-calibration.tldr",
        "07-framework-mapping.tldr",
    ]
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload["records"]
        assert records[0]["id"] == "document:document"
        assert records[1]["id"] == "page:page1"
        shapes = [record for record in records if record.get("typeName") == "shape"]
        ids = {shape["id"] for shape in shapes}
        indexes = [shape["index"] for shape in shapes]
        assert len(indexes) == len(set(indexes))
        for shape in shapes:
            if shape["type"] == "arrow":
                assert shape["props"]["start"]["boundShapeId"] in ids
                assert shape["props"]["end"]["boundShapeId"] in ids
