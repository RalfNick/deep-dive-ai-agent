from __future__ import annotations

import re
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXTERNAL_USER_PDF = "用户提供资料《AI学习资料.pdf》（未入库）"


_TITLE = re.compile(
    r"^#\s*第\s*6\s*章\s+长任务中的上下文架构"
    r"(?::|：)压缩之后，Agent\s*如何继续正确工作\s*$",
    re.MULTILINE,
)
_CORE_TERMS = (
    "Event Log",
    "RunCheckpoint",
    "Working Set",
    "CompactionArtifact",
    "Context Rehydration",
    "ContextPacket",
    "执行连续性",
    "语义连续性",
)
_CLAIMS_HEADING = re.compile(
    r"^##\s+.*(?:Claims|证明了什么)", re.IGNORECASE | re.MULTILINE
)
_NON_CLAIMS_HEADING = re.compile(
    r"^##\s+.*(?:Non-claims|没有证明什么|不声称)",
    re.IGNORECASE | re.MULTILINE,
)
_MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\((?P<path>[^)\s]+)")
_CHAPTER_SIX_FIGURE = re.compile(r"^fig6-(?P<number>\d+)[^/\\]*\.svg$", re.IGNORECASE)
_EXERCISE = re.compile(
    r"^(?P<number>\d+)\.\s+\*\*[★]+\s+(?P<title>[^*]+)\*\*",
    re.MULTILINE,
)
_ANSWER = re.compile(
    r"^##\s+(?P<category>基础题|实验题|设计与批判题)\s+"
    r"(?P<number>\d+)：(?P<title>.+?)\s*$",
    re.MULTILINE,
)
_ANSWER_CONTRACT_MARKERS = ("**预期推理：**", "**常见错误：**", "**可检查验收：**")
_EXPECTED_ANSWER_CATEGORIES = {"基础题": 4, "实验题": 5, "设计与批判题": 5}
_CHAPTER_SEVEN_BRIDGE = (
    "如果信息只服务当前长任务，它属于 Context/RunState/Session；"
    "只有未来独立任务仍需复用的受控信息，才进入第 7 章的 Memory 候选。"
)
_SOURCE_RECORD = re.compile(
    r"^### \[(?P<source_id>S\d+)\](?P<title>[^\n]*).*?"
    r"(?=^### \[S\d+\]|\Z)",
    re.MULTILINE | re.DOTALL,
)
_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_FENCE_OPENER = re.compile(
    r"^ {0,3}(?P<run>`{3,}|~{3,})(?P<info>[^\r\n]*)$"
)
_FENCE_CLOSER = re.compile(r"^ {0,3}(?P<run>`+|~+)[ \t]*$")
_CJK_UNIFIED_IDEOGRAPH = re.compile(r"[\u4e00-\u9fff]")
_WINDOWS_AUTHOR_PATH = re.compile(r"(?<![\w/])(?:[A-Za-z]:[\\/])[^\s`<>\])}]+")

_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9._~-]{20,}\b", re.IGNORECASE),
    re.compile(
        r"\b(?:OPENAI|ANTHROPIC|DEEPSEEK|CLAUDE)?_?API_KEY\s*=\s*[\"']?"
        r"(?!\$\{|<|your[-_]|example|placeholder)[A-Za-z0-9_-]{20,}",
        re.IGNORECASE,
    ),
)
_RANKING_PATTERNS = (
    re.compile(
        r"\b(?:Claude Code|Codex|LangGraph)\s+比\s+"
        r"(?:Claude Code|Codex|LangGraph)\s+"
        r"(?:更强|更聪明|更好|更可靠|更稳定|更适合|领先|优秀)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Claude Code|Codex|LangGraph)\s*(?:>|优于|胜过|碾压)\s*"
        r"(?:Claude Code|Codex|LangGraph)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Claude Code|Codex|LangGraph)\s+是(?:三个|三者|这些产品中)?"
        r"(?:最强|最聪明|最好|第一名)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Claude Code|Codex|LangGraph)\s+在.{0,24}?(?:上|方面)\s*"
        r"(?:优于|胜过|领先于|高于|好于|强于)\s*"
        r"(?:Claude Code|Codex|LangGraph)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Claude Code|Codex|LangGraph)\s+的"
        r"(?:可靠性|稳定性|适用性|长任务表现)\s*"
        r"(?:高于|优于|好于|强于)\s*"
        r"(?:Claude Code|Codex|LangGraph)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Claude Code|Codex|LangGraph)\s+"
        r"(?:is|was)\s+(?:more\s+reliable|more\s+suitable|more\s+stable|"
        r"better\s+suited|better|stronger)\s+than\s+"
        r"(?:Claude Code|Codex|LangGraph)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Claude Code|Codex|LangGraph)\s+"
        r"(?:outperforms|beats|ranks\s+above|is\s+superior\s+to)\s+"
        r"(?:Claude Code|Codex|LangGraph)\b",
        re.IGNORECASE,
    ),
)
_RANKING_DISCLAIMER = re.compile(
    r"(?:不能|无法|不足以|不应|并不|没有|未)\s*"
    r"(?:证明|说明|表明|声称|推断|比较)|"
    r"(?:不做|不进行|拒绝).{0,8}(?:产品)?(?:排名|比较)|"
    r"\b(?:does\s+not|cannot|can't|do\s+not|not\s+enough\s+to)\s+"
    r"(?:prove|show|claim|establish|rank|compare)|"
    r"\bno\s+(?:claim|ranking|comparison)\b",
    re.IGNORECASE,
)
_CLAUSE_BOUNDARY = re.compile(
    r"[。！？!?；;，,\n]+|(?<=[.])\s+|"
    r"\b(?:but|however|yet)\b|(?:不过|但是|然而|但|却)",
    re.IGNORECASE,
)
_OFFLINE_SCOPE = re.compile(
    r"(?:离线实验|固定报告|离线报告|本地报告|确定性报告|实验报告|实验)|"
    r"\b(?:offline\s+(?:experiments?|labs?|reports?)|"
    r"fixed\s+reports?|deterministic\s+reports?)\b",
    re.IGNORECASE,
)
_CHINESE_TOKEN_REDUCTION_PATTERNS = (
    re.compile(
        r"(?:Token|tokens?|令牌).{0,16}(?:节省|减少|下降|降低|缩减).{0,10}\d",
        re.IGNORECASE,
    ),
    re.compile(
        r"\d+(?:\.\d+)?\s*%\s*(?:Provider\s*)?(?:Token|tokens?|令牌)"
        r"\s*(?:节省|减少|下降|降低|缩减|reduction)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:节省|减少|下降|降低|缩减)\s*\d+(?:\.\d+)?\s*%\s*"
        r"(?:Provider\s*)?(?:Token|tokens?|令牌)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:Token|tokens?|令牌)\s*(?:从\s*)?\d[\d,.]*\s*"
        r"(?:降到|降至|减少到|变为).{0,10}\d[\d,.]*",
        re.IGNORECASE,
    ),
)
_PERCENTAGE = r"\d+(?:\.\d+)?(?:\s*%(?!\w)|\s+percent\b)"
_ENGLISH_TOKEN_REDUCTION_PATTERNS = (
    re.compile(
        rf"\b{_PERCENTAGE}\s+"
        r"(?:reduction|decrease|drop|savings?)\s+(?:in|of)\s+"
        r"(?:provider\s+)?tokens?(?:\s+(?:use|usage|count))?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_PERCENTAGE}\s+(?:fewer|less)\s+"
        r"(?:provider\s+)?tokens?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_PERCENTAGE}\s+(?:provider\s+)?tokens?\s+"
        r"(?:reduction|decrease|drop|savings?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:reduction|decrease|drop|savings?)\s+of\s+"
        rf"{_PERCENTAGE}\s+(?:in|of)\s+"
        r"(?:provider\s+)?tokens?(?:\s+(?:use|usage|count))?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:provider\s+)?tokens?(?:\s+(?:use|usage|count))?\s+"
        r"(?:(?:was|were|has\s+been|have\s+been)\s+)?"
        r"(?:fell|decreased|dropped|declined|reduced)\s+"
        r"(?:by|to|from)\s+\d[\d,.]*(?:\s*%)?(?!\w)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:provider\s+)?tokens?(?:\s+(?:use|usage|count))?\s+"
        r"(?:reduction|decrease|drop|savings?)\s+"
        r"(?:was|were|is|of|by|reached|amounted\s+to|totaled)\s+"
        rf"{_PERCENTAGE}",
        re.IGNORECASE,
    ),
)
_TOKEN_REDUCTION_PATTERNS = (
    *_CHINESE_TOKEN_REDUCTION_PATTERNS,
    *_ENGLISH_TOKEN_REDUCTION_PATTERNS,
)
_TOKEN_UNIT_DISCLAIMER = re.compile(
    r"(?:单位|指标).{0,16}(?:不是|并非|不等于).{0,12}(?:Token|tokens?|令牌)|"
    r"\b(?:unit|metric)\s+(?:is|was)\s+not\s+(?:Token|tokens?)\b",
    re.IGNORECASE,
)
_TOKEN_CLAIM_NEGATION = re.compile(
    r"(?:并未|没有|不能|无法|不)\s*(?:声称|显示|报告|证明|说明|表明)"
    r".{0,36}$|"
    r"\b(?:does\s+not|doesn't|did\s+not|cannot|can't|will\s+not)\s+"
    r"(?:claim|show|report|prove|state|say).{0,36}$",
    re.IGNORECASE,
)
_SCOPE_CLAUSE_BOUNDARY = re.compile(
    r"[。！？!?；;\n]+|(?<=[.])\s+|(?<!\d)[，,](?!\d)|"
    r"\b(?:but|however|yet)\b|(?:不过|但是|然而|但|却)",
    re.IGNORECASE,
)
_EXTERNAL_TOKEN_ATTRIBUTION = re.compile(
    r"(?:"
    r"^\s*according\s+to\s+(?:an?\s+|the\s+)?official\s+"
    r"(?:docs?|documentation)\b|"
    r"^\s*(?:an?\s+|the\s+)?official\s+(?:docs?|documentation)\s*"
    r"(?:say|says|state|states|report|reports|show|shows|describe|describes|"
    r"document|documents|[:：])|"
    r"\b(?:OpenAI|Anthropic|Claude|Codex|provider)\b.{0,48}"
    r"\b(?:official|docs?|documentation|model\s+usage|context\s+window)\b|"
    r"\b(?:official|docs?|documentation)\b.{0,48}"
    r"\b(?:OpenAI|Anthropic|provider|model\s+usage|context\s+window)\b|"
    r"(?:OpenAI|Anthropic|Claude|Codex|模型供应商|提供商)?.{0,16}"
    r"官方.{0,24}(?:文档|说明|模型|用量|上下文窗口)"
    r")",
    re.IGNORECASE,
)


def _numbered_headings(
    pattern: re.Pattern[str], text: str
) -> tuple[dict[int, str], tuple[int, ...], int]:
    matches = tuple(pattern.finditer(text))
    numbers = tuple(int(match.group("number")) for match in matches)
    headings: dict[int, str] = {}
    for match in matches:
        headings.setdefault(
            int(match.group("number")), match.group("title").strip()
        )
    duplicates = tuple(
        number for number, count in sorted(Counter(numbers).items()) if count > 1
    )
    return headings, duplicates, len(matches)


def publication_cjk_characters(chapter_text: str) -> int:
    """Count actual CJK unified ideographs outside Markdown code fences.

    This is a small line-state CommonMark fence parser rather than a whole-file
    regex. A fence may be indented by up to three spaces. A closing run must use
    the same character and be at least as long as the opener; an unmatched
    opener consumes through EOF. Backtick fence info cannot contain backticks.
    """

    count = 0
    fence_character: str | None = None
    fence_length = 0
    for raw_line in chapter_text.splitlines():
        if fence_character is not None:
            closer = _FENCE_CLOSER.fullmatch(raw_line)
            if closer is not None:
                run = closer.group("run")
                if run[0] == fence_character and len(run) >= fence_length:
                    fence_character = None
                    fence_length = 0
            continue

        opener = _FENCE_OPENER.fullmatch(raw_line)
        if opener is not None:
            run = opener.group("run")
            info = opener.group("info")
            if run[0] == "`" and "`" in info:
                count += len(_CJK_UNIFIED_IDEOGRAPH.findall(raw_line))
                continue
            fence_character = run[0]
            fence_length = len(run)
            continue

        count += len(_CJK_UNIFIED_IDEOGRAPH.findall(raw_line))
    return count


def _normalized_figure_reference(raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _figure_references_from_chapter(
    chapter_text: str,
) -> tuple[tuple[str, str], ...]:
    references: list[tuple[str, str]] = []
    for match in _MARKDOWN_IMAGE.finditer(chapter_text):
        reference = _normalized_figure_reference(match.group("path"))
        name = PurePosixPath(reference).name
        if _CHAPTER_SIX_FIGURE.fullmatch(name):
            references.append((reference, name.lower()))
    return tuple(references)


def _figure_names_from_inventory(
    image_paths: Sequence[str],
) -> tuple[tuple[tuple[str, Path], ...], tuple[str, ...]]:
    existing: list[tuple[str, Path]] = []
    missing: list[str] = []
    for raw_path in image_paths:
        normalized = str(raw_path).replace("\\", "/")
        name = PurePosixPath(normalized).name.lower()
        if not _CHAPTER_SIX_FIGURE.fullmatch(name):
            continue
        path = Path(raw_path)
        resolved = path if path.is_absolute() else _REPO_ROOT / path
        if resolved.is_file():
            existing.append((name, resolved.resolve()))
        else:
            missing.append(name)
    return tuple(existing), tuple(missing)


def _figure_reference_matches_inventory(
    reference: str, inventory_paths: Sequence[Path]
) -> bool:
    pure_reference = PurePosixPath(reference)
    if pure_reference.is_absolute() or ".." in pure_reference.parts:
        return False
    reference_parts = tuple(part.casefold() for part in pure_reference.parts if part != ".")
    if not reference_parts:
        return False
    for path in inventory_paths:
        inventory_parts = tuple(part.casefold() for part in path.parts)
        if inventory_parts[-len(reference_parts) :] == reference_parts:
            return True
    return False


def _field_value(record: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}：(.*)$", record, re.MULTILINE)
    return match.group(1).strip() if match else None


def _repo_relative_location_errors(
    source_id: str, location: str
) -> list[str]:
    errors: list[str] = []
    for raw_entry in re.split(r"[；;]", location):
        entry = raw_entry.strip().strip("`")
        if not entry or re.match(r"^https?://", entry, re.IGNORECASE):
            continue
        normalized = entry.replace("\\", "/")
        if normalized == _EXTERNAL_USER_PDF:
            continue
        if PureWindowsPath(normalized).is_absolute():
            errors.append(f"source_local_path_outside_repo:{source_id}:{normalized}")
            continue
        relative = PurePosixPath(normalized)
        candidate = (_REPO_ROOT / Path(*relative.parts)).resolve()
        try:
            candidate.relative_to(_REPO_ROOT)
        except ValueError:
            errors.append(f"source_local_path_outside_repo:{source_id}:{normalized}")
            continue
        if not candidate.exists():
            errors.append(f"source_local_path_missing:{source_id}:{normalized}")
    return errors


def _claim_clauses(text: str) -> tuple[str, ...]:
    return tuple(clause.strip() for clause in _CLAUSE_BOUNDARY.split(text) if clause.strip())


def _contains_ranking_claim(text: str) -> bool:
    for clause in _claim_clauses(text):
        if _RANKING_DISCLAIMER.search(clause):
            continue
        if any(pattern.search(clause) for pattern in _RANKING_PATTERNS):
            return True
    return False


def _contains_offline_token_claim(text: str) -> bool:
    for paragraph in re.split(r"\n\s*\n", text):
        scope = "unknown"
        clauses = (
            clause.strip()
            for clause in _SCOPE_CLAUSE_BOUNDARY.split(paragraph)
            if clause.strip()
        )
        for clause in clauses:
            if _EXTERNAL_TOKEN_ATTRIBUTION.search(clause):
                scope = "external"
            elif _OFFLINE_SCOPE.search(clause):
                scope = "offline"
            if scope != "offline":
                continue
            for pattern in _TOKEN_REDUCTION_PATTERNS:
                for match in pattern.finditer(clause):
                    prefix = clause[max(0, match.start() - 72) : match.start()]
                    if _TOKEN_CLAIM_NEGATION.search(prefix):
                        continue
                    local_claim = clause[
                        max(0, match.start() - 72) : min(len(clause), match.end() + 24)
                    ]
                    if _TOKEN_UNIT_DISCLAIMER.search(local_claim):
                        continue
                    return True
    return False


def _source_errors(source_text: str) -> list[str]:
    if not source_text.strip():
        return ["missing_source_ledger"]

    errors: list[str] = []
    if "核对日期：2026-08-17" not in source_text:
        errors.append("source_verification_date_missing")
    records = tuple(_SOURCE_RECORD.finditer(source_text))
    if not records:
        errors.append("missing_source_records")
        return errors
    required_fields = (
        ("URL / 本地路径", "location"),
        ("事实使用", "fact_used"),
        ("明确不声称", "non_claim"),
        ("最后核对", "verified_date"),
        ("出版前复核", "recheck_flag"),
    )
    for match in records:
        source_id = match.group("source_id")
        record = match.group(0)
        if not match.group("title").strip():
            errors.append(f"source_record_blank_title:{source_id}")
        values: dict[str, str] = {}
        for label, stable_name in required_fields:
            value = _field_value(record, label)
            if value is None:
                errors.append(f"source_record_missing_{stable_name}:{source_id}")
            elif not value:
                errors.append(f"source_record_blank_{stable_name}:{source_id}")
            else:
                values[stable_name] = value
        verified_date = values.get("verified_date")
        if verified_date is not None and verified_date != "2026-08-17":
            errors.append(f"source_record_invalid_verified_date:{source_id}")
        recheck_flag = values.get("recheck_flag")
        if recheck_flag is not None and recheck_flag not in ("是", "否"):
            errors.append(f"source_record_invalid_recheck_flag:{source_id}")
        location = values.get("location")
        if location is not None:
            errors.extend(_repo_relative_location_errors(source_id, location))
    return errors


def validate_chapter_contract(
    chapter_text: str,
    answer_text: str,
    source_text: str,
    image_paths: Sequence[str],
    *,
    enforce_manuscript_length: bool = False,
) -> tuple[str, ...]:
    """Return deterministic, stable publication errors for Chapter 6.

    The function deliberately checks static publication contracts only. It does
    not judge prose quality, validate remote links, or infer whether a product
    implementation matches undocumented internals.
    """

    errors: list[str] = []
    if enforce_manuscript_length:
        cjk_count = publication_cjk_characters(chapter_text)
        if not 25_000 <= cjk_count <= 30_000:
            errors.append(f"cjk_character_count:{cjk_count}")
    if not _TITLE.search(chapter_text):
        errors.append("invalid_title")
    for term in _CORE_TERMS:
        flexible_term = re.escape(term).replace(r"\ ", r"\s+")
        if not re.search(flexible_term, chapter_text):
            errors.append(f"missing_core_term:{term}")
    if not _CLAIMS_HEADING.search(chapter_text):
        errors.append("missing_claims")
    if not _NON_CLAIMS_HEADING.search(chapter_text):
        errors.append("missing_non_claims")
    if _CHAPTER_SEVEN_BRIDGE not in chapter_text:
        errors.append("missing_chapter7_bridge")

    figure_references = _figure_references_from_chapter(chapter_text)
    figure_names = tuple(name for _, name in figure_references)
    unique_figure_names = tuple(dict.fromkeys(figure_names))
    existing_inventory, missing_inventory = _figure_names_from_inventory(image_paths)
    inventory_names = tuple(dict.fromkeys(name for name, _ in existing_inventory))
    inventory_paths = tuple(path for _, path in existing_inventory)
    for name in tuple(dict.fromkeys(missing_inventory)):
        errors.append(f"missing_figure_file:{name}")
    if len(unique_figure_names) != 7:
        errors.append(f"figure_count:{len(unique_figure_names)}")
    if len(inventory_names) != 7:
        errors.append(f"figure_inventory_count:{len(inventory_names)}")
    figure_numbers = {
        int(_CHAPTER_SIX_FIGURE.fullmatch(name).group("number"))  # type: ignore[union-attr]
        for name in unique_figure_names
    }
    if unique_figure_names and figure_numbers != set(range(1, 8)):
        errors.append("figure_sequence_invalid")
    unmatched_references = tuple(
        reference
        for reference, _ in figure_references
        if not _figure_reference_matches_inventory(reference, inventory_paths)
    )
    for reference in tuple(dict.fromkeys(unmatched_references)):
        errors.append(f"missing_figure_reference_file:{reference}")
    if set(unique_figure_names) != set(inventory_names) or unmatched_references:
        errors.append("figure_reference_inventory_mismatch")

    exercises, duplicate_exercises, exercise_count = _numbered_headings(
        _EXERCISE, chapter_text
    )
    answers, duplicate_answers, _ = _numbered_headings(_ANSWER, answer_text)
    answer_matches = tuple(_ANSWER.finditer(answer_text))
    category_counts = Counter(match.group("category") for match in answer_matches)
    for category, expected_count in _EXPECTED_ANSWER_CATEGORIES.items():
        observed_count = category_counts[category]
        if observed_count != expected_count:
            errors.append(f"answer_category_count:{category}={observed_count}")
    for index, match in enumerate(answer_matches):
        body_end = (
            answer_matches[index + 1].start()
            if index + 1 < len(answer_matches)
            else len(answer_text)
        )
        body = answer_text[match.end() : body_end]
        if any(marker not in body for marker in _ANSWER_CONTRACT_MARKERS):
            errors.append(f"incomplete_answer_contract:{match.group('number')}")
    for number in duplicate_exercises:
        errors.append(f"duplicate_exercise_number:{number}")
    for number in duplicate_answers:
        errors.append(f"duplicate_answer_number:{number}")
    if exercise_count not in (14, 15):
        errors.append(f"exercise_count:{exercise_count}")
    if exercises and sorted(exercises) != list(range(1, len(exercises) + 1)):
        errors.append("exercise_numbers_not_consecutive")
    for number in sorted(exercises):
        if number not in answers:
            errors.append(f"missing_answer:{number}")
        elif answers[number] != exercises[number]:
            errors.append(f"answer_title_mismatch:{number}")
    for number in sorted(answers.keys() - exercises.keys()):
        errors.append(f"orphan_answer:{number}")

    errors.extend(_source_errors(source_text))

    all_publication_text = "\n".join((chapter_text, answer_text, source_text))
    if any(pattern.search(all_publication_text) for pattern in _SECRET_PATTERNS):
        errors.append("forbidden_secret_pattern")

    public_prose = _FENCED_CODE.sub("", "\n".join((chapter_text, answer_text)))
    if _WINDOWS_AUTHOR_PATH.search(public_prose):
        errors.append("bare_local_author_path")
    if _contains_ranking_claim(public_prose):
        errors.append("product_ranking_claim")
    if _contains_offline_token_claim(public_prose):
        errors.append("offline_bytes_mislabeled_as_tokens")

    return tuple(dict.fromkeys(errors))
