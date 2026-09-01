from __future__ import annotations

from chapter9.incident_domain.queries import FixtureRepository, IncidentService
from chapter9.tool_runtime.contracts import RiskLevel, ToolDefinition
from chapter9.tool_runtime.registry import ToolRegistry


def build_incident_registry(
    repository: FixtureRepository, service: IncidentService
) -> ToolRegistry:
    if service.repository is not repository:
        raise ValueError("service and registry must share one fixture repository")

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="get_service_status",
            description="读取支付服务的固定五分钟状态快照。",
            input_schema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "enum": ["payments"]},
                    "window_minutes": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 30,
                    },
                },
                "required": ["service", "window_minutes"],
                "additionalProperties": False,
            },
            risk_level=RiskLevel.READ,
        ),
        lambda arguments: service.get_service_status(
            str(arguments["service"]), int(arguments["window_minutes"])
        ),
    )
    registry.register(
        ToolDefinition(
            name="list_recent_deployments",
            description="查询指定 UTC 时间之后的支付服务部署。",
            input_schema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "enum": ["payments"]},
                    "since": {"type": "string"},
                },
                "required": ["service", "since"],
                "additionalProperties": False,
            },
            risk_level=RiskLevel.READ,
        ),
        lambda arguments: {
            "deployments": service.list_recent_deployments(
                str(arguments["service"]), str(arguments["since"])
            )
        },
    )
    registry.register(
        ToolDefinition(
            name="create_incident_ticket",
            description="根据已经收集的证据创建事件工单。",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "severity": {"type": "string", "enum": ["P1", "P2", "P3"]},
                    "evidence_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["title", "severity", "evidence_ids"],
                "additionalProperties": False,
            },
            risk_level=RiskLevel.WRITE,
        ),
        lambda arguments: service.create_incident_ticket(
            title=str(arguments["title"]),
            severity=str(arguments["severity"]),
            evidence_ids=tuple(str(item) for item in arguments["evidence_ids"]),
        ),
    )
    return registry
