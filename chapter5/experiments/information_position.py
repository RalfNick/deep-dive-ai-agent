from __future__ import annotations

from ..context.contracts import BuildConfig, ContextKind, DecisionKind
from ..fixtures.canonical import (
    EXPECTED_REQUIREMENTS,
    REPOSITORY,
    TARGET_PATH,
    TASK_ID,
    canonical_sources,
)
from ..probes import ModelProbe
from .common import CaseDefinition, render_records, run_case


POSITION_ORDERS = {
    "front": (
        ContextKind.FACT,
        ContextKind.INSTRUCTION,
        ContextKind.TASK,
        ContextKind.ARTIFACT,
        ContextKind.OBSERVATION,
        ContextKind.TOOL_SCHEMA,
    ),
    "middle": (
        ContextKind.INSTRUCTION,
        ContextKind.TASK,
        ContextKind.ARTIFACT,
        ContextKind.FACT,
        ContextKind.OBSERVATION,
        ContextKind.TOOL_SCHEMA,
    ),
    "back": (
        ContextKind.INSTRUCTION,
        ContextKind.TASK,
        ContextKind.ARTIFACT,
        ContextKind.OBSERVATION,
        ContextKind.TOOL_SCHEMA,
        ContextKind.FACT,
    ),
}


def run_information_position(
    probe: ModelProbe | None = None,
    *,
    live: bool = False,
) -> tuple:
    cases: list[CaseDefinition] = []
    for template in (1, 2, 3):
        sources = canonical_sources(task_template=template)
        for position in ("front", "middle", "back"):
            cases.append(
                CaseDefinition(
                    experiment="information_position",
                    variant=f"{position}_t{template}",
                    sources=sources,
                    config=BuildConfig.for_task(
                        REPOSITORY,
                        TARGET_PATH,
                        TASK_ID,
                        budget_units=5_000,
                        section_order=POSITION_ORDERS[position],
                        expected_requirements=EXPECTED_REQUIREMENTS,
                    ),
                    expected_kind=DecisionKind.TOOL,
                    expected_tool="apply_patch",
                    required_arguments=frozenset({"path", "old", "new"}),
                    irrelevant_source_ids=frozenset(),
                    supported_claims=("the same selected set can be serialized in different orders",),
                    unsupported_claims=("a universal lost-in-the-middle effect for every model",),
                )
            )
    return tuple(run_case(case, probe=probe, live=live) for case in cases)


if __name__ == "__main__":
    print(render_records(run_information_position()), end="")
