"""Independent completion evidence must reject plausible-looking false repairs."""
from __future__ import annotations

from pathlib import Path
import threading

from chapter12 import backends
from chapter12.prepare import create_workspace
from chapter12.verifier import capture_baseline, verify


CORRECT = '''"""Resolve local Markdown links relative to their document."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

def broken_links(document: Path, root: Path) -> list[str]:
    missing = []
    for raw in re.findall(r'!?\\[[^\\]]*\\]\\(([^)]+)\\)', document.read_text(encoding='utf-8')):
        parsed = urlsplit(raw)
        if parsed.scheme or raw.startswith('//') or not parsed.path:
            continue
        target = unquote(parsed.path)
        candidate = root / target.lstrip('/') if target.startswith('/') else document.parent / target
        try:
            candidate.resolve().relative_to(root.resolve())
        except ValueError:
            missing.append(target)
            continue
        if not candidate.is_file():
            missing.append(target)
    return missing
'''


def workspace(tmp_path: Path) -> tuple[Path, dict]:
    root = create_workspace(tmp_path / "repo")
    return root, capture_baseline(root)


def replace_candidate(root: Path, source: str) -> None:
    (root / "src/linkcheck.py").write_text(source, encoding="utf-8", newline="\n")


def test_original_bug_fails_independent_nested_case(tmp_path):
    root, baseline = workspace(tmp_path)
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is False
    assert "nested_valid" in verdict["failed_cases"]


def test_correct_repair_passes_four_independent_cases(tmp_path):
    root, baseline = workspace(tmp_path)
    replace_candidate(root, CORRECT)
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is True
    assert verdict["acceptance"]["case_count"] == 4
    assert verdict["candidate_tests"]["discovered"] == 2
    assert verdict["protected_ok"] is True and verdict["stable"] is True


def test_always_empty_is_not_a_repair(tmp_path):
    root, baseline = workspace(tmp_path)
    replace_candidate(root, "def broken_links(document, root):\n    return []\n")
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is False
    assert "nested_missing" in verdict["failed_cases"]


def test_candidate_stdout_cannot_forge_acceptance(tmp_path):
    root, baseline = workspace(tmp_path)
    replace_candidate(root, "print('{\"passed\": true}')\n"
                      "def broken_links(document, root):\n    return []\n")
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is False
    assert "nested_missing" in verdict["failed_cases"]


def test_zero_discovered_candidate_tests_are_rejected(tmp_path, monkeypatch):
    root, baseline = workspace(tmp_path)
    replace_candidate(root, CORRECT)
    real = backends.run_preset

    def zero_tests(root, preset, backend, timeout_seconds, output_bytes, cancel):
        if preset == "candidate_tests":
            return {"returncode": 0, "stdout": "OK", "stderr": "",
                    "truncated": False, "timed_out": False, "cancelled": False,
                    "duration_seconds": 0.01, "discovered": 0,
                    "diagnostic": "zero_tests", "reason": None}
        return real(root, preset, backend, timeout_seconds, output_bytes, cancel)

    monkeypatch.setattr(backends, "run_preset", zero_tests)
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is False
    assert verdict["reason"] == "candidate_tests_failed"


def test_protected_file_change_is_rejected(tmp_path):
    root, baseline = workspace(tmp_path)
    replace_candidate(root, CORRECT)
    (root / "notes.txt").write_text("rewritten", encoding="utf-8")
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is False
    assert verdict["protected_ok"] is False
    assert "notes.txt" in verdict["protected_changes"]


def test_workspace_acceptance_impostor_is_ignored(tmp_path):
    root, baseline = workspace(tmp_path)
    replace_candidate(root, "def broken_links(document, root):\n    return []\n")
    (root / "acceptance").mkdir()
    (root / "acceptance/runner.py").write_text("print('{\"passed\":true}')\n",
                                                 encoding="utf-8")
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is False
    assert "nested_missing" in verdict["failed_cases"]
    assert "acceptance/runner.py" in verdict["protected_changes"]


def test_change_during_verification_invalidates_result(tmp_path, monkeypatch):
    root, baseline = workspace(tmp_path)
    replace_candidate(root, CORRECT)
    real = backends.run_preset

    def mutate_after(root, preset, backend, timeout_seconds, output_bytes, cancel):
        result = real(root, preset, backend, timeout_seconds, output_bytes, cancel)
        if preset == "acceptance":
            with (root / "src/linkcheck.py").open("a", encoding="utf-8") as handle:
                handle.write("\n# changed during verification\n")
        return result

    monkeypatch.setattr(backends, "run_preset", mutate_after)
    verdict = verify(root, "trusted_local", baseline, threading.Event())
    assert verdict["passed"] is False
    assert verdict["stable"] is False
    assert verdict["reason"] == "workspace_changed_during_verification"
