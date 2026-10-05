from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "MIGRATION_MANIFEST.md"
ROW_RE = re.compile(
    r"^\| `(?P<target>[^`]+)` \| `(?P<source>[^`]+)` \| "
    r"`(?P<commit>[0-9a-f]{40})` \| (?P<size>\d+) \| `(?P<sha>[0-9a-f]{64})` \|$"
)
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
BINARY_SUFFIXES = {".gif", ".jpeg", ".jpg", ".pdf", ".png", ".webp"}


def canonical_payload(path: Path) -> bytes:
    payload = path.read_bytes()
    if path.suffix.casefold() in BINARY_SUFFIXES or b"\0" in payload:
        return payload
    return payload.replace(b"\r\n", b"\n")


@dataclass(frozen=True)
class ManifestRecord:
    target: str
    source: str
    commit: str
    size: int
    sha256: str


def parse_manifest(text: str) -> tuple[ManifestRecord, ...]:
    records: list[ManifestRecord] = []
    for line in text.splitlines():
        match = ROW_RE.fullmatch(line)
        if not match:
            continue
        records.append(
            ManifestRecord(
                target=match.group("target"),
                source=match.group("source"),
                commit=match.group("commit"),
                size=int(match.group("size")),
                sha256=match.group("sha"),
            )
        )
    return tuple(records)


class MigrationManifestTests(unittest.TestCase):
    def records(self) -> tuple[ManifestRecord, ...]:
        self.assertTrue(MANIFEST.is_file(), "docs/MIGRATION_MANIFEST.md is missing")
        records = parse_manifest(MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(records, "migration manifest has no machine-readable rows")
        return records

    def test_required_book_sources_are_recorded(self) -> None:
        targets = {record.target for record in self.records()}
        required = {"book/introduction.md"}
        required.update(f"book/chapter{number}.md" for number in range(1, 7))
        self.assertEqual(set(), required - targets)

    def test_recorded_target_bytes_match_size_and_digest(self) -> None:
        for record in self.records():
            relative = PurePosixPath(record.target)
            self.assertFalse(relative.is_absolute(), record.target)
            self.assertNotIn("..", relative.parts, record.target)
            target = ROOT.joinpath(*relative.parts)
            self.assertTrue(target.is_file(), record.target)
            payload = canonical_payload(target)
            self.assertEqual(record.size, len(payload), record.target)
            self.assertEqual(record.sha256, hashlib.sha256(payload).hexdigest(), record.target)

    def test_source_labels_are_portable_and_bounded(self) -> None:
        allowed = {"current-workspace", "chapter6-worktree", "new-repository"}
        for record in self.records():
            self.assertFalse(WINDOWS_ABSOLUTE_RE.search(record.source), record.source)
            self.assertNotIn("." + "worktrees", record.source)
            self.assertIn(record.source, allowed)


if __name__ == "__main__":
    unittest.main()
