from typing import Literal
from .contracts import BudgetLimits


class BudgetLedger:
    def __init__(self, limits: BudgetLimits):
        self.limits = limits
        self.worker_used = 0
        self.verifier_used = 0

    @property
    def used(self) -> int:
        return self.worker_used + self.verifier_used

    @property
    def remaining(self) -> int:
        return self.limits.tool_calls - self.used

    def charge(self, *, purpose: Literal["worker", "verifier"]) -> bool:
        if self.remaining <= 0:
            return False
        if purpose == "worker":
            if self.worker_used >= self.limits.tool_calls - self.limits.verifier_reserve:
                return False
            self.worker_used += 1
        elif purpose == "verifier":
            if self.verifier_used >= self.limits.verifier_reserve:
                return False
            self.verifier_used += 1
        else:
            raise ValueError("unknown budget purpose")
        return True
