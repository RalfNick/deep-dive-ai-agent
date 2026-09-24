"""Load and validate the fixed teaching evaluation suite."""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import TaskSpec


def load_tasks(path: Path | None = None) -> tuple[TaskSpec, ...]:
    source = path or Path(__file__).with_name("fixtures") / "tasks.json"
    rows = json.loads(Path(source).read_text(encoding="utf-8"))
    tasks = tuple(TaskSpec(
        task_id=row["task_id"], prompt=row["prompt"], slice=row["slice"],
        split=row["split"], expected_output=row["expected_output"],
        allowed_write_prefixes=tuple(row["allowed_write_prefixes"]),
        protected_paths=tuple(row["protected_paths"]), max_steps=row["max_steps"],
        max_tool_calls=row["max_tool_calls"], baseline_successes=row["baseline_successes"],
        candidate_successes=row["candidate_successes"],
        fixture_id=row["fixture_id"], labels=tuple(row["labels"]),
        success_conditions=tuple(row["success_conditions"]),
        seed_strategy=row["seed_strategy"],
    ) for row in rows)
    if len({task.task_id for task in tasks}) != len(tasks):
        raise ValueError("duplicate_task_id")
    return tasks
