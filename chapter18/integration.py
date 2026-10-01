from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from .budget import BudgetLedger
from .contracts import ActionReceipt, Event, PatchProposal, RunState, TaskPacket, Verification
from .fixtures import checked_path
from .verifier import verify_workspace
from .workspace import source_path


class IntegrationGateway:
    def __init__(self, workspace: Path, packet: TaskPacket, state: RunState, ledger: BudgetLedger, *, fixture_root: Path):
        self.workspace, self.packet, self.state, self.ledger, self.fixture_root = workspace, packet, state, ledger, fixture_root
        checked_path(fixture_root.parents[2], workspace, prefixes=("chapter18/.runs",))

    def _record(self, kind: str, **data) -> None:
        task = self.packet.task_id
        previous = [e for e in self.state.events if e.task_id == task]
        self.state.events += (Event(f"{task}:e{len(previous) + 1}", kind, task, self.state.attempts.get(task, ""),
            previous[-1].event_id if previous else None, tuple(sorted(data.items()))),)

    def _deny(self, proposal, status, reason):
        receipt = ActionReceipt(proposal.proposal_id, proposal.action_id, proposal.path, tuple(sorted(self.packet.allowed_writes)),
                                None, None, False, None, status, reason)
        self.state.receipts += (receipt,)
        if self.state.status not in {"stopped", "verified", "answer"}:
            self.state.status, self.state.reason_code = status, reason
        self._record("action_refused", action_id=proposal.action_id, reason=reason)
        return receipt

    def apply(self, proposal: PatchProposal, *, approved: bool) -> ActionReceipt:
        task = self.state.tasks.get(proposal.task_id)
        if (task is None or task.principal != self.state.principal or proposal.path not in task.allowed_writes
                or proposal.path not in self.packet.allowed_writes):
            return self._deny(proposal, "blocked", "write_scope_or_identity")
        try:
            target = source_path(self.workspace, proposal.path)
        except ValueError:
            return self._deny(proposal, "blocked", "unsafe_path")
        digest = sha256(proposal.replacement.encode("utf-8")).hexdigest()
        previous = next((r for r in self.state.receipts if r.action_id == proposal.action_id and r.executed), None)
        if previous:
            if (previous.path, previous.before_digest, previous.after_digest) != (proposal.path, proposal.before_digest, digest):
                return self._deny(proposal, "blocked", "action_id_conflict")
            self._record("action_replayed", action_id=proposal.action_id)
            return previous
        if self.state.status in {"stopped", "verified", "answer"}:
            return self._deny(proposal, "stopped", "run_closed")
        if not approved:
            self.state.pending_approval = proposal.action_id
            return self._deny(proposal, "needs_approval", "approval_required")
        before = sha256(target.read_bytes()).hexdigest()
        if before != proposal.before_digest:
            return self._deny(proposal, "conflict", "stale_patch")
        if not self.ledger.charge(purpose="worker", task_id=proposal.task_id):
            return self._deny(proposal, "stopped", self.ledger.last_refusal)
        target.write_bytes(proposal.replacement.encode("utf-8"))
        receipt = ActionReceipt(proposal.proposal_id, proposal.action_id, proposal.path, tuple(sorted(self.packet.allowed_writes)),
                                before, digest, True, None, "unknown", "executed_not_yet_verified")
        self.state.receipts += (receipt,)
        self.state.tool_calls = self.ledger.used
        self.state.pending_approval = None
        self.state.status, self.state.reason_code = "unknown", "executed_not_yet_verified"
        self._record("action_committed", action_id=proposal.action_id, proposal_id=proposal.proposal_id,
                     proposal_task_id=proposal.task_id, proposal_attempt_id=self.state.attempts.get(proposal.task_id, ""),
                     proposal_worker=task.worker_id, path=proposal.path, before_digest=before, after_digest=digest)
        return receipt

    def finish(self) -> Verification:
        if self.state.status == "verified":
            return next(r.verification for r in reversed(self.state.receipts) if r.executed and r.verification)
        if self.state.status in {"stopped", "conflict", "blocked", "needs_approval"}:
            return Verification(False, 0, 4, False, (), self.state.reason_code or "run_not_ready")
        if not any(r.executed for r in self.state.receipts):
            return Verification(False, 0, 4, False, (), "no_executed_proposal")
        if any(r.reason_code in {"stale_patch", "action_id_conflict"} for r in self.state.receipts):
            return Verification(False, 0, 4, False, (), "unresolved_action_conflict")
        before_calls = self.ledger.verifier_used
        verification = verify_workspace(self.workspace, fixture_root=self.fixture_root, ledger=self.ledger)
        self.state.tool_calls = self.ledger.used
        self._record("verification", calls=self.ledger.verifier_used - before_calls,
                     tests_passed=verification.tests_passed, tests_total=verification.tests_total,
                     behavior_passed=verification.behavior_passed, passed=verification.passed,
                     evidence_digest=sha256("\n".join(verification.evidence).encode()).hexdigest())
        status = "verified" if verification.passed else "unknown"
        self.state.receipts = tuple(replace(r, verification=verification, status=status,
                                          reason_code=verification.reason_code) if r.executed else r for r in self.state.receipts)
        self.state.status, self.state.reason_code = status, verification.reason_code
        self.state.acceptance = verification.evidence
        return verification
