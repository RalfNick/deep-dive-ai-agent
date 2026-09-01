from __future__ import annotations

import json

from chapter9.experiments.run_all import build_report


def main() -> int:
    cases = sorted(
        build_report()["groups"]["safety"]["cases"],
        key=lambda case: case["case_id"],
    )
    print(json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
