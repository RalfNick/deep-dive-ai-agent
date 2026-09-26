from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from chapter14.benchmark import compare_benchmark_cards, load_benchmark_cards
from chapter14.contracts import BenchmarkCard


ROOT = Path(__file__).resolve().parents[2]


def _card(**overrides: object) -> BenchmarkCard:
    values: dict[str, object] = {
        "benchmark_id": "repo-repair",
        "benchmark_version": "2026-09",
        "task_subset": "verified",
        "task_period": "2026-q3",
        "subject": "agent-system",
        "harness": "harness-a",
        "model": "model-a",
        "tools": ("read", "edit", "test"),
        "environment": "python-3.11",
        "step_budget": 40,
        "token_budget": 20_000,
        "timeout_ms": 30_000,
        "retry_policy": "bounded-1",
        "attempts_per_task": 1,
        "metric": "resolved_percent",
        "exclusions": (),
        "contamination_risk": "unknown",
        "source": "fixture://control-a",
        "score": 72.0,
    }
    values.update(overrides)
    return BenchmarkCard(**values)  # type: ignore[arg-type]


def test_exact_control_pair_is_comparable() -> None:
    result = compare_benchmark_cards(_card(), _card(source="fixture://control-b", score=74.0))

    assert result == {
        "verdict": "comparable",
        "different_fields": [],
        "missing_fields": [],
        "reason_codes": ["contracts_match"],
        "limits": ["contract_comparison_only", "task_representativeness_not_proven"],
    }


def test_same_score_with_harness_or_budget_changes_is_partial() -> None:
    result = compare_benchmark_cards(
        _card(),
        _card(harness="harness-b", step_budget=80, retry_policy="bounded-3"),
    )

    assert result["verdict"] == "partially_comparable"
    assert result["different_fields"] == ["harness", "retry_policy", "step_budget"]
    assert result["reason_codes"] == ["controlled_configuration_mismatch"]
    assert "score" not in result["different_fields"]


@pytest.mark.parametrize(
    "right",
    [
        _card(task_subset=""),
        _card(benchmark_version="2026-10"),
        _card(metric="pass_at_1"),
    ],
)
def test_missing_or_different_task_metric_contract_is_not_comparable(right: BenchmarkCard) -> None:
    result = compare_benchmark_cards(_card(), right)

    assert result["verdict"] == "not_comparable"
    assert result["reason_codes"] in (
        ["critical_contract_missing"],
        ["critical_contract_mismatch"],
    )


def test_fixture_contains_true_control_and_same_score_misleading_pairs() -> None:
    cards = load_benchmark_cards()
    by_source = {card.source: card for card in cards}

    control = compare_benchmark_cards(by_source["fixture://control-a"], by_source["fixture://control-b"])
    misleading = compare_benchmark_cards(
        by_source["fixture://same-score-a"], by_source["fixture://same-score-b"]
    )

    assert control["verdict"] == "comparable"
    assert misleading["verdict"] == "partially_comparable"
    assert by_source["fixture://same-score-a"].score == by_source["fixture://same-score-b"].score


def test_loader_rejects_missing_provenance(tmp_path: Path) -> None:
    raw = [_card().to_dict()]
    raw[0].pop("source")
    path = tmp_path / "cards.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError, match="missing_benchmark_field:source"):
        load_benchmark_cards(path)
