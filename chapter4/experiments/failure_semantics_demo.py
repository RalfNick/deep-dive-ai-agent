from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.reporting import run_fault_case  # noqa: E402


def main() -> None:
    cases = [
        run_fault_case(case_id)
        for case_id in (
            "transient_once",
            "timeout_once",
            "permanent",
            "cancelled",
            "step_budget",
        )
    ]
    print(json.dumps([asdict(case) for case in cases], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
