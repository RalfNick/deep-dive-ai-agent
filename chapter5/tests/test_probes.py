from __future__ import annotations

import json
import unittest
from dataclasses import asdict

from chapter5.context.builder import BuildConfig, ContextBuilder
from chapter5.context.contracts import DecisionKind, ProbeStatus, RawSource
from chapter5.context.source_policy import SourcePolicy
from chapter5.probes import (
    CredentialMissing,
    DeepSeekAdapter,
    HttpStatusError,
    RuleBasedProbe,
)


class FakeTransport:
    def __init__(self, response: dict[str, object] | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.last_url: str | None = None
        self.last_headers: dict[str, str] | None = None
        self.last_payload: dict[str, object] | None = None
        self.last_timeout: float | None = None

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]:
        self.last_url = url
        self.last_headers = dict(headers)
        self.last_payload = dict(payload)
        self.last_timeout = timeout
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _response(content: dict[str, object]) -> dict[str, object]:
    return {
        "id": "response-fixture",
        "object": "chat.completion",
        "created": 1786752000,
        "model": "deepseek-v4-pro-202608",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": json.dumps(content, ensure_ascii=False),
                },
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 24,
            "total_tokens": 144,
        },
    }


def _packet(*, missing: bool = False):
    policy = SourcePolicy()
    items = [
        policy.classify(
            RawSource("task", "user_request", "Repair pricing.py for the ￥12.30 case"),
            repository="price-lab",
            task_id="repair-price",
        ),
        policy.classify(
            RawSource(
                "apply_patch",
                "tool_schema",
                (
                    "apply_patch changes one exact old string to one exact new string. "
                    "Required arguments: path, old, new."
                ),
                version="1",
            ),
            repository="price-lab",
            task_id="repair-price",
        ),
    ]
    if missing:
        secret = policy.classify(
            RawSource("secret", "secret_fixture", "fixture-secret"),
            repository="price-lab",
            task_id="repair-price",
            required_for=frozenset({"required-test"}),
        )
        items.append(secret)
    return ContextBuilder().build(
        items,
        BuildConfig.for_task("price-lab", "pricing.py", "repair-price", budget_units=4_000),
    ).packet


class RuleBasedProbeTest(unittest.TestCase):
    def test_missing_required_information_returns_needs_context(self) -> None:
        run = RuleBasedProbe().probe(_packet(missing=True))

        self.assertEqual(ProbeStatus.OK, run.status)
        self.assertIsNotNone(run.decision)
        self.assertEqual(DecisionKind.NEEDS_CONTEXT, run.decision.kind)
        self.assertIsNone(run.decision.tool)

    def test_complete_packet_can_propose_patch_without_call_ids(self) -> None:
        run = RuleBasedProbe().probe(_packet())

        self.assertEqual(DecisionKind.TOOL, run.decision.kind)
        self.assertEqual("apply_patch", run.decision.tool.name)
        self.assertNotIn("call_id", run.decision.tool.arguments)
        self.assertNotIn("action_id", run.decision.tool.arguments)


class DeepSeekAdapterTest(unittest.TestCase):
    def test_from_environment_requires_explicit_key(self) -> None:
        with self.assertRaises(CredentialMissing):
            DeepSeekAdapter.from_environment(environ={})

    def test_adapter_sends_official_chat_completion_shape_and_redacts_key(self) -> None:
        transport = FakeTransport(
            _response(
                {
                    "kind": "needs_context",
                    "message": "The relevant test is missing.",
                    "tool": None,
                }
            )
        )
        adapter = DeepSeekAdapter(api_key="test-secret", transport=transport)

        run = adapter.probe(_packet())

        self.assertEqual(ProbeStatus.OK, run.status)
        self.assertEqual(DecisionKind.NEEDS_CONTEXT, run.decision.kind)
        self.assertEqual("deepseek-v4-pro", run.requested_model)
        self.assertEqual("deepseek-v4-pro-202608", run.returned_model)
        self.assertEqual(144, run.usage["total_tokens"])
        self.assertEqual("https://api.deepseek.com/chat/completions", transport.last_url)
        self.assertEqual("Bearer test-secret", transport.last_headers["Authorization"])
        self.assertEqual("deepseek-v4-pro", transport.last_payload["model"])
        self.assertNotIn("test-secret", json.dumps(asdict(run), ensure_ascii=False))

    def test_http_statuses_map_to_infrastructure_status(self) -> None:
        cases = (
            (401, ProbeStatus.AUTH_MISSING),
            (403, ProbeStatus.AUTH_MISSING),
            (429, ProbeStatus.RATE_LIMITED),
            (500, ProbeStatus.PROVIDER_ERROR),
            (503, ProbeStatus.PROVIDER_ERROR),
        )
        for status_code, expected in cases:
            with self.subTest(status_code=status_code):
                adapter = DeepSeekAdapter(
                    api_key="test-secret",
                    transport=FakeTransport(error=HttpStatusError(status_code, "fixture error")),
                )
                run = adapter.probe(_packet())
                self.assertEqual(expected, run.status)
                self.assertIsNone(run.decision)

    def test_timeout_is_distinct_from_provider_error(self) -> None:
        adapter = DeepSeekAdapter(
            api_key="test-secret",
            transport=FakeTransport(error=TimeoutError("fixture timeout")),
        )

        run = adapter.probe(_packet())

        self.assertEqual(ProbeStatus.TIMEOUT, run.status)
        self.assertIsNone(run.decision)

    def test_malformed_decision_is_invalid_response(self) -> None:
        adapter = DeepSeekAdapter(
            api_key="test-secret",
            transport=FakeTransport(_response({"unexpected": "shape"})),
        )

        run = adapter.probe(_packet())

        self.assertEqual(ProbeStatus.INVALID_RESPONSE, run.status)
        self.assertIsNone(run.decision)


if __name__ == "__main__":
    unittest.main()
