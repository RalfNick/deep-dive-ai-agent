"""Atomic artifact and checkpoint stores for committed context boundaries."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from chapter5.context.contracts import (
    ContextKind,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)

from .contracts import CarryItem, CompactionArtifact, EvidenceLocator, RunCheckpoint
from .trace import canonical_json, stable_digest


def _write_atomically(path: Path, value: object) -> None:
    """Flush a sibling temporary file before atomically replacing ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temp_name = stream.name
            stream.write(canonical_json(value))
            stream.flush()
            os.fsync(stream.fileno())
        Path(temp_name).replace(path)
    finally:
        if temp_name is not None:
            temporary_path = Path(temp_name)
            if temporary_path.exists():
                temporary_path.unlink()


def _publish_once(path: Path, value: object) -> bool:
    """Atomically publish a complete sibling file without replacing a winner."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temp_name = stream.name
            stream.write(canonical_json(value))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp_name, path)
        except FileExistsError:
            return False
        return True
    finally:
        if temp_name is not None:
            temporary_path = Path(temp_name)
            if temporary_path.exists():
                temporary_path.unlink()


def _safe_record_path(root: Path, record_id: str, error_code: str) -> Path:
    if not record_id or Path(record_id).name != record_id or record_id in {".", ".."}:
        raise ValueError(error_code)
    return root / f"{record_id}.json"


def _artifact_data(artifact: CompactionArtifact) -> dict[str, Any]:
    return json.loads(canonical_json(artifact))


def _checkpoint_data(checkpoint: RunCheckpoint) -> dict[str, Any]:
    return json.loads(canonical_json(checkpoint))


def _carry_item_from_data(data: object) -> CarryItem:
    if not isinstance(data, dict):
        raise ValueError("invalid_artifact_record")
    try:
        return CarryItem(
            key=data["key"],
            kind=ContextKind(data["kind"]),
            content=data["content"],
            authority=InstructionAuthority(data["authority"]),
            trust=TrustLevel(data["trust"]),
            retention_priority=RetentionPriority(data["retention_priority"]),
            sensitivity=Sensitivity(data["sensitivity"]),
            source_event_ids=tuple(data["source_event_ids"]),
            required_for=frozenset(data.get("required_for", ())),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_artifact_record") from error


def _artifact_from_data(data: object) -> CompactionArtifact:
    if not isinstance(data, dict):
        raise ValueError("invalid_artifact_record")
    try:
        evidence = tuple(
            EvidenceLocator(
                locator_id=item["locator_id"],
                kind=item["kind"],
                ref=item["ref"],
                content_digest=item["content_digest"],
                workspace_digest=item["workspace_digest"],
            )
            for item in data["evidence_locators"]
        )
        return CompactionArtifact(
            artifact_id=data["artifact_id"],
            run_id=data["run_id"],
            source_event_range=tuple(data["source_event_range"]),
            goal=_carry_item_from_data(data["goal"]),
            acceptance_criteria=tuple(_carry_item_from_data(item) for item in data["acceptance_criteria"]),
            constraints=tuple(_carry_item_from_data(item) for item in data["constraints"]),
            decisions=tuple(_carry_item_from_data(item) for item in data["decisions"]),
            rejected_hypotheses=tuple(
                _carry_item_from_data(item) for item in data["rejected_hypotheses"]
            ),
            open_issues=tuple(_carry_item_from_data(item) for item in data["open_issues"]),
            verification_state=tuple(
                _carry_item_from_data(item) for item in data["verification_state"]
            ),
            evidence_locators=evidence,
            next_intent=_carry_item_from_data(data["next_intent"]),
            created_at=data["created_at"],
            source_digest=data["source_digest"],
            workspace_digest=data["workspace_digest"],
            schema_version=data.get("schema_version", "1.0"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_artifact_record") from error


def _checkpoint_from_data(data: object) -> RunCheckpoint:
    if not isinstance(data, dict):
        raise ValueError("invalid_checkpoint_record")
    try:
        return RunCheckpoint(
            run_id=data["run_id"],
            checkpoint_id=data["checkpoint_id"],
            next_step=data["next_step"],
            completed_steps=tuple(data["completed_steps"]),
            pending_step=data.get("pending_step"),
            event_cursor=data["event_cursor"],
            workspace_digest=data["workspace_digest"],
            artifact_id=data["artifact_id"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_checkpoint_record") from error


class ArtifactStore:
    """Immutable-by-ID local storage for compaction artifacts."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def write(self, artifact: CompactionArtifact) -> None:
        record = _artifact_data(artifact)
        path = _safe_record_path(
            self.root, artifact.artifact_id, "invalid_artifact_id"
        )
        envelope = {"record": record, "record_digest": stable_digest(record)}
        if _publish_once(path, envelope):
            return

        try:
            authoritative = json.loads(path.read_text(encoding="utf-8"))
            authoritative_record = authoritative["record"]
            authoritative_digest = authoritative["record_digest"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError("artifact_id_conflict") from error
        if (
            not isinstance(authoritative_digest, str)
            or stable_digest(authoritative_record) != authoritative_digest
            or authoritative_record != record
        ):
            raise ValueError("artifact_id_conflict")

    def read(self, artifact_id: str) -> CompactionArtifact | None:
        path = _safe_record_path(self.root, artifact_id, "invalid_artifact_id")
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            record = envelope["record"]
            digest = envelope["record_digest"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError("invalid_artifact_record") from error
        if not isinstance(digest, str) or stable_digest(record) != digest:
            raise ValueError("artifact_digest_mismatch")
        artifact = _artifact_from_data(record)
        if artifact.artifact_id != artifact_id:
            raise ValueError("artifact_id_mismatch")
        return artifact


class CheckpointStore:
    """Checkpoint records accepted only when their artifact boundary still matches."""

    def __init__(self, root: Path, *, artifact_store: ArtifactStore | None = None) -> None:
        self.root = Path(root)
        self.artifact_store = artifact_store or ArtifactStore(self.root.parent / "artifacts")

    def commit(self, checkpoint: RunCheckpoint) -> None:
        artifact = self.artifact_store.read(checkpoint.artifact_id)
        if artifact is None:
            raise ValueError("checkpoint_artifact_missing")
        record = _checkpoint_data(checkpoint)
        _write_atomically(
            _safe_record_path(self.root, checkpoint.checkpoint_id, "invalid_checkpoint_id"),
            {
                "record": record,
                "record_digest": stable_digest(record),
                "artifact_digest": stable_digest(_artifact_data(artifact)),
            },
        )

    def latest(self, run_id: str) -> RunCheckpoint | None:
        if not self.root.exists():
            return None
        candidates: list[RunCheckpoint] = []
        for path in self.root.glob("*.json"):
            checkpoint = self._read_if_committed(path)
            if checkpoint is not None and checkpoint.run_id == run_id:
                candidates.append(checkpoint)
        if not candidates:
            return None
        return max(candidates, key=lambda item: (item.event_cursor, item.checkpoint_id))

    def _read_if_committed(self, path: Path) -> RunCheckpoint | None:
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            record = envelope["record"]
            record_digest = envelope["record_digest"]
            artifact_digest = envelope["artifact_digest"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError("invalid_checkpoint_record") from error
        if not isinstance(record_digest, str) or stable_digest(record) != record_digest:
            raise ValueError("checkpoint_digest_mismatch")
        if not isinstance(artifact_digest, str):
            raise ValueError("invalid_checkpoint_record")
        checkpoint = _checkpoint_from_data(record)
        try:
            artifact = self.artifact_store.read(checkpoint.artifact_id)
        except ValueError:
            return None
        if artifact is None:
            return None
        if stable_digest(_artifact_data(artifact)) != artifact_digest:
            return None
        return checkpoint


def commit_boundary(
    *,
    artifact_store: ArtifactStore,
    checkpoint_store: CheckpointStore,
    artifact: CompactionArtifact,
    checkpoint: RunCheckpoint,
) -> RunCheckpoint:
    """Persist the artifact before its checkpoint makes it recoverable."""
    if checkpoint.artifact_id != artifact.artifact_id:
        raise ValueError("checkpoint_artifact_mismatch")
    if checkpoint_store.artifact_store.root.resolve() != artifact_store.root.resolve():
        raise ValueError("checkpoint_artifact_store_mismatch")
    artifact_store.write(artifact)
    checkpoint_store.commit(checkpoint)
    return checkpoint
