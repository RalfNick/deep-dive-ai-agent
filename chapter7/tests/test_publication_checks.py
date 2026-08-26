import re
import tempfile
import unittest
from pathlib import Path

from chapter7.publication_checks import PublicationContract, publication_errors, strip_fenced_code


FIGURES = tuple(f"fig7-{index}-demo.svg" for index in range(1, 8))


def valid_chapter() -> str:
    figures = "\n".join(f"![图 {index}](./images/{name})" for index, name in enumerate(FIGURES, start=1))
    exercises = "\n".join(f'{index}. **{"★" * min(index, 4)} 练习 {index}**：验收标准。' for index in range(1, 15))
    return f"""# 第 7 章 记忆：不是把聊天记录全部塞回去

## 一个具体问题

先用具体例子解释记忆。这里有足够的中文内容用于最小测试。

## 实验与图

{figures}

> **实验 7-1 ★：对照**
>
> 本实验支持：固定夹具边界。
>
> 本实验不支持：真实模型质量。

## Claims：本章证明了什么

- 固定夹具支持一条边界结论。

## Non-claims：本章没有证明什么

- 不代表产品排名。

## 分层练习与参考答案

{exercises}
"""


def valid_answers() -> str:
    return "# 第 7 章参考答案\n\n" + "\n\n".join(
        f"## {index}. 练习 {index}\n\n**预期推理**：理由。\n\n**常见错误**：错误。\n\n**可检查验收**：检查。"
        for index in range(1, 15)
    )


def valid_sources() -> str:
    records = []
    for index in range(1, 16):
        records.append(
            f"""### [S{index:02d}] 来源 {index}
- 类型：官方文档
- URL / 本地路径：https://example.com/source-{index}
- 事实使用：只支持有限事实。
- 明确不声称：不外推产品能力。
- 最后核对：2026-08-25
- 出版前复核：是"""
        )
    return "# 来源台账\n\n" + "\n\n".join(records) + "\n"


class PublicationChecksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = PublicationContract(min_cjk=20, max_cjk=10_000, min_headings=3, max_headings=12)

    def _write_bundle(self, root: Path, *, chapter: str | None = None, answers: str | None = None, sources: str | None = None) -> tuple[Path, Path, Path, Path]:
        image_dir = root / "images"
        image_dir.mkdir(parents=True)
        for name in FIGURES:
            (image_dir / name).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675"><title>demo</title><desc>demo</desc></svg>', encoding="utf-8")
        chapter_path = root / "chapter7.md"
        answers_path = root / "answers.md"
        sources_path = root / "sources.md"
        chapter_path.write_text(chapter or valid_chapter(), encoding="utf-8")
        answers_path.write_text(answers or valid_answers(), encoding="utf-8")
        sources_path.write_text(sources or valid_sources(), encoding="utf-8")
        return chapter_path, answers_path, sources_path, image_dir

    def test_valid_synthetic_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._write_bundle(Path(temp_dir))
            self.assertEqual(publication_errors(*paths, contract=self.contract), ())

    def test_referenced_figure_must_exist_and_names_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._write_bundle(Path(temp_dir))
            (paths[3] / FIGURES[-1]).unlink()
            errors = publication_errors(*paths, contract=self.contract)
            self.assertIn("missing_figure:fig7-7-demo.svg", errors)

    def test_duplicate_exercise_and_answer_numbers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            chapter = valid_chapter() + "\n1. **★ 重复练习**：重复。\n"
            answers = valid_answers() + "\n## 1. 重复答案\n"
            paths = self._write_bundle(Path(temp_dir), chapter=chapter, answers=answers)
            errors = publication_errors(*paths, contract=self.contract)
            self.assertIn("duplicate_exercise_number:1", errors)
            self.assertIn("duplicate_answer_number:1", errors)

    def test_source_fields_must_be_nonblank(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sources = valid_sources().replace("- 事实使用：只支持有限事实。", "- 事实使用：", 1)
            paths = self._write_bundle(Path(temp_dir), sources=sources)
            self.assertIn("source_record_missing_field:S01:事实使用", publication_errors(*paths, contract=self.contract))

    def test_local_source_evidence_path_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sources = valid_sources().replace(
                "https://example.com/source-1",
                "chapter7/missing-evidence.json",
                1,
            )
            paths = self._write_bundle(Path(temp_dir), sources=sources)
            self.assertIn(
                "missing_local_source:S01:chapter7/missing-evidence.json",
                publication_errors(*paths, contract=self.contract),
            )

    def test_safety_scans_reject_absolute_paths_secrets_rankings_and_byte_token_claims(self) -> None:
        unsafe = valid_chapter() + "\nD:\\private\\draft.md\nAPI_KEY=live-secret-value\nCodex 比 Claude Code 更可靠。\n离线报告显示 Token 减少 42%。\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._write_bundle(Path(temp_dir), chapter=unsafe)
            errors = publication_errors(*paths, contract=self.contract)
            self.assertIn("absolute_author_path", errors)
            self.assertIn("possible_secret", errors)
            self.assertIn("unsupported_product_ranking", errors)
            self.assertIn("offline_bytes_mislabeled_as_tokens", errors)

    def test_fenced_code_is_excluded_from_prose_count(self) -> None:
        text = "正文中文\n~~~python\n围栏中的中文不算正文\n~~~\n结尾中文"
        stripped = strip_fenced_code(text)
        self.assertIn("正文中文", stripped)
        self.assertNotIn("围栏中的中文", stripped)

    def test_actual_chapter_bundle_passes_publication_contract(self) -> None:
        root = Path(__file__).resolve().parents[2]
        errors = publication_errors(
            root / "book" / "chapter7.md",
            root / "chapter7" / "reference-answers.md",
            root / "book" / "sources" / "chapter7-sources.md",
            root / "book" / "images",
        )
        self.assertEqual(errors, ())

    def test_actual_chapter_uses_an_ordered_from_scratch_reader_path(self) -> None:
        root = Path(__file__).resolve().parents[2]
        chapter = (root / "book" / "chapter7.md").read_text(encoding="utf-8")
        version_matches = tuple(
            re.finditer(r"^### v(?P<version>[0-7])：", chapter, re.MULTILINE)
        )
        self.assertEqual(
            [int(match.group("version")) for match in version_matches],
            list(range(8)),
        )
        for index, match in enumerate(version_matches):
            end = (
                version_matches[index + 1].start()
                if index + 1 < len(version_matches)
                else chapter.index("## 进阶阅读：Recall")
            )
            self.assertIn(
                "**运行结果：**",
                chapter[match.start() : end],
                f"v{index} must show an observable result",
            )
        self.assertLess(chapter.index("### v5：Recall"), chapter.index("### v6：Correct"))
        self.assertLess(chapter.index("### v6：Correct"), chapter.index("### v7：Forget"))
        self.assertLess(chapter.index("## 本章小结"), chapter.index("## Claims："))
        self.assertIn("## 进阶阅读：主流实现", chapter)
        self.assertIn("## 进阶阅读：生产治理", chapter)

if __name__ == "__main__":
    unittest.main()
