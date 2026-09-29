import json
import re
from pathlib import Path
from infographic.chapter16.generate_diagrams import build_scenes, generate

ROOT = Path(__file__).parents[2]

def test_seven_diagrams_editable_and_bound():
    scenes = build_scenes()
    assert len(scenes) == len({s.stem for s in scenes}) == 7
    text = (ROOT/"book/chapter16.md").read_text(encoding="utf-8")
    for scene in scenes:
        assert f"{scene.stem}.svg" in text
        svg = (ROOT/f"book/images/chapter16/{scene.stem}.svg").read_text(encoding="utf-8")
        assert 'viewBox="0 0 1600 960"' in svg and scene.title in svg
        assert not re.search(r'(href|src)="https?://', svg)
        source = json.loads((ROOT/f"infographic/chapter16/{scene.stem}.tldr").read_text(encoding="utf-8"))
        ids = {r["id"] for r in source["records"]}
        for record in source["records"]:
            if record.get("type") == "arrow":
                assert record["props"]["start"]["boundShapeId"] in ids
                assert record["props"]["end"]["boundShapeId"] in ids
    all_labels = " ".join(n.label for s in scenes for n in s.nodes)
    assert all(word in all_labels for word in ("Unknown","未批准","重新验证","过期","外部副作用"))

def test_generation_byte_stable(tmp_path):
    first = generate(tmp_path)
    before = {p.relative_to(tmp_path):p.read_bytes() for p in first}
    assert before == {p.relative_to(tmp_path):p.read_bytes() for p in generate(tmp_path)}
