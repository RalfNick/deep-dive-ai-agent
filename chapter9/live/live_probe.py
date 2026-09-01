from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Mapping
from urllib.request import Request, urlopen

from chapter9.live.provider_adapters import (
    AnthropicMessagesAdapter,
    OpenAIResponsesAdapter,
)
from chapter9.tool_runtime.persistence import write_json


ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = {
    "deepseek": {
        "credential": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
        "url": "https://api.deepseek.com/chat/completions",
    },
    "openai": {
        "credential": "OPENAI_API_KEY",
        "model": "gpt-5.4-mini",
        "url": "https://api.openai.com/v1/responses",
    },
    "anthropic": {
        "credential": "ANTHROPIC_API_KEY",
        "model": "claude-sonnet-4-6",
        "url": "https://api.anthropic.com/v1/messages",
    },
}


TOOL_SCHEMA = {
    "name": "get_service_status",
    "description": "Read one fixed service-health snapshot.",
    "input_schema": {
        "type": "object",
        "properties": {
            "service": {"type": "string", "enum": ["payments"]},
            "window_minutes": {"type": "integer", "minimum": 1, "maximum": 30},
        },
        "required": ["service", "window_minutes"],
        "additionalProperties": False,
    },
}


def _post_json(
    url: str,
    payload: Mapping[str, object],
    headers: Mapping[str, str],
) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **dict(headers)},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    if not isinstance(parsed, dict):
        raise RuntimeError("provider response must be a JSON object")
    return parsed


def _provider_request(provider: str, credential: str) -> dict[str, object]:
    config = PROVIDERS[provider]
    prompt = "查询 payments 服务最近五分钟状态；只提出工具调用，不要猜测结果。"
    if provider == "anthropic":
        payload = {
            "model": config["model"],
            "max_tokens": 256,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [TOOL_SCHEMA],
        }
        response = _post_json(
            str(config["url"]),
            payload,
            {
                "x-api-key": credential,
                "anthropic-version": "2023-06-01",
            },
        )
        blocks = response.get("content")
        if not isinstance(blocks, list):
            raise RuntimeError("Anthropic response has no content array")
        block = next(
            (item for item in blocks if isinstance(item, dict) and item.get("type") == "tool_use"),
            None,
        )
        if block is None:
            raise RuntimeError("Anthropic response proposed no tool")
        sanitized = {**block, "id": "live-call-redacted"}
        call = AnthropicMessagesAdapter().to_tool_call(sanitized, "live-step-1")
    elif provider == "openai":
        payload = {
            "model": config["model"],
            "input": prompt,
            "tools": [
                {
                    "type": "function",
                    "name": TOOL_SCHEMA["name"],
                    "description": TOOL_SCHEMA["description"],
                    "parameters": TOOL_SCHEMA["input_schema"],
                    "strict": True,
                }
            ],
        }
        response = _post_json(
            str(config["url"]),
            payload,
            {"Authorization": f"Bearer {credential}"},
        )
        output = response.get("output")
        if not isinstance(output, list):
            raise RuntimeError("OpenAI response has no output array")
        item = next(
            (entry for entry in output if isinstance(entry, dict) and entry.get("type") == "function_call"),
            None,
        )
        if item is None:
            raise RuntimeError("OpenAI response proposed no tool")
        sanitized = {**item, "call_id": "live-call-redacted"}
        call = OpenAIResponsesAdapter().to_tool_call(sanitized, "live-step-1")
    else:
        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": TOOL_SCHEMA["name"],
                        "description": TOOL_SCHEMA["description"],
                        "parameters": TOOL_SCHEMA["input_schema"],
                    },
                }
            ],
            "tool_choice": "auto",
            "stream": False,
        }
        response = _post_json(
            str(config["url"]),
            payload,
            {"Authorization": f"Bearer {credential}"},
        )
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("DeepSeek response has no choices")
        tool_calls = choices[0].get("message", {}).get("tool_calls", [])
        if not tool_calls:
            raise RuntimeError("DeepSeek response proposed no tool")
        function = tool_calls[0]["function"]
        call = OpenAIResponsesAdapter().to_tool_call(
            {
                "type": "function_call",
                "call_id": "live-call-redacted",
                "name": function["name"],
                "arguments": function["arguments"],
            },
            "live-step-1",
        )
    return {
        "call_id": call.call_id,
        "tool_name": call.tool_name,
        "arguments_digest_only": True,
    }


def run_probe(provider: str, *, execute: bool = False) -> dict[str, object]:
    if provider not in PROVIDERS:
        raise ValueError(f"unsupported provider: {provider}")
    if not execute:
        return {
            "network_access": False,
            "provider": provider,
            "status": "dry_run",
        }

    credential_name = str(PROVIDERS[provider]["credential"])
    credential = os.environ.get(credential_name)
    if not credential:
        return {
            "network_access": False,
            "provider": provider,
            "reason": "missing_provider_credential",
            "status": "skipped",
        }
    observation = _provider_request(provider, credential)
    return {
        "network_access": True,
        "observation": observation,
        "provider": provider,
        "status": "live",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args(argv)
    result = run_probe(arguments.provider, execute=arguments.execute)
    if result["status"] == "skipped":
        print("live probe skipped: missing provider credential", file=sys.stderr)
        return 2
    if result["status"] == "live":
        output = ROOT / "chapter9/live-reports" / f"{arguments.provider}-probe.json"
        write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

