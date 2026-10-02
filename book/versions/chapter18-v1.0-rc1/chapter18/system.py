"""Two minimal business paths sharing scopes, runtime, receipts and acceptance."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from .budget import BudgetLedger
from .context import assemble_context, eligible
from .contracts import BudgetLimits, CaseResult, ContextSnapshot, Decision, RunState, TaskPacket, ToolCall, ToolOutcome, WorkerResult
from .evidence import check_claims, claim_from_outcome, knowledge_tool
from .fixtures import checked_path, create_workspace, load_sources
from .integration import IntegrationGateway
from .policy import ScriptedPolicy
from .runtime import TeamRuntime
from .workspace import propose_patch, repair_text, snapshot_workspace, source_path


def encode(value):
    if is_dataclass(value):
        return encode(asdict(value))
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return [encode(v) for v in sorted(value)]
    if value is None or type(value) in {str, int, bool}:
        return value
    raise ValueError("non-canonical value")


def new_packet(**changes) -> TaskPacket:
    return replace(TaskPacket("root", None, "manager", "查证星舟工作台当前问答", "public", "v2", ("sharing",),
        frozenset({"public-current", "public-old", "parallel-product", "parallel-support", "conflict-a", "conflict-b"}),
        frozenset({"knowledge", "read", "propose"}), frozenset({"src/linkcheck.py", "src/policy.py"}),
        ("sharing",), (), BudgetLimits(), 0), **changes)


class ObservedScriptedPolicy(ScriptedPolicy):
    """Fixed read/propose steps, then a result constructed from actual observations."""
    def __init__(self, calls: tuple[ToolCall, ...], attempt_id: str):
        super().__init__(tuple(Decision("tool", call=c) for c in calls))
        self.attempt_id, self.returned = attempt_id, False

    def next(self, packet, observation):
        if self.position < len(self.script):
            return super().next(packet, observation)
        if self.returned:
            raise StopIteration
        self.returned = True
        successful = [o for o in observation.outcomes if o.status == "ok"]
        claims = tuple(claim_from_outcome(o) for o in successful if "source_id" in dict(o.data))
        patches = tuple(str(dict(o.data)["proposal_id"]) for o in successful if "proposal_id" in dict(o.data))
        covered = {c.key for c in claims} | ({"repair_correct"} if patches else set())
        missing = tuple(k for k in packet.output_requirements if k not in covered)
        result = WorkerResult(packet.task_id, self.attempt_id, packet.worker_id, "unknown" if missing else "done", claims, missing, patches)
        return Decision("result", result=result)


def derive_metrics(case: CaseResult) -> dict[str, int]:
    events = case["trajectory"]
    packets = case["input_proof"]["packets"]
    root = next(p for p in packets if p["parent_id"] is None)
    verdict = case.get("evidence_verdict", {"claims": [], "distinct_sources": []})
    values = {}
    for claim in verdict["claims"]:
        values.setdefault(claim["key"], set()).add(claim["value"])
    covered = sum(len(values.get(key, ())) == 1 for key in root["output_requirements"])
    if "repair_correct" in root["output_requirements"]:
        covered = int(case["status"] == "verified")
    goals = [(tuple(p["output_requirements"]), tuple(p["input_refs"]), tuple(p["allowed_sources"]),
              tuple(p["allowed_writes"]) if "repair_correct" in p["output_requirements"] else ())
             for p in packets if p["parent_id"] is not None]
    committed = [e["data"]["action_id"] for e in events if e["kind"] == "action_committed"]
    tool_calls = sum(e["kind"] in {"tool_returned", "action_committed"} for e in events)
    verifier_calls = sum(e["data"]["calls"] for e in events if e["kind"] == "verification")
    tool_calls += verifier_calls
    violations = sum(r["executed"] and (r["path"] not in r["allowed_writes"] or not r["path"].startswith("src/")) for r in case["receipts"])
    return {"coverage_numerator": covered, "coverage_denominator": len(root["output_requirements"]),
        "duplicate_tasks": len(goals) - len(set(goals)), "distinct_eligible_sources": len(verdict["distinct_sources"]),
        "unresolved_conflicts": sum(len(v) > 1 for v in values.values()) + sum(e["kind"] == "action_refused" and e["data"]["reason"] == "stale_patch" for e in events),
        "policy_refusals": sum(e["kind"] == "policy_refused" or (e["kind"] == "action_refused" and e["data"]["reason"] not in {"approval_required", "stale_patch"}) for e in events),
        "stale_patch_refusals": sum(e["kind"] == "action_refused" and e["data"]["reason"] == "stale_patch" for e in events),
        "duplicate_writes": len(committed) - len(set(committed)), "decisions": sum(e["kind"] == "decision" for e in events),
        "tool_calls": tool_calls, "budget_limit": root["limits"]["tool_calls"], "budget_remaining": root["limits"]["tool_calls"] - tool_calls,
        "verifier_calls": verifier_calls, "security_violations": violations}


class Session:
    def __init__(self, root: Path, workdir: Path, packet: TaskPacket, *, timeout_worker: str | None = None):
        self.root = root
        self.workdir = checked_path(root, workdir, prefixes=("chapter18/.runs",), new=True)
        self.workdir.mkdir(parents=True)
        self.sources = load_sources(root)
        self.contexts: dict[str, ContextSnapshot] = {}
        self.proposals = {}
        self.snapshots = {}
        self.timeout_worker = timeout_worker
        self.packet = packet
        self.runtime = TeamRuntime(RunState(packet.worker_id, packet.principal, shared_version=packet.target_version), BudgetLedger(packet.limits), self.execute)
        context = assemble_context(packet, self.sources)
        self.contexts[packet.task_id] = context
        self.runtime.start(packet, ScriptedPolicy(()), attempt_id="root-a1", context=context)
        self.integration = None

    def execute(self, packet: TaskPacket, call: ToolCall) -> ToolOutcome:
        if packet.worker_id == self.timeout_worker:
            return ToolOutcome(call.call_id, "timeout", (("reason", "injected_logical_timeout"),))
        if call.tool == "knowledge":
            return knowledge_tool(packet, call, self.sources)
        args = dict(call.arguments)
        path = args.get("path", "src/linkcheck.py")
        if path not in packet.allowed_writes or packet.worker_id not in self.snapshots:
            return ToolOutcome(call.call_id, "denied", (("reason", "file_scope"),))
        workspace = self.snapshots[packet.worker_id]
        if call.tool == "read":
            data = source_path(workspace, path).read_bytes()
            return ToolOutcome(call.call_id, "ok", (("path", path), ("digest", sha256(data).hexdigest()), ("text", data.decode("utf-8"))))
        if call.tool == "propose":
            observed = self.runtime.observations[packet.task_id].outcomes
            read = next((o for o in reversed(observed) if dict(o.data).get("path") == path and "text" in dict(o.data)), None)
            if read is None:
                return ToolOutcome(call.call_id, "permanent_error", (("reason", "read_before_propose"),))
            text = str(dict(read.data)["text"])
            replacement = repair_text(text) if path == "src/linkcheck.py" else text + "\n# scope reviewed independently\n"
            if args.get("variant") == "late":
                replacement += "\n# proposal from another worker\n"
            proposal = propose_patch(packet, workspace, path=path, replacement=replacement,
                                     proposal_id=packet.task_id + "-proposal", action_id=packet.task_id + "-action")
            self.proposals[proposal.proposal_id] = proposal
            return ToolOutcome(call.call_id, "ok", (("proposal_id", proposal.proposal_id), ("path", path), ("before_digest", proposal.before_digest)))
        return ToolOutcome(call.call_id, "denied", (("reason", "unknown_tool"),))

    def research(self, worker: str, source: str, key: str, *, missing_context: bool = False):
        p = replace(self.packet, task_id=worker, parent_id=self.packet.task_id, worker_id=worker, depth=1,
                    input_refs=() if missing_context else (key,), allowed_sources=frozenset({source}), output_requirements=(key,))
        context = assemble_context(p, self.sources)
        self.contexts[p.task_id] = context
        attempt = worker + "-a1"
        self.runtime.start(p, ObservedScriptedPolicy((ToolCall(worker + "-read", "knowledge", (("source_id", source), ("key", key))),), attempt), attempt_id=attempt, context=context)
        return p.task_id

    def run_workers(self, order):
        for task in order:
            for _ in range(self.packet.limits.worker_decisions):
                if self.runtime.state.status == "stopped" or any(r.task_id == task for r in self.runtime.state.results):
                    break
                self.runtime.step(task)

    def prepare_code(self):
        self.integration = create_workspace(self.root, self.workdir / "integration")
        hashes = tuple((path, sha256((self.integration / path).read_bytes()).hexdigest()) for path in sorted(self.packet.allowed_writes))
        self.packet = replace(self.packet, base_hashes=hashes)
        self.runtime.state.tasks[self.packet.task_id] = self.packet

    def coder(self, worker: str, path: str, *, late: bool = False):
        workspace = snapshot_workspace(self.root, self.integration, self.workdir / worker)
        self.snapshots[worker] = workspace
        p = replace(self.packet, task_id=worker, parent_id=self.packet.task_id, worker_id=worker, depth=1,
                    allowed_writes=frozenset({path}), base_hashes=tuple(x for x in self.packet.base_hashes if x[0] == path))
        sent = ((path, (workspace / path).read_text(encoding="utf-8")),)
        payload = json.dumps(sent, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        context = ContextSnapshot(p.task_id, p.principal, p.target_version, sent, sha256(payload).hexdigest(), p.base_hashes)
        self.contexts[p.task_id] = context
        calls = (ToolCall(worker + "-read", "read", (("path", path),)),
                 ToolCall(worker + "-propose", "propose", (("path", path), ("variant", "late" if late else "normal"))))
        self.runtime.start(p, ObservedScriptedPolicy(calls, worker + "-a1"), attempt_id=worker + "-a1", context=context)
        return p.task_id

    def gateway(self):
        return IntegrationGateway(self.integration, self.packet, self.runtime.state, self.runtime.ledger,
                                  fixture_root=self.root / "chapter18/fixtures/link-checker")

    def result(self, case_id: str, group: int, **extra) -> CaseResult:
        state = self.runtime.state
        claims = tuple(c for r in sorted(state.results, key=lambda r: r.task_id) for c in r.claims)
        current_sources = load_sources(self.root)
        current_index = {s.source_id: s for s in current_sources}
        verdict = check_claims(self.packet, claims, current_sources)
        is_repair = "repair_correct" in self.packet.output_requirements
        if state.status is None or (not is_repair and state.status != "stopped"):
            refused = any(e.kind == "policy_refused" for e in state.events)
            state.status = "blocked" if refused and not verdict.claims else verdict.status
            state.reason_code = "policy_refused" if state.status == "blocked" else verdict.reason_code
        if state.status == "answer":
            state.acceptance = tuple(f"source:{ref.source_id}:{ref.digest}" for c in verdict.claims for ref in c.evidence)
        elif not is_repair:
            state.acceptance = ()
        def public_ref(ref):
            doc = current_index.get(ref.source_id)
            return bool(doc and self.packet.principal in doc.principals and ref.source_id in self.packet.allowed_sources)
        safe_results = tuple(replace(r, claims=tuple(c for c in r.claims if all(public_ref(ref) for ref in c.evidence)))
                             for r in sorted(state.results, key=lambda r: r.task_id))
        safe_contexts = []
        for key in sorted(self.contexts):
            context = self.contexts[key]
            row = encode(context)
            sent = tuple((sid, text) for sid, text in context.sent if sid.startswith("src/") or
                         (sid in current_index and self.packet.principal in current_index[sid].principals and sid in self.packet.allowed_sources))
            row["sent"] = encode(sent)
            row["redacted"] = sent != context.sent
            safe_contexts.append(row)
        events = []
        for event in state.events:
            row = encode(event)
            row["data"] = dict(event.data)
            events.append(row)
        # task-local causal order, not invented wall-clock arrival order.
        events.sort(key=lambda e: (e["task_id"], int(e["event_id"].rsplit(":e", 1)[1])))
        result = {"case_id": case_id, "group": group, "status": state.status, "reason_code": state.reason_code,
            "controller": state.controller, "input_proof": {"packets": encode(tuple(state.tasks[k] for k in sorted(state.tasks))),
                "attempts": dict(sorted(state.attempts.items())),
                "source_digests": encode(tuple(sorted({pair for c in self.contexts.values() for pair in c.source_digests}))),
                "context_digests": safe_contexts},
            "trajectory": events, "worker_results": encode(safe_results),
            "receipts": encode(state.receipts), "acceptance": encode(state.acceptance), "evidence_verdict": encode(verdict),
            "limits": ["deterministic decision double, not model capability", "logical schedule, not measured concurrency", "trusted fixture, not OS sandbox"], **extra}
        result["metrics"] = derive_metrics(result)
        if result["metrics"]["tool_calls"] != self.runtime.ledger.used:
            raise ValueError("trajectory and global ledger disagree")
        return result


def run_system(kind: Literal["knowledge", "repair"], packet: TaskPacket, *, root: Path, workdir: Path, approved: bool = False) -> CaseResult:
    session = Session(root, workdir, packet)
    if kind == "knowledge":
        candidates = [(source.source_id, key) for key in packet.output_requirements
                      for source in sorted(session.sources, key=lambda s: s.source_id)
                      if eligible(packet, source) and key in dict(source.facts)]
        # No source-order authority rule: conflicting current evidence must survive.
        width = packet.limits.inflight
        if candidates and width == 0:
            session.runtime.record("policy_refused", packet.task_id, reason="inflight_limit")
        for start in range(0, len(candidates), max(1, width)):
            if session.runtime.state.status == "stopped" or width == 0:
                break
            workers = [session.research(f"research-{start + offset}", source, key)
                       for offset, (source, key) in enumerate(candidates[start:start + width])]
            session.run_workers(workers)
    elif kind == "repair":
        session.prepare_code()
        worker = session.coder("coder", "src/linkcheck.py")
        session.run_workers((worker,))
        gateway = session.gateway()
        accepted = {patch_id for result in session.runtime.state.results for patch_id in result.patch_ids}
        for proposal in session.proposals.values():
            if proposal.proposal_id not in accepted:
                continue
            gateway.apply(proposal, approved=approved)
        if approved:
            gateway.finish()
    else:
        raise ValueError("unsupported business path")
    return session.result("system-" + kind, 5)
