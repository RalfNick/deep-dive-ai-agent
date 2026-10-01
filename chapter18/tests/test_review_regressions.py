"""Consumer-visible failures reproduced by the independent whole-branch review."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from chapter18.contracts import BudgetLimits, Decision, ToolCall, ToolOutcome, WorkerResult
from chapter18.tests.helpers import fixture_repo
from chapter18.tests.test_runtime import child_of, make_runtime


def test_knowledge_business_path_preserves_all_eligible_conflicts(tmp_path):
    from chapter18.system import new_packet, run_system
    root = fixture_repo(tmp_path)
    p = new_packet(input_refs=("retention",), output_requirements=("retention",),
                   allowed_sources=frozenset({"conflict-a", "conflict-b"}))
    result = run_system("knowledge", p, root=root, workdir=root / "chapter18/.runs/conflict")
    assert result["status"] == "conflict"
    assert {c["value"] for c in result["evidence_verdict"]["claims"]} == {"30天", "90天"}


def test_knowledge_selects_qualified_sources_before_dispatch_and_batches(tmp_path):
    from chapter18.system import new_packet, run_system
    root = fixture_repo(tmp_path)
    index_path = root / "chapter18/fixtures/knowledge.json"
    rows = json.loads(index_path.read_text(encoding="utf-8"))
    old = next(r for r in rows if r["source_id"] == "public-old")
    index_path.write_text(json.dumps([old] + [r for r in rows if r is not old]), encoding="utf-8")
    p = new_packet(input_refs=("sharing", "edition", "support_hours"),
        output_requirements=("sharing", "edition", "support_hours"),
        allowed_sources=frozenset({"public-old", "public-current", "parallel-product", "parallel-support"}))
    result = run_system("knowledge", p, root=root, workdir=root / "chapter18/.runs/batches")
    assert result["status"] == "answer"
    assert len(result["worker_results"]) == 4  # 2 sharing + edition + hours, exceeds inflight=3.
    assert "public-old" not in result["evidence_verdict"]["distinct_sources"]
    assert result["metrics"]["tool_calls"] == 4


def test_worker_cannot_submit_another_existing_tasks_valid_identity():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime()
    a, b = child_of(p, 1), child_of(p, 2)
    stolen = WorkerResult(b.task_id, "b-1", b.worker_id, "done")
    runtime.start(a, ScriptedPolicy((Decision("result", result=stolen),)), attempt_id="a-1")
    runtime.start(b, ScriptedPolicy((Decision("result", result=stolen),)), attempt_id="b-1")
    runtime.step(a.task_id)
    assert runtime.state.results == ()
    assert any(e.kind == "result_rejected" and e.task_id == a.task_id for e in runtime.state.events)
    runtime.step(b.task_id)
    assert len(runtime.state.results) == 1 and runtime.state.results[0].decisions == 1


def test_zero_child_worker_quota_prevents_real_tool_execution():
    from chapter18.policy import ScriptedPolicy
    invoked = []
    runtime, p = make_runtime(lambda p, c: (invoked.append(p.task_id) or ToolOutcome(c.call_id, "ok")))
    child = replace(child_of(p, 1), limits=BudgetLimits(tool_calls=2, verifier_reserve=2))
    runtime.start(child, ScriptedPolicy((Decision("tool", call=ToolCall("read", "knowledge")),)), attempt_id="a-1")
    runtime.step(child.task_id)
    assert invoked == [] and runtime.ledger.used == 0
    assert runtime.state.status == "stopped" and runtime.state.reason_code == "task_budget_exhausted"


def test_retry_and_descendant_share_the_childs_tightened_quota():
    from chapter18.policy import ScriptedPolicy
    invoked = []
    runtime, p = make_runtime(lambda p, c: (invoked.append(p.task_id) or ToolOutcome(c.call_id, "transient_error")))
    child = replace(child_of(p, 1), limits=BudgetLimits(tool_calls=3))
    runtime.start(child, ScriptedPolicy(()), attempt_id="a-1")
    grandchild = replace(child, task_id="grandchild", worker_id="nested", parent_id=child.task_id, depth=2)
    runtime.start(grandchild, ScriptedPolicy((Decision("tool", call=ToolCall("read", "knowledge")),)), attempt_id="g-1")
    runtime.step(grandchild.task_id)
    assert invoked == ["grandchild"] and runtime.ledger.used == 1
    assert runtime.state.reason_code == "task_budget_exhausted"


def test_only_current_controller_can_handoff_to_an_active_recipient():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime()
    child = child_of(p, 1)
    runtime.start(child, ScriptedPolicy((Decision("tool", call=ToolCall("read", "knowledge")),)), attempt_id="a-1")
    assert runtime.handoff(child.worker_id, task_id=p.task_id)
    assert not runtime.handoff(p.worker_id, task_id=p.task_id)  # Old manager cannot seize control back.
    assert runtime.state.controller == child.worker_id and runtime.state.handoffs == 1
    runtime.step(child.task_id)
    assert runtime.ledger.used == 1
    assert runtime.handoff(p.worker_id, task_id=child.task_id)


def test_handoff_case_performs_recipient_decision_after_transfer(tmp_path):
    from chapter18.cases import run_case
    root = fixture_repo(tmp_path)
    case = run_case("handoff-transfer", root=root, workdir=root / "chapter18/.runs/handoff")
    transfers = [e for e in case["trajectory"] if e["kind"] == "handoff"]
    assert len(transfers) == 1 and transfers[0]["task_id"] == "root"
    assert any(e["kind"] == "decision" and e["task_id"] == "expert" and
               e["data"].get("controller") == "expert" for e in case["trajectory"])


@pytest.fixture
def current_report(tmp_path):
    from chapter18.experiments import run_all
    root = fixture_repo(tmp_path)
    return run_all(root=root, workdir=root / "chapter18/.runs/review-report")


@pytest.mark.parametrize("mutation", ["verification", "trajectory", "commit_digest", "commit_identity", "accepted_result"])
def test_complete_report_requires_correlated_execution_and_acceptance_events(current_report, mutation):
    from chapter18.reporting import build_report, validate_report
    data = deepcopy(current_report)
    case = next(c for g in data["groups"] for c in g["cases"] if c["case_id"] == "repair-verified")
    if mutation == "trajectory":
        case["trajectory"] = []
    elif mutation in {"verification", "accepted_result"}:
        kind = "verification" if mutation == "verification" else "result_accepted"
        case["trajectory"] = [e for e in case["trajectory"] if e["kind"] != kind]
    else:
        commit = next(e for e in case["trajectory"] if e["kind"] == "action_committed")
        commit["data"]["after_digest" if mutation == "commit_digest" else "proposal_task_id"] = "wrong"
    # Repair ordinary causal links and counters: the omitted semantic evidence must be the reason to reject.
    previous = {}
    for event in case["trajectory"]:
        event["parent_event_id"] = previous.get(event["task_id"])
        previous[event["task_id"]] = event["event_id"]
    for result in case["worker_results"]:
        result["decisions"] = sum(e["kind"] == "decision" and e["task_id"] == result["task_id"] for e in case["trajectory"])
        result["tool_calls"] = sum(e["kind"] == "tool_returned" and e["task_id"] == result["task_id"] for e in case["trajectory"])
    rebuilt = build_report(tuple(tuple(g["cases"]) for g in data["groups"]))
    with pytest.raises(ValueError):
        validate_report(rebuilt)


def test_preview_rejects_nested_output_with_wrong_relative_asset_base(tmp_path):
    import shutil
    from chapter18.preview import build_preview
    from chapter18.tests.helpers import ROOT
    root = tmp_path / "book-repo"
    (root / "book").mkdir(parents=True)
    shutil.copyfile(ROOT / "book/chapter18.md", root / "book/chapter18.md")
    with pytest.raises(ValueError):
        build_preview(root, output=root / "chapter18/preview-pages/nested/index.html")
