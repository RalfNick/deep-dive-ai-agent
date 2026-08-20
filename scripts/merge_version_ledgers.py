from __future__ import annotations

import argparse
from pathlib import Path
import re


CHAPTER_HEADING_RE = re.compile(r"(?m)^## 第 (?P<number>\d+) 章[^\n]*$")
TAIL_HEADING = "## 后续章节发布规则"


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _split_ledger(text: str) -> tuple[str, dict[int, str], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    chapter_matches = list(CHAPTER_HEADING_RE.finditer(normalized))
    tail_start = normalized.find(TAIL_HEADING)
    boundaries = [(match.start(), match) for match in chapter_matches]
    if tail_start >= 0:
        boundaries.append((tail_start, None))
    boundaries.sort(key=lambda item: item[0])

    first_boundary = boundaries[0][0] if boundaries else len(normalized)
    preamble = normalized[:first_boundary].strip()
    chapters: dict[int, str] = {}
    for index, (start, match) in enumerate(boundaries):
        if match is None:
            continue
        end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(normalized)
        chapters[int(match.group("number"))] = normalized[start:end].strip()
    tail = normalized[tail_start:].strip() if tail_start >= 0 else ""
    return preamble, chapters, tail


def _select_identical(label: str, left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    if _normalize(left) != _normalize(right):
        raise ValueError(f"conflicting {label}")
    return left


def merge_ledgers(current: str, later: str) -> str:
    """Merge non-conflicting chapter sections into numeric chapter order."""

    current_preamble, current_chapters, current_tail = _split_ledger(current)
    later_preamble, later_chapters, later_tail = _split_ledger(later)
    preamble = _select_identical("ledger preamble", current_preamble, later_preamble)
    tail = _select_identical("ledger tail", current_tail, later_tail)

    merged_chapters = dict(current_chapters)
    for number, section in later_chapters.items():
        if number in merged_chapters and _normalize(merged_chapters[number]) != _normalize(section):
            raise ValueError(f"conflicting chapter section: {number}")
        merged_chapters.setdefault(number, section)

    sections = [preamble]
    sections.extend(merged_chapters[number] for number in sorted(merged_chapters))
    if tail:
        sections.append(tail)
    return "\n\n".join(section for section in sections if section).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge chapter version ledgers")
    parser.add_argument("current", type=Path)
    parser.add_argument("later", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    merged = merge_ledgers(
        args.current.read_text(encoding="utf-8"),
        args.later.read_text(encoding="utf-8"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(merged, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
