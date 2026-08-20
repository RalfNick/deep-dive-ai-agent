from __future__ import annotations

import json
import multiprocessing
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from chapter5.context.contracts import (
    ContextKind,
    InstructionAuthority,
    RetentionPriority,
    Sensitivity,
    TrustLevel,
)
from chapter6.context_continuity.contracts import (
    CarryItem,
    CompactionArtifact,
    EventRecord,
    EventType,
    RunCheckpoint,
)
from chapter6.context_continuity.event_log import JsonlEventLog
from chapter6.context_continuity.stores import ArtifactStore, CheckpointStore, commit_boundary


def sample_event(sequence: int = 1) -> EventRecord:
    item = CarryItem(
        key="repair-price",
        kind=ContextKind.TASK,
        content="repair price calculation",
        authority=InstructionAuthority.NONE,
        trust=TrustLevel.VERIFIED,
        retention_priority=RetentionPriority.REQUIRED,
        sensitivity=Sensitivity.INTERNAL,
        source_event_ids=(f"evt-{sequence:03d}",),
    )
    return EventRecord(
        event_id=f"evt-{sequence:03d}",
        run_id="run-price",
        sequence=sequence,
        event_type=EventType.TASK,
        carry_items=(item,),
        workspace_digest="workspace-v1",
    )


def sample_checkpoint(artifact_id: str = "cmp-test") -> RunCheckpoint:
    return RunCheckpoint(
        run_id="run-price",
        checkpoint_id="chk-001",
        next_step="verify-price",
        completed_steps=("gather-price",),
        pending_step="verify-price",
        event_cursor=20,
        workspace_digest="workspace-v1",
        artifact_id=artifact_id,
    )


def process_artifact_write(
    root: str,
    artifact: CompactionArtifact,
    barrier: object,
    results: object,
) -> None:
    """Spawn-safe worker used to exercise the cross-process publish boundary."""
    barrier.wait(timeout=15)  # type: ignore[attr-defined]
    try:
        ArtifactStore(Path(root)).write(artifact)
    except ValueError as error:
        results.put(str(error))  # type: ignore[attr-defined]
    else:
        results.put("ok")  # type: ignore[attr-defined]


class PersistenceTest(unittest.TestCase):
    def test_event_log_round_trips_canonical_records_through_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = JsonlEventLog(Path(directory) / "events.jsonl")
            first = sample_event(sequence=1)
            second = sample_event(sequence=2)
            log.append(first)
            log.append(second)
            self.assertEqual((first,), log.read_through(1))
            self.assertEqual((first, second), log.read_through(2))

    def test_event_log_rejects_duplicate_or_out_of_order_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = JsonlEventLog(Path(directory) / "events.jsonl")
            log.append(sample_event(sequence=2))
            with self.assertRaisesRegex(ValueError, "duplicate_event_id"):
                log.append(sample_event(sequence=2))
            with self.assertRaisesRegex(ValueError, "non_monotonic_event_sequence"):
                log.append(sample_event(sequence=1))

    def test_event_log_does_not_persist_secret_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            secret = CarryItem(
                key="api-token",
                kind=ContextKind.FACT,
                content="super-secret-token",
                authority=InstructionAuthority.NONE,
                trust=TrustLevel.VERIFIED,
                retention_priority=RetentionPriority.REQUIRED,
                sensitivity=Sensitivity.SECRET,
                source_event_ids=("evt-secret",),
            )
            event = EventRecord(
                event_id="evt-secret",
                run_id="run-price",
                sequence=1,
                event_type=EventType.OBSERVATION,
                carry_items=(secret,),
            )
            log = JsonlEventLog(Path(directory) / "events.jsonl")
            with self.assertRaisesRegex(ValueError, "secret_event_payload"):
                log.append(event)
            self.assertFalse((Path(directory) / "events.jsonl").exists())

    def test_event_log_rejects_digest_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            log = JsonlEventLog(path)
            log.append(sample_event(sequence=1))
            path.write_text(
                path.read_text(encoding="utf-8").replace("repair", "replace"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "event_digest_mismatch"):
                log.read_through(1)

    def test_unreferenced_artifact_is_not_a_committed_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = ArtifactStore(root / "artifacts")
            checkpoints = CheckpointStore(root / "checkpoints")
            artifact = CompactionArtifact.minimal_for_test(artifact_id="cmp-orphan")
            artifacts.write(artifact)
            self.assertIsNone(checkpoints.latest("run-price"))

    def test_commit_boundary_persists_matching_artifact_and_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = ArtifactStore(root / "artifacts")
            checkpoints = CheckpointStore(root / "checkpoints")
            artifact = CompactionArtifact.minimal_for_test()
            checkpoint = sample_checkpoint(artifact.artifact_id)
            self.assertEqual(
                checkpoint,
                commit_boundary(
                    artifact_store=artifacts,
                    checkpoint_store=checkpoints,
                    artifact=artifact,
                    checkpoint=checkpoint,
                ),
            )
            self.assertEqual(artifact, artifacts.read(artifact.artifact_id))
            self.assertEqual(checkpoint, checkpoints.latest(checkpoint.run_id))

    def test_checkpoint_with_missing_or_changed_artifact_is_not_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = ArtifactStore(root / "artifacts")
            checkpoints = CheckpointStore(root / "checkpoints")
            artifact = CompactionArtifact.minimal_for_test()
            checkpoint = sample_checkpoint(artifact.artifact_id)
            commit_boundary(
                artifact_store=artifacts,
                checkpoint_store=checkpoints,
                artifact=artifact,
                checkpoint=checkpoint,
            )
            artifact_path = root / "artifacts" / f"{artifact.artifact_id}.json"
            artifact_path.write_text(
                artifact_path.read_text(encoding="utf-8").replace("repair", "replace"),
                encoding="utf-8",
            )
            self.assertIsNone(checkpoints.latest(checkpoint.run_id))

    def test_checkpoint_with_deleted_artifact_is_not_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = ArtifactStore(root / "artifacts")
            checkpoints = CheckpointStore(root / "checkpoints")
            artifact = CompactionArtifact.minimal_for_test()
            checkpoint = sample_checkpoint(artifact.artifact_id)
            commit_boundary(
                artifact_store=artifacts,
                checkpoint_store=checkpoints,
                artifact=artifact,
                checkpoint=checkpoint,
            )

            (root / "artifacts" / f"{artifact.artifact_id}.json").unlink()

            self.assertIsNone(checkpoints.latest(checkpoint.run_id))

    def test_artifact_store_rejects_same_id_with_different_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts = ArtifactStore(Path(directory) / "artifacts")
            artifact = CompactionArtifact.minimal_for_test()
            artifacts.write(artifact)

            with self.assertRaisesRegex(ValueError, "artifact_id_conflict"):
                artifacts.write(replace(artifact, source_digest="different-source"))

            self.assertEqual(artifact, artifacts.read(artifact.artifact_id))

    def test_artifact_store_allows_idempotent_same_content_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts = ArtifactStore(Path(directory) / "artifacts")
            artifact = CompactionArtifact.minimal_for_test()

            artifacts.write(artifact)
            artifacts.write(artifact)

            self.assertEqual(artifact, artifacts.read(artifact.artifact_id))

    def test_concurrent_threads_publish_exactly_one_different_artifact(self) -> None:
        for trial in range(20):
            with self.subTest(trial=trial), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "artifacts"
                store = ArtifactStore(root)
                artifact_id = f"cmp-thread-conflict-{trial}"
                first = replace(
                    CompactionArtifact.minimal_for_test(artifact_id=artifact_id),
                    source_digest=f"source-a-{trial}",
                )
                second = replace(first, source_digest=f"source-b-{trial}")
                barrier = threading.Barrier(3)

                def write_after_barrier(artifact: CompactionArtifact) -> str:
                    barrier.wait(timeout=10)
                    try:
                        store.write(artifact)
                    except ValueError as error:
                        return str(error)
                    return "ok"

                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = (
                        executor.submit(write_after_barrier, first),
                        executor.submit(write_after_barrier, second),
                    )
                    barrier.wait(timeout=10)
                    outcomes = [future.result(timeout=10) for future in futures]

                self.assertCountEqual(outcomes, ["ok", "artifact_id_conflict"])
                winner = store.read(artifact_id)
                self.assertIn(winner, (first, second))
                envelope = json.loads(
                    (root / f"{artifact_id}.json").read_text(encoding="utf-8")
                )
                self.assertEqual(
                    envelope["record"]["source_digest"],
                    winner.source_digest,  # type: ignore[union-attr]
                )
                self.assertEqual([], list(root.glob(f".{artifact_id}.json.*.tmp")))

    def test_concurrent_threads_accept_identical_artifact_idempotently(self) -> None:
        for trial in range(20):
            with self.subTest(trial=trial), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "artifacts"
                store = ArtifactStore(root)
                artifact = CompactionArtifact.minimal_for_test(
                    artifact_id=f"cmp-thread-same-{trial}"
                )
                barrier = threading.Barrier(3)

                def write_after_barrier() -> str:
                    barrier.wait(timeout=10)
                    store.write(artifact)
                    return "ok"

                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = (
                        executor.submit(write_after_barrier),
                        executor.submit(write_after_barrier),
                    )
                    barrier.wait(timeout=10)
                    outcomes = [future.result(timeout=10) for future in futures]

                self.assertEqual(["ok", "ok"], outcomes)
                self.assertEqual(artifact, store.read(artifact.artifact_id))
                envelope = json.loads(
                    (root / f"{artifact.artifact_id}.json").read_text(encoding="utf-8")
                )
                self.assertEqual({"record", "record_digest"}, set(envelope))
                self.assertEqual([], list(root.glob(f".{artifact.artifact_id}.json.*.tmp")))

    def test_concurrent_processes_publish_exactly_one_different_artifact(self) -> None:
        context = multiprocessing.get_context("spawn")
        for trial in range(3):
            with self.subTest(trial=trial), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "artifacts"
                artifact_id = f"cmp-process-conflict-{trial}"
                first = replace(
                    CompactionArtifact.minimal_for_test(artifact_id=artifact_id),
                    source_digest=f"process-a-{trial}",
                )
                second = replace(first, source_digest=f"process-b-{trial}")
                barrier = context.Barrier(3)
                results = context.Queue()
                processes = [
                    context.Process(
                        target=process_artifact_write,
                        args=(str(root), artifact, barrier, results),
                    )
                    for artifact in (first, second)
                ]
                for process in processes:
                    process.start()
                barrier.wait(timeout=15)
                for process in processes:
                    process.join(timeout=15)
                    self.assertFalse(process.is_alive())
                    self.assertEqual(0, process.exitcode)

                outcomes = [results.get(timeout=5) for _ in processes]
                results.close()
                self.assertCountEqual(outcomes, ["ok", "artifact_id_conflict"])
                self.assertIn(ArtifactStore(root).read(artifact_id), (first, second))

    def test_concurrent_processes_accept_identical_artifact_idempotently(self) -> None:
        context = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "artifacts"
            artifact = CompactionArtifact.minimal_for_test(
                artifact_id="cmp-process-same"
            )
            barrier = context.Barrier(3)
            results = context.Queue()
            processes = [
                context.Process(
                    target=process_artifact_write,
                    args=(str(root), artifact, barrier, results),
                )
                for _ in range(2)
            ]
            for process in processes:
                process.start()
            barrier.wait(timeout=15)
            for process in processes:
                process.join(timeout=15)
                self.assertFalse(process.is_alive())
                self.assertEqual(0, process.exitcode)

            outcomes = [results.get(timeout=5) for _ in processes]
            results.close()
            self.assertEqual(["ok", "ok"], outcomes)
            self.assertEqual(artifact, ArtifactStore(root).read(artifact.artifact_id))

    def test_checkpoint_store_preserves_replace_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = ArtifactStore(root / "artifacts")
            checkpoints = CheckpointStore(root / "checkpoints")
            artifact = CompactionArtifact.minimal_for_test()
            artifacts.write(artifact)
            first = sample_checkpoint(artifact.artifact_id)
            replacement = replace(
                first,
                next_step="publish-price",
                completed_steps=("gather-price", "verify-price"),
                pending_step="publish-price",
                event_cursor=21,
            )

            checkpoints.commit(first)
            checkpoints.commit(replacement)

            self.assertEqual(replacement, checkpoints.latest(replacement.run_id))

    def test_commit_boundary_rejects_checkpoint_for_another_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "checkpoint_artifact_mismatch"):
                commit_boundary(
                    artifact_store=ArtifactStore(root / "artifacts"),
                    checkpoint_store=CheckpointStore(root / "checkpoints"),
                    artifact=CompactionArtifact.minimal_for_test(),
                    checkpoint=sample_checkpoint("cmp-other"),
                )

    def test_commit_boundary_rejects_checkpoint_store_bound_to_different_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            committed_artifacts = ArtifactStore(root / "committed-artifacts")
            stale_artifacts = ArtifactStore(root / "stale-artifacts")
            checkpoints = CheckpointStore(
                root / "checkpoints",
                artifact_store=stale_artifacts,
            )
            artifact = CompactionArtifact.minimal_for_test()
            stale_artifacts.write(replace(artifact, source_digest="stale-source"))

            with self.assertRaisesRegex(ValueError, "checkpoint_artifact_store_mismatch"):
                commit_boundary(
                    artifact_store=committed_artifacts,
                    checkpoint_store=checkpoints,
                    artifact=artifact,
                    checkpoint=sample_checkpoint(artifact.artifact_id),
                )

            self.assertIsNone(committed_artifacts.read(artifact.artifact_id))
            self.assertIsNone(checkpoints.latest("run-price"))


if __name__ == "__main__":
    unittest.main()
