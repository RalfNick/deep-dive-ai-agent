import unittest

from chapter9.tool_runtime.contracts import (
    DomainError,
    ResultStatus,
    RiskLevel,
    ToolCall,
    ToolDefinition,
)
from chapter9.tool_runtime.registry import ToolRegistry
from chapter9.tool_runtime.schema import validate_arguments


class SchemaRegistryTests(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "type": "object",
            "properties": {
                "service": {"type": "string", "enum": ["payments"]},
                "window_minutes": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                },
            },
            "required": ["service", "window_minutes"],
            "additionalProperties": False,
        }

    def test_validator_reports_stable_json_pointer_paths(self):
        issues = validate_arguments(self.schema, {"service": "billing", "extra": True})

        self.assertEqual(
            [
                ("/extra", "additionalProperties"),
                ("/service", "enum"),
                ("/window_minutes", "required"),
            ],
            [(issue.path, issue.keyword) for issue in issues],
        )

    def test_validator_supports_nested_objects_and_array_items(self):
        schema = {
            "type": "object",
            "properties": {
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                        "required": ["id"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["evidence"],
            "additionalProperties": False,
        }

        issues = validate_arguments(schema, {"evidence": [{"id": 7}, {}]})

        self.assertEqual(
            [("/evidence/0/id", "type"), ("/evidence/1/id", "required")],
            [(issue.path, issue.keyword) for issue in issues],
        )

    def test_validator_rejects_keywords_outside_the_teaching_subset(self):
        with self.assertRaisesRegex(
            ValueError, "unsupported teaching schema keyword: pattern"
        ):
            validate_arguments({"type": "string", "pattern": "payments"}, "payments")

    def test_registry_rejects_duplicate_and_unknown_tools(self):
        registry = ToolRegistry()
        definition = ToolDefinition("status", "Read status", self.schema, RiskLevel.READ)
        registry.register(definition, lambda arguments: {"service": arguments["service"]})

        with self.assertRaises(ValueError):
            registry.register(definition, lambda arguments: {})

        result = registry.invoke(ToolCall("call-1", "missing", {}, "step-1"))
        self.assertEqual(ResultStatus.BUSINESS_ERROR, result.status)
        self.assertEqual("unknown_tool", result.failure.code)

    def test_registry_converts_domain_and_unexpected_failures(self):
        registry = ToolRegistry()
        domain_definition = ToolDefinition(
            "domain_failure", "Raise a domain failure", self.schema, RiskLevel.READ
        )
        crash_definition = ToolDefinition(
            "unexpected_failure", "Raise an unexpected failure", self.schema, RiskLevel.READ
        )
        registry.register(
            domain_definition,
            lambda arguments: (_ for _ in ()).throw(
                DomainError("snapshot_missing", "固定快照不存在。", retryable=False)
            ),
        )
        registry.register(
            crash_definition,
            lambda arguments: (_ for _ in ()).throw(RuntimeError("private detail")),
        )

        domain = registry.invoke(
            ToolCall("call-2", "domain_failure", {"service": "payments", "window_minutes": 5}, "step-2")
        )
        crash = registry.invoke(
            ToolCall("call-3", "unexpected_failure", {"service": "payments", "window_minutes": 5}, "step-3")
        )

        self.assertEqual("snapshot_missing", domain.failure.code)
        self.assertEqual(ResultStatus.EXECUTION_ERROR, crash.status)
        self.assertNotIn("private detail", crash.failure.message)


if __name__ == "__main__":
    unittest.main()
