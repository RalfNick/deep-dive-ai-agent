from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Mapping


class RiskLevel(str, Enum):
    READ = "read"
    WRITE = "write"


class ResultStatus(str, Enum):
    SUCCEEDED = "succeeded"
    INVALID_ARGUMENTS = "invalid_arguments"
    DENIED = "denied"
    BUSINESS_ERROR = "business_error"
    EXECUTION_ERROR = "execution_error"


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must be non-blank")


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: Mapping[str, object]
    risk_level: RiskLevel
    output_schema: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        _require_text(self.name, "tool name")
        _require_text(self.description, "tool description")


@dataclass(frozen=True, slots=True)
class ToolCall:
    call_id: str
    tool_name: str
    arguments: Mapping[str, object]
    step_id: str

    def __post_init__(self) -> None:
        if not self.call_id.strip() or not self.tool_name.strip() or not self.step_id.strip():
            raise ValueError("tool call identity fields must be non-blank")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    keyword: str
    message: str

    def __post_init__(self) -> None:
        _require_text(self.keyword, "validation keyword")
        _require_text(self.message, "validation message")


@dataclass(frozen=True, slots=True)
class ToolFailure:
    code: str
    message: str
    retryable: bool = False
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.code, "failure code")
        _require_text(self.message, "failure message")
        object.__setattr__(self, "issues", tuple(self.issues))


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    action_id: str
    tool_name: str
    arguments_digest: str
    external_id: str
    status: str
    occurred_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "action_id",
            "tool_name",
            "arguments_digest",
            "external_id",
            "status",
            "occurred_at",
        ):
            _require_text(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class ToolResult:
    call_id: str
    status: ResultStatus
    data: Mapping[str, object] | None = None
    failure: ToolFailure | None = None
    receipt: ExecutionReceipt | None = None

    def __post_init__(self) -> None:
        _require_text(self.call_id, "call id")
        if self.status is ResultStatus.SUCCEEDED and self.failure is not None:
            raise ValueError("a successful result cannot contain a failure")
        if self.status is not ResultStatus.SUCCEEDED and self.failure is None:
            raise ValueError("a failed result must contain failure details")

    @classmethod
    def succeeded(
        cls,
        call_id: str,
        data: Mapping[str, object],
        receipt: ExecutionReceipt | None = None,
    ) -> ToolResult:
        return cls(call_id=call_id, status=ResultStatus.SUCCEEDED, data=data, receipt=receipt)

    @classmethod
    def failed(
        cls,
        call_id: str,
        status: ResultStatus,
        code: str,
        message: str,
        retryable: bool = False,
        issues: tuple[ValidationIssue, ...] = (),
    ) -> ToolResult:
        if status is ResultStatus.SUCCEEDED:
            raise ValueError("failed() cannot create a succeeded result")
        return cls(
            call_id=call_id,
            status=status,
            failure=ToolFailure(
                code=code,
                message=message,
                retryable=retryable,
                issues=tuple(issues),
            ),
        )


@dataclass(frozen=True, slots=True)
class CallerContext:
    subject: str
    grants: frozenset[str]
    now: str

    def __post_init__(self) -> None:
        _require_text(self.subject, "caller subject")
        _require_text(self.now, "caller time")
        object.__setattr__(self, "grants", frozenset(self.grants))


class DomainError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        _require_text(code, "domain error code")
        _require_text(message, "domain error message")
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def _canonical_json_value(payload: object) -> object:
    if isinstance(payload, Enum):
        return payload.value
    if isinstance(payload, Mapping):
        return {
            str(key): _canonical_json_value(value)
            for key, value in sorted(payload.items(), key=lambda item: str(item[0]))
        }
    if isinstance(payload, (list, tuple)):
        return [_canonical_json_value(item) for item in payload]
    if isinstance(payload, (set, frozenset)):
        return sorted(_canonical_json_value(item) for item in payload)
    return payload


def stable_digest(payload: object) -> str:
    encoded = json.dumps(
        _canonical_json_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
