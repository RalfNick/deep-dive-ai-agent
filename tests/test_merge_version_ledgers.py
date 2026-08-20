import unittest


from scripts.merge_version_ledgers import merge_ledgers


class MergeVersionLedgersTests(unittest.TestCase):
    def test_merges_unique_chapter_sections_in_numeric_order(self) -> None:
        current = """# 版本记录

说明。

## 第 1 章：基础

| v1.0 | current |

## 第 3 章：Loop

| v1.0 | current |

## 后续章节发布规则

规则。
"""
        later = """# 版本记录

说明。

## 第 1 章：基础

| v1.0 | current |

## 第 5 章：上下文

| v1.0 | later |

## 第 6 章：连续性

| v1.0 | later |

## 后续章节发布规则

规则。
"""

        merged = merge_ledgers(current, later)

        self.assertEqual(1, merged.count("## 第 1 章：基础"))
        self.assertIn("## 第 3 章", merged)
        self.assertIn("## 第 5 章", merged)
        self.assertIn("## 第 6 章", merged)
        self.assertLess(merged.index("## 第 3 章"), merged.index("## 第 5 章"))
        self.assertLess(merged.index("## 第 5 章"), merged.index("## 第 6 章"))
        self.assertEqual(1, merged.count("## 后续章节发布规则"))

    def test_rejects_conflicting_duplicate_chapter_section(self) -> None:
        current = "# 版本记录\n\n## 第 1 章：基础\n\n| v1.0 | current |\n"
        later = "# 版本记录\n\n## 第 1 章：基础\n\n| v1.0 | changed |\n"

        with self.assertRaisesRegex(ValueError, "conflicting chapter section: 1"):
            merge_ledgers(current, later)


if __name__ == "__main__":
    unittest.main()
