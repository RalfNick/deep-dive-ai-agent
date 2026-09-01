import os
from unittest.mock import patch
import unittest

from chapter9.live.live_probe import run_probe
from chapter9.live.provider_adapters import (
    AnthropicMessagesAdapter,
    OpenAIResponsesAdapter,
)


class LiveProbeTests(unittest.TestCase):
    def test_openai_and_anthropic_shapes_map_to_the_same_tool_call(self):
        openai_item = {
            "type": "function_call",
            "call_id": "call-1",
            "name": "get_service_status",
            "arguments": '{"service":"payments","window_minutes":5}',
        }
        anthropic_block = {
            "type": "tool_use",
            "id": "call-1",
            "name": "get_service_status",
            "input": {"service": "payments", "window_minutes": 5},
        }

        self.assertEqual(
            OpenAIResponsesAdapter().to_tool_call(openai_item, "step-1"),
            AnthropicMessagesAdapter().to_tool_call(anthropic_block, "step-1"),
        )

    def test_adapters_reject_malformed_or_non_tool_payloads(self):
        with self.assertRaises(ValueError):
            OpenAIResponsesAdapter().to_tool_call(
                {
                    "type": "function_call",
                    "call_id": "call-1",
                    "name": "get_service_status",
                    "arguments": "{broken",
                },
                "step-1",
            )
        with self.assertRaises(ValueError):
            AnthropicMessagesAdapter().to_tool_call(
                {"type": "text", "text": "done"},
                "step-1",
            )

    def test_default_probe_is_offline_and_does_not_require_a_key(self):
        result = run_probe("deepseek", execute=False)

        self.assertEqual("dry_run", result["status"])
        self.assertFalse(result["network_access"])

    def test_execute_without_environment_credential_is_skipped(self):
        clean_environment = {
            key: value
            for key, value in os.environ.items()
            if key not in {"DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
        }
        with patch.dict(os.environ, clean_environment, clear=True):
            result = run_probe("deepseek", execute=True)

        self.assertEqual("skipped", result["status"])
        self.assertEqual("missing_provider_credential", result["reason"])
        self.assertNotIn("credential", result.get("request", {}))


if __name__ == "__main__":
    unittest.main()
