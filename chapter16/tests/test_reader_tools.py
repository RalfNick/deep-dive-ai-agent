import json
from pathlib import Path
import pytest
from chapter16.exercise_solutions import solve, payload, main
from chapter16.serialization import canonical_bytes

def test_all_thirteen_exercises_have_feedback():
    answers = [solve(n) for n in range(1,14)]
    assert [a["number"] for a in answers] == list(range(1,14))
    assert all(a["status"] in {"passed","answered"} and a["criteria"] for a in answers)
    assert solve(3)["evidence"]["independent_origins"] == 6
    assert solve(4)["evidence"] == {"coverage":0.7,"verified_subset_repair":5/7,"unknown_share":0.3}
    assert canonical_bytes(payload()) == canonical_bytes(payload())
    with pytest.raises(ValueError):
        solve(14)

def test_exercise_payload_and_readme_entry():
    root = Path(__file__).parents[2]
    text = (root/"chapter16/README.md").read_text(encoding="utf-8")
    assert "--group all --output" in text and "requirements-preview.txt" in text
    assert payload()["schema_version"] == "chapter16.exercises.v1"
    assert all(f"**{n}." in (root/"chapter16/reference-answers.md").read_text(encoding="utf-8") for n in range(1,14))
    # Pure solutions must not call the all-experiments entry and recurse.
    source = (root/"chapter16/exercise_solutions.py").read_text(encoding="utf-8")
    assert "from .experiments" not in source
