from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


FIGURES = (
    "fig9-1-tool-call-journey.png",
    "fig9-2-boundary-map.png",
    "fig9-3-tool-contract.png",
    "fig9-4-tool-loop.png",
    "fig9-5-mcp-architecture.png",
    "fig9-6-mcp-primitives.png",
    "fig9-7-protocol-eras.png",
    "fig9-8-failure-map.png",
)


@dataclass(frozen=True, slots=True)
class PublicationContract:
    min_cjk: int = 25_000
    max_cjk: int = 30_000
    min_headings: int = 20
    max_headings: int = 40
    figure_count: int = 8
    exercise_count: int = 14
    source_count: int = 20


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _prose_only(markdown: str) -> str:
    without_fences = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    without_targets = re.sub(r"\]\([^)]+\)", "]", without_fences)
    return re.sub(r"https?://\S+", "", without_targets)


def publication_errors(
    root: Path,
    contract: PublicationContract = PublicationContract(),
) -> tuple[str, ...]:
    chapter_path = root / "book/chapter9.md"
    sources_path = root / "book/sources/chapter9-sources.md"
    answers_path = root / "chapter9/reference-answers.md"
    readme_path = root / "chapter9/README.md"
    chapter = _read(chapter_path)
    sources = _read(sources_path)
    answers = _read(answers_path)
    errors: list[str] = []

    if not chapter:
        errors.append("missing_chapter:book/chapter9.md")
    if not readme_path.is_file():
        errors.append("missing_reader_file:chapter9/README.md")
    if not answers_path.is_file():
        errors.append("missing_reader_file:chapter9/reference-answers.md")

    prose = _prose_only(chapter)
    cjk_count = len(re.findall(r"[\u3400-\u9fff]", prose))
    if not contract.min_cjk <= cjk_count <= contract.max_cjk:
        errors.append(f"cjk_count_out_of_range:{cjk_count}")

    heading_count = len(re.findall(r"^#{2,3}\s+", chapter, re.MULTILINE))
    if not contract.min_headings <= heading_count <= contract.max_headings:
        errors.append(f"heading_count_out_of_range:{heading_count}")

    for version in range(7):
        if f"### v{version}：" not in chapter:
            errors.append(f"missing_version:v{version}")

    linked_figures = re.findall(r"!\[[^\]]+\]\(images/(fig9-[^)]+\.png)\)", chapter)
    if tuple(sorted(linked_figures)) != tuple(sorted(FIGURES)):
        errors.append("figure_set_mismatch:chapter9")
    if len(linked_figures) != len(set(linked_figures)):
        errors.append("duplicate_figure_link:chapter9")
    for figure in FIGURES:
        if not (root / "book/images" / figure).is_file():
            errors.append(f"missing_figure:{figure}")

    exercises = re.findall(r"^(\d+)\.\s+([★☆]{1,3})\s+", chapter, re.MULTILINE)
    exercise_numbers = [int(number) for number, _ in exercises]
    if exercise_numbers != list(range(1, contract.exercise_count + 1)):
        errors.append("exercise_numbers_invalid:chapter9")

    for number in range(1, contract.exercise_count + 1):
        marker = f"## 第 {number} 题"
        if marker not in answers:
            errors.append(f"missing_answer:{number}")
            continue
        start = answers.index(marker)
        next_match = re.search(r"^## 第 \d+ 题", answers[start + len(marker):], re.MULTILINE)
        end = len(answers) if next_match is None else start + len(marker) + next_match.start()
        answer_section = answers[start:end]
        for required in ("**推理：**", "**常见错误：**", "**验收：**"):
            if required not in answer_section:
                errors.append(f"answer_field_missing:{number}:{required}")

    source_count = len(re.findall(r"^### \[S\d{2}\]", sources, re.MULTILINE))
    if source_count < contract.source_count:
        errors.append(f"source_count_below_minimum:{source_count}")

    bundle_text = "\n".join((chapter, sources, answers, _read(readme_path)))
    if re.search(r"\bsk-[A-Za-z0-9_-]{24,}\b", bundle_text) or re.search(
        r"\b[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET)\s*=\s*[\"']?[A-Za-z0-9._~+/=-]{16,}",
        bundle_text,
    ):
        errors.append("secret_like_text:chapter9_bundle")
    if re.search(r"[A-Za-z]:[\\/](?:Users|private|Codex-Projects)[\\/]", bundle_text, re.IGNORECASE):
        errors.append("author_machine_path:chapter9_bundle")
    if re.search(r"(?:模型|产品|供应商|vendor)\s*(?:排名|ranking)", bundle_text, re.IGNORECASE):
        errors.append("unsupported_ranking_claim:chapter9_bundle")
    if re.search(
        r"(?:字节|字符(?:数)?|JSON\s*长度).{0,12}(?:就是|等于|作为|算作).{0,6}Token",
        bundle_text,
        re.IGNORECASE,
    ):
        errors.append("offline_unit_called_token:chapter9_bundle")

    return tuple(errors)
