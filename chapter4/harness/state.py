from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .contracts import RunState, ToolResult


def _key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


class JsonCheckpointStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve() / "checkpoints"

    def save(self, state: RunState) -> str:
        path = self.root / f"{_key(state.run_id)}.json"
        _atomic_write(path, state.to_json())
        return str(path)

    def load(self, run_id: str) -> RunState:
        path = self.root / f"{_key(run_id)}.json"
        if not path.exists():
            raise KeyError(f"checkpoint not found: {run_id}")
        state = RunState.from_json(path.read_text(encoding="utf-8"))
        if state.run_id != run_id:
            raise ValueError("checkpoint identity mismatch")
        return state


class ActionReceiptStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve() / "receipts"

    def record(self, action_id: str, result: ToolResult) -> None:
        if result.action_id != action_id:
            raise ValueError("receipt action_id mismatch")
        path = self.root / f"{_key(action_id)}.json"
        if path.exists():
            return
        payload = {"action_id": action_id, "result": asdict(result)}
        _atomic_write(
            path,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        )

    def get(self, action_id: str) -> ToolResult | None:
        path = self.root / f"{_key(action_id)}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("action_id") != action_id:
            raise ValueError("receipt identity mismatch")
        return ToolResult.from_dict(payload["result"])
