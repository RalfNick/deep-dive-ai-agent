from __future__ import annotations

import unittest
from pathlib import Path

from chapter5.publication_checks import validate_exercise_answer_alignment


REPO_ROOT = Path(__file__).resolve().parents[2]


class PublicationContractTest(unittest.TestCase):
    def test_chapter_exercises_and_reference_answers_stay_aligned(self) -> None:
        chapter = (REPO_ROOT / "book" / "chapter5.md").read_text(encoding="utf-8")
        answers = (REPO_ROOT / "chapter5" / "reference-answers.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual((), validate_exercise_answer_alignment(chapter, answers))

    def test_title_drift_is_reported_for_the_exact_exercise(self) -> None:
        chapter = "1. **★ 概念边界**：解释几个概念。\n"
        answers = "## 基础题 1：另一个题目\n"

        self.assertEqual(
            ("answer_title_mismatch:1",),
            validate_exercise_answer_alignment(chapter, answers),
        )

    def test_missing_numbers_are_reported_without_hiding_title_errors(self) -> None:
        chapter = (
            "1. **★ 第一题**：问题。\n"
            "2. **★★ 第二题**：问题。\n"
        )
        answers = "## 基础题 1：错误标题\n"

        self.assertEqual(
            ("answer_title_mismatch:1", "missing_answer:2"),
            validate_exercise_answer_alignment(chapter, answers),
        )


if __name__ == "__main__":
    unittest.main()
