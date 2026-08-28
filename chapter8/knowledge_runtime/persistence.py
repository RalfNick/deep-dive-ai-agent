from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": "))


def write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((canonical_json(payload) + "\n").encode("utf-8"))
    return path


def write_markdown(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
    path.write_bytes(normalized.encode("utf-8"))
    return path


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    path.write_bytes(payload)
    return path
