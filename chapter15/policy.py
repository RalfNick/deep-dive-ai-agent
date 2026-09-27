"""A tiny immutable finite-action policy used to explain objectives."""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class TabularPolicy:
    """Logits for a finite set of teaching states and actions.

    This is intentionally not a language model.  It makes the direction of an
    objective update inspectable and hand-checkable without GPU dependencies.
    """

    states: Sequence[str]
    actions: Sequence[str]
    logits: Mapping[str, Mapping[str, float]]

    def __post_init__(self) -> None:
        states = tuple(self.states)
        actions = tuple(self.actions)
        if not states or len(states) != len(set(states)):
            raise ValueError("invalid_policy_states")
        if not actions or len(actions) != len(set(actions)):
            raise ValueError("invalid_policy_actions")
        if set(self.logits) != set(states):
            raise ValueError("policy_state_logits_mismatch")
        frozen_rows: dict[str, Mapping[str, float]] = {}
        for state in states:
            row = self.logits[state]
            if set(row) != set(actions):
                raise ValueError("policy_action_logits_mismatch")
            numeric_row: dict[str, float] = {}
            for action in actions:
                value = row[action]
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                    raise ValueError("invalid_policy_logit")
                numeric_row[action] = float(value)
            frozen_rows[state] = MappingProxyType(numeric_row)
        object.__setattr__(self, "states", states)
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "logits", MappingProxyType(frozen_rows))

    def probability(self, state: str, action: str) -> float:
        if state not in self.logits:
            raise ValueError("unknown_policy_state")
        if action not in self.actions:
            raise ValueError("unknown_policy_action")
        row = self.logits[state]
        maximum = max(row.values())
        denominator = sum(math.exp(value - maximum) for value in row.values())
        return math.exp(row[action] - maximum) / denominator

    def snapshot(self) -> dict[str, Any]:
        return {
            "states": list(self.states),
            "actions": list(self.actions),
            "logits": {
                state: {action: self.logits[state][action] for action in self.actions}
                for state in self.states
            },
        }
