from typing import Literal
from .contracts import BudgetLimits, TaskPacket


class BudgetLedger:
    def __init__(self, limits: BudgetLimits):
        self.limits = limits
        self.worker_used = 0
        self.verifier_used = 0
        self._tasks: dict[str, TaskPacket] = {}
        self._subtree_used: dict[str, int] = {}
        self.last_refusal = "global_budget_exhausted"

    def register(self, packet: TaskPacket) -> None:
        if packet.task_id in self._tasks:
            raise ValueError("task budget cannot restart")
        self._tasks[packet.task_id] = packet
        self._subtree_used[packet.task_id] = 0

    @property
    def used(self) -> int:
        return self.worker_used + self.verifier_used

    @property
    def remaining(self) -> int:
        return self.limits.tool_calls - self.used

    def charge(self, *, purpose: Literal["worker", "verifier"], task_id: str | None = None) -> bool:
        self.last_refusal = "global_budget_exhausted"
        if self.remaining <= 0:
            return False
        if purpose == "worker":
            if self.worker_used >= self.limits.tool_calls - self.limits.verifier_reserve:
                return False
            ancestors = []
            task = self._tasks.get(task_id)
            while task is not None and task.parent_id is not None:
                ancestors.append(task)
                if self._subtree_used[task.task_id] >= task.limits.tool_calls - task.limits.verifier_reserve:
                    self.last_refusal = "task_budget_exhausted"
                    return False
                task = self._tasks.get(task.parent_id)
            for ancestor in ancestors:
                self._subtree_used[ancestor.task_id] += 1
            self.worker_used += 1
        elif purpose == "verifier":
            if self.verifier_used >= self.limits.verifier_reserve:
                return False
            self.verifier_used += 1
        else:
            raise ValueError("unknown budget purpose")
        return True
