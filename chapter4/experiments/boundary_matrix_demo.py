from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chapter4.harness.reporting import (  # noqa: E402
    run_boundary_failure_matrix,
    write_boundary_failure_matrix,
)


DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "harness-boundary-matrix.json"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run_boundary_failure_matrix()
    write_boundary_failure_matrix(args.output, report)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
