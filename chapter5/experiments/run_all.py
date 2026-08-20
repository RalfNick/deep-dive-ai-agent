from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import date
from pathlib import Path

from ..graders import ExperimentReport
from ..probes import CredentialMissing, DeepSeekAdapter, ModelProbe
from .assembly_ablation import run_assembly_ablation
from .information_position import run_information_position
from .instruction_conflict import run_instruction_conflict
from .noise_and_injection import run_noise_and_injection
from .tool_description import run_tool_description


DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"


def _run_groups(probe: ModelProbe | None, *, live: bool) -> tuple:
    return (
        *run_assembly_ablation(probe, live=live),
        *run_instruction_conflict(probe, live=live),
        *run_information_position(probe, live=live),
        *run_tool_description(probe, live=live),
        *run_noise_and_injection(probe, live=live),
    )


def run_all(*, live: bool, repeats: int) -> ExperimentReport:
    if repeats < 1:
        raise ValueError("repeats_must_be_positive")
    if not live and repeats != 1:
        raise ValueError("offline_suite_is_deterministic_and_runs_once")
    if not live:
        return ExperimentReport.from_records(_run_groups(None, live=False))

    run_date = date.today().isoformat()
    try:
        probe = DeepSeekAdapter.from_environment(model=DEFAULT_DEEPSEEK_MODEL)
    except CredentialMissing:
        return ExperimentReport.configuration_failure(
            reason="missing_credential",
            requested_model=DEFAULT_DEEPSEEK_MODEL,
            run_date=run_date,
        )
    records = []
    for repeat in range(1, repeats + 1):
        for record in _run_groups(probe, live=True):
            records.append(replace(record, variant=f"{record.variant}__run{repeat}"))
    return ExperimentReport.from_records(
        records,
        requested_model=probe.model,
        run_date=run_date,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Chapter 5 context experiments")
    parser.add_argument("--live", action="store_true", help="Call the configured DeepSeek API")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.live and args.output is None:
        parser.error("--live requires --output so redacted evidence has an explicit destination")
    report = run_all(live=args.live, repeats=args.repeats)
    rendered = report.to_json()
    if args.output is None:
        print(rendered, end="")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(args.output)
    if report.run_status == "config_error":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
