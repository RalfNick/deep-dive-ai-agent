import argparse
from pathlib import Path
from .cases import run_group
from .contracts import TeamReport
from .exercise_solutions import solution_payload
from .fixtures import checked_path
from .output import write_bundle, write_partial
from .reporting import build_report, validate_report


def run_all(*, root: Path, workdir: Path) -> TeamReport:
    report = build_report(tuple(run_group(group, root=root, workdir=workdir / f"group-{group}") for group in range(1, 6)))
    validate_report(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fixed-policy collaboration evidence, offline")
    parser.add_argument("--group", choices=("all", "1", "2", "3", "4", "5"), default="all")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        output = checked_path(root, args.output, prefixes=("chapter18/.runs", "chapter18/reports"), new=True)
        workdir = root / "chapter18/.runs" / (output.name + "-workspaces")
        checked_path(root, workdir, prefixes=("chapter18/.runs",), new=True)
        if args.group == "all":
            report = run_all(root=root, workdir=workdir / "experiments")
            answers = solution_payload(root=root, workdir=workdir / "answers")
            paths = write_bundle(root, output, report, answers)
            print(f"cases={report['summary']['cases_total']}; files={len(paths)}; schema=chapter18.team.v1")
        else:
            group = int(args.group)
            paths = write_partial(root, output, group, run_group(group, root=root, workdir=workdir / "experiments"))
            print(f"partial=true; group={group}; files={len(paths)}")
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
