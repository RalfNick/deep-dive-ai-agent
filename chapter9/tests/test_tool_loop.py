from dataclasses import asdict
import json
import unittest

from chapter9.tool_runtime.loop import build_demo_loop


class ToolLoopTests(unittest.TestCase):
    def test_scripted_loop_reads_twice_then_creates_one_ticket(self):
        outcome = build_demo_loop(
            grants=frozenset({"incident:create:p1"})
        )

        self.assertEqual(
            [
                "get_service_status",
                "list_recent_deployments",
                "create_incident_ticket",
            ],
            [
                event.tool_name
                for event in outcome.trace
                if event.event_type == "tool_call"
            ],
        )
        self.assertEqual("completed", outcome.status)
        self.assertIn("INC-0001", outcome.final_answer.text)
        self.assertEqual(1, outcome.side_effect_count)

    def test_loop_does_not_turn_approval_required_into_success(self):
        outcome = build_demo_loop(grants=frozenset())

        self.assertEqual("blocked", outcome.status)
        self.assertEqual("approval_required", outcome.final_answer.reason)
        self.assertEqual(0, outcome.side_effect_count)

    def test_trace_contains_digests_and_ids_but_not_sensitive_payloads(self):
        outcome = build_demo_loop(
            grants=frozenset({"incident:create:p1"})
        )
        serialized = json.dumps(
            [asdict(event) for event in outcome.trace],
            ensure_ascii=False,
            sort_keys=True,
        )

        self.assertIn("argument_digest", serialized)
        self.assertIn("call-ticket-003", serialized)
        for forbidden in (
            "支付服务大量超时",
            "incident:create:p1",
            "error_rate >= 0.15",
            "caller",
            "grants",
            "arguments\"",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
