from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat

from .contracts import JsonObject, SourceDoc, relative_path


def checked_path(root: Path, path: Path, *, prefixes: tuple[str, ...], new: bool = False) -> Path:
    root = Path(os.path.abspath(root))
    raw = path if path.is_absolute() else root / path
    if ".." in raw.parts:
        raise ValueError("parent traversal denied")
    target = Path(os.path.abspath(raw))
    try:
        rel = target.relative_to(root).as_posix()
    except ValueError:
        raise ValueError("path outside repository") from None
    if not any(rel.startswith(p + "/") for p in prefixes):
        raise ValueError("path outside authorized subtree")
    for part in (root, *target.parents, target):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("reparse path denied")
    if new and target.exists():
        raise ValueError("existing path refused")
    return target


def load_sources(root: Path) -> tuple[SourceDoc, ...]:
    index = json.loads((root / "chapter18/fixtures/knowledge.json").read_text(encoding="utf-8"))
    docs = []
    for row in index:
        relative_path(row["location"])
        file = checked_path(root, Path(row["location"]), prefixes=("chapter18/fixtures/knowledge",))
        data = file.read_bytes()
        docs.append(SourceDoc(row["source_id"], row["location"], row["version"], frozenset(row["principals"]),
                              row["eligible"], data.decode("utf-8"), tuple(sorted(row["facts"].items())), sha256(data).hexdigest()))
    if len({d.source_id for d in docs}) != len(docs):
        raise ValueError("duplicate source ID")
    return tuple(docs)


def load_case_specs(root: Path) -> tuple[JsonObject, ...]:
    rows = json.loads((root / "chapter18/fixtures/cases.json").read_text(encoding="utf-8"))
    if len(rows) != 20 or len({r["case_id"] for r in rows}) != 20:
        raise ValueError("twenty unique cases required")
    if [sum(r["group"] == g for r in rows) for g in range(1, 6)] != [4] * 5:
        raise ValueError("four cases per group required")
    return tuple(rows)


def create_workspace(root: Path, destination: Path) -> Path:
    dest = checked_path(root, destination, prefixes=("chapter18/.runs",), new=True)
    source = root / "chapter18/fixtures/link-checker"
    for entry in source.rglob("*"):
        checked_path(root, entry, prefixes=("chapter18/fixtures/link-checker",))
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)
    return dest
