from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tool_error_demo import PaymentTool, call_with_retry  # noqa: E402


class ToolErrorTest(unittest.TestCase):
    def test_retry_after_commit_timeout_has_one_side_effect(self) -> None:
        tool = PaymentTool()

        result = call_with_retry(tool, cents=1990)

        self.assertTrue(result.ok)
        self.assertEqual(tool.attempts, 2)
        self.assertEqual(tool.side_effects, 1)
        self.assertEqual(len(tool.ledger), 1)
        self.assertEqual(result.value, "receipt:order-42:1990")


if __name__ == "__main__":
    unittest.main()
