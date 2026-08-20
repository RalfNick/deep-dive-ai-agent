"""Optional DeepSeek probe kept separate from deterministic experiment evidence."""

from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass
from typing import Mapping

from chapter5.context.trace import canonical_json
from chapter5.probes import (
    CredentialMissing,
    HttpStatusError,
    HttpTransport,
    UrllibTransport,
)
from chapter6.fixtures.price_repair import (
    CANONICAL_COMPACTION_CURSOR,
    canonical_seed,
    canonical_trajectory,
)

from .trace import stable_digest


@dataclass(frozen=True)
class LiveCompactionRun:
    status: str
    requested_model: str
    returned_model: str | None
    request_digest: str
    retained_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]
    usage: tuple[tuple[str, int], ...]
    latency_ms: float
    infrastructure_failure: str | None


class DeepSeekCompactionProbe:
    """Ask one provider to emit semantic keys; never retain raw provider text."""

    def __init__(
        self,
        *,
        api_key: str,
        transport: HttpTransport | None = None,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        timeout: float = 45.0,
    ) -> None:
        if not api_key.strip():
            raise CredentialMissing("DEEPSEEK_API_KEY is not configured")
        self._api_key = api_key
        self._transport = transport or UrllibTransport()
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @classmethod
    def from_environment(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        **kwargs: object,
    ) -> "DeepSeekCompactionProbe":
        source = os.environ if environ is None else environ
        api_key = source.get("DEEPSEEK_API_KEY", "")
        if not api_key.strip():
            raise CredentialMissing("DEEPSEEK_API_KEY is not configured")
        return cls(api_key=api_key, **kwargs)

    def run(self) -> LiveCompactionRun:
        payload = self._request_payload()
        request_digest = stable_digest(payload)
        started = time.perf_counter()
        try:
            response = self._transport.post_json(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                payload=payload,
                timeout=self._timeout,
            )
        except HttpStatusError as error:
            failure = (
                "authentication"
                if error.status_code in {401, 403}
                else "rate_limit"
                if error.status_code == 429
                else "provider_error"
            )
            return self._failure(request_digest, started, failure)
        except (TimeoutError, socket.timeout):
            return self._failure(request_digest, started, "timeout")
        except Exception:
            return self._failure(request_digest, started, "transport_error")

        try:
            choices = response["choices"]
            if not isinstance(choices, list) or not choices:
                raise ValueError("choices_missing")
            message = choices[0]["message"]
            raw_content = message["content"]
            if not isinstance(raw_content, str):
                raise ValueError("content_missing")
            parsed = json.loads(raw_content)
            retained = parsed["retained_keys"]
            if (
                not isinstance(retained, list)
                or any(not isinstance(key, str) or not key.strip() for key in retained)
            ):
                raise ValueError("retained_keys_invalid")
            retained_keys = tuple(sorted(set(retained)))
            required = canonical_seed().required_keys
            missing_keys = tuple(sorted(required.difference(retained_keys)))
            returned_model = response.get("model")
            if not isinstance(returned_model, str):
                returned_model = None
            raw_usage = response.get("usage", {})
            usage = (
                tuple(
                    sorted(
                        (str(key), value)
                        for key, value in raw_usage.items()
                        if isinstance(value, int)
                    )
                )
                if isinstance(raw_usage, dict)
                else ()
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return self._failure(request_digest, started, "invalid_response")

        return LiveCompactionRun(
            status="ok",
            requested_model=self._model,
            returned_model=returned_model,
            request_digest=request_digest,
            retained_keys=retained_keys,
            missing_keys=missing_keys,
            usage=usage,
            latency_ms=(time.perf_counter() - started) * 1_000,
            infrastructure_failure=None,
        )

    def _request_payload(self) -> dict[str, object]:
        events = canonical_trajectory()[:CANONICAL_COMPACTION_CURSOR]
        event_data = json.loads(canonical_json(events))
        field_contract = {
            "retained_keys": "array of semantic key strings; include every required key",
            "required_keys": sorted(canonical_seed().required_keys),
        }
        return {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Select semantic continuity keys from the supplied event records. "
                        "Return exactly one JSON object matching field_contract."
                    ),
                },
                {
                    "role": "user",
                    "content": canonical_json(
                        {"events": event_data, "field_contract": field_contract}
                    ),
                },
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "stream": False,
        }

    def _failure(
        self,
        request_digest: str,
        started: float,
        failure: str,
    ) -> LiveCompactionRun:
        return LiveCompactionRun(
            status="infrastructure_failure",
            requested_model=self._model,
            returned_model=None,
            request_digest=request_digest,
            retained_keys=(),
            missing_keys=(),
            usage=(),
            latency_ms=(time.perf_counter() - started) * 1_000,
            infrastructure_failure=failure,
        )
