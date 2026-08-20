from __future__ import annotations

from ..context.contracts import BuildConfig, DecisionKind, RawSource
from ..fixtures.canonical import (
    EXPECTED_REQUIREMENTS,
    REPOSITORY,
    TARGET_PATH,
    TASK_ID,
    FixtureSource,
    canonical_sources,
)
from ..probes import ModelProbe
from .common import CaseDefinition, render_records, run_case


def _case(
    variant: str,
    sources: tuple[FixtureSource, ...],
    *,
    budget: int,
    expected_kind: DecisionKind,
) -> CaseDefinition:
    return CaseDefinition(
        experiment="assembly_ablation",
        variant=variant,
        sources=sources,
        config=BuildConfig.for_task(
            REPOSITORY,
            TARGET_PATH,
            TASK_ID,
            budget_units=budget,
            expected_requirements=EXPECTED_REQUIREMENTS,
        ),
        expected_kind=expected_kind,
        expected_tool="apply_patch" if expected_kind is DecisionKind.TOOL else None,
        required_arguments=(
            frozenset({"path", "old", "new"})
            if expected_kind is DecisionKind.TOOL
            else frozenset()
        ),
        irrelevant_source_ids=frozenset(),
        supported_claims=("required reservation, deduplication, and missing-context signaling",),
        unsupported_claims=("model capability or production success rate",),
    )


def run_assembly_ablation(
    probe: ModelProbe | None = None,
    *,
    live: bool = False,
) -> tuple:
    complete = canonical_sources()
    missing = tuple(
        source for source in complete if source.raw.source_id != "test_pricing.py"
    )
    duplicate_test = next(
        source for source in complete if source.raw.source_id == "test_pricing.py"
    )
    duplicate = complete + (
        FixtureSource(
            raw=RawSource(
                source_id="test_pricing-copy.py",
                channel=duplicate_test.raw.channel,
                content=duplicate_test.raw.content,
                path="tests/test_pricing-copy.py",
                version=duplicate_test.raw.version,
            ),
            required_for=duplicate_test.required_for,
        ),
    )
    cases = (
        _case("complete", complete, budget=4_000, expected_kind=DecisionKind.TOOL),
        _case(
            "missing_required",
            missing,
            budget=4_000,
            expected_kind=DecisionKind.NEEDS_CONTEXT,
        ),
        _case("duplicate", duplicate, budget=4_000, expected_kind=DecisionKind.TOOL),
        _case(
            "tight_budget",
            complete,
            budget=180,
            expected_kind=DecisionKind.NEEDS_CONTEXT,
        ),
        _case(
            "required_restored",
            complete,
            budget=1_200,
            expected_kind=DecisionKind.TOOL,
        ),
    )
    return tuple(run_case(case, probe=probe, live=live) for case in cases)


if __name__ == "__main__":
    print(render_records(run_assembly_ablation()), end="")
