from __future__ import annotations

from collections.abc import Mapping
from numbers import Real

from chapter9.tool_runtime.contracts import ValidationIssue


SUPPORTED_KEYWORDS = frozenset(
    {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "enum",
        "minimum",
        "maximum",
    }
)


def _pointer(parent: str, part: object) -> str:
    escaped = str(part).replace("~", "~0").replace("/", "~1")
    return f"{parent}/{escaped}"


def _validate_schema_shape(schema: Mapping[str, object]) -> None:
    for keyword in schema:
        if keyword not in SUPPORTED_KEYWORDS:
            raise ValueError(f"unsupported teaching schema keyword: {keyword}")

    properties = schema.get("properties")
    if properties is not None:
        if not isinstance(properties, Mapping):
            raise ValueError("properties must be an object")
        for child in properties.values():
            if not isinstance(child, Mapping):
                raise ValueError("property schema must be an object")
            _validate_schema_shape(child)

    items = schema.get("items")
    if items is not None:
        if not isinstance(items, Mapping):
            raise ValueError("items must be an object schema")
        _validate_schema_shape(items)


def _matches_type(expected: str, value: object) -> bool:
    checks = {
        "object": lambda candidate: isinstance(candidate, Mapping),
        "array": lambda candidate: isinstance(candidate, (list, tuple)),
        "string": lambda candidate: isinstance(candidate, str),
        "integer": lambda candidate: isinstance(candidate, int)
        and not isinstance(candidate, bool),
        "number": lambda candidate: isinstance(candidate, Real)
        and not isinstance(candidate, bool),
        "boolean": lambda candidate: isinstance(candidate, bool),
        "null": lambda candidate: candidate is None,
    }
    if expected not in checks:
        raise ValueError(f"unsupported teaching schema type: {expected}")
    return checks[expected](value)


def _issue(
    issues: list[ValidationIssue], path: str, keyword: str, message: str
) -> None:
    issues.append(ValidationIssue(path=path, keyword=keyword, message=message))


def _validate(
    schema: Mapping[str, object],
    value: object,
    *,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    expected_type = schema.get("type")
    if expected_type is not None:
        if not isinstance(expected_type, str):
            raise ValueError("type must be a string in the teaching schema subset")
        if not _matches_type(expected_type, value):
            _issue(issues, path, "type", f"值必须是 {expected_type} 类型。")
            return

    enum_values = schema.get("enum")
    if enum_values is not None:
        if not isinstance(enum_values, (list, tuple)):
            raise ValueError("enum must be an array")
        if value not in enum_values:
            _issue(issues, path, "enum", "值不在允许的枚举范围内。")

    if isinstance(value, Real) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            _issue(issues, path, "minimum", f"值不得小于 {minimum}。")
        if maximum is not None and value > maximum:
            _issue(issues, path, "maximum", f"值不得大于 {maximum}。")

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise ValueError("properties must be an object")

        required = schema.get("required", ())
        if not isinstance(required, (list, tuple)) or not all(
            isinstance(item, str) for item in required
        ):
            raise ValueError("required must be an array of strings")
        for name in required:
            if name not in value:
                _issue(issues, _pointer(path, name), "required", "缺少必填字段。")

        additional = schema.get("additionalProperties", True)
        if not isinstance(additional, bool):
            raise ValueError("additionalProperties must be a boolean")
        if not additional:
            for name in value:
                if name not in properties:
                    _issue(
                        issues,
                        _pointer(path, name),
                        "additionalProperties",
                        "字段未在工具合同中声明。",
                    )

        for name, child_schema in properties.items():
            if name in value:
                _validate(
                    child_schema,
                    value[name],
                    path=_pointer(path, name),
                    issues=issues,
                )

    if isinstance(value, (list, tuple)) and "items" in schema:
        item_schema = schema["items"]
        if not isinstance(item_schema, Mapping):
            raise ValueError("items must be an object schema")
        for index, item in enumerate(value):
            _validate(
                item_schema,
                item,
                path=_pointer(path, index),
                issues=issues,
            )


def validate_arguments(
    schema: Mapping[str, object], arguments: object
) -> tuple[ValidationIssue, ...]:
    """Validate against the chapter's deliberately small JSON Schema subset."""

    _validate_schema_shape(schema)
    issues: list[ValidationIssue] = []
    _validate(schema, arguments, path="", issues=issues)
    return tuple(sorted(issues, key=lambda item: (item.path, item.keyword)))

