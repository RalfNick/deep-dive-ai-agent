from __future__ import annotations

from ..context.contracts import BuildConfig, DecisionKind
from ..fixtures.canonical import (
    EXPECTED_REQUIREMENTS,
    REPOSITORY,
    TARGET_PATH,
    TASK_ID,
    canonical_sources,
)
from ..probes import ModelProbe
from .common import CaseDefinition, render_records, run_case


def run_tool_description(
    probe: ModelProbe | None = None,
    *,
    live: bool = False,
) -> tuple:
    cases: list[CaseDefinition] = []
    for variant in ("vague", "precise", "precise_with_negative_constraint"):
        expected = (
            DecisionKind.NEEDS_CONTEXT if variant == "vague" else DecisionKind.TOOL
        )
        cases.append(
            CaseDefinition(
                experiment="tool_description",
                variant=variant,
                sources=canonical_sources(tool_description=variant),
                config=BuildConfig.for_task(
                    REPOSITORY,
                    TARGET_PATH,
                    TASK_ID,
                    budget_units=5_000,
                    expected_requirements=EXPECTED_REQUIREMENTS,
                ),
                expected_kind=expected,
                expected_tool="apply_patch" if expected is DecisionKind.TOOL else None,
                required_arguments=(
                    frozenset({"path", "old", "new"})
                    if expected is DecisionKind.TOOL
                    else frozenset()
                ),
                irrelevant_source_ids=frozenset(),
                supported_claims=("tool-contract wording changes deterministic probe behavior",),
                unsupported_claims=("description clarity is isolated from length in natural language",),
            )
        )
    return tuple(run_case(case, probe=probe, live=live) for case in cases)


if __name__ == "__main__":
    print(render_records(run_tool_description()), end="")
