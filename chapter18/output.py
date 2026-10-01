from hashlib import sha256
import json
from pathlib import Path
from .contracts import ExerciseReport, TeamReport
from .fixtures import checked_path
from .reporting import validate_case, validate_exercises, validate_report
from .system import encode


def canonical_json(payload: object) -> bytes:
    return (json.dumps(encode(payload), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _write(root, destination, payloads, schema):
    dest = checked_path(root, destination, prefixes=("chapter18/.runs", "chapter18/reports"), new=True)
    manifest = canonical_json({"schema_version": schema, "files": {name: sha256(data).hexdigest() for name, data in sorted(payloads.items())}})
    dest.mkdir(parents=True)
    paths = []
    for name, data in (*sorted(payloads.items()), ("manifest.json", manifest)):
        path = dest / name
        with path.open("xb") as stream:
            stream.write(data)
        paths.append(path)
    return tuple(paths)


def write_bundle(root: Path, destination: Path, report: TeamReport, exercises: ExerciseReport) -> tuple[Path, ...]:
    validate_report(report)
    validate_exercises(exercises)
    payloads = {f"group-{g['group']}.json": canonical_json(g) for g in report["groups"]}
    payloads["team-report.json"] = canonical_json(report)
    payloads["exercise-results.json"] = canonical_json(exercises)
    lines = ["# 第18章协作机制报告", "", "固定策略教学案例，不是模型或SDK排名。", "", "| 案例 | 状态 | 覆盖 | 工具调用 |", "| --- | --- | --- | --- |"]
    for g in report["groups"]:
        for c in g["cases"]:
            m = c["metrics"]
            lines.append(f"| {c['case_id']} | {c['status']} | {m['coverage_numerator']}/{m['coverage_denominator']} | {m['tool_calls']} |")
    lines += ["", "状态、覆盖、冲突、拒绝、写入与验收分别统计；不提供成功率总分。"]
    payloads["summary.md"] = ("\n".join(lines) + "\n").encode()
    return _write(root, destination, payloads, "chapter18.team.v1")


def write_partial(root: Path, destination: Path, group: int, cases) -> tuple[Path, ...]:
    for case in cases:
        validate_case(case)
    payload = {"schema_version": "chapter18.team.partial.v1", "group": group, "cases": list(cases), "partial": True}
    return _write(root, destination, {f"group-{group}.json": canonical_json(payload)}, "chapter18.team.partial.v1")


def write_answer(root: Path, destination: Path, exercises: ExerciseReport) -> Path:
    validate_exercises(exercises)
    path = checked_path(root, destination, prefixes=("chapter18/.runs",), new=True)
    if path.suffix != ".json":
        raise ValueError("answer output must be JSON")
    payload = canonical_json(exercises)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
    return path
