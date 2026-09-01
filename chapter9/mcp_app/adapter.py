from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from mcp import Client
from mcp.server import MCPServer

from chapter9.tool_runtime.contracts import CallerContext


@dataclass(frozen=True, slots=True)
class HostCallResult:
    is_error: bool
    error_code: str | None
    protocol_version: str | None
    mcp_result: object | None = None


class HostMCPAdapter:
    """Apply Host consent before crossing the MCP client boundary."""

    def __init__(self, server: MCPServer) -> None:
        self._server = server

    async def call_tool(
        self,
        name: str,
        arguments: Mapping[str, object],
        caller: CallerContext,
    ) -> HostCallResult:
        if name == "create_incident_ticket":
            severity = str(arguments.get("severity", ""))
            required_scope = f"incident:create:{severity.casefold()}"
            if required_scope not in caller.grants:
                return HostCallResult(
                    is_error=True,
                    error_code="approval_required",
                    protocol_version=None,
                )

        async with Client(self._server, raise_exceptions=True) as client:
            result = await client.call_tool(name, dict(arguments))
            return HostCallResult(
                is_error=result.is_error,
                error_code="mcp_tool_error" if result.is_error else None,
                protocol_version=client.protocol_version,
                mcp_result=result,
            )
