"""CI must run the real SFT experiment without rewriting frozen evidence."""
import hashlib
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CIExperimentIsolationTests(unittest.TestCase):
    def test_real_sft_ci_command_trains_without_overwriting_historical_artifacts(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
        commands = [shlex.split(line) for job in workflow["jobs"].values()
                    for step in job["steps"] for line in step.get("run", "").splitlines()
                    if "chapter2/real_sft_evidence.py" in line]
        self.assertEqual(1, len(commands), "CI must still run the real SFT experiment")
        self.assertEqual(["python", "chapter2/real_sft_evidence.py"], commands[0][:2])
        protected = (
            "chapter2/results/real_sft_summary.json",
            "chapter2/results/real_sft_curves.csv",
            "book/images/fig2-7-real-sft-curves.svg",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "chapter2/real_sft_evidence.py"
            script.parent.mkdir(parents=True)
            script.write_bytes((ROOT / "chapter2/real_sft_evidence.py").read_bytes())
            frozen = {}
            for relative in protected:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                # Distinct valid formatting detects a rewrite even when local floating-point values match.
                path.write_bytes((ROOT / relative).read_bytes() + b"\n")
                frozen[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            result = subprocess.run([sys.executable, "-X", "utf8", "-B", *commands[0][1:]],
                                    cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=120)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            for expected in ("micro-11k", "micro-40k", "SFT 后验证提示的贪心输出", "expected=测试"):
                self.assertIn(expected, result.stdout)
            for relative, digest in frozen.items():
                with self.subTest(artifact=relative):
                    self.assertEqual(digest, hashlib.sha256((root / relative).read_bytes()).hexdigest(),
                                     "CI must preserve historical artifact bytes")


if __name__ == "__main__":
    unittest.main()
