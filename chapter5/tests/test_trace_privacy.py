from __future__ import annotations

import json
import unittest
from dataclasses import asdict, fields

from chapter5.context.builder import BuildConfig, ContextBuilder
from chapter5.context.contracts import ContextBuildTrace, RawSource, TraceEntry
from chapter5.context.source_policy import SourcePolicy


class ContextTracePrivacyTest(unittest.TestCase):
    def test_trace_contract_has_no_content_field(self) -> None:
        self.assertNotIn("content", {field.name for field in fields(TraceEntry)})
        self.assertNotIn("content", {field.name for field in fields(ContextBuildTrace)})

    def test_trace_serialization_never_contains_filtered_secret(self) -> None:
        secret_value = "fixture-secret-that-must-not-appear"
        secret = SourcePolicy().classify(
            RawSource("secret", "secret_fixture", secret_value),
            repository="price-lab",
            task_id="repair-price",
            required_for=frozenset({"secret-check"}),
        )
        config = BuildConfig.for_task(
            "price-lab",
            "pricing.py",
            "repair-price",
            budget_units=500,
        )

        result = ContextBuilder().build([secret], config)
        encoded = json.dumps(asdict(result.trace), ensure_ascii=False, default=str)

        self.assertNotIn(secret_value, encoded)
        self.assertIn("sensitive", encoded)
        self.assertNotIn(secret.provenance.content_digest, encoded)
        self.assertIn('"content_digest": "redacted"', encoded)


if __name__ == "__main__":
    unittest.main()
