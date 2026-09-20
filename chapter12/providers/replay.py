"""Deterministic decisions for tests and offline book experiments."""
from __future__ import annotations

import copy

from ..contracts import Record, validate_call


def validate_decision(value: Record) -> Record:
    if type(value) is not dict or set(value) != {"kind", "text", "call"}:
        raise ValueError("invalid_decision")
    if value["kind"] not in {"plan", "tool", "final"} or type(value["text"]) is not str:
        raise ValueError("invalid_decision")
    if value["kind"] == "tool":
        if value["call"] is None:
            raise ValueError("invalid_decision")
        value = copy.deepcopy(value)
        value["call"] = validate_call(value["call"])
    elif value["call"] is not None:
        raise ValueError("invalid_decision")
    return copy.deepcopy(value)


class ReplayModel:
    def __init__(self, decisions: list[Record], provider_state: Record | None = None):
        self._decisions = [validate_decision(item) for item in decisions]
        state = provider_state or {"cursor": 0}
        if set(state) != {"cursor"} or type(state["cursor"]) is not int \
                or not 0 <= state["cursor"] <= len(self._decisions):
            raise ValueError("invalid_replay_state")
        self.provider_state = copy.deepcopy(state)

    def next(self, messages: list[Record]) -> Record:
        del messages
        cursor = self.provider_state["cursor"]
        if cursor >= len(self._decisions):
            raise ValueError("replay_exhausted")
        decision = copy.deepcopy(self._decisions[cursor])
        self.provider_state = {"cursor": cursor + 1}
        return decision
