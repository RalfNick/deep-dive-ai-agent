from pathlib import Path
import json
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "chapter8" / "live" / "live_probe.py"


class LiveProbeTests(unittest.TestCase):
    def test_documented_direct_dry_run_succeeds_without_api_key(self) -> None:
        with TemporaryDirectory() as raw:
            output = Path(raw) / "probe.json"
            environment = dict(os.environ)
            environment.pop("DEEPSEEK_API_KEY", None)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--provider",
                    "deepseek",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual("dry_run", payload["status"])
        self.assertFalse(payload["credential_present"])
        self.assertIsNone(payload["usage"])
        self.assertNotIn("DEEPSEEK_API_KEY=", completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
