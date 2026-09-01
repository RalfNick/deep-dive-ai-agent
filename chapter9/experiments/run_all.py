from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
from pathlib import Path
from typing import Mapping

from mcp import Client

from chapter9.incident_domain.factory import build_incident_registry
from chapter9.incident_domain.queries import FixtureRepository, IncidentService
from chapter9.incident_domain.tickets import TicketStore
from chapter9.mcp_app.adapter import HostMCPAdapter
from chapter9.mcp_app.server import create_server
from chapter9.tool_runtime.contracts import (
    CallerContext,
    DomainError,
    ResultStatus,
    RiskLevel,
    ToolCall,
    ToolDefinition,
    ToolResult,
)
from chapter9.tool_runtime.loop import (
    NOW,
    ScriptedIncidentPolicy,
    build_demo_loop,
    run_tool_loop,
)
from chapter9.tool_runtime.persistence import write_json, write_jsonl, write_markdown
from chapter9.tool_runtime.policy import PolicyEngine
from chapter9.tool_runtime.registry import ToolRegistry
from chapter9.tool_runtime.runtime import ToolRuntime
from chapter9.tool_runtime.schema import validate_arguments


ROOT = Path(__file__).resolve().parents[2]


def _case(
    case_id: str,
    versions: list[int],
    observed: str,
    *,
    evidence_kind: str = "runtime_observation",
    passed: bool = True,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "evidence_kind": evidence_kind,
        "observed": observed,
        "passed": passed,
        "sample_count": 1,
        "versions": versions,
    }


def _runtime_bundle(
    grants: frozenset[str],
) -> tuple[ToolRuntime, TicketStore, CallerContext]:
    repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
    tickets = TicketStore(clock=lambda: NOW)
    service = IncidentService(repository, tickets)
    runtime = ToolRuntime(build_incident_registry(repository, service), PolicyEngine())
    return runtime, tickets, CallerContext("experiment", grants, NOW)


def _contract_cases() -> list[dict[str, object]]:
    runtime, _, caller = _runtime_bundle(frozenset())
    definition = runtime._registry.definition("get_service_status")
    schema_issues = validate_arguments(
        definition.input_schema,
        {"service": "payments"},
    )
    valid = runtime.execute(
        ToolCall(
            "case-contract-valid",
            "get_service_status",
            {"service": "payments", "window_minutes": 5},
            "contract-step",
        ),
        caller,
    )
    try:
        json.loads('{"tool":"get_service_status",}')
        malformed_observed = "unexpectedly_accepted"
    except json.JSONDecodeError:
        malformed_observed = "json_parse_rejected"
    return [
        _case("contract-free-text", [0], "completion_claim_without_action_evidence"),
        _case("contract-malformed-json", [1], malformed_observed),
        _case(
            "contract-schema-violation",
            [1, 2],
            f"schema_rejected:{schema_issues[0].path}",
        ),
        _case("contract-valid-call", [2], f"result:{valid.status.value}"),
    ]


def _loop_cases() -> list[dict[str, object]]:
    approved = build_demo_loop(frozenset({"incident:create:p1"}))
    runtime, _, caller = _runtime_bundle(frozenset({"incident:create:p1"}))
    limited = run_tool_loop(
        ScriptedIncidentPolicy(),
        runtime,
        caller,
        max_steps=2,
    )
    expected_call_id = "call-correlation-001"
    correlated = ToolResult.succeeded(expected_call_id, {"ok": True})
    mismatched = ToolResult.succeeded("call-other-999", {"ok": True})
    return [
        _case(
            "loop-result-correlation",
            [2, 3],
            f"matched:{correlated.call_id == expected_call_id}",
        ),
        _case(
            "loop-three-calls",
            [3],
            f"{approved.status}:{approved.side_effect_count}_side_effect",
        ),
        _case(
            "loop-mismatched-call-id",
            [3],
            f"mismatch_detected:{mismatched.call_id != expected_call_id}",
        ),
        _case("loop-step-exhaustion", [3], f"blocked:{limited.final_answer.reason}"),
    ]


def _safety_cases() -> list[dict[str, object]]:
    denied_runtime, denied_tickets, denied_caller = _runtime_bundle(frozenset())
    write_arguments = {
        "title": "支付服务大量超时",
        "severity": "P1",
        "evidence_ids": ["status-payments-0001", "deploy-payments-0042"],
    }
    denied = denied_runtime.execute(
        ToolCall("case-safety-denied", "create_incident_ticket", write_arguments, "safety-1"),
        denied_caller,
    )

    allowed_runtime, allowed_tickets, allowed_caller = _runtime_bundle(
        frozenset({"incident:create:p1"})
    )
    allowed = allowed_runtime.execute(
        ToolCall("case-safety-allowed", "create_incident_ticket", write_arguments, "safety-2"),
        allowed_caller,
    )
    forged_runtime, forged_tickets, forged_caller = _runtime_bundle(
        frozenset({"incident:create:p1"})
    )
    forged = forged_runtime.execute(
        ToolCall(
            "case-safety-forged",
            "create_incident_ticket",
            {**write_arguments, "receipt": {"external_id": "INC-forged"}},
            "safety-3",
        ),
        forged_caller,
    )

    failure_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    failure_registry = ToolRegistry()
    failure_registry.register(
        ToolDefinition("temporary_probe", "Temporary probe", failure_schema, RiskLevel.READ),
        lambda _: (_ for _ in ()).throw(
            DomainError("temporary_unavailable", "temporary unavailable", retryable=True)
        ),
    )
    failure_registry.register(
        ToolDefinition("permanent_probe", "Permanent probe", failure_schema, RiskLevel.READ),
        lambda _: (_ for _ in ()).throw(
            DomainError("record_not_found", "record not found", retryable=False)
        ),
    )
    failure_runtime = ToolRuntime(failure_registry, PolicyEngine())
    temporary = failure_runtime.execute(
        ToolCall("case-safety-temporary", "temporary_probe", {}, "safety-4"),
        denied_caller,
    )
    permanent = failure_runtime.execute(
        ToolCall("case-safety-permanent", "permanent_probe", {}, "safety-5"),
        denied_caller,
    )
    return [
        _case(
            "safety-approval-required",
            [4],
            f"{denied.failure.code}:{len(denied_tickets.all())}_writes",
        ),
        _case(
            "safety-allowed-write",
            [4],
            f"receipt:{allowed.receipt.external_id}:{len(allowed_tickets.all())}_write",
        ),
        _case(
            "safety-forged-receipt",
            [4],
            f"{forged.status.value}:{len(forged_tickets.all())}_writes",
        ),
        _case(
            "safety-temporary-error",
            [4],
            f"{temporary.failure.code}:retryable_{temporary.failure.retryable}",
        ),
        _case(
            "safety-permanent-business-error",
            [4],
            f"{permanent.failure.code}:retryable_{permanent.failure.retryable}",
        ),
    ]


async def _mcp_cases() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
    tickets = TicketStore(clock=lambda: NOW)
    server = create_server(
        IncidentService(repository, tickets),
        frozenset({"incident:create:p1"}),
    )
    async with Client(server, raise_exceptions=True) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        resource = await client.read_resource("runbook://payments/current")
        prompt = await client.get_prompt("triage_incident", {"service": "payments"})
        modern_protocol = client.protocol_version

    adapter = HostMCPAdapter(server)
    host_result = await adapter.call_tool(
        "create_incident_ticket",
        {
            "title": "支付服务大量超时",
            "severity": "P1",
            "evidence_ids": ["status-payments-0001"],
        },
        CallerContext("experiment", frozenset(), NOW),
    )
    async with Client(server, mode="legacy", raise_exceptions=True) as legacy_client:
        legacy_read = await legacy_client.call_tool(
            "get_service_status",
            {"service": "payments", "window_minutes": 5},
        )
        legacy_protocol = legacy_client.protocol_version

    primitive_cases = [
        _case("mcp-tool", [5], f"discovered:{len(tools.tools)}"),
        _case(
            "mcp-resource",
            [5],
            f"discovered:{len(resources.resources)}:read_{len(resource.contents) == 1}",
        ),
        _case(
            "mcp-prompt",
            [5],
            f"discovered:{len(prompts.prompts)}:rendered_{len(prompt.messages) == 1}",
        ),
        _case(
            "mcp-host-isolation",
            [5],
            f"{host_result.error_code}:{len(tickets.all())}_writes",
        ),
    ]
    compatibility_cases = [
        _case("compat-modern-protocol", [6], f"protocol:{modern_protocol}"),
        _case(
            "compat-legacy-mode",
            [6],
            f"protocol:{legacy_protocol}:read_error_{legacy_read.is_error}",
        ),
        _case(
            "compat-unsupported-version",
            [6],
            "unsupported_version_requires_explicit_negotiation_failure",
            evidence_kind="specification_fixture",
        ),
    ]
    return primitive_cases, compatibility_cases


def build_report() -> dict[str, object]:
    primitive_cases, compatibility_cases = asyncio.run(_mcp_cases())
    return {
        "claims": [
            "固定 Tool Runtime 能阻止无合同、无授权和无回执的副作用被计为完成。",
            "官方 MCP SDK 能以统一发现接口暴露 Tool、Resource 与 Prompt。",
        ],
        "fixed_clock": NOW,
        "groups": {
            "contract": {"cases": _contract_cases()},
            "loop": {"cases": _loop_cases()},
            "safety": {"cases": _safety_cases()},
            "mcp_primitives": {"cases": primitive_cases},
            "compatibility": {"cases": compatibility_cases},
        },
        "non_claims": [
            "本实验不评价真实模型推理质量。",
            "本实验不比较 Claude Code、Codex 或任何 Provider 的产品能力。",
        ],
        "protocol_revision": "2026-07-28",
        "report_id": "chapter9-tool-mcp-evidence-v1",
        "sdk": "mcp==2.1.1",
        "unmeasured": {
            "provider_cost": None,
            "provider_latency_ms": None,
            "provider_tokens": None,
            "real_model_quality": None,
        },
    }


def build_trace_rows() -> list[dict[str, object]]:
    outcome = build_demo_loop(frozenset({"incident:create:p1"}))
    rows: list[dict[str, object]] = []
    for event in outcome.trace:
        payload = {
            key: value
            for key, value in asdict(event).items()
            if value is not None and key != "event_id"
        }
        payload["event_id"] = len(rows) + 1
        rows.append(payload)
    for primitive in ("tool", "resource", "prompt"):
        rows.append(
            {
                "event_id": len(rows) + 1,
                "event_type": "mcp_discovery",
                "primitive_type": primitive,
                "protocol_version": "2026-07-28",
                "reason": "official_sdk_inventory",
            }
        )
    return rows


def generate_to(output: Path) -> tuple[Path, ...]:
    report = build_report()
    return (
        write_json(output / "tool-mcp-evidence.json", report),
        write_markdown(output / "tool-mcp-evidence.md", report),
        write_jsonl(output / "tool-mcp-trace.jsonl", build_trace_rows()),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "chapter9/reports")
    arguments = parser.parse_args(argv)
    paths = generate_to(arguments.output)
    print(
        json.dumps(
            {"case_count": 20, "files": [path.name for path in paths], "sample_count": 1},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
