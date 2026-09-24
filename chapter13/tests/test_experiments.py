from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from chapter13.dataset import load_tasks
from chapter13.experiments import _variant_summary, build_evaluation, main, run_group


def test_full_evaluation_runs_120_trials_and_produces_expected_teaching_delta(tmp_path):
    report = build_evaluation(tmp_path / "work")
    assert report["schema_version"] == "chapter13.eval.v1"
    assert report["trial_count"] == 120
    assert report["variants"]["baseline"]["pass_1"] == 0.55
    assert report["variants"]["candidate"]["pass_1"] == 0.75
    assert report["paired_confidence"] == {
        "estimate": 0.2, "lower": 0.2, "upper": 0.2,
        "iterations": 10000, "seed": 20260924,
    }
    assert report["release"]["decision"] == "pass"
    assert report["variants"]["candidate"]["safety_violations"] == 0
    assert report["variants"]["candidate"]["environment_errors"] == 0
    assert report["failures"]
    assert all("trial_id" in item and "failed_graders" in item
               for item in report["failures"])
    assert report["provenance"]["suite"]["sha256"]
    assert report["provenance"]["gate"]["version"] == "chapter13.release-gate.v1"
    assert report["summary"]["trial_statuses"] == {"completed": 105, "agent_failed": 15}
    assert report["summary"]["failure_count"] == len(report["failures"])
    assert report["diagnostics"]["environment_error_trial"]["status"] == "environment_error"
    assert report["diagnostics"]["scored_in_suite_metrics"] is False


def test_reports_are_reproducible_and_do_not_leak_workspace_paths(tmp_path):
    left = build_evaluation(tmp_path / "left")
    right = build_evaluation(tmp_path / "right")
    assert left == right
    serialized = json.dumps(left, ensure_ascii=False)
    assert str(tmp_path) not in serialized
    assert "input_tokens" in serialized
    assert '"input_tokens": null' in serialized


def test_reliability_metrics_become_not_applicable_when_environment_errors_leave_fewer_than_k(tmp_path):
    report = build_evaluation(tmp_path / "few-usable")
    records = [deepcopy(item) for item in report["trials"] if item["variant"] == "baseline"]
    target = "basic-nested-relative"
    selected = [item for item in records if item["task_id"] == target]
    for item in selected[:3]:
        item["status"] = "environment_error"
        item["error"] = "fixture_unavailable"
    summary, _ = _variant_summary(records, load_tasks())
    assert summary["per_task"][target]["trials"] == 2
    assert summary["per_task"][target]["pass_at_3"] is None
    assert summary["per_task"][target]["pass_all_3"] is None


def test_five_groups_have_evidence_and_explicit_limits(tmp_path):
    for group in range(1, 6):
        report = run_group(group, tmp_path / f"group-{group}")
        assert report["schema_version"] == "chapter13.group.v1"
        assert report["evidence"]
        assert report["observations"]
        assert report["does_not_prove"]
    group_one = run_group(1, tmp_path / "group-one-again")
    assert group_one["observations"]["same_final_answer"] is True
    assert group_one["observations"]["same_outcome"] is False
    group_two = run_group(2, tmp_path / "group-two-again")
    assert group_two["observations"]["environment_error_is_separate_status"] is True
    assert group_two["observations"]["environment_error_example"]["status"] == "environment_error"


def test_cli_refuses_overwrite_and_replace_archives_previous_output(tmp_path, capsys):
    output = tmp_path / "reports"
    assert main(["--group", "all", "--output", str(output)]) == 0
    first = (output / "evaluation-report.json").read_bytes()
    assert main(["--group", "all", "--output", str(output)]) == 2
    assert (output / "evaluation-report.json").read_bytes() == first
    assert "output_exists" in capsys.readouterr().err
    assert main(["--group", "all", "--output", str(output), "--replace"]) == 0
    assert output.with_name("reports.previous-1").is_dir()
    assert (output / "evaluation-report.md").is_file()
    markdown = (output / "evaluation-report.md").read_text(encoding="utf-8")
    assert "原因：`all_hard_and_regression_gates_passed`" in markdown
    assert "error=`null`" in markdown
    assert "error=`None`" not in markdown
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["evaluation-report.json"]
    assert manifest["artifacts"]["evaluation-report.md"]


def test_versioned_json_schema_covers_every_stable_report_field(tmp_path):
    report = build_evaluation(tmp_path / "schema-work")
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "evaluation-report-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["$id"].endswith("chapter13.eval.v1.schema.json")
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(report)

    definitions = schema["$defs"]
    for name in (
        "variantSummary",
        "taskMetric",
        "trial",
        "event",
        "outcome",
        "usage",
        "grader",
        "failure",
        "judgeCalibration",
        "provenance",
        "summary",
    ):
        assert definitions[name]["additionalProperties"] is False

    assert schema["properties"]["diagnostics"]["additionalProperties"] is False

    assert definitions["trial"]["properties"]["status"]["enum"] == [
        "completed",
        "agent_failed",
        "environment_error",
        "invalid",
    ]
    assert definitions["variantSummary"]["properties"]["pass_1"]["$ref"] == "#/$defs/nullableRate"
    assert definitions["grader"]["properties"]["verdict"]["enum"] == [
        "pass",
        "fail",
        "unknown",
        "not_applicable",
    ]
    delta_schema = definitions["deltaMap"]["properties"]["safety"]
    assert delta_schema == {"type": "number", "minimum": -1, "maximum": 1}
