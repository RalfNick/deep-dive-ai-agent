from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

from chapter1.attention_demo import causal_attention
from chapter1.token_demo import inspect_text


class TokenRepresentationTest(unittest.TestCase):
    def test_token_bytes_reconstruct_the_original_utf8_bytes(self) -> None:
        result = inspect_text("深入浅出 AI Agent")

        self.assertEqual(b"".join(result["token_bytes"]), result["utf8_bytes"])
        self.assertEqual(result["utf8_bytes"].decode("utf-8"), result["text"])

    def test_cli_survives_a_non_utf8_windows_console(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "gbk"

        result = subprocess.run(
            [sys.executable, "chapter1/token_demo.py"],
            cwd=repo_root,
            env=environment,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode("gbk"))


class CausalAttentionTest(unittest.TestCase):
    def test_weights_are_normalized_and_future_positions_are_hidden(self) -> None:
        tokens = np.array([[1.0, 0.0], [0.8, 0.2], [0.0, 1.0]])

        _, _, _, weights, _ = causal_attention(tokens, tokens, tokens)

        self.assertTrue(np.allclose(weights.sum(axis=1), 1.0))
        self.assertTrue(np.allclose(np.triu(weights, k=1), 0.0))


if __name__ == "__main__":
    unittest.main()
