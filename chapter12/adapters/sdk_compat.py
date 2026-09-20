"""The only module that knows the installed SDK RunState serialization API."""
from __future__ import annotations

import json
from typing import Any

from agents.run_state import RunState


def _context_payload(value: Any) -> dict[str, object]:
    del value
    return {"kind": "chapter12-services", "schema_version": 1}


def dump_state(value: Any) -> str:
    payload = value.to_json(context_serializer=_context_payload,
                            strict_context=True,
                            include_tracing_api_key=False)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


async def load_state(agent: Any, text: str) -> Any:
    payload = json.loads(text)
    return await RunState.from_json(agent, payload,
                                    context_override={"kind": "chapter12-services"})


async def load_state_with_context(agent: Any, text: str, context: Any) -> Any:
    payload = json.loads(text)
    return await RunState.from_json(agent, payload, context_override=context)
