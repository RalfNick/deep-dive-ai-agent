from pathlib import Path
import unittest

from chapter9.incident_domain.factory import build_incident_registry
from chapter9.incident_domain.queries import FixtureRepository, IncidentService
from chapter9.incident_domain.tickets import TicketStore
from chapter9.tool_runtime.contracts import CallerContext, ResultStatus, ToolCall
from chapter9.tool_runtime.policy import PolicyEngine
from chapter9.tool_runtime.runtime import ToolRuntime


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-09-01T00:00:00Z"


class PolicyRuntimeTests(unittest.TestCase):
    def setUp(self):
        repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
        self.tickets = TicketStore(clock=lambda: NOW)
        registry = build_incident_registry(
            repository, IncidentService(repository, self.tickets)
        )
        self.runtime = ToolRuntime(registry, PolicyEngine())

    def test_invalid_arguments_never_reach_handler(self):
        result = self.runtime.execute(
            ToolCall(
                "call-1",
                "get_service_status",
                {"service": "payments"},
                "step-1",
            ),
            CallerContext("reader", frozenset(), NOW),
        )

        self.assertEqual(ResultStatus.INVALID_ARGUMENTS, result.status)
        self.assertEqual("/window_minutes", result.failure.issues[0].path)
        self.assertEqual((), self.tickets.all())

    def test_p1_write_requires_host_grant(self):
        call = ToolCall(
            "call-2",
            "create_incident_ticket",
            {
                "title": "支付服务大量超时",
                "severity": "P1",
                "evidence_ids": [
                    "status-payments-0001",
                    "deploy-payments-0042",
                ],
            },
            "step-3",
        )

        denied = self.runtime.execute(
            call, CallerContext("oncall", frozenset(), NOW)
        )
        approved_call = ToolCall("call-3", call.tool_name, call.arguments, call.step_id)
        allowed = self.runtime.execute(
            approved_call,
            CallerContext("oncall", frozenset({"incident:create:p1"}), NOW),
        )

        self.assertEqual(ResultStatus.DENIED, denied.status)
        self.assertEqual("approval_required", denied.failure.code)
        self.assertEqual(ResultStatus.SUCCEEDED, allowed.status)
        self.assertEqual("INC-0001", allowed.receipt.external_id)
        self.assertEqual(1, len(self.tickets.all()))

    def test_model_cannot_supply_a_forged_receipt(self):
        result = self.runtime.execute(
            ToolCall(
                "call-4",
                "create_incident_ticket",
                {
                    "title": "支付服务大量超时",
                    "severity": "P1",
                    "evidence_ids": ["status-payments-0001"],
                    "receipt": {"external_id": "INC-forged"},
                },
                "step-4",
            ),
            CallerContext("oncall", frozenset({"incident:create:p1"}), NOW),
        )

        self.assertEqual(ResultStatus.INVALID_ARGUMENTS, result.status)
        self.assertEqual((), self.tickets.all())

    def test_duplicate_call_id_is_rejected_before_a_second_execution(self):
        caller = CallerContext("reader", frozenset(), NOW)
        first = self.runtime.execute(
            ToolCall(
                "call-repeat",
                "get_service_status",
                {"service": "payments", "window_minutes": 5},
                "step-1",
            ),
            caller,
        )
        second = self.runtime.execute(
            ToolCall(
                "call-repeat",
                "list_recent_deployments",
                {"service": "payments", "since": "2026-08-31T23:00:00Z"},
                "step-2",
            ),
            caller,
        )

        self.assertEqual(ResultStatus.SUCCEEDED, first.status)
        self.assertEqual(ResultStatus.BUSINESS_ERROR, second.status)
        self.assertEqual("duplicate_call_id", second.failure.code)


if __name__ == "__main__":
    unittest.main()
