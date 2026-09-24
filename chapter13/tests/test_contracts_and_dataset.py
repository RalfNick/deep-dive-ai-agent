from __future__ import annotations

import pytest

from chapter13.contracts import EvaluationReport, GraderResult, TaskSpec, TrialRecord
from chapter13.dataset import load_tasks


def test_task_spec_rejects_unknown_slice_and_invalid_budget():
    with pytest.raises(ValueError, match="unknown_task_slice"):
        TaskSpec("bad", "prompt", "unknown", "train", "ok", ("src/",), (), 1, 1, 1, 2)
    with pytest.raises(ValueError, match="invalid_budget"):
        TaskSpec("bad", "prompt", "basic", "train", "ok", ("src/",), (), 0, 1, 1, 2)


def test_dataset_has_twelve_unique_tasks_in_four_balanced_slices():
    tasks = load_tasks()
    assert len(tasks) == 12
    assert len({task.task_id for task in tasks}) == 12
    counts = {name: sum(task.slice == name for task in tasks)
              for name in ("basic", "edge", "safety", "recovery")}
    assert counts == {"basic": 3, "edge": 3, "safety": 3, "recovery": 3}
    assert all(task.candidate_successes == task.baseline_successes + 1 for task in tasks)
    assert all(task.fixture_id == "linkcheck-v1" for task in tasks)
    assert all(task.labels and task.slice in task.labels for task in tasks)
    assert all(task.success_conditions for task in tasks)
    assert all(task.seed_strategy == "fixed-five-v1" for task in tasks)


def test_trial_serialization_keeps_environment_errors_separate_from_agent_failure():
    trial = TrialRecord(
        task_id="basic-nested-relative", variant="candidate", trial_id="t-1",
        seed=101, environment_id="env-1", status="environment_error",
        final_answer="", outcome={}, events=(), usage={"steps": 0, "tool_calls": 0},
        error="fixture_missing", graders=(),
    )
    payload = trial.to_dict()
    assert payload["status"] == "environment_error"
    assert payload["error"] == "fixture_missing"
    assert payload["events"] == []


def test_grader_result_accepts_only_declared_verdicts():
    assert GraderResult("outcome", "pass", ("solution_matches",), ("src/solution.txt",), {}).verdict == "pass"
    with pytest.raises(ValueError, match="invalid_grader_verdict"):
        GraderResult("outcome", "maybe", (), (), {})


def test_evaluation_report_serializes_explicit_failures_and_release_decision():
    report = EvaluationReport(
        schema_version="chapter13.eval.v1", decision_source="scripted",
        task_count=1, trial_count=1, seeds=(101,), variants={}, slice_deltas={},
        paired_confidence={"lower": -0.1, "upper": 0.2},
        release={"decision": "inconclusive"}, judge_calibration={},
        usage_boundary={}, provenance={}, summary={}, diagnostics={},
        failures=({"trial_id": "t-1", "failed_graders": ["outcome"]},),
        trials=(), limits=("teaching fixture",),
    )
    payload = report.to_dict()
    assert payload["schema_version"] == "chapter13.eval.v1"
    assert payload["failures"] == [{"trial_id": "t-1", "failed_graders": ["outcome"]}]
    assert payload["release"]["decision"] == "inconclusive"
