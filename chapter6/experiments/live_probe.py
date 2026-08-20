"""Explicit live-only DeepSeek probe CLI; never writes offline baselines."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Mapping

from chapter5.probes import CredentialMissing
from chapter6.context_continuity.live_probe import DeepSeekCompactionProbe


_CANONICAL_REPORT_NAMES = (
    "context-continuity.json",
    "context-continuity.md",
    "context-continuity-trace.jsonl",
)


def _normalized_resolved(path: Path) -> str:
    return os.path.normcase(str(path.resolve(strict=False)))


def _is_canonical_offline_report(path: Path) -> bool:
    report_root = Path(__file__).resolve().parents[1] / "reports"
    protected = {
        _normalized_resolved(report_root / name) for name in _CANONICAL_REPORT_NAMES
    }
    return _normalized_resolved(path) in protected


def run_cli(
    argv: list[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    probe_factory: Callable[..., DeepSeekCompactionProbe] = DeepSeekCompactionProbe.from_environment,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.repeats <= 0:
        parser.error("--repeats must be positive")
    if _is_canonical_offline_report(args.output):
        print(
            "error: live probe output cannot replace a canonical offline report",
            file=sys.stderr,
        )
        return 2
    source = os.environ if environ is None else environ
    try:
        probe = probe_factory(environ=source)
    except CredentialMissing:
        return 2

    runs = tuple(probe.run() for _ in range(args.repeats))
    valid = sum(run.status == "ok" for run in runs)
    payload = {
        "comparison_scope": "live provider probe only; excluded from offline behavior denominator",
        "provider_failures": len(runs) - valid,
        "requested_model": runs[0].requested_model if runs else None,
        "returned_models": sorted(
            {run.returned_model for run in runs if run.returned_model is not None}
        ),
        "runs": [asdict(run) for run in runs],
        "valid_attempts": valid,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())
