from __future__ import annotations

import re


_EXERCISE = re.compile(
    r"^(?P<number>\d+)\.\s+\*\*[★]+\s+(?P<title>[^*]+)\*\*",
    re.MULTILINE,
)
_ANSWER = re.compile(
    r"^##\s+(?:基础题|实验题|设计与批判题)\s+"
    r"(?P<number>\d+)：(?P<title>.+?)\s*$",
    re.MULTILINE,
)


def _headings(pattern: re.Pattern[str], text: str) -> dict[int, str]:
    return {
        int(match.group("number")): match.group("title").strip()
        for match in pattern.finditer(text)
    }


def validate_exercise_answer_alignment(
    chapter_text: str,
    answer_text: str,
) -> tuple[str, ...]:
    """Return stable publication-contract errors for exercise/answer drift."""

    exercises = _headings(_EXERCISE, chapter_text)
    answers = _headings(_ANSWER, answer_text)
    errors: list[str] = []
    for number in sorted(exercises):
        if number not in answers:
            errors.append(f"missing_answer:{number}")
        elif answers[number] != exercises[number]:
            errors.append(f"answer_title_mismatch:{number}")
    for number in sorted(answers.keys() - exercises.keys()):
        errors.append(f"orphan_answer:{number}")
    return tuple(errors)
