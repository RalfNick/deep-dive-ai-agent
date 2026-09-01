from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from chapter9.incident_domain.factory import build_incident_registry
from chapter9.incident_domain.queries import FixtureRepository, IncidentService
from chapter9.incident_domain.tickets import TicketStore
from chapter9.tool_runtime.contracts import (
    CallerContext,
    ResultStatus,
    ToolCall,
    ToolResult,
)
from chapter9.tool_runtime.policy import PolicyEngine
from chapter9.tool_runtime.runtime import ToolRuntime
from chapter9.tool_runtime.trace import TraceEvent, TraceRecorder


NOW = "2026-09-01T00:00:00Z"


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    text: str
    reason: str
    status: str


@dataclass(frozen=True, slots=True)
class LoopState:
    calls: tuple[ToolCall, ...]
    results: tuple[ToolResult, ...]

    @classmethod
    def empty(cls) -> LoopState:
        return cls(calls=(), results=())

    def append(self, call: ToolCall, result: ToolResult) -> LoopState:
        return LoopState(
            calls=(*self.calls, call),
            results=(*self.results, result),
        )


@dataclass(frozen=True, slots=True)
class LoopOutcome:
    status: str
    final_answer: FinalAnswer
    trace: tuple[TraceEvent, ...]
    side_effect_count: int


class DecisionPolicy(Protocol):
    def decide(self, state: LoopState) -> ToolCall | FinalAnswer: ...


class ScriptedIncidentPolicy:
    """Freeze model decisions so experiments isolate Harness behavior."""

    def decide(self, state: LoopState) -> ToolCall | FinalAnswer:
        completed_steps = len(state.results)
        if completed_steps == 0:
            return ToolCall(
                call_id="call-status-001",
                tool_name="get_service_status",
                arguments={"service": "payments", "window_minutes": 5},
                step_id="step-1",
            )

        if completed_steps == 1:
            status_result = state.results[0]
            if status_result.status is not ResultStatus.SUCCEEDED:
                return FinalAnswer("服务状态查询失败，未创建事件。", "status_read_failed", "blocked")
            error_rate = status_result.data.get("error_rate") if status_result.data else None
            if not isinstance(error_rate, (int, float)) or error_rate < 0.15:
                return FinalAnswer("当前证据未达到 P1 阈值。", "threshold_not_met", "completed")
            return ToolCall(
                call_id="call-deploy-002",
                tool_name="list_recent_deployments",
                arguments={
                    "service": "payments",
                    "since": "2026-08-31T23:00:00Z",
                },
                step_id="step-2",
            )

        if completed_steps == 2:
            deployment_result = state.results[1]
            if deployment_result.status is not ResultStatus.SUCCEEDED:
                return FinalAnswer("部署记录查询失败，未创建事件。", "deployment_read_failed", "blocked")
            deployments = (
                deployment_result.data.get("deployments")
                if deployment_result.data is not None
                else None
            )
            deployment_ids = {
                item.get("deployment_id")
                for item in deployments
                if isinstance(item, dict)
            } if isinstance(deployments, list) else set()
            if "deploy-payments-0042" not in deployment_ids:
                return FinalAnswer("未找到与异常窗口对应的部署证据。", "deployment_not_found", "blocked")
            return ToolCall(
                call_id="call-ticket-003",
                tool_name="create_incident_ticket",
                arguments={
                    "title": "支付服务大量超时",
                    "severity": "P1",
                    "evidence_ids": [
                        "status-payments-0001",
                        "deploy-payments-0042",
                    ],
                },
                step_id="step-3",
            )

        ticket_result = state.results[2]
        if ticket_result.status is ResultStatus.SUCCEEDED and ticket_result.receipt:
            return FinalAnswer(
                f"事件已经创建并取得执行回执：{ticket_result.receipt.external_id}",
                "verified_receipt",
                "completed",
            )
        reason = (
            ticket_result.failure.code
            if ticket_result.failure is not None
            else "ticket_creation_failed"
        )
        return FinalAnswer("事件尚未创建，需要处理执行边界。", reason, "blocked")


def run_tool_loop(
    policy: DecisionPolicy,
    runtime: ToolRuntime,
    caller: CallerContext,
    *,
    max_steps: int = 6,
) -> LoopOutcome:
    state = LoopState.empty()
    recorder = TraceRecorder()
    for _ in range(max_steps):
        decision = policy.decide(state)
        if isinstance(decision, FinalAnswer):
            recorder.record_final(status=decision.status, reason=decision.reason)
            return LoopOutcome(
                status=decision.status,
                final_answer=decision,
                trace=recorder.events(),
                side_effect_count=sum(
                    result.receipt is not None for result in state.results
                ),
            )
        recorder.record_call(decision)
        result = runtime.execute(decision, caller)
        recorder.record_result(decision, result)
        state = state.append(decision, result)

    final = FinalAnswer("达到最大步骤数，运行已停止。", "step_limit", "blocked")
    recorder.record_final(status=final.status, reason=final.reason)
    return LoopOutcome(
        status=final.status,
        final_answer=final,
        trace=recorder.events(),
        side_effect_count=sum(result.receipt is not None for result in state.results),
    )


def build_demo_loop(grants: frozenset[str]) -> LoopOutcome:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures"
    repository = FixtureRepository.load(fixture_root)
    tickets = TicketStore(clock=lambda: NOW)
    service = IncidentService(repository, tickets)
    registry = build_incident_registry(repository, service)
    runtime = ToolRuntime(registry, PolicyEngine())
    caller = CallerContext("oncall", grants, NOW)
    return run_tool_loop(ScriptedIncidentPolicy(), runtime, caller)
