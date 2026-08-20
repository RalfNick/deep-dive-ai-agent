"""Generate all deterministic Chapter 6 reports without network access."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from chapter6.context_continuity.graders import ExperimentCase, ExperimentReport
from .common import ExperimentTraceRecord, UNSUPPORTED_CLAIMS

from . import (
    checkpoint_vs_rehydration,
    context_growth,
    failure_matrix,
    generational_drift,
    sliding_window,
    summary_vs_structured,
)


COMPARISON_SCOPE = (
    "deterministic semantic-continuity contract; not model or product ranking"
)
REPORT_FILENAMES = (
    "context-continuity.json",
    "context-continuity.md",
    "context-continuity-trace.jsonl",
)


@dataclass(frozen=True)
class CaseExpectation:
    decision_kind: str | None
    goal_retained: bool
    acceptance_retention: float
    constraint_retention: float
    negative_constraint_retention: float
    open_issue_retention: float
    rejected_hypothesis_retention: float
    locator_integrity: float | None
    resume_correct: bool | None
    duplicate_work_count: int | None
    false_completion: bool
    packet_contract_passed: bool | None
    trace_contract_passed: bool


@dataclass(frozen=True)
class ClaimExpectation:
    supported_claims: tuple[str, ...]
    unsupported_claims: tuple[str, ...]


def _expected(
    decision_kind: str | None,
    *,
    goal: bool,
    acceptance: float,
    constraint: float,
    negative: float,
    open_issue: float,
    rejected: float,
    locator: float | None = None,
    resume: bool | None = None,
    duplicate: int | None = None,
    false_completion: bool = False,
    packet: bool | None = None,
) -> CaseExpectation:
    return CaseExpectation(
        decision_kind=decision_kind,
        goal_retained=goal,
        acceptance_retention=acceptance,
        constraint_retention=constraint,
        negative_constraint_retention=negative,
        open_issue_retention=open_issue,
        rejected_hypothesis_retention=rejected,
        locator_integrity=locator,
        resume_correct=resume,
        duplicate_work_count=duplicate,
        false_completion=false_completion,
        packet_contract_passed=packet,
        trace_contract_passed=True,
    )


REFERENCE_EXPECTATIONS: dict[tuple[str, str], CaseExpectation] = {
    ("context_growth", "append-all-cursor-08"): _expected(
        None, goal=True, acceptance=1.0, constraint=1.0, negative=1.0, open_issue=1.0, rejected=1.0
    ),
    ("context_growth", "append-all-cursor-24"): _expected(
        "apply_legacy_compatible_patch", goal=True, acceptance=1.0, constraint=1.0, negative=1.0, open_issue=1.0, rejected=1.0
    ),
    ("sliding_window", "sliding-window-8-events"): _expected(
        "unsafe_signature_change", goal=True, acceptance=0.0, constraint=0.5, negative=0.0, open_issue=0.0, rejected=1.0
    ),
    ("summary_vs_structured", "summary-only-v1"): _expected(
        "unsafe_signature_change", goal=True, acceptance=0.0, constraint=0.0, negative=0.0, open_issue=0.0, rejected=0.0
    ),
    ("summary_vs_structured", "structured-compaction-v1"): _expected(
        "apply_legacy_compatible_patch", goal=True, acceptance=1.0, constraint=1.0, negative=1.0, open_issue=1.0, rejected=1.0, locator=1.0
    ),
    ("checkpoint_vs_rehydration", "checkpoint-only-v1"): _expected(
        "unsafe_signature_change", goal=True, acceptance=0.0, constraint=0.0, negative=0.0, open_issue=0.0, rejected=0.0
    ),
    ("checkpoint_vs_rehydration", "rehydrated-context-v1"): _expected(
        "apply_legacy_compatible_patch", goal=True, acceptance=1.0, constraint=1.0, negative=1.0, open_issue=1.0, rejected=1.0, locator=1.0, resume=True, duplicate=0, packet=True
    ),
    ("generational_drift", "summary-generation-1"): _expected(
        "unsafe_signature_change", goal=True, acceptance=0.0, constraint=0.0, negative=0.0, open_issue=0.0, rejected=0.0
    ),
    ("generational_drift", "summary-generation-2"): _expected(
        "unsafe_signature_change", goal=True, acceptance=0.0, constraint=0.0, negative=0.0, open_issue=0.0, rejected=0.0
    ),
    ("generational_drift", "structured-regenerated-v1"): _expected(
        "apply_legacy_compatible_patch", goal=True, acceptance=1.0, constraint=1.0, negative=1.0, open_issue=1.0, rejected=1.0, locator=1.0
    ),
    ("failure_matrix", "early-constraint-loss"): _expected(
        "unsafe_signature_change", goal=True, acceptance=0.0, constraint=0.5, negative=0.0, open_issue=0.0, rejected=1.0
    ),
    ("failure_matrix", "omitted-open-failure"): _expected(
        "injected_summary_claims_complete", goal=True, acceptance=1.0, constraint=1.0, negative=1.0, open_issue=0.0, rejected=1.0, false_completion=True
    ),
    ("failure_matrix", "workspace-digest-mismatch"): _expected(
        "rejected_stale_workspace_digest", goal=False, acceptance=0.0, constraint=0.0, negative=0.0, open_issue=0.0, rejected=0.0
    ),
    ("failure_matrix", "unsupported-artifact-schema"): _expected(
        "rejected_artifact_schema", goal=False, acceptance=0.0, constraint=0.0, negative=0.0, open_issue=0.0, rejected=0.0
    ),
    ("failure_matrix", "corrupt-artifact-source-digest"): _expected(
        "rejected_artifact_source_digest_mismatch", goal=False, acceptance=0.0, constraint=0.0, negative=0.0, open_issue=0.0, rejected=0.0
    ),
}

REFERENCE_BYTES: dict[tuple[str, str], tuple[int, int]] = {
    ("checkpoint_vs_rehydration", "checkpoint-only-v1"): (12_108, 583),
    ("checkpoint_vs_rehydration", "rehydrated-context-v1"): (12_108, 3_447),
    ("context_growth", "append-all-cursor-08"): (3_950, 3_950),
    ("context_growth", "append-all-cursor-24"): (12_108, 12_108),
    ("failure_matrix", "corrupt-artifact-source-digest"): (12_108, 7_217),
    ("failure_matrix", "early-constraint-loss"): (12_108, 4_337),
    ("failure_matrix", "omitted-open-failure"): (12_108, 3_579),
    ("failure_matrix", "unsupported-artifact-schema"): (12_108, 7_272),
    ("failure_matrix", "workspace-digest-mismatch"): (12_108, 3_579),
    ("generational_drift", "structured-regenerated-v1"): (12_108, 3_579),
    ("generational_drift", "summary-generation-1"): (12_108, 843),
    ("generational_drift", "summary-generation-2"): (843, 16),
    ("sliding_window", "sliding-window-8-events"): (12_108, 4_337),
    ("summary_vs_structured", "structured-compaction-v1"): (12_108, 3_579),
    ("summary_vs_structured", "summary-only-v1"): (12_108, 843),
}


def _claims(*supported_claims: str) -> ClaimExpectation:
    return ClaimExpectation(
        supported_claims=tuple(supported_claims),
        unsupported_claims=UNSUPPORTED_CLAIMS,
    )


REFERENCE_CLAIMS: dict[tuple[str, str], ClaimExpectation] = {
    ("checkpoint_vs_rehydration", "checkpoint-only-v1"): _claims(
        "the checkpoint restores the declared next step while the stable task contract provides only the goal anchor",
        "no ContextPacket contract is measured for the checkpoint-only control",
    ),
    ("checkpoint_vs_rehydration", "rehydrated-context-v1"): _claims(
        "rehydration produced an actual Chapter 5 ContextPacket and ContextBuildTrace",
        "the fixed policy continued with the compatible patch without repeating the rejected attempt",
    ),
    ("context_growth", "append-all-cursor-08"): _claims(
        "canonical UTF-8 bytes are measured after event 8",
        "append-all retains each observed event at that cursor",
    ),
    ("context_growth", "append-all-cursor-24"): _claims(
        "canonical UTF-8 bytes are measured after event 24",
        "append-all retains each observed event at that cursor",
    ),
    ("failure_matrix", "corrupt-artifact-source-digest"): _claims(
        "the injected boundary was rejected with artifact_source_digest_mismatch",
    ),
    ("failure_matrix", "early-constraint-loss"): _claims(
        "dropping event 2 sends the fixed policy into its unsafe-signature branch",
    ),
    ("failure_matrix", "omitted-open-failure"): _claims(
        "the injected summary replaces an unresolved issue with an unsupported completion claim",
    ),
    ("failure_matrix", "unsupported-artifact-schema"): _claims(
        "the injected boundary was rejected with artifact_rejected_schema",
    ),
    ("failure_matrix", "workspace-digest-mismatch"): _claims(
        "the stale workspace was rejected with stale_workspace_digest",
    ),
    ("generational_drift", "structured-regenerated-v1"): _claims(
        "structured regeneration from the frozen event log is byte-stable: true",
    ),
    ("generational_drift", "summary-generation-1"): _claims(
        "the first controlled free-text generation loses structured constraints and open state",
    ),
    ("generational_drift", "summary-generation-2"): _claims(
        "the declared second-generation transform retains only the goal key",
    ),
    ("sliding_window", "sliding-window-8-events"): _claims(
        "the eight-event window omits the event-2 public-signature constraint",
        "the fixed policy enters its unsafe-signature controlled failure branch",
    ),
    ("summary_vs_structured", "structured-compaction-v1"): _claims(
        "the structured artifact retains every declared semantic field",
        "all generated evidence locators match the frozen workspace digest",
    ),
    ("summary_vs_structured", "summary-only-v1"): _claims(
        "the fixed summary rule omits declared constraints and the open failure",
        "the comparison measures this controlled rule, not model summarization quality",
    ),
}


def validate_reference_cases(cases: tuple[ExperimentCase, ...]) -> bool:
    indexed = {(case.experiment, case.variant): case for case in cases}
    if (
        len(indexed) != len(cases)
        or set(indexed) != set(REFERENCE_EXPECTATIONS)
        or set(indexed) != set(REFERENCE_BYTES)
        or set(indexed) != set(REFERENCE_CLAIMS)
    ):
        return False
    for key, expectation in REFERENCE_EXPECTATIONS.items():
        case = indexed[key]
        grade = case.grade
        claims = REFERENCE_CLAIMS[key]
        observed = CaseExpectation(
            decision_kind=case.decision_kind,
            goal_retained=grade.goal_retained,
            acceptance_retention=grade.acceptance_retention,
            constraint_retention=grade.constraint_retention,
            negative_constraint_retention=grade.negative_constraint_retention,
            open_issue_retention=grade.open_issue_retention,
            rejected_hypothesis_retention=grade.rejected_hypothesis_retention,
            locator_integrity=grade.locator_integrity,
            resume_correct=grade.resume_correct,
            duplicate_work_count=grade.duplicate_work_count,
            false_completion=grade.false_completion,
            packet_contract_passed=grade.packet_contract_passed,
            trace_contract_passed=grade.trace_contract_passed,
        )
        if (
            case.sample_count != 1
            or (
                case.serialized_bytes_before,
                case.serialized_bytes_after,
            )
            != REFERENCE_BYTES[key]
            or case.supported_claims != claims.supported_claims
            or case.unsupported_claims != claims.unsupported_claims
            or observed != expectation
        ):
            return False
    return True


def build_report(cases: tuple[ExperimentCase, ...]) -> ExperimentReport:
    return ExperimentReport(
        comparison_scope=COMPARISON_SCOPE,
        cases=cases,
        run_status="passed" if validate_reference_cases(cases) else "failed",
    )


def run_all_with_traces() -> tuple[ExperimentReport, tuple[ExperimentTraceRecord, ...]]:
    outputs = (
        context_growth.run_with_trace(),
        sliding_window.run_with_trace(),
        summary_vs_structured.run_with_trace(),
        checkpoint_vs_rehydration.run_with_trace(),
        generational_drift.run_with_trace(),
        failure_matrix.run_with_trace(),
    )
    cases = tuple(sorted((case for group, _ in outputs for case in group), key=lambda case: (case.experiment, case.variant)))
    traces = tuple(
        sorted(
            (record for _, group in outputs for record in group),
            key=lambda record: (
                record.experiment,
                record.variant,
                record.stage,
                record.outcome,
                record.item_key or "",
                record.evidence_digest,
            ),
        )
    )
    report = build_report(cases)
    return report, traces


def run_all() -> ExperimentReport:
    return run_all_with_traces()[0]


def _cell(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _markdown(report: ExperimentReport) -> str:
    lines = [
        "# Chapter 6 deterministic context-continuity report",
        "",
        f"Scope: {report.comparison_scope}",
        "",
        "All rows use `sample_count=1`. Byte columns are canonical UTF-8 bytes, not provider tokens.",
        "",
        "| Experiment | Variant | Sample count | Bytes before | Bytes after | Goal | Acceptance | Constraint | Negative constraint | Open issue | Rejected hypothesis | Locator integrity | Resume | Duplicate work | False completion | Packet | Trace | Decision |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- | --- |",
    ]
    for case in report.cases:
        grade = case.grade
        lines.append(
            "| "
            + " | ".join(
                (
                    case.experiment,
                    case.variant,
                    str(case.sample_count),
                    str(case.serialized_bytes_before),
                    str(case.serialized_bytes_after),
                    _cell(grade.goal_retained),
                    _cell(grade.acceptance_retention),
                    _cell(grade.constraint_retention),
                    _cell(grade.negative_constraint_retention),
                    _cell(grade.open_issue_retention),
                    _cell(grade.rejected_hypothesis_retention),
                    _cell(grade.locator_integrity),
                    _cell(grade.resume_correct),
                    _cell(grade.duplicate_work_count),
                    _cell(grade.false_completion),
                    _cell(grade.packet_contract_passed),
                    _cell(grade.trace_contract_passed),
                    _cell(case.decision_kind),
                )
            )
            + " |"
        )
    lines.extend(("", f"Run status: `{report.run_status}`", ""))
    return "\n".join(lines)


def _trace_jsonl(records: tuple[ExperimentTraceRecord, ...]) -> str:
    return "".join(
        json.dumps(asdict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    )


def write_reports(output: Path) -> tuple[Path, Path, Path]:
    report, traces = run_all_with_traces()
    output.mkdir(parents=True, exist_ok=True)
    paths = tuple(output / filename for filename in REPORT_FILENAMES)
    paths[0].write_text(report.to_json(), encoding="utf-8", newline="\n")
    paths[1].write_text(_markdown(report), encoding="utf-8", newline="\n")
    paths[2].write_text(_trace_jsonl(traces), encoding="utf-8", newline="\n")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = write_reports(args.output)
    report = run_all()
    for path in paths:
        print(path.as_posix())
    return 0 if report.run_status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
