"""Test-only preservation adapter for the authorized reader revision.

Historical hashes describe frozen bytes, not every later editorial edition.
Only named manuscripts and documentation contracts may use this archive.
Agent implementations, images and canonical reports are never exempted.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from typing import Sequence


ARCHIVE = "book/versions/whole-book-reader-v2-before-2026-10-03"
BASELINE = "c8f2995343e90de0721c4236f880c88bbcb3d324"
PROSE_ARCHIVE = "book/versions/whole-book-prose-v3-before-2026-10-05"
PUBLICATION_BASELINE = "363b05a0ed080abc2e251c3be5d68668b8508934"
PUBLICATION_METADATA = frozenset(f"chapter{n}/README.md" for n in range(15, 19)) | {"book/README.md"}
PROSE_DOCUMENTATION_TESTS = frozenset({
    "chapter12/tests/test_manuscript.py",
    "chapter15/tests/test_manuscript.py",
})
DOCUMENTATION_TESTS = frozenset({
    "tests/test_migration_manifest.py",
    "chapter12/tests/test_delivery.py",
    "chapter14/tests/test_reader_tools.py",
    "chapter16/tests/test_delivery.py",
    "chapter16/tests/test_manuscript.py",
    "chapter18/tests/test_delivery.py",
})
EDITABLE_SOURCES = frozenset(f"book/chapter{n}.md" for n in range(1, 19)) | {
    "book/OUTLINE.md", "book/versions/CHAPTER_VERSIONS.md", "chapter12/README.md",
} | DOCUMENTATION_TESTS | PROSE_DOCUMENTATION_TESTS
ARCHIVED_SOURCES = EDITABLE_SOURCES | {"book/chapter18.md", "book/WRITING_GUIDE.md"}


def preserved_payload(root: Path, relative: str) -> bytes:
    """Return verified frozen bytes when archived, otherwise current bytes."""
    relative_path = PurePosixPath(relative)
    assert not relative_path.is_absolute() and ".." not in relative_path.parts
    assert ":" not in relative
    root = root.resolve()
    current = root.joinpath(*relative_path.parts)
    assert current.resolve().is_relative_to(root), relative
    if relative in PUBLICATION_METADATA:
        return subprocess.run(
            ["git", "show", f"{PUBLICATION_BASELINE}:{relative}"], cwd=root,
            check=True, capture_output=True,
        ).stdout
    prose_contract = relative in PROSE_DOCUMENTATION_TESTS
    archive = root / (PROSE_ARCHIVE if prose_contract else ARCHIVE)
    manifest_path = archive / "snapshot-hashes.json"
    if not manifest_path.is_file():
        return current.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_version = ("whole-book-prose-v3-before-2026-10-05" if prose_contract
                        else "whole-book-reader-v2-before-2026-10-03")
    assert manifest["version"] == expected_version
    assert manifest["baseline_commit"] == BASELINE
    if prose_contract:
        assert manifest["predecessor_edition"] == "editorial-v2-local"
    rows = {row["source"]: row for row in manifest["files"]}
    assert len(rows) == len(manifest["files"]), "duplicate archive source"
    if not prose_contract:
        assert set(rows).issubset(ARCHIVED_SOURCES), "unauthorized archive source"
    if relative not in rows:
        assert not prose_contract, f"missing frozen documentation contract: {relative}"
        return current.read_bytes()
    snapshot = archive / (relative + ".snapshot")
    assert snapshot.resolve().is_relative_to(archive.resolve()), relative
    assert snapshot.is_file(), f"missing snapshot: {relative}"
    payload = snapshot.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == rows[relative]["sha256"].lower(), relative
    return payload


def assert_frozen_history(root: Path, base: str, protected: Sequence[str]) -> None:
    """Changed approved text must retain its actual frozen Git bytes."""
    changes = subprocess.run(
        ["git", "diff", "--name-only", base, "--", *protected], cwd=root,
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    for relative in changes:
        assert relative in EDITABLE_SOURCES | PUBLICATION_METADATA, f"unexpected protected edit: {relative}"
        if relative not in PUBLICATION_METADATA:
            archive = PROSE_ARCHIVE if relative in PROSE_DOCUMENTATION_TESTS else ARCHIVE
            snapshot = root / archive / (relative + ".snapshot")
            assert snapshot.is_file(), f"unarchived protected edit: {relative}"
        archived = preserved_payload(root, relative)
        original = subprocess.run(
            ["git", "show", f"{base}:{relative}"], cwd=root,
            check=True, capture_output=True,
        ).stdout
        assert archived.replace(b"\r\n", b"\n") == original.replace(b"\r\n", b"\n"), relative
