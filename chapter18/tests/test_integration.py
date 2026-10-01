from dataclasses import replace
from hashlib import sha256
import os
import pytest
from chapter18.contracts import BudgetLimits, RunState, PatchProposal
from chapter18.budget import BudgetLedger
from chapter18.tests.helpers import fixture_repo, packet
from chapter18.fixtures import create_workspace


def setup_gateway(tmp_path):
    from chapter18.integration import IntegrationGateway
    root = fixture_repo(tmp_path)
    workspace = create_workspace(root, root / "chapter18/.runs/first/integration")
    state = RunState("manager", "public")
    p = packet()
    state.tasks[p.task_id] = p
    state.attempts[p.task_id] = "root-1"
    ledger = BudgetLedger(BudgetLimits())
    return IntegrationGateway(workspace, p, state, ledger, fixture_root=root / "chapter18/fixtures/link-checker"), workspace, state, ledger


def fix(workspace, action="write-1", path="src/linkcheck.py"):
    from chapter18.workspace import propose_patch
    text = (workspace / path).read_text(encoding="utf-8")
    replacement = text.replace("    return path\n", "    return posixpath.normpath(posixpath.join(posixpath.dirname(document), path))\n")
    return propose_patch(packet(), workspace, path=path, replacement=replacement, proposal_id=action + "-proposal", action_id=action)


def test_no_approval_and_protected_paths_never_write(tmp_path):
    gateway, workspace, state, ledger = setup_gateway(tmp_path)
    proposal = fix(workspace)
    before = (workspace / proposal.path).read_bytes()
    assert gateway.apply(proposal, approved=False).status == "needs_approval"
    assert (workspace / proposal.path).read_bytes() == before and ledger.used == 0
    bad = replace(proposal, path="tests/test_existing.py")
    assert gateway.apply(bad, approved=True).status == "blocked"
    assert state.receipts[-1].executed is False


def test_stale_second_patch_cannot_overwrite_first_commit(tmp_path):
    gateway, workspace, state, ledger = setup_gateway(tmp_path)
    first = fix(workspace)
    second = replace(first, proposal_id="p-2", action_id="write-2", replacement=first.replacement + "\n# late edit\n")
    assert gateway.apply(first, approved=True).executed
    current = (workspace / first.path).read_bytes()
    rejected = gateway.apply(second, approved=True)
    assert rejected.status == "conflict" and rejected.reason_code == "stale_patch"
    assert (workspace / first.path).read_bytes() == current
    assert state.receipts[0].before_digest != state.receipts[0].after_digest


def test_duplicate_action_replays_once_and_same_id_different_content_is_denied(tmp_path):
    gateway, workspace, state, ledger = setup_gateway(tmp_path)
    proposal = fix(workspace)
    first = gateway.apply(proposal, approved=True)
    assert gateway.apply(proposal, approved=True) == first
    assert ledger.worker_used == 1
    assert sum(r.executed for r in state.receipts) == 1
    assert gateway.apply(replace(proposal, replacement=proposal.replacement + "\n# conflict"), approved=True).status == "blocked"


def test_disjoint_patches_need_one_final_integrated_verification(tmp_path):
    from chapter18.workspace import propose_patch
    gateway, workspace, state, ledger = setup_gateway(tmp_path)
    assert gateway.apply(fix(workspace), approved=True).status == "unknown"
    text = (workspace / "src/policy.py").read_text(encoding="utf-8")
    p = propose_patch(packet(), workspace, path="src/policy.py", replacement=text + "\n# reviewed independently\n", proposal_id="policy-p", action_id="policy-a")
    assert gateway.apply(p, approved=True).status == "unknown"
    assert state.status != "verified"
    verification = gateway.finish()
    assert verification.passed and verification.tests_passed == verification.tests_total == 4
    assert verification.behavior_passed and ledger.verifier_used == 2
    assert ledger.used == 4 and state.status == "verified"


def test_cancel_after_commit_retains_receipt_and_never_becomes_verified(tmp_path):
    gateway, workspace, state, ledger = setup_gateway(tmp_path)
    receipt = gateway.apply(fix(workspace), approved=True)
    state.status, state.reason_code = "stopped", "cancelled_after_commit"
    assert not gateway.finish().passed
    assert state.receipts[0].executed and state.receipts[0].after_digest == receipt.after_digest
    assert state.status == "stopped"


def test_reparse_source_is_denied(tmp_path):
    gateway, workspace, state, ledger = setup_gateway(tmp_path)
    other = workspace.parent / "outside.py"
    other.write_text("preserve", encoding="utf-8")
    link = workspace / "src/linked.py"
    try:
        os.symlink(other, link)
    except OSError as exc:
        pytest.skip(str(exc))
    proposal = PatchProposal("symlink-p", "symlink-a", packet().task_id, "src/linked.py", sha256(b"preserve").hexdigest(), "overwrite")
    gateway.packet = replace(gateway.packet, allowed_writes=frozenset({"src/linked.py"}))
    assert gateway.apply(proposal, approved=True).status == "blocked"
    assert other.read_text() == "preserve"


def test_finished_verification_and_receipt_replay_do_not_spend_new_quota(tmp_path):
    gateway, workspace, state, ledger = setup_gateway(tmp_path)
    proposal = fix(workspace)
    gateway.apply(proposal, approved=True)
    checked = gateway.finish()
    assert checked.passed
    assert gateway.finish() == checked
    assert gateway.apply(proposal, approved=True).status == "verified"
    assert ledger.used == 3 and state.status == "verified"
