from __future__ import annotations

from pathlib import Path


class PathGuardViolation(PermissionError):
    """A proposed path resolves outside the configured workspace root."""


class WorkspacePathGuard:
    """Application-level path containment, not an operating-system sandbox."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, relative_path: str, *, for_write: bool) -> Path:
        del for_write
        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise PathGuardViolation(
                f"path escapes workspace: {relative_path}"
            ) from exc
        return candidate
