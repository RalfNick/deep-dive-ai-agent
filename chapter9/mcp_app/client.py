from __future__ import annotations

from dataclasses import dataclass

from mcp import Client
from mcp.server import MCPServer


@dataclass(frozen=True, slots=True)
class MCPInventory:
    protocol_version: str
    capabilities: tuple[str, ...]
    tools: tuple[str, ...]
    resources: tuple[str, ...]
    prompts: tuple[str, ...]


async def inspect_server(server: MCPServer) -> MCPInventory:
    """Discover inventory only; this function never invokes a write tool."""

    async with Client(server, raise_exceptions=True) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        capability_payload = client.server_capabilities.model_dump(
            by_alias=True,
            exclude_none=True,
        )
        return MCPInventory(
            protocol_version=client.protocol_version,
            capabilities=tuple(sorted(capability_payload)),
            tools=tuple(sorted(item.name for item in tools.tools)),
            resources=tuple(sorted(str(item.uri) for item in resources.resources)),
            prompts=tuple(sorted(item.name for item in prompts.prompts)),
        )

