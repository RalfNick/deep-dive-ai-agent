"""Field-level redaction and a fail-closed export gate."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import re
from typing import Any

from .contracts import SpanRecord, TraceRecord, ValidationIssue


SECRET_KEYS = frozenset({"authorization", "cookie", "apikey", "token", "password", "credential"})
IDENTITY_KEYS = frozenset({"email", "userid", "accountid", "customerid"})
CONTENT_KEYS = frozenset({"toolarguments", "filecontent", "hiddenanswer", "chainofthought"})
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_PATTERN = re.compile(r"(?:\bBearer\s+\S+|\bsk-[A-Za-z0-9_-]{6,})", re.IGNORECASE)


def _normalized(key: object) -> str:
    return "".join(character for character in str(key).lower() if character.isalnum())


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: object, salt: str) -> str:
    return hashlib.sha256(f"{salt}\0{_canonical(value)}".encode()).hexdigest()


def redact_payload(value: object, *, salt: str) -> object:
    if not salt:
        raise ValueError("redaction_salt_required")

    def redact(item: object, key: object | None = None) -> object:
        normalized = _normalized(key) if key is not None else ""
        if normalized in SECRET_KEYS:
            return "[REDACTED]"
        if normalized in IDENTITY_KEYS:
            return f"hash:{_digest(item, salt)[:16]}"
        if normalized in CONTENT_KEYS:
            return {"redacted": True, "digest": f"sha256:{_digest(item, salt)}"}
        if isinstance(item, Mapping):
            return {str(child_key): redact(child, child_key) for child_key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [redact(child) for child in item]
        if isinstance(item, str) and EMAIL_PATTERN.search(item):
            return f"hash:{_digest(item, salt)[:16]}"
        if isinstance(item, str) and SECRET_PATTERN.search(item):
            return "[REDACTED]"
        return item

    return redact(value)


def redact_trace(trace: TraceRecord, *, salt: str) -> TraceRecord:
    """Return a structurally equivalent TraceRecord with sensitive fields transformed."""
    payload = redact_payload(trace.to_dict(), salt=salt)
    assert isinstance(payload, dict)
    span_payloads = payload.pop("spans")
    assert isinstance(span_payloads, list)
    spans = tuple(SpanRecord(**item) for item in span_payloads)
    safe = TraceRecord(**payload, spans=spans)
    if validate_export_safe(safe.to_dict()):
        raise ValueError("unsafe_trace_after_redaction")
    return safe


def validate_export_safe(value: object) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []

    def walk(item: object, path: str, key: object | None = None) -> None:
        normalized = _normalized(key) if key is not None else ""
        if normalized in CONTENT_KEYS:
            safe_marker = isinstance(item, Mapping) and item.get("redacted") is True and isinstance(item.get("digest"), str)
            if not safe_marker:
                issues.append(ValidationIssue("forbidden_export_field", "raw content field cannot be exported", field=path))
        if normalized in SECRET_KEYS and item != "[REDACTED]":
            issues.append(ValidationIssue("forbidden_export_field", "secret field is not redacted", field=path))
        if normalized in IDENTITY_KEYS and not (isinstance(item, str) and item.startswith("hash:")):
            issues.append(ValidationIssue("forbidden_export_field", "identity field is not hashed", field=path))

        if isinstance(item, Mapping):
            for child_key, child in item.items():
                child_path = f"{path}.{child_key}" if path else str(child_key)
                walk(child, child_path, child_key)
        elif isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                walk(child, f"{path}[{index}]")
        elif isinstance(item, str) and item not in {"[REDACTED]"} and not item.startswith("hash:"):
            if EMAIL_PATTERN.search(item):
                issues.append(ValidationIssue("pii_in_export", "email-like value cannot be exported", field=path))
            if SECRET_PATTERN.search(item):
                issues.append(ValidationIssue("secret_in_export", "credential-like value cannot be exported", field=path))

    walk(value, "")
    unique = {(issue.code, issue.field): issue for issue in issues}
    return tuple(unique[key] for key in sorted(unique))
