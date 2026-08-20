from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.contracts import PolicyDecision  # noqa: E402
from chapter4.harness.environment import RepairEnvironment  # noqa: E402
from chapter4.harness.policy import ScriptedModel  # noqa: E402
from chapter4.harness.runtime import HarnessRuntime, InlineLoop  # noqa: E402


def main() -> None:
    script = (PolicyDecision.final("问题已经修复，测试已经通过。"),)
    with RepairEnvironment() as environment:
        control = InlineLoop().run(ScriptedModel(script), environment)
        candidate = HarnessRuntime(environment.parent / "candidate").start(
            "candidate", ScriptedModel(script), environment
        )
    print(json.dumps({
        "fixed_decisions": 1,
        "inline_status": control.state.status.value,
        "harness_status": candidate.state.status.value,
        "harness_failure": candidate.state.failure_code,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
