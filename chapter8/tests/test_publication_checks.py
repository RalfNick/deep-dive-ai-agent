import tempfile
import unittest
from pathlib import Path

from chapter8.publication_checks import PublicationContract, publication_errors, strip_fenced_code


FIGURES = tuple(f"fig8-{index}-demo.svg" for index in range(1, 9))


def valid_chapter() -> str:
    figures = "\n".join(f"![figure {index}](./images/{name})" for index, name in enumerate(FIGURES, start=1))
    star = "\u2605"
    exercises = "\n".join(
        f'{index}. **{star * min(index, 4)} exercise {index}**: acceptance.'
        for index in range(1, 15)
    )
    return f"""# \u7b2c 8 \u7ae0 RAG

## \u5177\u4f53\u95ee\u9898

\u7528\u7248\u672c\u6743\u9650\u65f6\u6548\u51b2\u7a81\u89e3\u91ca RAG\u3002\u8fd9\u91cc\u6709\u8db3\u591f\u4e2d\u6587\u7528\u4e8e\u6700\u5c0f\u6d4b\u8bd5\u3002

## v0 to v7

{figures}

> **experiment**
>
> \u672c\u5b9e\u9a8c\u652f\u6301\uff1a\u56fa\u5b9a\u5939\u5177\u7684\u8fb9\u754c\u5224\u65ad\u3002
>
> \u672c\u5b9e\u9a8c\u4e0d\u652f\u6301\uff1a\u771f\u5b9e\u6a21\u578b\u8d28\u91cf\u3002

## Claims\uff1a\u672c\u7ae0\u8bc1\u660e\u4e86\u4ec0\u4e48

- \u56fa\u5b9a\u5939\u5177\u652f\u6301\u8fb9\u754c\u7ed3\u8bba\u3002

## Non-claims\uff1a\u672c\u7ae0\u6ca1\u6709\u8bc1\u660e\u4ec0\u4e48

- \u4e0d\u4ee3\u8868\u4ea7\u54c1\u6392\u540d\u3002

## \u7ec3\u4e60

{exercises}
"""


def valid_answers() -> str:
    return "# answers\n\n" + "\n\n".join(
        f"## {index}. answer {index}\n\n**reasoning**: reason.\n\n**error**: error.\n\n**acceptance**: check."
        for index in range(1, 15)
    )


def valid_sources() -> str:
    records = []
    for index in range(1, 16):
        records.append(
            f"""### [S{index:02d}] source {index}
- \u7c7b\u578b\uff1a\u5b98\u65b9\u6587\u6863
- URL / \u672c\u5730\u8def\u5f84\uff1ahttps://example.com/source-{index}
- \u4e8b\u5b9e\u4f7f\u7528\uff1a\u6709\u9650\u4e8b\u5b9e\u3002
- \u660e\u786e\u4e0d\u58f0\u79f0\uff1a\u4e0d\u5916\u63a8\u3002
- \u6700\u540e\u6838\u5bf9\uff1a2026-08-28
- \u51fa\u7248\u524d\u590d\u6838\uff1a\u662f"""
        )
    return "# sources\n\n" + "\n\n".join(records) + "\n"


class PublicationChecksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = PublicationContract(min_cjk=20, max_cjk=10_000, min_headings=3, max_headings=12)

    def _write_bundle(self, root: Path, *, chapter=None, answers=None, sources=None):
        image_dir = root / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        for name in FIGURES:
            (image_dir / name).write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675"><title>demo</title><desc>demo</desc></svg>',
                encoding="utf-8",
            )
        chapter_path, answers_path, sources_path = root / "chapter8.md", root / "answers.md", root / "sources.md"
        chapter_path.write_text(chapter or valid_chapter(), encoding="utf-8")
        answers_path.write_text(answers or valid_answers(), encoding="utf-8")
        sources_path.write_text(sources or valid_sources(), encoding="utf-8")
        return chapter_path, answers_path, sources_path, image_dir

    def test_valid_synthetic_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._write_bundle(Path(temp_dir))
            self.assertEqual(publication_errors(*paths, contract=self.contract), ())

    def test_figures_and_exercises_must_be_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._write_bundle(Path(temp_dir))
            (paths[3] / FIGURES[-1]).unlink()
            self.assertIn("missing_figure:fig8-8-demo.svg", publication_errors(*paths, contract=self.contract))
            duplicate = valid_chapter() + "\n1. **\u2605 duplicate**: duplicate.\n"
            paths = self._write_bundle(Path(temp_dir), chapter=duplicate)
            self.assertIn("duplicate_exercise_number:1", publication_errors(*paths, contract=self.contract))

    def test_sources_need_fields_and_existing_local_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sources = valid_sources().replace("- \u4e8b\u5b9e\u4f7f\u7528\uff1a\u6709\u9650\u4e8b\u5b9e\u3002", "- \u4e8b\u5b9e\u4f7f\u7528\uff1a", 1)
            paths = self._write_bundle(Path(temp_dir), sources=sources)
            self.assertIn("source_record_missing_field:S01:\u4e8b\u5b9e\u4f7f\u7528", publication_errors(*paths, contract=self.contract))
            sources = valid_sources().replace("https://example.com/source-1", "chapter8/missing-evidence.json", 1)
            paths = self._write_bundle(Path(temp_dir), sources=sources)
            self.assertIn("missing_local_source:S01:chapter8/missing-evidence.json", publication_errors(*paths, contract=self.contract))

    def test_safety_scans_reject_paths_secrets_rankings_and_fake_token_claims(self) -> None:
        unsafe = valid_chapter() + "\nD:\\private\\draft.md\nAPI_KEY=live-secret-value\nCodex \u6bd4 Claude Code \u66f4\u53ef\u9760\u3002\n\u56fa\u5b9a\u62a5\u544a\u663e\u793a Token \u51cf\u5c11 42%\u3002\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._write_bundle(Path(temp_dir), chapter=unsafe)
            errors = publication_errors(*paths, contract=self.contract)
            self.assertIn("absolute_author_path", errors)
            self.assertIn("possible_secret", errors)
            self.assertIn("unsupported_product_ranking", errors)
            self.assertIn("offline_bytes_mislabeled_as_tokens", errors)

    def test_fenced_code_is_excluded_from_prose_count(self) -> None:
        text = "\u6b63\u6587\u4e2d\u6587\n~~~python\n\u56f4\u680f\u4e2d\u7684\u4e2d\u6587\u4e0d\u7b97\u6b63\u6587\n~~~\n\u7ed3\u5c3e\u4e2d\u6587"
        stripped = strip_fenced_code(text)
        self.assertIn("\u6b63\u6587\u4e2d\u6587", stripped)
        self.assertNotIn("\u56f4\u680f\u4e2d\u7684\u4e2d\u6587", stripped)


if __name__ == "__main__":
    unittest.main()
