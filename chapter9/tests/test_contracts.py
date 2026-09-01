from dataclasses import FrozenInstanceError
from pathlib import Path
import json
import unittest

from chapter9.tool_runtime.contracts import (
    CallerContext,
    ExecutionReceipt,
    ResultStatus,
    RiskLevel,
    ToolCall,
    ToolDefinition,
    ToolResult,
    stable_digest,
)


ROOT = Path(__file__).resolve().parents[2]


class ContractTests(unittest.TestCase):
    def test_fixed_fixtures_describe_payment_status_deployment_and_runbook(self):
        status = json.loads(
            (ROOT / "chapter9/fixtures/service-status.json").read_text(encoding="utf-8")
        )
        deployments = json.loads(
            (ROOT / "chapter9/fixtures/recent-deployments.json").read_text(encoding="utf-8")
        )
        runbook = (ROOT / "chapter9/fixtures/runbooks/payments-current.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual("2026-09-01T00:00:00Z", status["observed_at"])
        self.assertEqual(0.182, status["services"]["payments"]["error_rate"])
        self.assertEqual("deploy-payments-0042", deployments[0]["deployment_id"])
        self.assertIn("error_rate >= 0.15", runbook)

    def test_tool_contracts_reject_blank_identity_and_are_frozen(self):
        with self.assertRaises(ValueError):
            ToolCall(
                call_id="",
                tool_name="get_service_status",
                arguments={},
                step_id="step-1",
            )

        definition = ToolDefinition(
            name="get_service_status",
            description="Read the fixed service snapshot.",
            input_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            risk_level=RiskLevel.READ,
        )
        with self.assertRaises(FrozenInstanceError):
            definition.name = "changed"

        self.assertEqual(
            stable_digest({"b": 2, "a": 1}),
            stable_digest({"a": 1, "b": 2}),
        )

    def test_results_use_explicit_success_and_failure_contracts(self):
        receipt = ExecutionReceipt(
            action_id="action-0001",
            tool_name="create_incident_ticket",
            arguments_digest=stable_digest({"severity": "P1"}),
            external_id="INC-0001",
            status="committed",
            occurred_at="2026-09-01T00:00:00Z",
        )
        success = ToolResult.succeeded("call-1", {"ticket_id": "INC-0001"}, receipt)
        failure = ToolResult.failed(
            "call-2",
            ResultStatus.DENIED,
            "approval_required",
            "写工具需要批准。",
        )

        self.assertEqual(ResultStatus.SUCCEEDED, success.status)
        self.assertEqual("INC-0001", success.receipt.external_id)
        self.assertEqual("approval_required", failure.failure.code)
        self.assertIsNone(failure.data)

    def test_caller_identity_is_non_blank(self):
        with self.assertRaises(ValueError):
            CallerContext(" ", frozenset(), "2026-09-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
