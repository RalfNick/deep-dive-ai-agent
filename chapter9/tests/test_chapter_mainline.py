from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "book/sources/chapter9-sources.md"
CHAPTER = ROOT / "book/chapter9.md"


class ChapterMainlineTests(unittest.TestCase):
    def test_source_ledger_has_current_official_protocol_and_sdk_records(self):
        sources = SOURCES.read_text(encoding="utf-8")

        self.assertGreaterEqual(
            len(re.findall(r"^### \[S\d{2}\]", sources, re.MULTILINE)),
            20,
        )
        for value in (
            "2026-07-28",
            "mcp==2.1.1",
            "2026-09-01",
            "JSON Schema 2020-12",
            "JSON-RPC 2.0",
        ):
            self.assertIn(value, sources)

    def test_every_source_declares_use_non_claim_and_review_status(self):
        sources = SOURCES.read_text(encoding="utf-8")
        records = re.split(r"(?=^### \[S\d{2}\])", sources, flags=re.MULTILINE)[1:]

        self.assertTrue(records)
        for record in records:
            for field in ("- 类型：", "- 地址：", "- 用于：", "- 不用于证明：", "- 最后核对：", "- 出版前复核："):
                self.assertIn(field, record)
            self.assertIn("2026-09-01", record)
            self.assertIn("出版前复核：是", record)

    def test_chapter_shell_orders_mainline_before_advanced_material(self):
        chapter = CHAPTER.read_text(encoding="utf-8")
        positions = [chapter.index(f"### v{version}：") for version in range(7)]

        self.assertEqual(positions, sorted(positions))
        self.assertLess(chapter.index("### v6："), chapter.index("## 进阶阅读："))
        for link in (
            "../chapter9/README.md",
            "../chapter9/reference-answers.md",
            "../chapter9/reports/tool-mcp-evidence.json",
            "../chapter9/reports/tool-mcp-evidence.md",
            "../chapter9/reports/tool-mcp-trace.jsonl",
        ):
            self.assertIn(link, chapter)

    def test_v0_through_v4_follow_the_same_evidence_rhythm(self):
        chapter = CHAPTER.read_text(encoding="utf-8")
        markers = (
            "**输入：**",
            "**关键代码：**",
            "**运行结果：**",
            "**解决了什么：**",
            "**还没有解决什么：**",
        )
        for version in range(5):
            start = chapter.index(f"### v{version}：")
            end_marker = f"### v{version + 1}：" if version < 4 else "### v5："
            section = chapter[start:chapter.index(end_marker)]
            for marker in markers:
                self.assertIn(marker, section, f"v{version} missing {marker}")

        for distinction in (
            "JSON 语法正确 ≠ Tool Call 合法",
            "Tool Call 是提议",
            "Execution Receipt 来自执行边界",
        ):
            self.assertIn(distinction, chapter)


if __name__ == "__main__":
    unittest.main()
