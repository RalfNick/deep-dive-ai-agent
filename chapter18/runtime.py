from dataclasses import replace
from typing import Callable

from .budget import BudgetLedger
from .contracts import ContextSnapshot, Event, RunState, TaskPacket, ToolCall, ToolOutcome, WorkerObservation, WorkerResult, validate_packet
from .policy import DecisionPolicy, ScriptedPolicy


class TeamRuntime:
    def __init__(self, state: RunState, ledger: BudgetLedger,
                 executor: Callable[[TaskPacket, ToolCall], ToolOutcome]):
        self.state, self.ledger, self.executor = state, ledger, executor
        self.observations: dict[str, WorkerObservation] = {}
        self._policies: dict[str, DecisionPolicy] = {}
        self._decisions: dict[str, int] = {}
        self._calls: dict[str, int] = {}
        self._call_outcomes: dict[tuple[str, str], tuple[ToolCall, ToolOutcome]] = {}
        self._finished: set[str] = set()

    def record(self, kind: str, task_id: str, **data) -> None:
        prior = [e for e in self.state.events if e.task_id == task_id]
        event = Event(f"{task_id}:e{len(prior) + 1}", kind, task_id, self.state.attempts.get(task_id, ""),
                      prior[-1].event_id if prior else None, tuple(sorted(data.items())))
        self.state.events += (event,)

    def start(self, packet: TaskPacket, policy: DecisionPolicy, *, attempt_id: str, context: ContextSnapshot | None = None) -> None:
        if self.state.status == "stopped" or packet.task_id in self.state.tasks or not attempt_id:
            raise ValueError("stopped, duplicate task or missing attempt")
        parent = self.state.tasks.get(packet.parent_id) if packet.parent_id else None
        if packet.parent_id and parent is None:
            raise ValueError("parent task missing")
        validate_packet(packet, parent)
        if context and (context.task_id, context.principal, context.target_version) != (packet.task_id, packet.principal, packet.target_version):
            raise ValueError("context identity mismatch")
        if packet.principal != self.state.principal or packet.target_version != self.state.shared_version:
            raise ValueError("run identity/version mismatch")
        active_children = sum(p.parent_id is not None and key not in self._finished for key, p in self.state.tasks.items())
        if packet.parent_id and active_children >= self.ledger.limits.inflight:
            raise ValueError("inflight limit")
        self.state.tasks[packet.task_id] = packet
        self.state.attempts[packet.task_id] = attempt_id
        self._policies[packet.task_id] = policy
        self._decisions[packet.task_id] = self._calls[packet.task_id] = 0
        self.observations[packet.task_id] = WorkerObservation(context=context)
        self.record("task_started", packet.task_id, worker=packet.worker_id, parent=packet.parent_id)

    def accept_result(self, result: WorkerResult) -> bool:
        packet = self.state.tasks.get(result.task_id)
        if (self.state.status == "stopped" or packet is None or result.task_id in self._finished
                or self.state.attempts.get(result.task_id) != result.attempt_id or packet.worker_id != result.worker_id):
            if packet:
                self.record("result_rejected", result.task_id, reason="late_duplicate_or_identity")
            return False
        result = replace(result, decisions=self._decisions[result.task_id], tool_calls=self._calls[result.task_id])
        self.state.results += (result,)
        self._finished.add(result.task_id)
        self.record("result_accepted", result.task_id, worker_state=result.state)
        return True

    def step(self, task_id: str) -> None:
        if self.state.status == "stopped" or task_id in self._finished:
            return
        packet = self.state.tasks[task_id]
        if self._decisions[task_id] >= packet.limits.worker_decisions:
            self.cancel("worker_decision_limit")
            return
        try:
            decision = self._policies[task_id].next(packet, self.observations[task_id])
        except StopIteration:
            self.accept_result(WorkerResult(task_id, self.state.attempts[task_id], packet.worker_id, "unknown",
                                           missing=packet.output_requirements))
            return
        self._decisions[task_id] += 1
        self.record("decision", task_id, decision_kind=decision.kind)
        if decision.kind == "result":
            self.accept_result(decision.result)
        elif decision.kind == "handoff":
            self.handoff(decision.next_controller, task_id=task_id)
        elif decision.kind == "delegate":
            try:
                if decision.packet.parent_id != task_id:
                    raise ValueError("delegation parent mismatch")
                self.start(decision.packet, ScriptedPolicy(()), attempt_id=decision.packet.task_id + "-1")
            except ValueError:
                self.record("policy_refused", task_id, reason="scope_or_depth_or_inflight")
        else:
            self._run_tool(packet, decision.call)

    def _run_tool(self, packet: TaskPacket, call: ToolCall) -> None:
        task_id = packet.task_id
        key = (task_id, call.call_id)
        cached = self._call_outcomes.get(key)
        if cached:
            if cached[0] != call:
                self.cancel("call_id_conflict")
                return
            outcome = cached[1]
            self.record("call_replayed", task_id, call_id=call.call_id)
        elif call.tool not in packet.allowed_tools:
            outcome = ToolOutcome(call.call_id, "denied", (("reason", "tool_not_allowed"),))
            self.record("policy_refused", task_id, call_id=call.call_id, reason="tool_not_allowed")
        else:
            for attempt in range(packet.limits.extra_retries + 1):
                if not self.ledger.charge(purpose="worker"):
                    self.cancel("global_budget_exhausted")
                    return
                self._calls[task_id] += 1
                self.state.tool_calls = self.ledger.used
                outcome = self.executor(packet, call)
                if outcome.call_id != call.call_id:
                    self.cancel("tool_result_identity_mismatch")
                    return
                self.record("tool_returned", task_id, call_id=call.call_id, tool=call.tool,
                            outcome=outcome.status, attempt=attempt + 1)
                if outcome.status != "transient_error":
                    break
            self._call_outcomes[key] = (call, outcome)
            if outcome.status == "denied":
                self.record("policy_refused", task_id, call_id=call.call_id, reason="source_scope")
        previous = self.observations[task_id]
        self.observations[task_id] = replace(previous, outcomes=previous.outcomes + (outcome,))
        # Retry outcomes remain visible; counters are not invented by the policy.
        retries = [e for e in self.state.events if e.task_id == task_id and e.kind == "tool_returned"
                   and dict(e.data).get("call_id") == call.call_id]
        if len(retries) > 1 and not cached:
            self.observations[task_id] = replace(self.observations[task_id],
                outcomes=previous.outcomes + tuple(ToolOutcome(call.call_id, str(dict(e.data)["outcome"])) for e in retries[:-1]) + (outcome,))
        if outcome.status in {"timeout", "permanent_error", "transient_error", "denied"}:
            self.accept_result(WorkerResult(task_id, self.state.attempts[task_id], packet.worker_id,
                                           "failed" if outcome.status != "denied" else "unknown", missing=packet.output_requirements))

    def handoff(self, target: str, *, task_id: str) -> bool:
        if self.state.status == "stopped":
            return False
        if target not in {p.worker_id for p in self.state.tasks.values()}:
            self.record("policy_refused", task_id, reason="unknown_controller")
            return False
        if self.state.handoffs >= self.ledger.limits.handoffs:
            self.cancel("handoff_limit")
            return False
        self.state.handoffs += 1
        self.state.controller = target
        self.record("handoff", task_id, controller=target)
        return True

    def cancel(self, reason: str) -> None:
        self.state.status, self.state.reason_code = "stopped", reason
        root = next(iter(self.state.tasks), "run")
        self.record("stopped", root, reason=reason)
