"""Trusted local teaching workbench. Requires Python 3.11+ and Git.

This is not a sandbox for untrusted repositories. Commands execute trusted
fixture code in temporary repositories; the single-writer patch check does
not provide a cross-process compare-and-swap guarantee.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


BUG_LINE = "    base = root\n"
FIX_LINE = "    base = document.parent\n"
SOURCE = '''from pathlib import Path
import re

LINK = re.compile(r"(?<!!)\\[[^\\]\\n]+\\]\\(([^()\\s]+)\\)")


def resolve_link(root: Path, document: Path, target: str) -> Path:
    base = root
    return (base / target).resolve()


def broken_links(root: Path, document: Path) -> list[str]:
    # Teaching subset: inline relative file links, no titles or nested syntax.
    missing = []
    for target in LINK.findall(document.read_text(encoding="utf-8")):
        if target.startswith(("#", "/")) or ":" in target:
            continue
        path = target.split("#", 1)[0]
        if path and not resolve_link(root, document, path).is_file():
            missing.append(target)
    return missing
'''
BASE_TESTS = '''from pathlib import Path
import unittest
from linkcheck import broken_links

ROOT = Path(__file__).resolve().parents[1]


class LinkTests(unittest.TestCase):
    def test_root_document(self):
        self.assertEqual([], broken_links(ROOT, ROOT / "README.md"))

    def test_missing_file(self):
        self.assertEqual(["missing.md"], broken_links(ROOT, ROOT / "missing-example.md"))

    def test_external_link_is_skipped(self):
        self.assertEqual([], broken_links(ROOT, ROOT / "external-example.md"))
'''
REGRESSION = '''
    def test_nested_document(self):
        self.assertEqual([], broken_links(ROOT, ROOT / "docs/guide/start.md"))
'''
GUIDANCE = '''# Repository working agreement

The active implementation is linkcheck.py; legacy/ is an archived example.
Run from the repository root: python -m unittest discover -s tests -v.
Relative links are resolved from the document's containing directory.
Preserve notes.txt and unrelated user edits. Add a regression for the bug.
Report the tested revision, commands, test count, and the final diff.
This fixture supports only simple inline relative file links.
'''


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "core.hooksPath=/dev/null",
         "-c", "commit.gpgsign=false", "-c", "user.name=Book Fixture",
         "-c", "user.email=fixture@example.invalid", *args],
        cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    if result.returncode:
        raise RuntimeError("fixture_git_failed: " + result.stderr.strip())
    return result.stdout


def create_workspace(root: Path) -> None:
    if root.exists() and any(root.iterdir()):
        raise ValueError("not_empty")
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "linkcheck.py": SOURCE,
        "legacy/linkcheck_old.py": SOURCE,
        "tests/test_links.py": BASE_TESTS,
        "tests/__init__.py": "",
        "empty_tests/__init__.py": "",
        "README.md": "# Link checker\n[FAQ](docs/faq.md)\n",
        "docs/faq.md": "# FAQ\nPaths are relative to each document.\n",
        "docs/guide/start.md": "# Start\n[FAQ](../faq.md)\n",
        "missing-example.md": "[Missing](missing.md)\n",
        "external-example.md": "[External](https://example.invalid)\n",
        "notes.txt": "User draft; preserve this file.\n",
        ".gitignore": "__pycache__/\n*.pyc\n",
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    git(root, "init", "-q")
    git(root, "add", "--", *files)
    git(root, "commit", "-qm", "trusted teaching baseline")


def fingerprint(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    rows = []
    for item in sorted(path.rglob("*")):
        relative = item.relative_to(path)
        if {".git", "__pycache__"}.intersection(relative.parts):
            continue
        if item.is_file():
            rows.append([relative.as_posix(), fingerprint(item)])
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def patch_file(root: Path, relative: str, expected: str, old: str, new: str) -> None:
    if relative != "linkcheck.py":
        raise ValueError("outside_patch_scope")
    source = root / relative
    if source.is_symlink() or source.resolve().parent != root.resolve():
        raise ValueError("outside_patch_scope")
    if fingerprint(source) != expected:
        raise ValueError("stale_source")
    text = source.read_text(encoding="utf-8")
    if not old or text.count(old) != 1:
        raise ValueError("hunk_mismatch")
    # Same-directory replacement avoids a partially written file, but does not
    # lock out another process between the preceding check and os.replace.
    descriptor, temporary = tempfile.mkstemp(dir=root, prefix=".patch-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text.replace(old, new, 1))
        os.replace(temporary, source)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


RUNNER = '''import json, pathlib, sys, unittest
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
suite = unittest.TestLoader().discover(str(root / sys.argv[2]))
result = unittest.TextTestRunner(verbosity=0).run(suite)
print(json.dumps({"count": result.testsRun, "failures": len(result.failures),
                  "errors": len(result.errors), "ok": result.wasSuccessful()}))
sys.exit(0 if result.wasSuccessful() else 1)
'''


def run_tests(root: Path, scope: str = "tests") -> dict:
    if scope not in {"tests", "empty_tests"}:
        raise ValueError("unknown_test_scope")
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", RUNNER, str(root), scope],
        cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    try:
        evidence = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"count": 0, "ok": False, "exit_code": result.returncode,
                "scope": scope, "error": "invalid_test_report"}
    return {**evidence, "exit_code": result.returncode, "scope": scope}


ACCEPTANCE = '''import json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from linkcheck import broken_links, resolve_link
checks = {
 "nested_path": resolve_link(root, root / "docs/guide/start.md", "../faq.md") == (root / "docs/faq.md").resolve(),
 "nested_valid": broken_links(root, root / "docs/guide/start.md") == [],
 "root_valid": broken_links(root, root / "README.md") == [],
 "missing_still_fails": broken_links(root, root / "missing-example.md") == ["missing.md"],
}
print(json.dumps({"checks": checks, "ok": all(checks.values())}))
'''


def verify(root: Path, expected_tests: str, scope: str = "tests") -> dict:
    before = fingerprint(root)
    tests = run_tests(root, scope)
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", ACCEPTANCE, str(root)],
        cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    acceptance = {"ok": False, "checks": {}}
    if result.returncode == 0:
        try:
            acceptance = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            pass
    tests_unchanged = fingerprint(root / "tests") == expected_tests
    stable = before == fingerprint(root)
    return {
        "tests": tests, "acceptance": acceptance,
        "tests_unchanged": tests_unchanged, "snapshot_stable": stable,
        "snapshot": before,
        "accepted": bool(tests["ok"] and tests["count"] >= 3 and scope == "tests"
                         and acceptance["ok"] and tests_unchanged and stable),
    }


def evidence_is_current(root: Path, evidence: dict) -> bool:
    return bool(evidence.get("accepted") and fingerprint(root) == evidence.get("snapshot"))


def instruction_inventory(root: Path) -> dict:
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    return {"agents_exists": agents.is_file(), "claude_exists": claude.is_file(),
            "agents_bytes": agents.stat().st_size if agents.is_file() else 0,
            "product_adherence": "not_measured"}
