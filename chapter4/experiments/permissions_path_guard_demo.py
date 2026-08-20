from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.contracts import ToolCall  # noqa: E402
from chapter4.harness.environment import RepairEnvironment  # noqa: E402
from chapter4.harness.gateway import ActionGateway  # noqa: E402
from chapter4.harness.path_guard import (  # noqa: E402
    PathGuardViolation,
    WorkspacePathGuard,
)


def main() -> None:
    call = ToolCall(
        "call-escape", "escape-write", "apply_patch",
        {"path": "../secret.txt", "old": "outside", "new": "changed"},
    )
    soft = ActionGateway(require_approval_for_writes=False).evaluate(call)
    with RepairEnvironment() as environment:
        try:
            WorkspacePathGuard(environment.root).resolve(
                "../secret.txt", for_write=True
            )
            enforced = "allowed"
        except PathGuardViolation:
            enforced = "blocked"
    print(json.dumps({
        "soft_policy": soft.kind.value,
        "path_guard_enforcement": enforced,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
