from pathlib import Path
import pytest
from chapter18.tests.helpers import fixture_repo


@pytest.fixture
def results(tmp_path):
    from chapter18.cases import run_group
    root = fixture_repo(tmp_path)
    return {c["case_id"]: c for group in range(1, 6) for c in run_group(group, root=root, workdir=root / f"chapter18/.runs/group-{group}")}


def test_twenty_cases_show_evidence_not_role_count(results):
    assert len(results) == 20
    assert results["single-sufficient"]["status"] == "answer"
    assert results["parallel-separated"]["logical_schedule"]["serial_units"] == 23
    assert results["parallel-separated"]["logical_schedule"]["parallel_units"] == 16
    assert results["duplicate-research"]["metrics"]["duplicate_tasks"] == 1
    assert results["delegation-return"]["controller"] == "manager"
    assert results["handoff-transfer"]["controller"] == "expert"
    assert results["context-not-forwarded"]["status"] == "unknown"
    assert results["scope-escalation"]["status"] == "blocked"


def test_conflicts_and_three_votes_do_not_become_success(results):
    assert results["source-version-conflict"]["status"] == "conflict"
    votes = results["same-source-three-votes"]
    assert votes["metrics"]["distinct_eligible_sources"] == 1
    assert votes["status"] == "unknown"
    assert results["stale-patch"]["metrics"]["stale_patch_refusals"] == 1
    assert results["stale-patch"]["status"] == "conflict"
    assert results["disjoint-patches"]["status"] == "verified"


def test_partial_timeout_global_budget_and_late_result_remain_explicit(results):
    timeout = results["one-worker-timeout"]
    assert timeout["status"] == "unknown"
    assert (timeout["metrics"]["coverage_numerator"], timeout["metrics"]["coverage_denominator"]) == (1, 2)
    exhausted = results["global-budget-exhausted"]
    assert exhausted["status"] == "stopped"
    assert exhausted["metrics"]["tool_calls"] == 6
    assert exhausted["metrics"]["budget_remaining"] == 2
    assert results["cancel-late-result"]["status"] == "stopped"
    assert any(r["executed"] for r in results["cancel-late-result"]["receipts"])
    assert results["handoff-cycle"]["reason_code"] == "handoff_limit"


def test_final_paths_are_real_and_permission_safe(results):
    assert results["kb-verified-answer"]["status"] == "answer"
    denied = results["kb-permission-denied"]
    assert denied["status"] == "blocked" and "内部额度" not in str(denied)
    repaired = results["repair-verified"]
    assert repaired["status"] == "verified"
    receipt = next(r for r in repaired["receipts"] if r["executed"])
    assert receipt["before_digest"] != receipt["after_digest"]
    assert receipt["verification"]["tests_passed"] == 4
    pending = results["repair-needs-approval"]
    assert pending["status"] == "needs_approval"
    assert not any(r["executed"] for r in pending["receipts"])


def test_reverse_completion_order_keeps_same_accepted_answer(tmp_path):
    from chapter18.cases import run_case
    root = fixture_repo(tmp_path)
    first = run_case("parallel-separated", root=root, workdir=root / "chapter18/.runs/first")
    second = run_case("parallel-separated", root=root, workdir=root / "chapter18/.runs/second", order=("support", "edition", "product"))
    assert first["status"] == second["status"] == "answer"
    assert first["evidence_verdict"] == second["evidence_verdict"]
    assert first["metrics"] == second["metrics"]


def test_system_uses_supplied_packet_and_never_auto_approves(tmp_path):
    from chapter18.system import run_system
    from chapter18.tests.helpers import packet
    root = fixture_repo(tmp_path)
    p = packet(allowed_sources=frozenset(), output_requirements=("sharing",))
    result = run_system("knowledge", p, root=root, workdir=root / "chapter18/.runs/system")
    assert result["status"] in {"blocked", "unknown"}


def test_final_acceptance_reloads_source_bytes_and_permission(tmp_path):
    import json
    from chapter18.system import Session, new_packet
    root = fixture_repo(tmp_path)
    session = Session(root, root / "chapter18/.runs/revoke", new_packet())
    session.run_workers((session.research("expert", "public-current", "sharing"),))
    index_path = root / "chapter18/fixtures/knowledge.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index[0]["principals"] = ["staff"]
    index_path.write_text(json.dumps(index), encoding="utf-8")
    result = session.result("kb-revoked", 5)
    assert result["status"] == "blocked"
    assert "支持工作区共享。共享前需由工作区管理员配置成员范围。" not in str(result)


def test_changed_source_after_worker_return_cannot_become_answer(tmp_path):
    from chapter18.system import Session, new_packet
    root = fixture_repo(tmp_path)
    session = Session(root, root / "chapter18/.runs/changed", new_packet())
    session.run_workers((session.research("expert", "public-current", "sharing"),))
    path = root / "chapter18/fixtures/knowledge/public-current.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n更正记录\n", encoding="utf-8")
    assert session.result("kb-changed", 5)["status"] == "unknown"
