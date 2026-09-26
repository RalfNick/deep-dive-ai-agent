from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from chapter14.experiments import build_diagnostics, main, run_group


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "chapter14" / "schemas" / "production-diagnostics-v1.schema.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_five_groups_expose_the_promised_evidence(tmp_path: Path) -> None:
    output = tmp_path / "groups"
    output.mkdir()
    groups = {number: run_group(number, output) for number in range(1, 6)}

    assert groups[1]["comparisons"]["control"]["verdict"] == "comparable"
    assert groups[1]["comparisons"]["same_score_misleading"]["verdict"] == "partially_comparable"
    assert groups[2]["log_view"]["causal_edges_available"] is False
    assert groups[2]["trace_view"]["dependency_edge_count"] > 0
    assert groups[3]["release_summaries"]["incident"]["latency_ms"]["p95"] > groups[3]["release_summaries"]["stable"]["latency_ms"]["p95"]
    assert groups[4]["sampling"]["population_metrics"]["request_count"] == 72
    assert groups[4]["privacy"]["export_safe"] is True
    assert groups[5]["incident_report"]["root_cause"] == "retry_policy"
    assert len(groups[5]["regression_tasks"]) == 3


def test_full_report_is_stable_safe_and_refuses_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-environment-secret")
    first = tmp_path / "first"
    second = tmp_path / "second"
    report = build_diagnostics(first)
    build_diagnostics(second)

    assert report["schema_version"] == "chapter14.diagnostics.v1"
    assert report["fixture"]["scored_trace_count"] == 72
    assert sorted(path.name for path in first.iterdir()) == [
        "diagnostic-report.json", "diagnostic-report.md", "group-1.json", "group-2.json",
        "group-3.json", "group-4.json", "group-5.json", "manifest.json",
    ]
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    assert "generated_at" not in serialized
    assert str(ROOT) not in serialized
    assert "sk-environment-secret" not in serialized
    assert "Authorization" not in serialized
    with pytest.raises(FileExistsError, match="output_directory_not_empty"):
        build_diagnostics(first)


def test_replace_keeps_previous_output_recoverable(tmp_path: Path) -> None:
    output = tmp_path / "candidate"
    build_diagnostics(output)
    (output / "reader-note.txt").write_text("preserve me", encoding="utf-8")

    assert main(["--group", "all", "--output", str(output), "--replace"]) == 0

    assert (output / "diagnostic-report.json").exists()
    assert (tmp_path / "candidate.previous" / "reader-note.txt").read_text(encoding="utf-8") == "preserve me"


def test_report_schema_accepts_real_report_and_rejects_semantic_mutations(tmp_path: Path) -> None:
    report = build_diagnostics(tmp_path / "report")
    schema = _load(SCHEMA_PATH)
    validator = Draft202012Validator(schema)

    assert list(validator.iter_errors(report)) == []

    mutations = []
    invalid_release = deepcopy(report)
    invalid_release["fixture"]["release_ids"][0] = "preview"
    mutations.append(invalid_release)
    invalid_conclusion = deepcopy(report)
    invalid_conclusion["incident_report"]["conclusion"] = "certain"
    mutations.append(invalid_conclusion)
    nested_unknown = deepcopy(report)
    nested_unknown["release_summaries"]["stable"]["latency_ms"]["surprise"] = 1
    mutations.append(nested_unknown)
    negative_duration = deepcopy(report)
    negative_duration["release_summaries"]["stable"]["latency_ms"]["p95"] = -1
    mutations.append(negative_duration)
    missing_completeness = deepcopy(report)
    del missing_completeness["sampling"]["telemetry_completeness"]
    mutations.append(missing_completeness)

    assert all(list(validator.iter_errors(item)) for item in mutations)
