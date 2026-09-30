"""Constrained fixture loader: no caller-supplied path traversal."""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> bytes:
    if not name or name in {".", ".."} or "/" in name or "\\" in name or ":" in name:
        raise ValueError("fixture name must be a single file name")
    path = _ROOT / name
    if path.is_symlink() or not path.is_file():
        if path.is_symlink():
            raise ValueError("fixture symlink not allowed")
        raise FileNotFoundError(name)
    return path.read_bytes()
