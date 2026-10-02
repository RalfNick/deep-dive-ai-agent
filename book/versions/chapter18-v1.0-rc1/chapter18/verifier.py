"""Runs only this book's trusted fixture; it is not an untrusted-code sandbox."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

from .budget import BudgetLedger
from .contracts import Verification
from .fixtures import checked_path


def verify_workspace(workspace: Path, *, fixture_root: Path, ledger: BudgetLedger | None = None) -> Verification:
    root = fixture_root.parents[2]
    checked_path(root, workspace, prefixes=("chapter18/.runs",))
    frozen = fixture_root / "tests/test_existing.py"
    copy = workspace / "tests/test_existing.py"
    checked_path(workspace, copy, prefixes=("tests",))
    if not copy.is_file() or copy.read_bytes() != frozen.read_bytes():
        return Verification(False, 0, 4, False, (), "protected_tests_changed")
    if {p.relative_to(workspace / "tests").as_posix() for p in (workspace / "tests").rglob("*.py")} != {"test_existing.py"}:
        return Verification(False, 0, 4, False, (), "protected_tests_changed")
    for path in (workspace / "src").rglob("*"):
        checked_path(workspace, path, prefixes=("src",))
    if ledger and not ledger.charge(purpose="verifier"):
        return Verification(False, 0, 4, False, (), "verification_budget_exhausted")
    try:
        run = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(fixture_root / "tests"), "-p", "test_existing.py"],
                             cwd=workspace, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return Verification(False, 0, 4, False, (), "test_environment_error")
    output = run.stdout + run.stderr
    total_match = re.search(r"Ran (\d+) tests?", output)
    total = int(total_match.group(1)) if total_match else 0
    failures = sum(int(m) for m in re.findall(r"(?:failures|errors)=(\d+)", output))
    passed = max(0, total - failures) if total and run.returncode in {0, 1} else 0
    if ledger and not ledger.charge(purpose="verifier"):
        return Verification(False, passed, total, False, (), "verification_budget_exhausted")
    probe = "import sys,json;sys.path.insert(0,'src');from linkcheck import resolve_link;print(json.dumps([resolve_link('docs/nested/a.md','../guide.md'),resolve_link('docs/a.md','https://example.invalid')]))"
    try:
        behavior = subprocess.run([sys.executable, "-B", "-c", probe], cwd=workspace,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        behavior_ok = behavior.returncode == 0 and json.loads(behavior.stdout) == ["docs/guide.md", None]
    except (OSError, subprocess.TimeoutExpired, ValueError):
        behavior_ok = False
    evidence = ("frozen-tests:" + sha256(frozen.read_bytes()).hexdigest(),
                f"tests:{passed}/{total}", "behavior:nested-relative-and-external=" + str(behavior_ok).lower())
    okay = run.returncode == 0 and total == 4 and passed == 4 and behavior_ok
    return Verification(okay, passed, total, behavior_ok, evidence,
                        "integrated_checks_passed" if okay else "acceptance_failed")
