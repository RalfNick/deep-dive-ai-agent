"""A deterministic test Model implemented against the installed Agents SDK API."""
from __future__ import annotations

import copy
import json
from typing import Any, AsyncIterator

from agents.models.interface import Model, ModelResponse
from agents.usage import Usage
from openai.types.responses import (ResponseFunctionToolCall,
                                    ResponseOutputMessage, ResponseOutputText)

from ..contracts import Record, validate_call


class ReplaySDKModel(Model):
    def __init__(self, decisions: list[Record]):
        self.decisions = copy.deepcopy(decisions)
        self.cursor = 0

    async def get_response(self, system_instructions: str | None, input: Any,
                           model_settings: Any, tools: list[Any], output_schema: Any,
                           handoffs: list[Any], tracing: Any, *,
                           previous_response_id: str | None,
                           conversation_id: str | None, prompt: Any) -> ModelResponse:
        del system_instructions, input, model_settings, output_schema, handoffs
        del tracing, previous_response_id, conversation_id, prompt
        if self.cursor >= len(self.decisions):
            raise ValueError("replay_exhausted")
        decision = self.decisions[self.cursor]
        self.cursor += 1
        response_id = f"replay-response-{self.cursor}"
        if decision.get("kind") == "tool":
            call = validate_call(decision["call"])
            available = {getattr(tool, "name", None) for tool in tools}
            if call["name"] not in available:
                raise ValueError("sdk_tool_unavailable")
            output = [ResponseFunctionToolCall(
                id=response_id, call_id=call["call_id"], name=call["name"],
                arguments=json.dumps(call["arguments"], ensure_ascii=False,
                                     sort_keys=True, separators=(",", ":")),
                type="function_call")]
        elif decision.get("kind") in {"final", "plan"}:
            text = decision.get("text")
            if not isinstance(text, str):
                raise ValueError("invalid_decision")
            output = [ResponseOutputMessage(id=response_id, role="assistant",
                status="completed", type="message", content=[ResponseOutputText(
                    text=text, type="output_text", annotations=[], logprobs=[])])]
        else:
            raise ValueError("invalid_decision")
        return ModelResponse(output=output, usage=Usage(requests=1),
                             response_id=response_id)

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        del args, kwargs
        if False:  # make this an async generator without inventing stream events
            yield None
        raise NotImplementedError("streaming_not_used_in_chapter12")


def make_model(decisions: list[Record]) -> Model:
    return ReplaySDKModel(decisions)
