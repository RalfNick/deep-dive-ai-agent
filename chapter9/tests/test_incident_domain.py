from pathlib import Path
import unittest

from chapter9.incident_domain.factory import build_incident_registry
from chapter9.incident_domain.queries import FixtureRepository, IncidentService
from chapter9.incident_domain.tickets import TicketStore
from chapter9.tool_runtime.contracts import DomainError, RiskLevel


ROOT = Path(__file__).resolve().parents[2]


class IncidentDomainTests(unittest.TestCase):
    def setUp(self):
        self.repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
        self.tickets = TicketStore(clock=lambda: "2026-09-01T00:00:00Z")
        self.service = IncidentService(self.repository, self.tickets)

    def test_queries_return_fixed_status_and_sorted_deployments(self):
        status = self.service.get_service_status("payments", 5)
        deployments = self.service.list_recent_deployments(
            "payments", "2026-08-31T23:00:00Z"
        )

        self.assertEqual(0.182, status["error_rate"])
        self.assertEqual("status-payments-0001", status["evidence_id"])
        self.assertEqual(
            ["deploy-payments-0042"],
            [item["deployment_id"] for item in deployments],
        )

    def test_queries_reject_data_the_fixture_does_not_contain(self):
        with self.assertRaisesRegex(DomainError, "five-minute") as context:
            self.service.get_service_status("payments", 10)
        self.assertEqual("unsupported_window", context.exception.code)

        with self.assertRaises(DomainError) as context:
            self.service.get_service_status("billing", 5)
        self.assertEqual("unknown_service", context.exception.code)

    def test_current_runbook_returns_only_the_fixed_document(self):
        runbook = self.service.current_runbook()

        self.assertIn("支付服务当前处置手册", runbook)
        self.assertIn("error_rate >= 0.15", runbook)

    def test_ticket_store_changes_only_after_real_creation(self):
        self.assertEqual((), self.tickets.all())

        ticket = self.service.create_incident_ticket(
            title="支付服务大量超时",
            severity="P1",
            evidence_ids=("status-payments-0001", "deploy-payments-0042"),
        )

        self.assertEqual("INC-0001", ticket["ticket_id"])
        self.assertEqual(1, len(self.tickets.all()))

    def test_registry_exposes_three_closed_contracts_and_one_write_tool(self):
        registry = build_incident_registry(self.repository, self.service)
        definitions = registry.definitions()

        self.assertEqual(
            [
                "create_incident_ticket",
                "get_service_status",
                "list_recent_deployments",
            ],
            [definition.name for definition in definitions],
        )
        self.assertEqual(
            [RiskLevel.WRITE, RiskLevel.READ, RiskLevel.READ],
            [definition.risk_level for definition in definitions],
        )
        self.assertTrue(
            all(
                definition.input_schema["additionalProperties"] is False
                for definition in definitions
            )
        )


if __name__ == "__main__":
    unittest.main()
