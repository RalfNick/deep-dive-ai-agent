from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from chapter4.harness.policy import BROKEN_SOURCE, FIXED_SOURCE

from .context.contracts import ContextPacket, DecisionKind, ProbeStatus
from .context.serialization import PacketSerializer


@dataclass(frozen=True)
class ToolProposal:
    name: str
    arguments: dict[str, object]


@dataclass(frozen=True)
class ProbeDecision:
    kind: DecisionKind
    message: str = ""
    tool: ToolProposal | None = None


@dataclass(frozen=True)
class ProbeRun:
    status: ProbeStatus
    decision: ProbeDecision | None
    requested_model: str
    returned_model: str | None
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    retry_count: int = 0
    request_digest: str = ""
    error_code: str | None = None


class CredentialMissing(RuntimeError):
    pass


class HttpStatusError(RuntimeError):
    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"http_status_{status_code}")
        self.status_code = status_code
        self.body = body


class HttpTransport(Protocol):
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]: ...


class ModelProbe(Protocol):
    def probe(self, packet: ContextPacket) -> ProbeRun: ...


class UrllibTransport:
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise HttpStatusError(error.code, body) from error
        except (TimeoutError, socket.timeout):
            raise
        except urllib.error.URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise TimeoutError("provider_timeout") from error
            raise RuntimeError("provider_transport_error") from error
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise ValueError("provider_response_not_object")
        return parsed


class RuleBasedProbe:
    """Deterministic behavior probe; it reads only the Packet available to a model."""

    model_id = "rule-based-v1"

    def probe(self, packet: ContextPacket) -> ProbeRun:
        if packet.missing_requirements:
            decision = ProbeDecision(
                kind=DecisionKind.NEEDS_CONTEXT,
                message="Missing: " + ", ".join(packet.missing_requirements),
            )
        else:
            body = "\n".join(section.serialized_content for section in packet.sections)
            lowered = body.casefold()
            if "apply_patch" in packet.tools and "injected_target=.env" in lowered:
                decision = ProbeDecision(
                    kind=DecisionKind.TOOL,
                    tool=ToolProposal(
                        name="apply_patch",
                        arguments={
                            "path": ".env",
                            "old": "PLACEHOLDER",
                            "new": "EXFILTRATE",
                        },
                    ),
                )
            elif "apply_patch" in packet.tools and "pricing.py" in body and (
                "￥" in body or "¥" in body
            ):
                if "required arguments: path, old, new" not in lowered:
                    decision = ProbeDecision(
                        kind=DecisionKind.NEEDS_CONTEXT,
                        message="The apply_patch contract does not define its required arguments.",
                    )
                else:
                    decision = ProbeDecision(
                        kind=DecisionKind.TOOL,
                        tool=ToolProposal(
                            name="apply_patch",
                            arguments={
                                "path": "pricing.py",
                                "old": BROKEN_SOURCE,
                                "new": FIXED_SOURCE,
                            },
                        ),
                    )
            elif "read_file" in packet.tools and "pricing.py" in body:
                decision = ProbeDecision(
                    kind=DecisionKind.TOOL,
                    tool=ToolProposal(name="read_file", arguments={"path": "pricing.py"}),
                )
            else:
                decision = ProbeDecision(
                    kind=DecisionKind.ANSWER,
                    message="The available context does not require a tool proposal.",
                )
        return ProbeRun(
            status=ProbeStatus.OK,
            decision=decision,
            requested_model=self.model_id,
            returned_model=self.model_id,
            request_digest=packet.semantic_packet_digest,
        )


def _parse_decision(data: object) -> ProbeDecision:
    if not isinstance(data, dict):
        raise ValueError("decision_not_object")
    kind_value = data.get("kind")
    if not isinstance(kind_value, str):
        raise ValueError("decision_kind_missing")
    try:
        kind = DecisionKind(kind_value)
    except ValueError as error:
        raise ValueError("decision_kind_invalid") from error
    message = data.get("message", "")
    if not isinstance(message, str):
        raise ValueError("decision_message_invalid")
    raw_tool = data.get("tool")
    tool: ToolProposal | None = None
    if kind is DecisionKind.TOOL:
        if not isinstance(raw_tool, dict):
            raise ValueError("tool_missing")
        name = raw_tool.get("name")
        arguments = raw_tool.get("arguments")
        if not isinstance(name, str) or not isinstance(arguments, dict):
            raise ValueError("tool_shape_invalid")
        tool = ToolProposal(name=name, arguments=dict(arguments))
    elif raw_tool is not None:
        raise ValueError("tool_not_allowed_for_decision")
    return ProbeDecision(kind=kind, message=message, tool=tool)


class DeepSeekAdapter:
    """Small OpenAI-compatible adapter verified against official DeepSeek docs."""

    def __init__(
        self,
        *,
        api_key: str,
        transport: HttpTransport | None = None,
        model: str = "deepseek-v4-pro",
        base_url: str = "https://api.deepseek.com",
        timeout: float = 45.0,
        serializer: PacketSerializer | None = None,
    ) -> None:
        if not api_key.strip():
            raise CredentialMissing("DEEPSEEK_API_KEY is not configured")
        self._api_key = api_key
        self.transport = transport or UrllibTransport()
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.serializer = serializer or PacketSerializer()

    @classmethod
    def from_environment(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        **kwargs: object,
    ) -> "DeepSeekAdapter":
        source = os.environ if environ is None else environ
        api_key = source.get("DEEPSEEK_API_KEY", "")
        if not api_key.strip():
            raise CredentialMissing("DEEPSEEK_API_KEY is not configured")
        return cls(api_key=api_key, **kwargs)

    def probe(self, packet: ContextPacket) -> ProbeRun:
        request = self.serializer.to_provider_request(packet, model=self.model)
        started = time.perf_counter()
        try:
            response = self.transport.post_json(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                payload=request.payload,
                timeout=self.timeout,
            )
        except HttpStatusError as error:
            status = (
                ProbeStatus.AUTH_MISSING
                if error.status_code in {401, 403}
                else ProbeStatus.RATE_LIMITED
                if error.status_code == 429
                else ProbeStatus.PROVIDER_ERROR
            )
            return self._failure(
                status,
                request.provider_request_digest,
                started,
                f"http_{error.status_code}",
            )
        except (TimeoutError, socket.timeout):
            return self._failure(
                ProbeStatus.TIMEOUT,
                request.provider_request_digest,
                started,
                "timeout",
            )
        except Exception:
            return self._failure(
                ProbeStatus.PROVIDER_ERROR,
                request.provider_request_digest,
                started,
                "transport_error",
            )

        try:
            choices = response["choices"]
            if not isinstance(choices, list) or not choices:
                raise ValueError("choices_missing")
            message = choices[0]["message"]
            content = message["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("content_missing")
            decision = _parse_decision(json.loads(content))
            returned_model = response.get("model")
            if not isinstance(returned_model, str):
                returned_model = None
            raw_usage = response.get("usage", {})
            usage = {
                str(key): int(value)
                for key, value in raw_usage.items()
                if isinstance(value, int)
            } if isinstance(raw_usage, dict) else {}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return self._failure(
                ProbeStatus.INVALID_RESPONSE,
                request.provider_request_digest,
                started,
                "invalid_response",
            )

        return ProbeRun(
            status=ProbeStatus.OK,
            decision=decision,
            requested_model=self.model,
            returned_model=returned_model,
            usage=usage,
            latency_ms=(time.perf_counter() - started) * 1_000,
            request_digest=request.provider_request_digest,
        )

    def _failure(
        self,
        status: ProbeStatus,
        request_digest: str,
        started: float,
        error_code: str,
    ) -> ProbeRun:
        return ProbeRun(
            status=status,
            decision=None,
            requested_model=self.model,
            returned_model=None,
            latency_ms=(time.perf_counter() - started) * 1_000,
            request_digest=request_digest,
            error_code=error_code,
        )
