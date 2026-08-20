"""区分 JSON 语法、Schema 形状与业务语义三层校验。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PatchPlan:
    file: str
    start_line: int
    end_line: int
    risk: str


ALLOWED_RISKS = {"low", "medium", "high"}


def validate(raw: str) -> tuple[str, PatchPlan | None]:
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        return f"syntax_error: {error.msg}", None

    if not isinstance(data, dict):
        return "schema_error: root must be object", None
    expected = {"file", "start_line", "end_line", "risk"}
    if set(data) != expected:
        return f"schema_error: keys must equal {sorted(expected)}", None
    if not isinstance(data["file"], str) or not data["file"].endswith(".py"):
        return "schema_error: file must be a .py string", None
    if type(data["start_line"]) is not int or type(data["end_line"]) is not int:
        return "schema_error: line numbers must be integers", None
    if data["risk"] not in ALLOWED_RISKS:
        return f"schema_error: risk must be one of {sorted(ALLOWED_RISKS)}", None

    plan = PatchPlan(**data)
    if plan.start_line < 1 or plan.end_line < plan.start_line:
        return "semantic_error: require 1 <= start_line <= end_line", None
    if ".." in plan.file or plan.file.startswith(("/", "\\")):
        return "policy_error: file must stay inside the workspace", None
    return "ok", plan


def main() -> None:
    samples = {
        "invalid-json": '{"file": "app.py",}',
        "missing-field": '{"file":"app.py","start_line":8,"end_line":9}',
        "wrong-enum": '{"file":"app.py","start_line":8,"end_line":9,"risk":"tiny"}',
        "wrong-order": '{"file":"app.py","start_line":9,"end_line":8,"risk":"low"}',
        "path-escape": '{"file":"../app.py","start_line":8,"end_line":9,"risk":"high"}',
        "valid": '{"file":"src/app.py","start_line":8,"end_line":9,"risk":"low"}',
    }
    for name, raw in samples.items():
        status, plan = validate(raw)
        print(f"{name:<14} -> {status}")
        if plan:
            print(f"{'':<17} parsed={plan}")

    print("\n结论：结构化输出能解决形状问题，但业务约束和权限仍由应用负责。")


if __name__ == "__main__":
    main()
