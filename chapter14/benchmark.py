"""Benchmark Card loading and deterministic comparability auditing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import BenchmarkCard


FIXTURE_PATH = Path(__file__).with_name("fixtures") / "benchmark-cards.json"

CRITICAL_FIELDS = (
    "benchmark_id",
    "benchmark_version",
    "task_subset",
    "metric",
)

CONTROLLED_FIELDS = (
    "attempts_per_task",
    "contamination_risk",
    "environment",
    "exclusions",
    "harness",
    "model",
    "retry_policy",
    "step_budget",
    "subject",
    "task_period",
    "timeout_ms",
    "token_budget",
    "tools",
)

REQUIRED_PROVENANCE_FIELDS = tuple(BenchmarkCard.__dataclass_fields__)


def load_benchmark_cards(path: Path | None = None) -> tuple[BenchmarkCard, ...]:
    """Load repository cards while refusing incomplete provenance."""
    source_path = path or FIXTURE_PATH
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("benchmark_cards_must_be_a_list")

    cards: list[BenchmarkCard] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"invalid_benchmark_card:{index}")
        for field_name in REQUIRED_PROVENANCE_FIELDS:
            if field_name not in item:
                raise ValueError(f"missing_benchmark_field:{field_name}")
        for field_name in (*CRITICAL_FIELDS, *CONTROLLED_FIELDS, "source"):
            if item.get(field_name) in (None, ""):
                raise ValueError(f"missing_benchmark_field:{field_name}")
        cards.append(BenchmarkCard(**item))
    return tuple(cards)


def compare_benchmark_cards(left: BenchmarkCard, right: BenchmarkCard) -> dict[str, object]:
    """Compare measurement contracts; scores deliberately do not affect comparability."""
    missing_fields = sorted(
        field_name
        for field_name in CRITICAL_FIELDS
        if getattr(left, field_name) in (None, "") or getattr(right, field_name) in (None, "")
    )
    critical_differences = sorted(
        field_name
        for field_name in CRITICAL_FIELDS
        if field_name not in missing_fields and getattr(left, field_name) != getattr(right, field_name)
    )
    controlled_differences = sorted(
        field_name
        for field_name in CONTROLLED_FIELDS
        if getattr(left, field_name) != getattr(right, field_name)
    )
    different_fields = sorted((*critical_differences, *controlled_differences))

    if missing_fields:
        verdict = "not_comparable"
        reason_codes = ["critical_contract_missing"]
    elif critical_differences:
        verdict = "not_comparable"
        reason_codes = ["critical_contract_mismatch"]
    elif controlled_differences:
        verdict = "partially_comparable"
        reason_codes = ["controlled_configuration_mismatch"]
    else:
        verdict = "comparable"
        reason_codes = ["contracts_match"]

    return {
        "verdict": verdict,
        "different_fields": different_fields,
        "missing_fields": missing_fields,
        "reason_codes": reason_codes,
        "limits": ["contract_comparison_only", "task_representativeness_not_proven"],
    }
