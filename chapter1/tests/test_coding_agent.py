from __future__ import annotations

import unittest

from chapter1.coding_agent_demo import (
    BROKEN_SOURCE,
    FIXED_SOURCE,
    evaluate_source,
)


class CodingAgentContractTest(unittest.TestCase):
    def test_broken_source_fails_the_verifier(self) -> None:
        result = evaluate_source(BROKEN_SOURCE)

        self.assertNotEqual(result.returncode, 0)

    def test_candidate_source_passes_prefix_and_internal_symbol_cases(self) -> None:
        result = evaluate_source(FIXED_SOURCE)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
