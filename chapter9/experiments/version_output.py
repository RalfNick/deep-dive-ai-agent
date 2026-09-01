from __future__ import annotations

import json

from chapter9.experiments.run_all import build_report


def print_version(version: int, input_label: str, non_claim: str) -> int:
    report = build_report()
    cases = [
        case["case_id"]
        for group in report["groups"].values()
        for case in group["cases"]
        if version in case["versions"]
    ]
    print(
        json.dumps(
            {
                "input": input_label,
                "non_claim": non_claim,
                "observed_boundary": cases,
                "version": f"v{version}",
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0

