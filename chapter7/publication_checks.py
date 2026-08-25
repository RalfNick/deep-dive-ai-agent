from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re


CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
FENCE = re.compile(r"^(?P<indent> {0,3})(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
FIGURE_REF = re.compile(r"!\[[^\]]*\]\((?:\./)?images/(?P<name>fig7-[^)\s]+\.svg)\)")
EXERCISE = re.compile(r"^(?P<number>\d+)\. \*\*[★]+", re.MULTILINE)
ANSWER = re.compile(r"^## (?P<number>\d+)\.", re.MULTILINE)
SOURCE_HEADING = re.compile(r"^### \[(?P<id>S\d{2})\] .+$", re.MULTILINE)
SOURCE_LOCATION = re.compile(r"^- URL / 本地路径：[ \t]*(?P<value>\S.*)$", re.MULTILINE)


@dataclass(frozen=True)
class PublicationContract:
    min_cjk: int = 25_000
    max_cjk: int = 30_000
    min_headings: int = 20
    max_headings: int = 35
    figure_count: int = 7
    exercise_count: int = 14
    source_count: int = 15


def strip_fenced_code(markdown: str) -> str:
    kept: list[str] = []
    marker_char: str | None = None
    marker_length = 0
    for line in markdown.splitlines():
        match = FENCE.match(line)
        if marker_char is None:
            if match:
                marker = match.group("marker")
                info = match.group("info")
                if marker.startswith("`") and "`" in info:
                    kept.append(line)
                    continue
                marker_char = marker[0]
                marker_length = len(marker)
                continue
            kept.append(line)
            continue
        if match:
            marker = match.group("marker")
            if marker[0] == marker_char and len(marker) >= marker_length and not match.group("info").strip():
                marker_char = None
                marker_length = 0
    return "\n".join(kept)


def _duplicates(values: list[int]) -> tuple[int, ...]:
    return tuple(sorted(value for value, count in Counter(values).items() if count > 1))


def _source_records(source_text: str) -> tuple[tuple[str, str], ...]:
    matches = tuple(SOURCE_HEADING.finditer(source_text))
    records: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source_text)
        records.append((match.group("id"), source_text[match.end() : end]))
    return tuple(records)


def _safety_errors(text: str) -> list[str]:
    errors: list[str] = []
    if re.search(r"(?i)\b[A-Z]:[\\/]", text):
        errors.append("absolute_author_path")
    if re.search(r"(?i)\b(?:api[_-]?key|password|secret)\s*=\s*(?!\[REDACTED\])\S+", text):
        errors.append("possible_secret")
    ranking_patterns = (
        r"(?i)\b(?:Codex|Claude Code)\b.{0,30}\b(?:better|more reliable|superior)\b.{0,30}\b(?:Codex|Claude Code)\b",
        r"(?:Codex|Claude Code).{0,20}(?:比|优于|强于).{0,20}(?:Codex|Claude Code).{0,20}(?:可靠|适合|强|好)",
    )
    if any(re.search(pattern, text) for pattern in ranking_patterns):
        errors.append("unsupported_product_ranking")
    if re.search(r"(?:离线|固定)(?:实验|报告|夹具).{0,80}(?:Token|tokens?).{0,40}(?:减少|下降|节省|更少|%|percent)", text, re.IGNORECASE):
        errors.append("offline_bytes_mislabeled_as_tokens")
    return errors


def publication_errors(
    chapter_path: Path,
    answers_path: Path,
    sources_path: Path,
    image_dir: Path,
    *,
    contract: PublicationContract = PublicationContract(),
) -> tuple[str, ...]:
    chapter = chapter_path.read_text(encoding="utf-8")
    answers = answers_path.read_text(encoding="utf-8")
    sources = sources_path.read_text(encoding="utf-8")
    errors: list[str] = []

    prose = strip_fenced_code(chapter)
    cjk_count = len(CJK.findall(prose))
    if not contract.min_cjk <= cjk_count <= contract.max_cjk:
        errors.append(f"cjk_count_out_of_range:{cjk_count}")
    heading_count = len(re.findall(r"^#{2,3} ", chapter, re.MULTILINE))
    if not contract.min_headings <= heading_count <= contract.max_headings:
        errors.append(f"heading_count_out_of_range:{heading_count}")

    references = FIGURE_REF.findall(chapter)
    if len(references) != contract.figure_count or len(set(references)) != contract.figure_count:
        errors.append(f"figure_reference_count:{len(references)}")
    inventory = {path.name for path in image_dir.glob("fig7-*.svg")}
    for name in sorted(set(references) - inventory):
        errors.append(f"missing_figure:{name}")
    for name in sorted(inventory - set(references)):
        errors.append(f"unreferenced_figure:{name}")

    exercise_numbers = [int(match.group("number")) for match in EXERCISE.finditer(chapter)]
    answer_numbers = [int(match.group("number")) for match in ANSWER.finditer(answers)]
    for number in _duplicates(exercise_numbers):
        errors.append(f"duplicate_exercise_number:{number}")
    for number in _duplicates(answer_numbers):
        errors.append(f"duplicate_answer_number:{number}")
    expected_numbers = list(range(1, contract.exercise_count + 1))
    if sorted(set(exercise_numbers)) != expected_numbers:
        errors.append("exercise_number_set_mismatch")
    if sorted(set(answer_numbers)) != expected_numbers:
        errors.append("answer_number_set_mismatch")

    source_records = _source_records(sources)
    if len(source_records) < contract.source_count:
        errors.append(f"source_record_count:{len(source_records)}")
    required_fields = ("类型", "URL / 本地路径", "事实使用", "明确不声称", "最后核对", "出版前复核")
    for source_id, body in source_records:
        for field in required_fields:
            if not re.search(rf"^- {re.escape(field)}：[ \t]*\S", body, re.MULTILINE):
                errors.append(f"source_record_missing_field:{source_id}:{field}")
        location = SOURCE_LOCATION.search(body)
        if location:
            for item in re.split(r"[；;]", location.group("value")):
                relative = item.strip().rstrip("/")
                if not relative or "://" in relative:
                    continue
                repository_root = sources_path.resolve().parents[2]
                if not (repository_root / relative).exists():
                    errors.append(f"missing_local_source:{source_id}:{relative}")

    if "## Claims：本章证明了什么" not in chapter:
        errors.append("missing_claims_section")
    if "## Non-claims：本章没有证明什么" not in chapter:
        errors.append("missing_non_claims_section")
    if "本实验支持" not in chapter or "本实验不支持" not in chapter:
        errors.append("missing_experiment_claim_boundary")

    errors.extend(_safety_errors("\n".join((chapter, answers, sources))))
    return tuple(dict.fromkeys(errors))
