"""A deterministic, local simulation of a Coding Agent verification loop.

This demo does not call an LLM. It makes the model/runtime boundary observable:
a proposed patch is only a string until the harness writes it, runs the tests,
and checks the process exit code.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


BROKEN_SOURCE = '''def parse_price(value: str) -> float:
    """Parse a decimal price."""
    return float(value)
'''

FIXED_SOURCE = '''def parse_price(value: str) -> float:
    """Parse a decimal price with one optional leading yuan symbol."""
    normalized = value.strip()
    if normalized.startswith(("\\uffe5", "\\u00a5")):
        normalized = normalized[1:]
    return float(normalized)
'''

TEST_SOURCE = '''import unittest

from pricing import parse_price


class ParsePriceTest(unittest.TestCase):
    def test_plain_decimal(self) -> None:
        self.assertEqual(parse_price("12.50"), 12.5)

    def test_full_width_yuan_symbol(self) -> None:
        try:
            result = parse_price("\\uffe519.90")
        except ValueError:
            self.fail("parse_price cannot handle the U+FFE5 prefix")
        self.assertEqual(result, 19.9)

    def test_internal_yuan_symbol_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_price("1\\u00a52")


if __name__ == "__main__":
    unittest.main()
'''


def run_tests(workspace: Path) -> subprocess.CompletedProcess[str]:
    """Run the isolated fixture and return observable process evidence."""
    return subprocess.run(
        [sys.executable, "-m", "unittest", "-v"],
        cwd=workspace,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )


def evaluate_source(source: str) -> subprocess.CompletedProcess[str]:
    """Verify one candidate implementation in a disposable workspace."""
    with tempfile.TemporaryDirectory(prefix="chapter1-contract-") as temp_dir:
        workspace = Path(temp_dir)
        (workspace / "pricing.py").write_text(source, encoding="utf-8")
        (workspace / "test_pricing.py").write_text(TEST_SOURCE, encoding="utf-8")
        return run_tests(workspace)


def print_result(label: str, result: subprocess.CompletedProcess[str]) -> None:
    """Print a compact test trace with the exit code."""
    output = (result.stdout + result.stderr).strip()
    print(f"\n{label}: exit_code={result.returncode}")
    print(output)


def main() -> None:
    print('[goal] make parse_price("U+FFE5 19.90") return 19.9')
    print("[boundary] the proposed patch does not change files by itself")

    with tempfile.TemporaryDirectory(prefix="chapter1-agent-") as temp_dir:
        workspace = Path(temp_dir)
        source_path = workspace / "pricing.py"
        test_path = workspace / "test_pricing.py"

        source_path.write_text(BROKEN_SOURCE, encoding="utf-8")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        print(f"[observe] isolated workspace: {workspace}")
        print("[observe] pricing.py before patch:\n" + BROKEN_SOURCE.rstrip())

        before = run_tests(workspace)
        print_result("[verify before patch]", before)
        assert before.returncode != 0, "the fixture must fail before the patch"

        print("\n[model proposal] replace the implementation with:\n" + FIXED_SOURCE.rstrip())
        source_path.write_text(FIXED_SOURCE, encoding="utf-8")
        print("[harness action] patch written inside the isolated workspace")

        after = run_tests(workspace)
        print_result("[verify after patch]", after)
        assert after.returncode == 0, "the fixture must pass after the patch"

        print("\n[accept] file changed, required test ran, exit code is 0")


if __name__ == "__main__":
    main()
