from copy import deepcopy
import pytest
from chapter18.tests.helpers import fixture_repo


@pytest.fixture
def report(tmp_path):
    from chapter18.experiments import run_all
    root = fixture_repo(tmp_path)
    return run_all(root=root, workdir=root / "chapter18/.runs/report")


def test_report_aggregates_actual_metrics_and_validates(report):
    from chapter18.reporting import validate_report
    assert report["schema_version"] == "chapter18.team.v1"
    assert report["summary"]["cases_total"] == 20
    assert len(report["groups"]) == 5
    assert report["summary"]["security_violations"] == 0
    assert report["summary"]["stale_patch_refusals"] == 1
    assert report["summary"]["duplicate_writes"] == 0
    validate_report(report)


def test_safety_metric_is_derived_not_a_preset_zero(report):
    from chapter18.reporting import build_report
    groups = tuple(tuple(deepcopy(g["cases"])) for g in report["groups"])
    repaired = next(c for g in groups for c in g if c["case_id"] == "repair-verified")
    repaired["receipts"][0]["path"] = "tests/test_existing.py"
    assert build_report(groups)["summary"]["security_violations"] == 1


@pytest.mark.parametrize("mutation", ["missing_group", "duplicate_case", "budget", "causal", "evidence", "verification", "source_proof", "context_content"])
def test_semantic_corruption_is_rejected(report, mutation):
    from chapter18.reporting import validate_report
    data = deepcopy(report)
    case = data["groups"][0]["cases"][0]
    if mutation == "missing_group":
        data["groups"].pop()
    elif mutation == "duplicate_case":
        data["groups"][0]["cases"][1]["case_id"] = case["case_id"]
    elif mutation == "budget":
        case["metrics"]["budget_remaining"] += 1
    elif mutation == "causal":
        case["trajectory"][0]["parent_event_id"] = "nonexistent"
    elif mutation == "evidence":
        case["worker_results"][0]["claims"][0]["evidence"][0]["digest"] = "0" * 64
    elif mutation == "source_proof":
        case["input_proof"]["source_digests"][0][1] = "0" * 64
    elif mutation == "context_content":
        from hashlib import sha256
        import json
        context = case["input_proof"]["context_digests"][0]
        context["sent"][0][1] = "伪造的输入资料"
        context["sent_digest"] = sha256(json.dumps(context["sent"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    else:
        repaired = next(c for g in data["groups"] for c in g["cases"] if c["case_id"] == "repair-verified")
        repaired["acceptance"] = []
    with pytest.raises(ValueError):
        validate_report(data)
