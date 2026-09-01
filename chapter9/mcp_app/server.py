from __future__ import annotations

from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from chapter9.incident_domain.queries import FixtureRepository, IncidentService
from chapter9.incident_domain.tickets import TicketStore
from chapter9.tool_runtime.contracts import DomainError


NOW = "2026-09-01T00:00:00Z"


def _as_tool_error(error: DomainError) -> ToolError:
    return ToolError(f"{error.code}: {error.message}")


def create_server(
    incident_service: IncidentService,
    authorized_scopes: frozenset[str],
) -> MCPServer:
    """Expose the same domain through the official SDK's three MCP primitives."""

    mcp = MCPServer(
        "Starboard Incident",
        description="Deterministic incident-response capabilities for Chapter 9.",
        version="1.0.0",
    )

    @mcp.tool()
    def get_service_status(
        service: str,
        window_minutes: int = 5,
    ) -> dict[str, object]:
        """Read one fixed service-health snapshot."""

        try:
            return incident_service.get_service_status(service, window_minutes)
        except DomainError as error:
            raise _as_tool_error(error) from error

    @mcp.tool()
    def list_recent_deployments(
        service: str,
        since: str,
    ) -> dict[str, object]:
        """List fixed deployment evidence at or after one UTC timestamp."""

        try:
            return {
                "deployments": incident_service.list_recent_deployments(service, since)
            }
        except DomainError as error:
            raise _as_tool_error(error) from error

    @mcp.tool()
    def create_incident_ticket(
        title: str,
        severity: str,
        evidence_ids: list[str],
    ) -> dict[str, object]:
        """Create one incident ticket after server-side authorization."""

        required_scope = f"incident:create:{severity.casefold()}"
        if required_scope not in authorized_scopes:
            raise ToolError(f"approval_required: missing grant {required_scope}")
        try:
            return incident_service.create_incident_ticket(
                title=title,
                severity=severity,
                evidence_ids=tuple(evidence_ids),
            )
        except DomainError as error:
            raise _as_tool_error(error) from error

    @mcp.resource("runbook://payments/current")
    def payments_runbook() -> str:
        """Return the current payment incident runbook."""

        return incident_service.current_runbook()

    @mcp.prompt()
    def triage_incident(service: str = "payments") -> str:
        """Create a user-selected incident triage request."""

        return f"请先查询 {service} 状态和最近部署；证据不足时不要创建故障单。"

    return mcp


def build_default_server(
    authorized_scopes: frozenset[str] = frozenset(),
) -> MCPServer:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures"
    repository = FixtureRepository.load(fixture_root)
    tickets = TicketStore(clock=lambda: NOW)
    service = IncidentService(repository, tickets)
    return create_server(service, authorized_scopes)


def main() -> int:
    build_default_server().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

