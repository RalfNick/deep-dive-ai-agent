from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from chapter6.publication_checks import publication_cjk_characters, validate_chapter_contract


CHAPTER_SIX_FIGURES = (
    "fig6-1-context-growth.svg",
    "fig6-2-state-surfaces.svg",
    "fig6-3-context-lifecycle.svg",
    "fig6-4-compaction-artifact.svg",
    "fig6-5-dual-continuity-timeline.svg",
    "fig6-6-experiment-matrix.svg",
    "fig6-7-product-responsibility-map.svg",
)


def normalized_svg_text(path: Path) -> str:
    root = ElementTree.parse(path).getroot()
    return " ".join(" ".join(root.itertext()).split())


def mobile_text_size_violations(
    *,
    raw: str,
    mobile: ElementTree.Element,
    output_scale: float,
    minimum_core: float = 10.0,
    minimum_source: float = 8.0,
) -> tuple[str, ...]:
    """Resolve mobile text sizes from SVG attributes, classes and inheritance."""
    class_styles: list[tuple[str, float | None, int | None]] = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", raw):
        size = re.search(r"font-size\s*:\s*([\d.]+)px", body)
        weight = re.search(r"font-weight\s*:\s*(\d+|bold|normal)", body)
        if size is None and weight is None:
            continue
        for class_name in re.findall(r"\.([A-Za-z_][\w-]*)", selector):
            class_styles.append(
                (
                    class_name,
                    float(size.group(1)) if size is not None else None,
                    700
                    if weight is not None and weight.group(1) == "bold"
                    else 400
                    if weight is not None and weight.group(1) == "normal"
                    else int(weight.group(1))
                    if weight is not None
                    else None,
                )
            )

    violations: list[str] = []

    def visit(
        element: ElementTree.Element,
        inherited_size: float,
        inherited_weight: int,
    ) -> None:
        classes = set(element.attrib.get("class", "").split())
        presentation_size = element.attrib.get("font-size")
        resolved_size = (
            float(presentation_size.rstrip("px"))
            if presentation_size is not None
            else inherited_size
        )
        presentation_weight = element.attrib.get("font-weight")
        resolved_weight = (
            700
            if presentation_weight == "bold"
            else 400
            if presentation_weight == "normal"
            else int(presentation_weight)
            if presentation_weight is not None
            else inherited_weight
        )
        for class_name, class_size, class_weight in class_styles:
            if class_name in classes:
                if class_size is not None:
                    resolved_size = class_size
                if class_weight is not None:
                    resolved_weight = class_weight
        inline_style = element.attrib.get("style", "")
        inline_size = re.search(r"font-size\s*:\s*([\d.]+)px", inline_style)
        if inline_size is not None:
            resolved_size = float(inline_size.group(1))
        inline_weight = re.search(
            r"font-weight\s*:\s*(\d+|bold|normal)", inline_style
        )
        if inline_weight is not None:
            resolved_weight = (
                700
                if inline_weight.group(1) == "bold"
                else 400
                if inline_weight.group(1) == "normal"
                else int(inline_weight.group(1))
            )

        if element.tag.rsplit("}", 1)[-1] == "text":
            is_core = bool(
                classes
                & {
                    "mobile-core-responsive",
                    "mobile-system-responsive",
                    "mobile-title-responsive",
                }
            ) or resolved_weight >= 600
            minimum = minimum_core if is_core else minimum_source
            effective = resolved_size * output_scale
            if effective + 1e-9 < minimum:
                label = " ".join(" ".join(element.itertext()).split())
                violations.append(
                    f"{label!r}: {effective:.3f}px < {minimum:.1f}px "
                    f"(declared {resolved_size:g}px)"
                )

        for child in element:
            visit(child, resolved_size, resolved_weight)

    visit(mobile, 16.0, 400)
    return tuple(violations)


def figure_metric_label(value: object) -> str:
    if value is None:
        return "未测"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def valid_publication_inputs(
    figure_root: Path,
) -> tuple[str, str, str, tuple[str, ...]]:
    figure_directory = figure_root / "images"
    figure_directory.mkdir(parents=True, exist_ok=True)
    image_paths: list[str] = []
    for index in range(1, 8):
        path = figure_directory / f"fig6-{index}-figure.svg"
        path.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
        image_paths.append(str(path))
    figures = "\n".join(
        f"![图 {index}](./images/fig6-{index}-figure.svg)"
        for index in range(1, 8)
    )
    exercises = "\n".join(
        f'{index}. **★ 练习 {index}**：说明验收条件。'
        for index in range(1, 15)
    )
    answer_sections = []
    for index in range(1, 15):
        category = "基础题" if index <= 4 else "实验题" if index <= 9 else "设计与批判题"
        answer_sections.append(
            f"## {category} {index}：练习 {index}\n\n"
            "**预期推理：** 可解释的判断。\n\n"
            "**常见错误：** 不可接受的混淆。\n\n"
            "**可检查验收：** 可复现规则。"
        )
    answers = "\n\n".join(answer_sections)
    chapter = f"""# 第 6 章 长任务中的上下文架构：压缩之后，Agent 如何继续正确工作

## 双连续性

Event Log、RunCheckpoint、Working Set 与 CompactionArtifact 共同支持 Context
Rehydration，并复用 ContextPacket。执行连续性与语义连续性是不同问题。

## Claims / 本章证明了什么

本章实验只检查确定性的语义连续性合同，体积指标是 serialized_bytes。

## Non-claims / 本章没有证明什么

本章不比较真实模型能力，不做产品排名，也不证明生产成功率。

{figures}

## 分层练习

{exercises}

## 与第 7 章“记忆”的衔接

如果信息只服务当前长任务，它属于 Context/RunState/Session；只有未来独立任务仍需复用的受控信息，才进入第 7 章的 Memory 候选。
"""
    source = """# 第 6 章资料台账

核对日期：2026-08-17

### [S01] 示例一手来源
- 类型：官方一手资料
- URL / 本地路径：https://example.com/primary
- 事实使用：用于说明一个公开接口。
- 明确不声称：不据此推断内部实现或产品排名。
- 最后核对：2026-08-17
- 出版前复核：是
"""
    return chapter, answers, source, tuple(image_paths)


class PublicationChecksTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.inputs = valid_publication_inputs(Path(self._temporary_directory.name))

    def test_publication_gate_rejects_token_claim_for_byte_metric(self) -> None:
        errors = validate_chapter_contract(
            chapter_text="实验节省 42% Token",
            answer_text="",
            source_text="",
            image_paths=(),
        )

        self.assertIn("offline_bytes_mislabeled_as_tokens", errors)

    def test_publication_gate_rejects_missing_non_claims_and_images(self) -> None:
        errors = validate_chapter_contract(
            chapter_text="# 第六章",
            answer_text="",
            source_text="",
            image_paths=(),
        )

        self.assertIn("missing_non_claims", errors)
        self.assertIn("figure_count:0", errors)

    def test_synthetic_complete_chapter_passes(self) -> None:
        self.assertEqual(validate_chapter_contract(*self.inputs), ())

    def test_real_chapter_complete_artifact_passes_shape_and_publication_gate(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        chapter_path = repo_root / "book" / "chapter6.md"
        answer_path = repo_root / "chapter6" / "reference-answers.md"
        source_path = repo_root / "book" / "sources" / "chapter6-sources.md"
        image_paths = tuple(
            str(repo_root / "book" / "images" / name)
            for name in CHAPTER_SIX_FIGURES
        )
        chapter = chapter_path.read_text(encoding="utf-8")

        self.assertEqual(
            validate_chapter_contract(
                chapter,
                answer_path.read_text(encoding="utf-8"),
                source_path.read_text(encoding="utf-8"),
                image_paths,
                enforce_manuscript_length=True,
            ),
            (),
        )
        self.assertGreaterEqual(publication_cjk_characters(chapter), 25_000)
        self.assertLessEqual(publication_cjk_characters(chapter), 30_000)
        self.assertGreaterEqual(len(re.findall(r"^#{2,3}\s", chapter, re.MULTILINE)), 25)
        self.assertLessEqual(len(re.findall(r"^#{2,3}\s", chapter, re.MULTILINE)), 30)

    def test_cjk_metric_accepts_longer_closing_fence(self) -> None:
        manuscript = "正文\n```text\n围栏中文\n````\n结尾"

        self.assertEqual(publication_cjk_characters(manuscript), 4)

    def test_cjk_metric_unmatched_fence_consumes_to_eof(self) -> None:
        manuscript = "开头\n```text\n围栏中文直到结尾"

        self.assertEqual(publication_cjk_characters(manuscript), 2)

    def test_cjk_metric_shorter_fence_does_not_close(self) -> None:
        manuscript = "前\n````text\n隐藏一\n```\n隐藏二\n````\n后"

        self.assertEqual(publication_cjk_characters(manuscript), 2)

    def test_cjk_metric_supports_tilde_fences(self) -> None:
        manuscript = "甲乙\n~~~json\n围栏中文\n~~~~\n丙丁"

        self.assertEqual(publication_cjk_characters(manuscript), 4)

    def test_cjk_metric_honors_commonmark_indentation_limit(self) -> None:
        fenced = "前文\n   ```text\n围栏中文\n   ```   \n后文"
        four_spaces_are_prose = "    ```text\n仍是普通文字\n    ```"

        self.assertEqual(publication_cjk_characters(fenced), 4)
        self.assertEqual(publication_cjk_characters(four_spaces_are_prose), 6)

    def test_cjk_metric_does_not_treat_inline_backticks_as_fence(self) -> None:
        manuscript = "段落里的 ```行内中文``` 不是围栏"

        self.assertEqual(publication_cjk_characters(manuscript), 12)

    def test_cjk_metric_counts_ordinary_prose(self) -> None:
        self.assertEqual(publication_cjk_characters("# 标题\n中文段落。"), 6)

    def test_cjk_metric_rejects_backtick_in_backtick_fence_info(self) -> None:
        manuscript = "```bad`info\n仍是正文\n```"

        self.assertEqual(publication_cjk_characters(manuscript), 4)

    def test_cjk_metric_cannot_be_inflated_by_markdown_or_whitespace(self) -> None:
        compact = "甲乙丙丁"
        inflated = "# 标题\n\n甲  乙\n\n---\n\n丙\t丁" + (" \n" * 10_000)

        self.assertEqual(publication_cjk_characters(compact), 4)
        self.assertEqual(publication_cjk_characters(inflated), 6)

    def test_explicit_manuscript_length_gate_uses_cjk_count(self) -> None:
        _, answers, sources, images = self.inputs
        chapter = "文" * 24_999

        errors = validate_chapter_contract(
            chapter,
            answers,
            sources,
            images,
            enforce_manuscript_length=True,
        )

        self.assertIn("cjk_character_count:24999", errors)

    def test_exact_chapter_seven_bridge_is_required(self) -> None:
        chapter, answers, sources, images = self.inputs
        chapter = chapter.replace(
            "如果信息只服务当前长任务，它属于 Context/RunState/Session；"
            "只有未来独立任务仍需复用的受控信息，才进入第 7 章的 Memory 候选。",
            "下一章讨论长期记忆。",
        )

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn("missing_chapter7_bridge", errors)

    def test_answers_require_reasoning_error_and_acceptance_contracts(self) -> None:
        chapter, answers, sources, images = self.inputs
        answers = answers.replace("**常见错误：**", "**容易混淆：**", 1)

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn("incomplete_answer_contract:1", errors)

    def test_answer_categories_are_four_five_five(self) -> None:
        chapter, answers, sources, images = self.inputs
        answers = answers.replace("## 实验题 5：", "## 基础题 5：")

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn("answer_category_count:基础题=5", errors)
        self.assertIn("answer_category_count:实验题=4", errors)

    def test_title_and_core_contract_terms_are_required(self) -> None:
        chapter, answers, sources, images = self.inputs
        chapter = chapter.replace(
            "# 第 6 章 长任务中的上下文架构：压缩之后，Agent 如何继续正确工作",
            "# 第 6 章 普通上下文技巧",
        ).replace("CompactionArtifact", "交接摘要")

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn("invalid_title", errors)
        self.assertIn("missing_core_term:CompactionArtifact", errors)

    def test_figures_are_unique_references_and_match_inventory(self) -> None:
        chapter, answers, sources, images = self.inputs
        chapter = chapter.replace(
            "![图 7](./images/fig6-7-figure.svg)",
            "![图 7](./images/fig6-6-figure.svg)",
        )

        errors = validate_chapter_contract(chapter, answers, sources, images[1:])

        self.assertIn("figure_count:6", errors)
        self.assertIn("figure_inventory_count:6", errors)
        self.assertIn("figure_reference_inventory_mismatch", errors)

    def test_ghost_figure_paths_are_rejected_even_when_names_match(self) -> None:
        chapter, answers, sources, images = self.inputs
        Path(images[3]).unlink()

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn("missing_figure_file:fig6-4-figure.svg", errors)
        self.assertIn("figure_inventory_count:6", errors)
        self.assertIn("figure_reference_inventory_mismatch", errors)

    def test_markdown_figure_path_must_correspond_to_the_real_inventory_path(self) -> None:
        chapter, answers, sources, images = self.inputs
        chapter = chapter.replace(
            "./images/fig6-1-figure.svg",
            "./ghost/fig6-1-figure.svg",
        )

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn(
            "missing_figure_reference_file:ghost/fig6-1-figure.svg",
            errors,
        )
        self.assertIn("figure_reference_inventory_mismatch", errors)

    def test_exercises_must_be_consecutive_and_answers_aligned(self) -> None:
        chapter, answers, sources, images = self.inputs
        chapter = chapter.replace("14. **★ 练习 14**", "16. **★ 练习 16**")
        answers = answers.replace("## 基础题 3：练习 3", "## 基础题 3：错误标题")

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn("exercise_numbers_not_consecutive", errors)
        self.assertIn("answer_title_mismatch:3", errors)
        self.assertIn("missing_answer:16", errors)
        self.assertIn("orphan_answer:14", errors)

    def test_exercise_count_must_be_fourteen_or_fifteen(self) -> None:
        chapter, answers, sources, images = self.inputs
        chapter = re.sub(r"^14\..*$", "", chapter, flags=re.MULTILINE)
        answers = re.sub(
            r"^## 基础题 14：练习 14\n答案与可检查标准。$",
            "",
            answers,
            flags=re.MULTILINE,
        )

        self.assertIn(
            "exercise_count:13",
            validate_chapter_contract(chapter, answers, sources, images),
        )

    def test_duplicate_exercise_and_answer_numbers_are_rejected(self) -> None:
        chapter, answers, sources, images = self.inputs
        chapter += "\n1. **★ 练习 1 的重复版本**：不得覆盖原题。\n"
        answers += "\n## 基础题 2：练习 2 的重复答案\n不得覆盖原答案。\n"

        errors = validate_chapter_contract(chapter, answers, sources, images)

        self.assertIn("duplicate_exercise_number:1", errors)
        self.assertIn("duplicate_answer_number:2", errors)

    def test_secret_scanner_catches_realistic_secrets_but_not_placeholders(self) -> None:
        chapter, answers, sources, images = self.inputs
        for leaked in (
            "DEEPSEEK_API_KEY=" + "sk-" + "0123456789abcdef" * 2,
            "Authorization: " + "Bearer " + "abcdefghijklmnopqrstuvwxyz012345",
            "AWS key AKIA1234567890ABCDEF",
        ):
            with self.subTest(leaked=leaked):
                self.assertIn(
                    "forbidden_secret_pattern",
                    validate_chapter_contract(
                        chapter + leaked, answers, sources, images
                    ),
                )

        harmless = chapter + "\n使用 `DEEPSEEK_API_KEY` 环境变量；示例写成 `sk-...`。"
        self.assertNotIn(
            "forbidden_secret_pattern",
            validate_chapter_contract(harmless, answers, sources, images),
        )

    def test_bare_author_paths_are_rejected_only_in_public_prose(self) -> None:
        chapter, answers, sources, images = self.inputs
        leaked = chapter + "\n作者文件位于 " + "E:" + "\\Codex-Projects\\private\\notes.md。"

        self.assertIn(
            "bare_local_author_path",
            validate_chapter_contract(leaked, answers, sources, images),
        )

        code_example = chapter + "\n```powershell\nSet-Location C:\\demo\\repo\n```"
        source_with_local_path = (
            sources + "\n- URL / 本地路径：用户提供资料《AI学习资料.pdf》（未入库）"
        )
        self.assertNotIn(
            "bare_local_author_path",
            validate_chapter_contract(code_example, answers, source_with_local_path, images),
        )

    def test_ranking_claims_are_rejected_without_blocking_explicit_non_claims(self) -> None:
        chapter, answers, sources, images = self.inputs

        ranked = chapter + "\nClaude Code 比 Codex 更聪明，因而全面领先。"
        self.assertIn(
            "product_ranking_claim",
            validate_chapter_contract(ranked, answers, sources, images),
        )

        bounded = chapter + "\n这些观察不能证明 Claude Code 或 Codex 谁更聪明。"
        self.assertNotIn(
            "product_ranking_claim",
            validate_chapter_contract(bounded, answers, sources, images),
        )

    def test_ranking_gate_catches_english_and_reliability_suitability_claims(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "Claude Code is more reliable than Codex for long tasks.",
            "Codex outperforms Claude Code on context continuity.",
            "Claude Code 比 Codex 更可靠。",
            "Codex 比 Claude Code 更适合长任务。",
            "LangGraph 在恢复可靠性上优于 Codex。",
            "Claude Code 的稳定性高于 Codex。",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "product_ranking_claim",
                    validate_chapter_contract(
                        chapter + "\n" + claim, answers, sources, images
                    ),
                )

    def test_ranking_disclaimers_do_not_hide_a_later_ranking_claim(self) -> None:
        chapter, answers, sources, images = self.inputs
        disclaimer = chapter + (
            "\nThis does not prove Claude Code is more reliable than Codex."
            "\n这些观察不能证明 Claude Code 比 Codex 更可靠。"
        )
        bypass = disclaimer + "\nHowever, Codex outperforms Claude Code in practice."

        self.assertNotIn(
            "product_ranking_claim",
            validate_chapter_contract(disclaimer, answers, sources, images),
        )
        self.assertIn(
            "product_ranking_claim",
            validate_chapter_contract(bypass, answers, sources, images),
        )

    def test_ranking_disclaimer_exempts_only_its_negated_claim_span(self) -> None:
        chapter, answers, sources, images = self.inputs
        english = chapter + (
            "\nThis does not prove Claude Code is more reliable than Codex, "
            "but Codex outperforms Claude Code in practice."
        )
        chinese = chapter + (
            "\n这些观察不能证明 Claude Code 比 Codex 更可靠，不过 "
            "Codex 比 Claude Code 更稳定。"
        )
        disclaimer_only = chapter + (
            "\nThis does not prove Claude Code is more reliable than Codex."
            "\n这些观察不能证明 Claude Code 比 Codex 更可靠。"
        )

        for bypass in (english, chinese):
            with self.subTest(bypass=bypass[-100:]):
                self.assertIn(
                    "product_ranking_claim",
                    validate_chapter_contract(bypass, answers, sources, images),
                )
        self.assertNotIn(
            "product_ranking_claim",
            validate_chapter_contract(disclaimer_only, answers, sources, images),
        )

    def test_byte_metric_gate_allows_correct_units_and_general_token_facts(self) -> None:
        chapter, answers, sources, images = self.inputs
        bounded = chapter + (
            "\n离线实验的 serialized_bytes 下降 42%，不是 Provider Token。"
            "\n官方文档以 Token 描述上下文窗口容量。"
        )

        self.assertNotIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(bounded, answers, sources, images),
        )

    def test_offline_report_token_reductions_are_rejected_without_word_experiment(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "固定报告显示 Token 减少 42%。",
            "离线报告中 Token 从 1,200 降到 600。",
            "The offline lab reports a 42% Token reduction.",
            "The deterministic report says tokens fell from 1200 to 600.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n" + claim, answers, sources, images
                    ),
                )

    def test_english_offline_measurement_scope_variants_are_rejected(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "The offline experiment found a 42% Token reduction.",
            "OFFLINE EXPERIMENTS report Token savings of 42%.",
            "The fixed report shows a 42% token reduction.",
            "Fixed reports show Token savings of 42%.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n" + claim, answers, sources, images
                    ),
                )

    def test_bounded_english_token_reduction_grammar_catches_both_word_orders(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "The offline experiment reports a 42% reduction in Token use.",
            "The fixed report shows 42% fewer tokens.",
            "In the offline lab, tokens fell by 42%.",
            "The offline report says tokens decreased to 600.",
            "The fixed report records Token savings of 42%.",
            "The offline experiment found a reduction of 42% in Token usage.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + claim, answers, sources, images
                    ),
                )

    def test_token_savings_predicates_and_written_percentages_are_rejected(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "The offline report says Token savings were 42%.",
            "The fixed report says Token savings was 42 percent.",
            "The offline lab says Token savings reached 42%.",
            "The fixed report says Token savings amounted to 42 percent.",
            "The offline experiment says Token savings totaled 42%.",
            "The offline report found a 42 percent reduction in Token use.",
            "The fixed report found 42 percent fewer tokens.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + claim, answers, sources, images
                    ),
                )

    def test_generic_offline_token_mentions_without_reduction_are_allowed(self) -> None:
        chapter, answers, sources, images = self.inputs
        controls = (
            "The offline report records 1,200 tokens.",
            "The fixed report discusses Token usage.",
            "The offline experiment uses a 200K Token context window.",
            "The offline lab stores a Token count field.",
        )
        for control in controls:
            with self.subTest(control=control):
                self.assertNotIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + control, answers, sources, images
                    ),
                )

    def test_offline_scope_propagates_across_clauses_in_the_same_paragraph(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "The offline report is measured in bytes, Token reduction was 42%.",
            "离线报告以字节测量，Token 减少了 42%。",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + claim, answers, sources, images
                    ),
                )

    def test_official_token_discussion_and_negated_offline_claims_are_allowed(self) -> None:
        chapter, answers, sources, images = self.inputs
        bounded = chapter + (
            "\n\nOfficial model usage documentation reports Token usage and savings."
            "\nThe official context window is described as 200K tokens."
            "\n\nThe offline experiment does not claim a 42% Token reduction."
            "\n离线实验并未声称 Token 减少 42%。"
        )

        self.assertNotIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(bounded, answers, sources, images),
        )

    def test_prior_offline_scope_does_not_capture_external_official_token_usage(self) -> None:
        chapter, answers, sources, images = self.inputs
        bounded = chapter + (
            "\n\nThe offline report uses serialized_bytes. "
            "OpenAI official model usage documentation says tokens fell from "
            "1,200 to 600."
        )

        self.assertNotIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(bounded, answers, sources, images),
        )

    def test_external_attribution_overrides_inherited_offline_scope_by_clause(self) -> None:
        chapter, answers, sources, images = self.inputs
        bounded = chapter + (
            "\n\nThe offline report uses serialized_bytes, but OpenAI official "
            "model usage documentation says tokens fell by 42%."
        )

        self.assertNotIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(bounded, answers, sources, images),
        )

    def test_standalone_official_docs_reset_inherited_offline_scope(self) -> None:
        chapter, answers, sources, images = self.inputs
        controls = (
            "The offline report uses serialized_bytes, but official docs say "
            "Token savings reached 42%.",
            "The fixed report uses bytes, however OFFICIAL DOCUMENTATION says "
            "tokens decreased by 42 percent.",
            "The offline experiment uses bytes, but an official doc says "
            "42 percent fewer tokens were used.",
        )
        for control in controls:
            with self.subTest(control=control):
                self.assertNotIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + control, answers, sources, images
                    ),
                )

    def test_offline_report_self_labels_do_not_reset_scope(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "The offline report has official docs: Token savings reached 42%.",
            "The fixed report says official documentation: Token savings were 42%.",
            "The deterministic report calls itself official docs: Token savings "
            "totaled 42%.",
            "The offline report official documentation: Token savings amounted "
            "to 42%.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + claim, answers, sources, images
                    ),
                )

    def test_clause_initial_documentation_attribution_remains_external(self) -> None:
        chapter, answers, sources, images = self.inputs
        controls = (
            "Official docs: tokens fell by 42%.",
            "According to official documentation, tokens fell by 42%.",
            "The offline report uses serialized_bytes, but Official docs: "
            "tokens fell by 42%.",
            "The fixed report uses bytes, however OpenAI official documentation "
            "says Token savings reached 42%.",
            "The offline report uses bytes, but Anthropic official docs report "
            "42 percent fewer tokens.",
        )
        for control in controls:
            with self.subTest(control=control):
                self.assertNotIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + control, answers, sources, images
                    ),
                )

    def test_offline_reports_cannot_escape_by_calling_themselves_official(self) -> None:
        chapter, answers, sources, images = self.inputs
        claims = (
            "The offline report is official, Token savings reached 42%.",
            "The offline report carries an official docs label, Token savings "
            "reached 42%.",
        )
        generic = chapter + (
            "\n\nThe offline report has an official label and records 42 tokens."
        )

        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIn(
                    "offline_bytes_mislabeled_as_tokens",
                    validate_chapter_contract(
                        chapter + "\n\n" + claim, answers, sources, images
                    ),
                )
        self.assertNotIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(generic, answers, sources, images),
        )

    def test_later_offline_attribution_reestablishes_scope_after_external_clause(self) -> None:
        chapter, answers, sources, images = self.inputs
        claim = chapter + (
            "\n\nThe offline report uses serialized_bytes, but OpenAI official "
            "model usage documentation says tokens fell by 42%, however the "
            "fixed report claims 42% fewer tokens."
        )

        self.assertIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(claim, answers, sources, images),
        )

    def test_token_unit_disclaimer_does_not_hide_a_later_mislabeled_claim(self) -> None:
        chapter, answers, sources, images = self.inputs
        disclaimer = chapter + (
            "\n固定报告的单位不是 Token，而是 serialized_bytes，下降 42%。"
            "\n官方文档说明 context window 容量以 200K tokens 表示。"
        )
        bypass = disclaimer + "\n但固定报告仍显示 Token 减少 42%。"

        self.assertNotIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(disclaimer, answers, sources, images),
        )
        self.assertIn(
            "offline_bytes_mislabeled_as_tokens",
            validate_chapter_contract(bypass, answers, sources, images),
        )

    def test_source_ledger_requires_a_complete_record_shape(self) -> None:
        chapter, answers, sources, images = self.inputs
        incomplete = sources.replace("- 明确不声称：不据此推断内部实现或产品排名。\n", "")

        self.assertIn(
            "source_record_missing_non_claim:S01",
            validate_chapter_contract(chapter, answers, incomplete, images),
        )

    def test_source_ledger_rejects_blank_title_and_field_values(self) -> None:
        chapter, answers, sources, images = self.inputs
        mutations = (
            ("### [S01] 示例一手来源", "### [S01]   ", "source_record_blank_title:S01"),
            (
                "- URL / 本地路径：https://example.com/primary",
                "- URL / 本地路径：   ",
                "source_record_blank_location:S01",
            ),
            (
                "- 事实使用：用于说明一个公开接口。",
                "- 事实使用：   ",
                "source_record_blank_fact_used:S01",
            ),
            (
                "- 明确不声称：不据此推断内部实现或产品排名。",
                "- 明确不声称：   ",
                "source_record_blank_non_claim:S01",
            ),
            (
                "- 最后核对：2026-08-17",
                "- 最后核对：   ",
                "source_record_blank_verified_date:S01",
            ),
            (
                "- 出版前复核：是",
                "- 出版前复核：   ",
                "source_record_blank_recheck_flag:S01",
            ),
        )
        for old, new, expected in mutations:
            with self.subTest(expected=expected):
                errors = validate_chapter_contract(
                    chapter, answers, sources.replace(old, new), images
                )
                self.assertIn(expected, errors)


class ChapterSixSourceLedgerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = Path("book/sources/chapter6-sources.md")
        cls.text = cls.path.read_text(encoding="utf-8")

    def test_ledger_records_use_the_frozen_publication_date_and_fields(self) -> None:
        records = re.split(r"(?=^### \[S\d+\])", self.text, flags=re.MULTILINE)[1:]
        self.assertGreaterEqual(len(records), 17)
        for record in records:
            source_id = re.match(r"### \[(S\d+)\]", record).group(1)  # type: ignore[union-attr]
            with self.subTest(source=source_id):
                self.assertIn("- URL / 本地路径：", record)
                self.assertIn("- 事实使用：", record)
                self.assertIn("- 明确不声称：", record)
                self.assertIn("- 最后核对：2026-08-17", record)
                self.assertRegex(record, r"- 出版前复核：(是|否)")

    def test_ledger_covers_required_primary_and_local_materials(self) -> None:
        required_fragments = (
            "https://openai.com/index/unrolling-the-codex-agent-loop/",
            "https://developers.openai.com/api/docs/guides/compaction",
            "https://openai.github.io/openai-agents-python/sessions/",
            "https://code.claude.com/docs/en/context-window",
            "https://code.claude.com/docs/en/how-claude-code-works",
            "https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents",
            "https://www.anthropic.com/engineering/harness-design-long-running-apps",
            "https://docs.langchain.com/oss/python/langgraph/persistence",
            "https://docs.langchain.com/oss/python/langchain/short-term-memory",
            "https://aclanthology.org/2024.tacl-1.9/",
            "book/chapter4.md",
            "chapter4/reports/harness-boundary-matrix.json",
            "book/chapter5.md",
            "chapter5/context/",
            "docs/author-sources/phase-4/03-agent-memory-system.md",
            "docs/author-sources/phase-4/05-agent-runtime-integration.md",
            "docs/author-sources/codex-tutorial/2026-08-12-from-ai-coding-to-digital-employee.md",
            "https://github.com/bojieli/ai-agent-book",
            "用户提供资料《AI学习资料.pdf》（未入库）",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.text)

    def test_every_repo_relative_location_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            chapter, answers, _, images = valid_publication_inputs(
                Path(temporary_directory)
            )
            errors = validate_chapter_contract(chapter, answers, self.text, images)

        self.assertFalse(
            tuple(error for error in errors if error.startswith("source_local_path_")),
            errors,
        )

    def test_missing_repo_relative_location_has_explicit_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            chapter, answers, _, images = valid_publication_inputs(
                Path(temporary_directory)
            )
            corrupted = self.text.replace(
                "chapter4/reports/harness-boundary-matrix.json",
                "chapter4/reports/ghost-report.json",
            )
            errors = validate_chapter_contract(chapter, answers, corrupted, images)

        self.assertIn(
            "source_local_path_missing:S12:chapter4/reports/ghost-report.json",
            errors,
        )

    def test_pdf_is_explicitly_secondary_and_not_used_for_product_facts(self) -> None:
        pdf_record = next(
            record
            for record in re.split(
                r"(?=^### \[S\d+\])", self.text, flags=re.MULTILINE
            )
            if "用户提供资料《AI学习资料.pdf》（未入库）" in record
        )
        self.assertIn("二手", pdf_record)
        self.assertIn("23 页", pdf_record)
        self.assertIn("无可提取文本层", pdf_record)
        self.assertIn("不用于产品事实", pdf_record)


class ChapterSixFigurePublicationTest(unittest.TestCase):
    image_root = Path("book/images")
    report_path = Path("chapter6/reports/context-continuity.json")

    def test_all_seven_figures_are_safe_parseable_accessible_svg(self) -> None:
        paths = sorted(self.image_root.glob("fig6-*.svg"))
        self.assertEqual(tuple(path.name for path in paths), CHAPTER_SIX_FIGURES)

        for path in paths:
            with self.subTest(figure=path.name):
                root = ElementTree.parse(path).getroot()
                self.assertEqual(root.attrib.get("width"), "1200")
                self.assertEqual(root.attrib.get("height"), "675")
                self.assertEqual(root.attrib.get("viewBox"), "0 0 1200 675")
                self.assertEqual(root.attrib.get("role"), "img")
                self.assertEqual(root.attrib.get("aria-labelledby"), "title desc")
                children = list(root)
                self.assertGreaterEqual(len(children), 2)
                self.assertTrue(children[0].tag.endswith("title"))
                self.assertEqual(children[0].attrib.get("id"), "title")
                self.assertTrue(children[1].tag.endswith("desc"))
                self.assertEqual(children[1].attrib.get("id"), "desc")
                self.assertTrue((children[0].text or "").strip())
                self.assertTrue((children[1].text or "").strip())

                raw = path.read_text(encoding="utf-8")
                lowered = raw.lower()
                self.assertNotIn("<script", lowered)
                self.assertNotIn("<foreignobject", lowered)
                self.assertNotIn("<image", lowered)
                self.assertNotRegex(lowered, r"(?:xlink:)?href\s*=")
                external_text = lowered.replace(
                    'xmlns="http://www.w3.org/2000/svg"', ""
                )
                self.assertNotRegex(external_text, r"https?://")
                self.assertIn("#172033", lowered)
                self.assertIn("microsoft yahei", lowered)

    def test_context_growth_labels_come_from_fixed_report(self) -> None:
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        cases = {
            case["variant"]: case
            for case in report["cases"]
            if case["experiment"] == "context_growth"
        }
        text = normalized_svg_text(self.image_root / CHAPTER_SIX_FIGURES[0])

        cursor_variants = (
            ("事件 8", "append-all-cursor-08"),
            ("事件 24", "append-all-cursor-24"),
        )
        for cursor, variant in cursor_variants:
            case = cases[variant]
            with self.subTest(variant=variant):
                self.assertIn(cursor, text)
                self.assertIn(f'{case["serialized_bytes_after"]:,} B', text)
                self.assertIn(variant, text)
        self.assertIn("canonical UTF-8 bytes", text)
        self.assertNotIn("Token", text)

    def test_experiment_matrix_uses_separate_report_metrics_and_marks_null(self) -> None:
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        cases = {case["variant"]: case for case in report["cases"]}
        text = normalized_svg_text(self.image_root / CHAPTER_SIX_FIGURES[5])

        def labels_for(
            variant: str, *metrics: tuple[str, str]
        ) -> tuple[str, ...]:
            case = cases[variant]
            grade = case["grade"]
            labels = tuple(
                f"{display} {figure_metric_label(grade[field])}"
                for display, field in metrics
            )
            return labels + (f'{case["serialized_bytes_after"]:,} B',)

        expected = {
            "structured-compaction-v1": labels_for(
                "structured-compaction-v1",
                ("约束", "constraint_retention"),
                ("开放问题", "open_issue_retention"),
            ),
            "summary-only-v1": labels_for(
                "summary-only-v1",
                ("约束", "constraint_retention"),
                ("开放问题", "open_issue_retention"),
            ),
            "sliding-window-8-events": labels_for(
                "sliding-window-8-events",
                ("约束", "constraint_retention"),
                ("开放问题", "open_issue_retention"),
            ),
            "checkpoint-only-v1": labels_for(
                "checkpoint-only-v1",
                ("约束", "constraint_retention"),
                ("恢复", "resume_correct"),
                ("Packet", "packet_contract_passed"),
            ),
            "rehydrated-context-v1": labels_for(
                "rehydrated-context-v1",
                ("约束", "constraint_retention"),
                ("恢复", "resume_correct"),
                ("Packet", "packet_contract_passed"),
            ),
        }
        for variant, labels in expected.items():
            self.assertIn(variant, cases)
            self.assertIn(variant, text)
            for label in labels:
                self.assertIn(label, text)
        self.assertIn("独立指标，无聚合总分", text)

    def test_semantic_contract_figures_keep_boundaries_explicit(self) -> None:
        state_surfaces = normalized_svg_text(
            self.image_root / CHAPTER_SIX_FIGURES[1]
        )
        self.assertIn("七个状态表面", state_surfaces)
        self.assertIn("Commit boundary 是操作关系，不是状态表面", state_surfaces)

        artifact_path = self.image_root / CHAPTER_SIX_FIGURES[3]
        artifact = normalized_svg_text(artifact_path)
        self.assertIn("自由文本摘要", artifact)
        root = ElementTree.parse(artifact_path).getroot()
        contract_fields: dict[str, set[str]] = {}
        for element in root.iter():
            contract = element.attrib.get("data-contract")
            field = element.attrib.get("data-field")
            if contract and field:
                contract_fields.setdefault(contract, set()).add(field)

        self.assertEqual(
            contract_fields["CompactionArtifact"],
            {
                "artifact_id",
                "run_id",
                "source_event_range",
                "goal",
                "acceptance_criteria",
                "constraints",
                "decisions",
                "rejected_hypotheses",
                "open_issues",
                "verification_state",
                "evidence_locators",
                "next_intent",
                "created_at",
                "source_digest",
                "workspace_digest",
                "schema_version",
            },
        )
        self.assertEqual(
            contract_fields["CarryItem"],
            {
                "key",
                "kind",
                "content",
                "authority",
                "trust",
                "retention_priority",
                "sensitivity",
                "source_event_ids",
                "required_for",
            },
        )
        self.assertEqual(
            contract_fields["EvidenceLocator"],
            {
                "locator_id",
                "kind",
                "ref",
                "content_digest",
                "workspace_digest",
            },
        )

        continuity = normalized_svg_text(self.image_root / CHAPTER_SIX_FIGURES[4])
        self.assertIn("执行连续性", continuity)
        self.assertIn("Checkpoint → next_step", continuity)
        self.assertIn("语义连续性", continuity)
        self.assertIn("Artifact → Rehydrator → Packet", continuity)
        self.assertIn("Checkpoint 不能单独恢复语义", continuity)
        self.assertIn("先持久化 Artifact", continuity)
        self.assertIn("再保存 RunCheckpoint", continuity)
        self.assertIn("artifact_id 单向引用", continuity)
        self.assertNotIn("commit_id", continuity)

    def test_product_map_uses_sourced_dimensions_without_ranking(self) -> None:
        path = self.image_root / CHAPTER_SIX_FIGURES[6]
        text = normalized_svg_text(path)
        for product in ("Claude Code", "OpenAI Agent surfaces", "LangGraph"):
            self.assertIn(product, text)
        for dimension in (
            "历史归属",
            "压缩触发",
            "压缩制品",
            "执行恢复",
            "语义重建",
            "跨任务状态",
            "可观测证据",
        ):
            self.assertIn(dimension, text)
        for source_id in ("S01", "S02", "S04", "S05", "S06", "S09", "S10"):
            self.assertIn(source_id, text)
        for attribution in (
            "Codex · S01",
            "Responses API · S02",
            "Agents SDK · S04",
            "Claude Code · S05",
            "Claude Code · S06",
            "LangGraph · S09",
            "LangChain · S10",
        ):
            self.assertIn(attribution, text)
        self.assertIn("产品表面不可互换", text)
        ranking_terms = ("排名", "更强", "更好", "领先", "胜出")
        for term in ranking_terms:
            self.assertNotIn(term, text)

        root = ElementTree.parse(path).getroot()
        layouts = {
            element.attrib["data-layout"]: element
            for element in root.iter()
            if element.attrib.get("data-layout")
        }
        for layout_name in ("desktop", "mobile"):
            chips = [
                element
                for element in layouts[layout_name].iter()
                if element.attrib.get("data-dimension")
            ]
            with self.subTest(layout=layout_name):
                self.assertEqual(len(chips), 21)
                self.assertTrue(
                    all(element.attrib.get("data-source") for element in chips)
                )

    def test_semantic_figures_have_real_responsive_mobile_layouts(self) -> None:
        for name in CHAPTER_SIX_FIGURES[1:]:
            path = self.image_root / name
            raw = path.read_text(encoding="utf-8")
            root = ElementTree.parse(path).getroot()
            layouts = {
                element.attrib["data-layout"]: element
                for element in root.iter()
                if element.attrib.get("data-layout")
            }
            with self.subTest(figure=name):
                self.assertEqual(set(layouts), {"desktop", "mobile"})
                self.assertIn("@media (max-width: 600px)", raw)
                self.assertIn(".desktop{display:none}", raw)
                self.assertIn(".mobile{display:inline}", raw)

                mobile = layouts["mobile"]
                transform = mobile.attrib.get("transform", "")
                scale_match = re.fullmatch(r"scale\(([\d.]+)\)", transform)
                self.assertIsNotNone(scale_match)
                scale = float(scale_match.group(1))  # type: ignore[union-attr]

                output_scale = scale * min(390 / 1200, 219 / 675)
                self.assertEqual(
                    (),
                    mobile_text_size_violations(
                        raw=raw,
                        mobile=mobile,
                        output_scale=output_scale,
                    ),
                )

    def test_explicit_mobile_font_size_cannot_escape_threshold(self) -> None:
        raw = """<svg xmlns="http://www.w3.org/2000/svg">
        <style>.mobile-source-responsive{font-size:8px}.mobile-core-responsive{font-size:9px}.tiny{font-size:7px}</style>
        <g data-layout="mobile" transform="scale(3.083)">
          <text class="mobile-source-responsive">class source</text>
          <text font-size="7">explicit source escape</text>
          <text class="tiny">class source escape</text>
          <g font-size="7"><text>inherited source escape</text></g>
          <text style="font-size:7px">inline source escape</text>
          <text class="mobile-core-responsive">class core escape</text>
          <g font-size="9" font-weight="700"><text>inherited core escape</text></g>
        </g></svg>"""
        root = ElementTree.fromstring(raw)
        mobile = next(
            element
            for element in root.iter()
            if element.attrib.get("data-layout") == "mobile"
        )

        self.assertEqual(
            (
                "'explicit source escape': 7.000px < 8.0px (declared 7px)",
                "'class source escape': 7.000px < 8.0px (declared 7px)",
                "'inherited source escape': 7.000px < 8.0px (declared 7px)",
                "'inline source escape': 7.000px < 8.0px (declared 7px)",
                "'class core escape': 9.000px < 10.0px (declared 9px)",
                "'inherited core escape': 9.000px < 10.0px (declared 9px)",
            ),
            mobile_text_size_violations(raw=raw, mobile=mobile, output_scale=1.0),
        )

    def test_experiment_matrix_mobile_keeps_evidence_labels(self) -> None:
        matrix_root = ElementTree.parse(
            self.image_root / CHAPTER_SIX_FIGURES[5]
        ).getroot()
        matrix_mobile = next(
            element
            for element in matrix_root.iter()
            if element.attrib.get("data-layout") == "mobile"
        )
        matrix_text = " ".join(" ".join(matrix_mobile.itertext()).split())
        for label in (
            "事件 8 3,950 B",
            "事件 24 12,108 B",
            "结构化 C/O 1.0/1.0",
            "摘要 C/O 0.0/0.0",
            "恢复 未测",
            "Packet 未测",
            "开放问题丢失 → 误报完成",
        ):
            self.assertIn(label, matrix_text)


if __name__ == "__main__":
    unittest.main()
