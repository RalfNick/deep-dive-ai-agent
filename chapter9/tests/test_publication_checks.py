from pathlib import Path
import tempfile
import unittest

from chapter9.publication_checks import PublicationContract, publication_errors


ROOT = Path(__file__).resolve().parents[2]
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


class PublicationChecksTests(unittest.TestCase):
    def test_real_bundle_only_waits_for_the_eight_named_figures(self):
        self.assertEqual(
            tuple(f"missing_figure:{name}" for name in FIGURES),
            publication_errors(ROOT),
        )

    def test_synthetic_bundle_exposes_every_publication_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book/sources").mkdir(parents=True)
            (root / "book/images").mkdir(parents=True)
            (root / "chapter9").mkdir(parents=True)
            (root / "book/chapter9.md").write_text(
                "# 第 9 章\n\n"
                "### v0：只有一个版本\n\n"
                "1. ★ 重复编号\n"
                "1. ★ 再次重复\n\n"
                "模型排名：第一。字符数就是 Token。\n"
                "DEEPSEEK_API_KEY=sk-" + "x" * 30 + "\n"
                "D:/private/book.md # safety-fixture: allow\n",
                encoding="utf-8",
            )
            (root / "book/sources/chapter9-sources.md").write_text(
                "### [S01] 唯一来源\n",
                encoding="utf-8",
            )
            (root / "chapter9/reference-answers.md").write_text(
                "## 第 1 题\n\n没有固定字段。\n",
                encoding="utf-8",
            )
            (root / "chapter9/README.md").write_text("# 实验\n", encoding="utf-8")

            errors = publication_errors(root, PublicationContract(min_cjk=200, max_cjk=300))

        prefixes = {error.split(":", 1)[0] for error in errors}
        for expected in (
            "cjk_count_out_of_range",
            "heading_count_out_of_range",
            "missing_version",
            "figure_set_mismatch",
            "exercise_numbers_invalid",
            "missing_answer",
            "source_count_below_minimum",
            "secret_like_text",
            "author_machine_path",
            "unsupported_ranking_claim",
            "offline_unit_called_token",
        ):
            self.assertIn(expected, prefixes)


if __name__ == "__main__":
    unittest.main()
