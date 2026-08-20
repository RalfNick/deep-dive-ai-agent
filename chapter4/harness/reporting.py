from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .contracts import PolicyDecision, RunStatus, ToolCall
from .environment import RepairEnvironment
from .gateway import ActionGateway
from .path_guard import WorkspacePathGuard
from .policy import FIXED_SOURCE, ScriptedModel, canonical_repair_script
from .recorder import grade_trace
from .runtime import HarnessRuntime, InlineLoop
from .verifier import TestVerifier


COMPARISON_SCOPE = (
    "separate deterministic boundary cases; not a single-variable ablation, "
    "statistical rate, model quality, or SDK ranking"
)


@dataclass(frozen=True)
class FaultCaseResult:
    case_id: str
    status: str
    failure_code: str | None
    attempts: int


@dataclass(frozen=True)
class BoundaryCaseMetrics:
    accepted: bool | None
    false_completed: bool | None
    policy_violations: int | None
    duplicate_side_effects: int | None
    recovery_succeeded: bool | None
    trace_contract_passed: bool | None
    steps: int
    simulated_cost_units: int
    sample_count: int = 1


@dataclass(frozen=True)
class BoundaryFailureMatrix:
    comparison_scope: str
    cases: dict[str, BoundaryCaseMetrics]

    def to_dict(self) -> dict[str, object]:
        return {
            "comparison_scope": self.comparison_scope,
            "cases": {
                name: asdict(metrics)
                for name, metrics in self.cases.items()
            },
        }


def run_fault_case(case_id: str) -> FaultCaseResult:
    if case_id in {"transient_once", "timeout_once", "permanent"}:
        fault = {
            "transient_once": "transient_error",
            "timeout_once": "timeout",
            "permanent": "permanent_error",
        }[case_id]
        with RepairEnvironment(
            faults={"read-price-file": (fault,)}
        ) as environment:
            outcome = HarnessRuntime(environment.parent / "run-data").start(
                f"fault-{case_id}",
                ScriptedModel(canonical_repair_script()),
                environment,
            )
            attempts = environment.attempt_count("read-price-file")
        return FaultCaseResult(
            case_id,
            outcome.state.status.value,
            outcome.state.failure_code,
            attempts,
        )

    if case_id == "cancelled":
        with RepairEnvironment() as environment:
            runtime = HarnessRuntime(environment.parent / "run-data")
            runtime.start(
                "fault-cancelled",
                ScriptedModel(canonical_repair_script()),
                environment,
            )
            outcome = runtime.resume(
                "fault-cancelled",
                approved=False,
                environment=environment,
                model=ScriptedModel(canonical_repair_script()),
            )
        return FaultCaseResult(
            case_id,
            outcome.state.status.value,
            outcome.state.failure_code,
            0,
        )

    if case_id == "step_budget":
        with RepairEnvironment() as environment:
            outcome = HarnessRuntime(
                environment.parent / "run-data", max_steps=1
            ).start(
                "fault-budget",
                ScriptedModel(canonical_repair_script()),
                environment,
            )
            attempts = environment.attempt_count("read-price-file")
        return FaultCaseResult(
            case_id,
            outcome.state.status.value,
            outcome.state.failure_code,
            attempts,
        )
    raise ValueError(f"unknown fault case: {case_id}")


def run_boundary_failure_matrix() -> BoundaryFailureMatrix:
    reference = _run_reference_run()
    cases = {
        "reference_run": reference,
        "policy_missing": _run_policy_missing(),
        "checkpoint_missing": _run_checkpoint_missing(),
        "receipt_missing": _run_receipt_missing(),
        "verifier_missing": _run_verifier_missing(),
        "trace_evidence_lost": BoundaryCaseMetrics(
            accepted=reference.accepted,
            false_completed=reference.false_completed,
            policy_violations=reference.policy_violations,
            duplicate_side_effects=reference.duplicate_side_effects,
            recovery_succeeded=reference.recovery_succeeded,
            trace_contract_passed=False,
            steps=reference.steps,
            simulated_cost_units=reference.simulated_cost_units,
        ),
    }
    return BoundaryFailureMatrix(COMPARISON_SCOPE, cases)


def write_boundary_failure_matrix(
    path: Path,
    report: BoundaryFailureMatrix,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _run_reference_run() -> BoundaryCaseMetrics:
    with RepairEnvironment() as environment:
        runtime = HarnessRuntime(environment.parent / "run-data")
        runtime.start(
            "boundary-reference",
            ScriptedModel(canonical_repair_script()),
            environment,
        )
        outcome = HarnessRuntime(environment.parent / "run-data").resume(
            "boundary-reference",
            approved=True,
            environment=environment,
            model=ScriptedModel(canonical_repair_script()),
        )
        complete = grade_trace(outcome.events).complete
        attempts = sum(
            environment.attempt_count(action_id)
            for action_id in (
                "read-price-file",
                "patch-price",
                "run-price-tests",
            )
        )
        return BoundaryCaseMetrics(
            accepted=bool(outcome.evidence and outcome.evidence.accepted),
            false_completed=False,
            policy_violations=0,
            duplicate_side_effects=max(
                0, environment.side_effect_count("patch-price") - 1
            ),
            recovery_succeeded=outcome.state.status == RunStatus.COMPLETED,
            trace_contract_passed=complete,
            steps=outcome.state.step,
            simulated_cost_units=outcome.state.step + attempts,
        )


def _run_policy_missing() -> BoundaryCaseMetrics:
    with RepairEnvironment() as environment:
        call = ToolCall(
            call_id="call-secret",
            action_id="read-secret",
            name="read_file",
            arguments={"path": ".env"},
        )
        gateway = ActionGateway(
            require_approval_for_writes=False,
            protected_paths=frozenset(),
        )
        allowed = gateway.evaluate(call).kind.value == "allow"
        result = environment.execute(
            call,
            WorkspacePathGuard(environment.root).resolve(
                ".env", for_write=False
            ),
        )
    return BoundaryCaseMetrics(
        accepted=None,
        false_completed=None,
        policy_violations=int(allowed and result.ok),
        duplicate_side_effects=None,
        recovery_succeeded=None,
        trace_contract_passed=None,
        steps=1,
        simulated_cost_units=1,
    )


def _run_checkpoint_missing() -> BoundaryCaseMetrics:
    with RepairEnvironment() as environment:
        data_root = environment.parent / "run-data"
        HarnessRuntime(data_root).start(
            "boundary-no-checkpoint",
            ScriptedModel(canonical_repair_script()),
            environment,
        )
        for checkpoint in (data_root / "checkpoints").glob("*.json"):
            checkpoint.unlink()
        recovered = True
        try:
            HarnessRuntime(data_root).resume(
                "boundary-no-checkpoint",
                approved=True,
                environment=environment,
                model=ScriptedModel(canonical_repair_script()),
            )
        except KeyError:
            recovered = False
    return BoundaryCaseMetrics(
        accepted=None,
        false_completed=None,
        policy_violations=None,
        duplicate_side_effects=None,
        recovery_succeeded=recovered,
        trace_contract_passed=None,
        steps=2,
        simulated_cost_units=2,
    )


def _run_receipt_missing() -> BoundaryCaseMetrics:
    with RepairEnvironment() as environment:
        path = WorkspacePathGuard(environment.root).resolve(
            "pricing.py", for_write=True
        )
        first = canonical_repair_script()[1].call
        assert first is not None
        environment.execute(first, path)
        second = ToolCall(
            call_id="call-patch-replay",
            action_id="patch-price",
            name="apply_patch",
            arguments={
                "path": "pricing.py",
                "old": FIXED_SOURCE,
                "new": FIXED_SOURCE + "\n# replayed side effect\n",
            },
        )
        environment.execute(second, path)
        accepted = TestVerifier().verify(environment).accepted
        duplicate = max(0, environment.side_effect_count("patch-price") - 1)
    return BoundaryCaseMetrics(
        accepted=accepted,
        false_completed=None,
        policy_violations=None,
        duplicate_side_effects=duplicate,
        recovery_succeeded=None,
        trace_contract_passed=None,
        steps=2,
        simulated_cost_units=2,
    )


def _run_verifier_missing() -> BoundaryCaseMetrics:
    with RepairEnvironment() as environment:
        outcome = InlineLoop().run(
            ScriptedModel((PolicyDecision.final("已经完成。"),)),
            environment,
        )
        accepted = TestVerifier().verify(environment).accepted
    return BoundaryCaseMetrics(
        accepted=accepted,
        false_completed=(
            outcome.state.status == RunStatus.COMPLETED and not accepted
        ),
        policy_violations=None,
        duplicate_side_effects=None,
        recovery_succeeded=None,
        trace_contract_passed=grade_trace(outcome.events).complete,
        steps=outcome.state.step,
        simulated_cost_units=outcome.state.step,
    )
