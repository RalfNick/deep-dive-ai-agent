from pathlib import Path
import unittest

from mcp import Client

from chapter9.incident_domain.queries import FixtureRepository, IncidentService
from chapter9.incident_domain.tickets import TicketStore
from chapter9.mcp_app.adapter import HostMCPAdapter
from chapter9.mcp_app.client import inspect_server
from chapter9.mcp_app.server import create_server
from chapter9.tool_runtime.contracts import CallerContext


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-01T00:00:00Z"


def build_service():
    repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
    tickets = TicketStore(clock=lambda: NOW)
    return IncidentService(repository, tickets), tickets


class MCPAppTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        service, self.tickets = build_service()
        self.server = create_server(
            service,
            authorized_scopes=frozenset({"incident:create:p1"}),
        )

    async def test_modern_client_discovers_three_primitives(self):
        async with Client(self.server, raise_exceptions=True) as client:
            self.assertEqual("2026-07-28", client.protocol_version)
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()

            self.assertEqual(
                [
                    "create_incident_ticket",
                    "get_service_status",
                    "list_recent_deployments",
                ],
                sorted(tool.name for tool in tools.tools),
            )
            self.assertEqual(
                ["runbook://payments/current"],
                [str(item.uri) for item in resources.resources],
            )
            self.assertEqual(
                ["triage_incident"],
                [item.name for item in prompts.prompts],
            )

    async def test_tool_error_is_a_result_and_resource_is_not_a_tool(self):
        async with Client(self.server, raise_exceptions=True) as client:
            unknown = await client.call_tool("runbook://payments/current", {})
            resource = await client.read_resource("runbook://payments/current")

        self.assertTrue(unknown.is_error)
        self.assertIn("error_rate >= 0.15", resource.contents[0].text)

    async def test_server_authorization_remains_when_host_is_bypassed(self):
        service, tickets = build_service()
        unauthorized = create_server(service, authorized_scopes=frozenset())
        async with Client(unauthorized, raise_exceptions=True) as client:
            result = await client.call_tool(
                "create_incident_ticket",
                {
                    "title": "支付服务大量超时",
                    "severity": "P1",
                    "evidence_ids": ["status-payments-0001"],
                },
            )

        self.assertTrue(result.is_error)
        self.assertEqual((), tickets.all())

    async def test_legacy_client_can_still_call_the_read_tool(self):
        async with Client(self.server, mode="legacy", raise_exceptions=True) as client:
            self.assertNotEqual("2026-07-28", client.protocol_version)
            result = await client.call_tool(
                "get_service_status",
                {"service": "payments", "window_minutes": 5},
            )

        self.assertFalse(result.is_error)

    async def test_inventory_and_host_consent_do_not_call_a_write_tool(self):
        inventory = await inspect_server(self.server)
        self.assertEqual("2026-07-28", inventory.protocol_version)
        self.assertEqual(0, len(self.tickets.all()))

        adapter = HostMCPAdapter(self.server)
        blocked = await adapter.call_tool(
            "create_incident_ticket",
            {
                "title": "支付服务大量超时",
                "severity": "P1",
                "evidence_ids": ["status-payments-0001"],
            },
            CallerContext("reader", frozenset(), NOW),
        )
        self.assertTrue(blocked.is_error)
        self.assertEqual("approval_required", blocked.error_code)
        self.assertEqual(0, len(self.tickets.all()))


if __name__ == "__main__":
    unittest.main()
