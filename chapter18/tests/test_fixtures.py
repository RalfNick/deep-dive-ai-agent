from hashlib import sha256
import pytest
from chapter18.tests.helpers import ROOT, fixture_repo


def test_twenty_unique_cases_and_seven_original_sources():
    from chapter18.fixtures import load_sources, load_case_specs
    cases = load_case_specs(ROOT)
    assert len(cases) == len({c["case_id"] for c in cases}) == 20
    assert [sum(c["group"] == g for c in cases) for g in range(1, 6)] == [4] * 5
    sources = load_sources(ROOT)
    assert len(sources) == 7
    for doc in sources:
        assert sha256((ROOT / doc.location).read_bytes()).hexdigest() == doc.digest
    conflict = [s for s in sources if s.source_id in {"conflict-a", "conflict-b"}]
    assert all(s.eligible and s.version == "v2" for s in conflict)
    assert len({s.facts for s in conflict}) == 2


def test_workspace_is_new_inside_runs_and_refuses_overwrite(tmp_path):
    from chapter18.fixtures import create_workspace
    root = fixture_repo(tmp_path)
    dest = root / "chapter18/.runs/first/integration"
    assert create_workspace(root, dest) == dest
    assert (dest / "src/linkcheck.py").is_file()
    assert (dest / "tests/test_existing.py").is_file()
    with pytest.raises(ValueError):
        create_workspace(root, dest)
    with pytest.raises(ValueError):
        create_workspace(root, tmp_path / "outside")


def test_source_index_refuses_parent_traversal(tmp_path):
    import json
    from chapter18.fixtures import load_sources
    root = fixture_repo(tmp_path)
    path = root / "chapter18/fixtures/knowledge.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data[0]["location"] = "../private.md"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_sources(root)
