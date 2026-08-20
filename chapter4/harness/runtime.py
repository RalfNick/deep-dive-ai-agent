from __future__ import annotations

from pathlib import Path

from .contracts import (
    DecisionKind,
    RunOutcome,
    RunState,
    RunStatus,
    ToolCall,
    ToolResult,
    VerificationEvidence,
)
from .environment import RepairEnvironment
from .gateway import ActionGateway, GatewayDecisionKind
from .path_guard import PathGuardViolation, WorkspacePathGuard
from .policy import ScriptedModel, canonical_repair_script
from .recorder import EventRecorder
from .state import ActionReceiptStore, JsonCheckpointStore
from .verifier import TestVerifier


class SimulatedCrashAfterReceipt(RuntimeError):
    """Failure injection for the receipt-written/checkpoint-stale window."""


class InlineLoop:
    """A closed loop that intentionally fuses execution and completion."""

    def __init__(self, max_steps: int = 10) -> None:
        self.max_steps = max_steps

    def run(
        self,
        model: ScriptedModel,
        environment: RepairEnvironment,
    ) -> RunOutcome:
        state = RunState(run_id="inline-loop")
        recorder = EventRecorder(state.run_id)
        path_guard = WorkspacePathGuard(environment.root)
        for _ in range(self.max_steps):
            decision = model.next_decision(state)
            state.decision_index += 1
            state.step += 1
            if decision.kind == DecisionKind.FINAL:
                state.final_message = decision.message
                state.status = RunStatus.COMPLETED
                recorder.emit(
                    "completed",
                    cause_id=None,
                    basis="model_final_message",
                )
                state.events = recorder.events
                return RunOutcome(state, tuple(recorder.events))
            assert decision.call is not None
            call_event = recorder.emit(
                "tool_call",
                cause_id=None,
                call_id=decision.call.call_id,
                action_id=decision.call.action_id,
                tool=decision.call.name,
            )
            result = _execute(environment, path_guard, decision.call)
            recorder.emit(
                "tool_result",
                cause_id=call_event.event_id,
                call_id=result.call_id,
                action_id=result.action_id,
                ok=result.ok,
                error_type=result.error_type,
            )
        state.status = RunStatus.STOPPED
        state.failure_code = "max_steps"
        recorder.emit("stopped", cause_id=None, failure_code="max_steps")
        state.events = recorder.events
        return RunOutcome(state, tuple(recorder.events))


class HarnessRuntime:
    def __init__(
        self,
        data_root: Path,
        *,
        gateway: ActionGateway | None = None,
        verifier: TestVerifier | None = None,
        max_steps: int = 10,
        max_retries: int = 1,
        crash_after_receipt_action_ids: frozenset[str] = frozenset(),
    ) -> None:
        self.checkpoints = JsonCheckpointStore(data_root)
        self.receipts = ActionReceiptStore(data_root)
        self.gateway = gateway or ActionGateway()
        self.verifier = verifier or TestVerifier()
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.crash_after_receipt_action_ids = crash_after_receipt_action_ids

    def start(
        self,
        run_id: str,
        model: ScriptedModel,
        environment: RepairEnvironment,
    ) -> RunOutcome:
        state = RunState(run_id=run_id)
        recorder = EventRecorder(run_id)
        recorder.emit("run_started", cause_id=None)
        return self._drive(state, recorder, model, environment)

    def resume(
        self,
        run_id: str,
        *,
        approved: bool,
        environment: RepairEnvironment,
        model: ScriptedModel | None = None,
    ) -> RunOutcome:
        state = self.checkpoints.load(run_id)
        recorder = EventRecorder(run_id, state.events)
        if state.status != RunStatus.WAITING_APPROVAL:
            return RunOutcome(state, tuple(recorder.events))

        resumed = recorder.emit("run_resumed", cause_id=None)
        if not approved:
            state.status = RunStatus.CANCELLED
            state.failure_code = "approval_rejected"
            recorder.emit(
                "approval_rejected",
                cause_id=resumed.event_id,
            )
            recorder.emit("cancelled", cause_id=resumed.event_id)
            return self._save_outcome(state, recorder)

        approval = recorder.emit(
            "approval_granted",
            cause_id=resumed.event_id,
        )
        call = state.pending_call
        if call is None:
            state.status = RunStatus.FAILED
            state.failure_code = "missing_pending_call"
            recorder.emit("failed", cause_id=approval.event_id)
            return self._save_outcome(state, recorder)

        current_digest = environment.state_digest()
        existing_receipt = self.receipts.get(call.action_id)
        receipt_matches_current = bool(
            existing_receipt is not None
            and existing_receipt.side_effect_applied
            and existing_receipt.state_digest == current_digest
        )
        if (
            not receipt_matches_current
            and state.state_digest != current_digest
        ):
            state.status = RunStatus.APPROVAL_STALE
            state.failure_code = "approval_stale"
            recorder.emit(
                "approval_stale",
                cause_id=approval.event_id,
                action_id=call.action_id,
                expected_state_digest=state.state_digest,
                current_state_digest=current_digest,
            )
            return self._save_outcome(state, recorder)

        call_event = next(
            event for event in reversed(recorder.events)
            if event.kind == "tool_call"
            and event.data.get("call_id") == call.call_id
        )
        result = self._execute_with_receipt(
            call,
            call_event.event_id,
            recorder,
            environment,
        )
        state.pending_call = None
        if not result.ok:
            state.status = RunStatus.FAILED
            state.failure_code = result.error_type
            recorder.emit(
                "failed",
                cause_id=approval.event_id,
                failure_code=result.error_type,
            )
            return self._save_outcome(state, recorder)

        state.status = RunStatus.RUNNING
        actual_model = model or ScriptedModel(canonical_repair_script())
        return self._drive(state, recorder, actual_model, environment)

    def _drive(
        self,
        state: RunState,
        recorder: EventRecorder,
        model: ScriptedModel,
        environment: RepairEnvironment,
    ) -> RunOutcome:
        while state.step < self.max_steps:
            decision = model.next_decision(state)
            state.decision_index += 1
            state.step += 1
            decision_event = recorder.emit(
                "model_decision",
                cause_id=None,
                decision=decision.kind.value,
            )

            if decision.kind == DecisionKind.FINAL:
                return self._verify_final(
                    state,
                    recorder,
                    decision.message,
                    decision_event.event_id,
                    environment,
                )

            assert decision.call is not None
            call = decision.call
            call_event = recorder.emit(
                "tool_call",
                cause_id=decision_event.event_id,
                call_id=call.call_id,
                action_id=call.action_id,
                tool=call.name,
            )
            gateway_decision = self.gateway.evaluate(call)
            policy_event = recorder.emit(
                "policy_decision",
                cause_id=call_event.event_id,
                decision=gateway_decision.kind.value,
                reason=gateway_decision.reason,
            )
            if gateway_decision.kind == GatewayDecisionKind.DENY:
                state.status = RunStatus.FAILED
                state.failure_code = gateway_decision.reason
                recorder.emit(
                    "failed",
                    cause_id=policy_event.event_id,
                    failure_code=gateway_decision.reason,
                )
                return self._save_outcome(state, recorder)
            if gateway_decision.kind == GatewayDecisionKind.ASK:
                state.status = RunStatus.WAITING_APPROVAL
                state.pending_call = call
                state.state_digest = environment.state_digest()
                state.events = list(recorder.events)
                self.checkpoints.save(state)
                checkpoint = recorder.emit(
                    "checkpoint_saved",
                    cause_id=policy_event.event_id,
                )
                approval = recorder.emit(
                    "approval_requested",
                    cause_id=checkpoint.event_id,
                    action_id=call.action_id,
                    state_digest=state.state_digest,
                )
                recorder.emit(
                    "waiting_approval",
                    cause_id=approval.event_id,
                )
                return self._save_outcome(state, recorder)

            result = self._execute_with_receipt(
                call,
                call_event.event_id,
                recorder,
                environment,
            )
            if not result.ok:
                state.status = RunStatus.FAILED
                state.failure_code = result.error_type
                recorder.emit(
                    "failed",
                    cause_id=call_event.event_id,
                    failure_code=result.error_type,
                )
                return self._save_outcome(state, recorder)

        state.status = RunStatus.STOPPED
        state.failure_code = "max_steps"
        recorder.emit("stopped", cause_id=None, failure_code="max_steps")
        return self._save_outcome(state, recorder)

    def _execute_with_receipt(
        self,
        call: ToolCall,
        call_event_id: str,
        recorder: EventRecorder,
        environment: RepairEnvironment,
    ) -> ToolResult:
        existing = self.receipts.get(call.action_id)
        if existing is not None and existing.side_effect_applied:
            recorder.emit(
                "action_deduplicated",
                cause_id=call_event_id,
                action_id=call.action_id,
            )
            return existing

        for attempt in range(1, self.max_retries + 2):
            result = _execute(
                environment,
                WorkspacePathGuard(environment.root),
                call,
            )
            result_event = recorder.emit(
                "tool_result",
                cause_id=call_event_id,
                call_id=result.call_id,
                action_id=result.action_id,
                ok=result.ok,
                error_type=result.error_type,
                retryable=result.retryable,
                attempt=attempt,
                state_digest=result.state_digest,
            )
            if result.ok and result.side_effect_applied:
                self.receipts.record(call.action_id, result)
                if call.action_id in self.crash_after_receipt_action_ids:
                    raise SimulatedCrashAfterReceipt(
                        f"simulated crash after receipt: {call.action_id}"
                    )
                recorder.emit(
                    "action_committed",
                    cause_id=result_event.event_id,
                    action_id=call.action_id,
                )
            if result.ok or not result.retryable:
                return result
            if attempt <= self.max_retries:
                recorder.emit(
                    "retry_scheduled",
                    cause_id=result_event.event_id,
                    action_id=call.action_id,
                    next_attempt=attempt + 1,
                )
        return result

    def _verify_final(
        self,
        state: RunState,
        recorder: EventRecorder,
        message: str,
        cause_id: str,
        environment: RepairEnvironment,
    ) -> RunOutcome:
        state.final_message = message
        candidate = recorder.emit(
            "final_candidate",
            cause_id=cause_id,
            message=message,
        )
        state.status = RunStatus.VERIFYING
        verification_started = recorder.emit(
            "verification_started",
            cause_id=candidate.event_id,
            status=state.status.value,
        )
        evidence = self.verifier.verify(environment)
        verification = recorder.emit(
            "verification",
            cause_id=verification_started.event_id,
            accepted=evidence.accepted,
            state_digest=evidence.state_digest,
            test_exit_code=evidence.test_exit_code,
        )
        state.state_digest = evidence.state_digest
        if evidence.accepted:
            state.status = RunStatus.COMPLETED
            recorder.emit("completed", cause_id=verification.event_id)
        else:
            state.status = RunStatus.FAILED_VERIFICATION
            state.failure_code = "verification_rejected"
            recorder.emit(
                "failed_verification",
                cause_id=verification.event_id,
            )
        return self._save_outcome(state, recorder, evidence)

    def _save_outcome(
        self,
        state: RunState,
        recorder: EventRecorder,
        evidence: VerificationEvidence | None = None,
    ) -> RunOutcome:
        state.events = list(recorder.events)
        self.checkpoints.save(state)
        return RunOutcome(state, tuple(recorder.events), evidence)


def _execute(
    environment: RepairEnvironment,
    path_guard: WorkspacePathGuard,
    call: ToolCall,
) -> ToolResult:
    try:
        resolved = None
        if "path" in call.arguments:
            resolved = path_guard.resolve(
                str(call.arguments["path"]),
                for_write=call.name == "apply_patch",
            )
        return environment.execute(call, resolved)
    except PathGuardViolation:
        return ToolResult(
            call_id=call.call_id,
            action_id=call.action_id,
            ok=False,
            error_type="path_guard_violation",
        )
