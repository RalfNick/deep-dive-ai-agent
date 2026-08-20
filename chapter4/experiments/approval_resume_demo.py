from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.environment import RepairEnvironment  # noqa: E402
from chapter4.harness.policy import ScriptedModel, canonical_repair_script  # noqa: E402
from chapter4.harness.runtime import (  # noqa: E402
    HarnessRuntime,
    SimulatedCrashAfterReceipt,
)


def main() -> None:
    with RepairEnvironment() as environment:
        root = environment.parent / "run-data"
        paused = HarnessRuntime(root).start(
            "approval-demo",
            ScriptedModel(canonical_repair_script()),
            environment,
        )
        crashed_after_receipt = False
        try:
            HarnessRuntime(
                root,
                crash_after_receipt_action_ids=frozenset({"patch-price"}),
            ).resume(
                "approval-demo", approved=True, environment=environment,
                model=ScriptedModel(canonical_repair_script()),
            )
        except SimulatedCrashAfterReceipt:
            crashed_after_receipt = True
        writes_after_crash = environment.side_effect_count("patch-price")
        recovered = HarnessRuntime(root).resume(
            "approval-demo", approved=True, environment=environment,
            model=ScriptedModel(canonical_repair_script()),
        )
        receipt_recovery = {
            "paused_status": paused.state.status.value,
            "crashed_after_receipt": crashed_after_receipt,
            "write_count_after_crash": writes_after_crash,
            "recovered_status": recovered.state.status.value,
            "action_deduplicated": any(
                event.kind == "action_deduplicated"
                for event in recovered.events
            ),
            "write_count_after_recovery": environment.side_effect_count(
                "patch-price"
            ),
            "event_order": [event.kind for event in recovered.events],
        }

    with RepairEnvironment() as environment:
        root = environment.parent / "stale-data"
        paused = HarnessRuntime(root).start(
            "stale-approval-demo",
            ScriptedModel(canonical_repair_script()),
            environment,
        )
        pricing = environment.root / "pricing.py"
        pricing.write_text(
            pricing.read_text(encoding="utf-8") + "\n# concurrent edit\n",
            encoding="utf-8",
        )
        stale = HarnessRuntime(root).resume(
            "stale-approval-demo", approved=True, environment=environment,
            model=ScriptedModel(canonical_repair_script()),
        )
        stale_approval = {
            "approved_state_digest": paused.state.state_digest,
            "current_state_digest": environment.state_digest(),
            "status": stale.state.status.value,
            "write_count": environment.side_effect_count("patch-price"),
        }

    payload = {
        "receipt_recovery": receipt_recovery,
        "stale_approval": stale_approval,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
