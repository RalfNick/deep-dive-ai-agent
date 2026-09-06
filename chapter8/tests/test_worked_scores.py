"""The worked answer must execute the real rankers and expose checkable scores."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


class WorkedScoresTests(unittest.TestCase):
    def test_cli_matches_hand_calculated_bm25_and_rrf(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-B", "-m", "chapter8.experiments.worked_scores"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual([row["id"] for row in data["bm25"]], ["D1", "D2", "D3"])
        for row, expected in zip(data["bm25"], [1.9208365115, 0.4700036292, 0.4700036292]):
            self.assertAlmostEqual(row["score"], expected, places=8)
        self.assertEqual([row["id"] for row in data["bm25_without_team"]], ["D1", "D2", "D3"])
        for row, expected in zip(data["bm25_without_team"], [0.9400072585, 0.4700036292, 0.4700036292]):
            self.assertAlmostEqual(row["score"], expected, places=8)
        self.assertEqual([row["id"] for row in data["rrf"]], ["A", "C", "B", "D"])
        for row, expected in zip(data["rrf"], [0.0322664585, 0.0322664585, 0.0322580645, 0.03125]):
            self.assertAlmostEqual(row["score"], expected, places=9)
        self.assertEqual(data["rrf"], data["rrf_reordered_channels"])
        self.assertEqual([row["id"] for row in data["rrf_one_channel"]], ["A", "B", "C", "D"])
        for rank, row in enumerate(data["rrf_one_channel"], 1):
            self.assertAlmostEqual(row["score"], 1 / (60 + rank), places=12)


if __name__ == "__main__":
    unittest.main()
