"""Canonical bundle writer with conservative output boundaries."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import stat

from .evidence import validate_report


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       separators=(",", ": ")) + "\n").encode("utf-8")


def _is_reparse(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) &
                                     getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _new_destination(root: Path, destination: Path) -> Path:
    root = Path(os.path.abspath(root))
    raw = destination if destination.is_absolute() else root / destination
    if ".." in raw.parts:
        raise ValueError("parent traversal not allowed")
    path = Path(os.path.abspath(raw))
    try:
        rel = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("output is outside repository") from exc
    parts = rel.parts
    if len(parts) < 3 or parts[0] != "chapter17" or parts[1] not in {".runs", "reports"}:
        raise ValueError("output must be within chapter17/.runs or chapter17/reports")
    for candidate in (root, *reversed(path.parents)):
        if _is_reparse(candidate):
            raise ValueError("reparse/symlink parent not allowed")
    if _is_reparse(path):
        raise ValueError("reparse/symlink destination not allowed")
    if path.exists():
        raise FileExistsError(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def _finish(path: Path, payloads: dict[str, bytes]) -> tuple[Path, ...]:
    manifest = {name: sha256(data).hexdigest() for name, data in sorted(payloads.items())}
    payloads["manifest.json"] = canonical_json({"schema_version": "chapter17.bundle.v1",
                                                "sha256": manifest})
    result = []
    for name, data in sorted(payloads.items()):
        target = path / name
        with target.open("xb") as stream:
            stream.write(data)
        result.append(target)
    return tuple(result)


def write_bundle(root: Path, destination: Path, report: dict,
                 exercises: dict | None = None) -> tuple[Path, ...]:
    validate_report(report)
    payloads = {f"group-{group['id']}.json": canonical_json(group) for group in report["groups"]}
    payloads["report.json"] = canonical_json(report)
    summary = report["summary"]
    payloads["summary.md"] = (
        "# 第17章固定实验摘要\n\n"
        f"案例：{summary['cases_total']}；回答：{summary['answers']}；未知：{summary['unknown']}；"
        f"阻断：{summary['blocked']}；刷新：{summary['refresh']}；"
        f"安全违规：{summary['security_violations']}；证据覆盖："
        f"{summary['evidence_covered']}/{summary['evidence_total']}。\n\n"
        "这只证明固定夹具下的边界行为，不衡量真实模型能力。\n"
    ).encode("utf-8")
    if exercises is not None:
        payloads["exercise-results.json"] = canonical_json(exercises)
    path = _new_destination(root, destination)
    return _finish(path, payloads)


def write_single_group(root: Path, destination: Path, group: dict,
                       proofs: dict[str, str]) -> tuple[Path, ...]:
    if any(not set(case["evidence_ids"]) <= set(proofs) for case in group["cases"]):
        raise ValueError("unresolved group evidence")
    path = _new_destination(root, destination)
    return _finish(path, {f"group-{group['id']}.json": canonical_json(group)})
