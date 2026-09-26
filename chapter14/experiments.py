"""Five deterministic experiments and the canonical Chapter 14 report."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Sequence

from .benchmark import compare_benchmark_cards, load_benchmark_cards
from .diagnosis import build_regression_tasks, diagnose_incident, run_ablations
from .metrics import compare_releases, critical_path, summarize_release
from .privacy import redact_payload, validate_export_safe
from .sampling import combined_sample, sampling_report
from .trace_builder import build_shuffled_log_fixture, build_trace_fixture


ROOT = Path(__file__).resolve().parent
RATE_CARD_PATH = ROOT / "fixtures" / "rate-card.json"
DEFAULT_REPORT_DIR = ROOT / "reports"


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _group_payload(group: int) -> dict[str, object]:
    traces = build_trace_fixture()
    if group == 1:
        cards = {card.source: card for card in load_benchmark_cards()}
        return {
            "group": 1,
            "title": "same score, different measurement contract",
            "comparisons": {
                "control": compare_benchmark_cards(cards["fixture://control-a"], cards["fixture://control-b"]),
                "same_score_misleading": compare_benchmark_cards(
                    cards["fixture://same-score-a"], cards["fixture://same-score-b"]
                ),
            },
            "cards": [card.to_dict() for card in cards.values()],
        }
    if group == 2:
        trace = next(item for item in traces if item.trace_id == "trace-incident-retrieval-02")
        return {
            "group": 2,
            "title": "unordered logs versus causal trace",
            "trace_id": trace.trace_id,
            "log_view": {
                "causal_edges_available": False,
                "records": list(build_shuffled_log_fixture(trace)),
            },
            "trace_view": {
                "span_count": len(trace.spans),
                "parent_edge_count": sum(span.parent_span_id is not None for span in trace.spans),
                "dependency_edge_count": sum(len(span.depends_on_span_ids) for span in trace.spans),
                "parallel_span_ids": [span.span_id for span in trace.spans if span.kind == "retrieval"],
            },
            "limits": ["logs_deliberately_omit_parent_and_dependency_edges"],
        }
    if group == 3:
        rate_card = json.loads(RATE_CARD_PATH.read_text(encoding="utf-8"))
        summaries = {
            release: summarize_release(tuple(item for item in traces if item.release_id == release), rate_card)
            for release in ("stable", "incident", "fixed")
        }
        exemplar = next(item for item in traces if item.trace_id == "trace-stable-retrieval-02")
        return {
            "group": 3,
            "title": "latency, critical path, usage, and retry amplification",
            "release_summaries": summaries,
            "release_comparison": compare_releases(summaries),
            "parallel_trace_example": critical_path(exemplar),
        }
    if group == 4:
        thresholds = {"slow_ms": 450, "new_releases": ("incident",)}
        decisions = tuple(combined_sample(trace, 0.1, thresholds, "combined.v1") for trace in traces)
        sample = sampling_report(traces, decisions, salt="chapter14-canonical-salt")
        redacted = redact_payload(
            {
                "headers": {"Authorization": "Bearer teaching-secret"},
                "email": "reader@example.com",
                "tool_arguments": {"path": "private/answer.txt"},
            },
            salt="chapter14-canonical-salt",
        )
        return {
            "group": 4,
            "title": "sampling, privacy, and observability blind spots",
            "sampling": sample,
            "privacy": {
                "redacted_example": redacted,
                "export_safe": not validate_export_safe(redacted),
                "ordering": ["record", "redact", "sample", "export", "store"],
            },
        }
    if group == 5:
        ablations = run_ablations(traces)
        report = diagnose_incident(traces, ablation_results=ablations)
        return {
            "group": 5,
            "title": "alert to root cause to regression tasks",
            "ablations": list(ablations),
            "incident_report": report.to_dict(),
            "regression_tasks": list(build_regression_tasks(report)),
        }
    raise ValueError("group_must_be_1_to_5")


def run_group(group: int, directory: Path) -> dict[str, object]:
    payload = _group_payload(group)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"group-{group}.json"
    if target.exists():
        raise FileExistsError(f"artifact_exists:{target.name}")
    target.write_bytes(_json_bytes(payload))
    return payload


def _diagnostic_report(groups: dict[int, dict[str, object]]) -> dict[str, object]:
    traces = build_trace_fixture()
    release_summaries = groups[3]["release_summaries"]
    incident_report = groups[5]["incident_report"]
    sampling = groups[4]["sampling"]
    return {
        "schema_version": "chapter14.diagnostics.v1",
        "fixture": {
            "fixture_version": "chapter14.trace-fixture.v1",
            "scored_trace_count": len(traces),
            "release_ids": ["stable", "incident", "fixed"],
            "release_counts": dict(sorted(Counter(trace.release_id for trace in traces).items())),
            "slice_counts": dict(sorted(Counter(trace.slice for trace in traces).items())),
        },
        "benchmark": {
            "control_verdict": groups[1]["comparisons"]["control"]["verdict"],
            "same_score_verdict": groups[1]["comparisons"]["same_score_misleading"]["verdict"],
        },
        "release_summaries": release_summaries,
        "release_comparison": groups[3]["release_comparison"],
        "sampling": sampling,
        "incident_report": incident_report,
        "regression_tasks": groups[5]["regression_tasks"],
        "group_artifacts": [f"group-{number}.json" for number in range(1, 6)],
        "evidence_limits": [
            "deterministic_fixture_not_real_model_measurement",
            "cost_units_are_not_provider_prices",
            "tail_samples_are_diagnostic_not_population_denominators",
            "no_platform_conformance_claim",
        ],
    }


def _report_markdown(report: dict[str, object]) -> str:
    releases = report["release_summaries"]
    incident = report["incident_report"]
    lines = [
        "# Chapter 14 deterministic production-diagnostics report",
        "",
        "> Offline teaching fixture. Cost units are not provider prices; Tail samples are not population denominators.",
        "",
        "## Release comparison",
        "",
        "| Release | Outcome | p95 latency (ms) | Cost units | Retry amplification | Telemetry completeness |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for release in ("stable", "incident", "fixed"):
        item = releases[release]
        lines.append(
            f"| {release} | {item['outcome_score_mean']:.6f} | {item['latency_ms']['p95']} | "
            f"{item['usage']['cost_units_total']:.6f} | {item['retry_amplification']:.6f} | "
            f"{item['telemetry_complete_rate']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Incident conclusion",
            "",
            f"- Conclusion: `{incident['conclusion']}`",
            f"- Root cause: `{incident['root_cause']}`",
            f"- Data completeness: `{incident['data_completeness']}`",
            f"- Supporting traces: `{len(incident['supporting_trace_ids'])}`",
            f"- Counterevidence traces: `{len(incident['counterevidence_trace_ids'])}`",
            "",
            "## Stable artifact contract",
            "",
            "- Schema: `chapter14.diagnostics.v1`",
            "- Scored traces: `72`",
            "- Experiment groups: `5`",
            "",
        ]
    )
    return "\n".join(lines)


def _write_artifacts(directory: Path, groups: dict[int, dict[str, object]], report: dict[str, object]) -> None:
    for number, payload in groups.items():
        (directory / f"group-{number}.json").write_bytes(_json_bytes(payload))
    (directory / "diagnostic-report.json").write_bytes(_json_bytes(report))
    (directory / "diagnostic-report.md").write_text(_report_markdown(report), encoding="utf-8", newline="\n")
    artifact_names = ["diagnostic-report.json", "diagnostic-report.md", *(f"group-{number}.json" for number in range(1, 6))]
    manifest = {
        "schema_version": "chapter14.artifact-manifest.v1",
        "artifacts": [
            {
                "name": name,
                "bytes": (directory / name).stat().st_size,
                "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest(),
            }
            for name in artifact_names
        ],
    }
    (directory / "manifest.json").write_bytes(_json_bytes(manifest))


def build_diagnostics(directory: Path) -> dict[str, object]:
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError("output_directory_not_empty")
    groups = {number: _group_payload(number) for number in range(1, 6)}
    report = _diagnostic_report(groups)
    staging = directory.parent / f".{directory.name}.staging"
    if staging.exists():
        raise FileExistsError("staging_directory_exists")
    staging.mkdir(parents=True)
    try:
        _write_artifacts(staging, groups, report)
        if directory.exists():
            directory.rmdir()
        staging.rename(directory)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return report


def _replace_diagnostics(directory: Path) -> dict[str, object]:
    backup = directory.parent / f"{directory.name}.previous"
    if backup.exists():
        raise FileExistsError("recoverable_backup_exists")
    if directory.exists():
        directory.rename(backup)
    try:
        return build_diagnostics(directory)
    except Exception:
        if directory.exists():
            shutil.rmtree(directory)
        if backup.exists():
            backup.rename(directory)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("1", "2", "3", "4", "5", "all"), default="all")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    if args.group == "all":
        if args.replace:
            _replace_diagnostics(args.output)
        else:
            build_diagnostics(args.output)
    else:
        if args.replace and args.output.exists():
            target = args.output / f"group-{args.group}.json"
            if target.exists():
                target.rename(target.with_suffix(".json.previous"))
        run_group(int(args.group), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
