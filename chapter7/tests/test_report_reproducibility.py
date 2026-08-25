from pathlib import Path
import tempfile
import unittest

from chapter7.experiments.run_all import write_reports


class ReportReproducibilityTest(unittest.TestCase):
    def test_three_report_formats_are_reproducible_and_trace_is_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as left_dir, tempfile.TemporaryDirectory() as right_dir:
            left = write_reports(Path(left_dir))
            right = write_reports(Path(right_dir))
            self.assertEqual(set(left), {"json", "markdown", "trace"})
            for key in left:
                self.assertEqual(left[key].read_bytes(), right[key].read_bytes(), key)
            trace = left["trace"].read_text(encoding="utf-8")
            self.assertNotIn("sk-", trace)
            self.assertNotIn("password=", trace.lower())
            self.assertNotIn("代码示例优先使用 Python", trace)


if __name__ == "__main__":
    unittest.main()
