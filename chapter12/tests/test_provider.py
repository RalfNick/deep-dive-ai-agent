from __future__ import annotations

import json
from pathlib import Path

import pytest

from chapter12.providers.chat import ChatModel, parse_response
from chapter12.providers.replay import ReplayModel


def tool_response(arguments='{"path":"README.md"}', finish_reason="tool_calls"):
    return {"choices": [{"finish_reason": finish_reason, "message": {
        "content": None, "refusal": None, "tool_calls": [{"id": "c1", "type": "function",
        "function": {"name": "read_file", "arguments": arguments}}]}}],
        "usage": {"prompt_tokens": 7, "completion_tokens": 3}}


def test_truncated_arguments_are_never_executed():
    response = tool_response('{"path":', "length")
    with pytest.raises(ValueError, match="truncated_response"):
        parse_response(response)


@pytest.mark.parametrize("mutate,error", [
    (lambda value: value["choices"][0]["message"]["tool_calls"].append(
        {"id": "c2", "type": "function",
         "function": {"name": "show_diff", "arguments": "{}"}}), "multiple_tool_calls"),
    (lambda value: value["choices"][0]["message"]["tool_calls"][0].update(id=""),
     "invalid_call_id"),
    (lambda value: value["choices"][0]["message"]["tool_calls"][0]["function"].update(
        arguments="{not-json"), "invalid_arguments"),
    (lambda value: value["choices"][0]["message"].update(refusal="no"), "model_refusal"),
])
def test_invalid_model_outputs_are_explicit(mutate, error):
    value = tool_response()
    mutate(value)
    with pytest.raises(ValueError, match=error):
        parse_response(value)


def test_empty_response_is_not_guessed():
    with pytest.raises(ValueError, match="empty_response"):
        parse_response({"choices": [{"finish_reason": "stop", "message": {"content": ""}}]})


def test_valid_tool_and_final_are_normalized():
    assert parse_response(tool_response()) == {
        "kind": "tool", "text": "",
        "call": {"call_id": "c1", "name": "read_file",
                 "arguments": {"path": "README.md"}}}
    final = {"choices": [{"finish_reason": "stop",
                           "message": {"content": "Implemented and tested.", "tool_calls": []}}]}
    assert parse_response(final) == {"kind": "final", "text": "Implemented and tested.",
                                      "call": None}


def test_replay_cursor_is_explicit_and_resumable():
    decisions = [{"kind": "plan", "text": "inspect", "call": None},
                 {"kind": "final", "text": "done", "call": None}]
    first = ReplayModel(decisions)
    assert first.next([])["kind"] == "plan"
    assert first.provider_state == {"cursor": 1}
    resumed = ReplayModel(decisions, first.provider_state)
    assert resumed.next([])["kind"] == "final"
    assert resumed.provider_state == {"cursor": 2}
    with pytest.raises(ValueError, match="replay_exhausted"):
        resumed.next([])


class FakeCompletions:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeClient:
    def __init__(self, response):
        self.chat = type("Chat", (), {"completions": FakeCompletions(response)})()


def test_chat_request_has_five_tools_single_call_and_usage():
    client = FakeClient(tool_response())
    model = ChatModel({"model": "model-under-test", "timeout": 12}, client)
    decision = model.next([{"role": "user", "content": "inspect"}])
    request = client.chat.completions.kwargs
    assert decision["call"]["name"] == "read_file"
    assert request["model"] == "model-under-test" and request["timeout"] == 12
    assert request["parallel_tool_calls"] is False
    assert len(request["tools"]) == 5
    assert model.last_usage == {"prompt_tokens": 7, "completion_tokens": 3}
    serialized = json.dumps(request)
    assert "sk-" not in serialized and "linkcheck" not in serialized


def test_server_without_parallel_parameter_still_uses_local_enforcement():
    client = FakeClient(tool_response())
    model = ChatModel({"model": "compatible", "parallel_tool_calls_supported": False}, client)
    model.next([])
    assert "parallel_tool_calls" not in client.chat.completions.kwargs
    value = tool_response()
    value["choices"][0]["message"]["tool_calls"] *= 2
    client.chat.completions.response = value
    with pytest.raises(ValueError, match="multiple_tool_calls"):
        model.next([])


def test_transport_timeout_is_explicit_and_adapter_has_no_fixture_solution():
    model = ChatModel({"model": "m"}, FakeClient(TimeoutError("slow")))
    with pytest.raises(TimeoutError, match="model_timeout"):
        model.next([])
    provider_source = "".join(path.read_text(encoding="utf-8") for path in
        (Path(__file__).parents[1] / "providers").glob("*.py"))
    assert "linkcheck" not in provider_source
    assert "document.parent" not in provider_source
