from typing import Protocol
from .contracts import Decision, TaskPacket, WorkerObservation


class DecisionPolicy(Protocol):
    def next(self, packet: TaskPacket, observation: WorkerObservation) -> Decision: ...


class ScriptedPolicy:
    """A finite deterministic decision double; not an LLM or autonomous planner."""
    def __init__(self, script: tuple[Decision, ...]):
        self.script = script
        self.position = 0

    def next(self, packet: TaskPacket, observation: WorkerObservation) -> Decision:
        if self.position >= len(self.script):
            raise StopIteration
        decision = self.script[self.position]
        self.position += 1
        return decision
