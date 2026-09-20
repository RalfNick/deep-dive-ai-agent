"""Host-owned completion checks; model prose is never completion evidence."""
from __future__ import annotations

import json
from pathlib import Path
import threading

from . import backends
from .contracts import Record
from .prepare import control_path
from .tools import manifest_hash, workspace_manifest, writable

CASES = Path(__file__).parent / "acceptance" / "cases.json"


def capture_baseline(root: Path) -> Record:
    original = control_path(root) / "baseline.json"
    if original.is_file():
        document = json.loads(original.read_text(encoding="utf-8"))
        files = document["files"]
    else:
        files = workspace_manifest(root)
    protected = {name: value for name, value in files.items() if not writable(name)}
    return {"schema_version": 1, "protected_files": protected,
            "allowed_changes": ["src/linkcheck.py", "tests/test_agent_*.py"],
            "workspace_hash": manifest_hash(files)}


def _protected_changes(files: Record, baseline: Record) -> list[str]:
    protected = baseline["protected_files"]
    changed = {name for name, digest in protected.items() if files.get(name) != digest}
    changed.update(name for name in files if name not in protected and not writable(name))
    return sorted(changed)


def _parse_acceptance(result: Record) -> tuple[Record | None, str | None]:
    if (result.get("returncode") != 0 or result.get("timed_out")
            or result.get("cancelled") or result.get("truncated")):
        return None, "acceptance_execution_failed"
    try:
        payload = json.loads(result["stdout"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None, "acceptance_protocol_invalid"
    if type(payload) is not dict or set(payload) != {"schema_version", "case_ids", "cases"}:
        return None, "acceptance_protocol_invalid"
    if payload["schema_version"] != 1 or type(payload["case_ids"]) is not list or type(payload["cases"]) is not dict:
        return None, "acceptance_protocol_invalid"
    if any(type(item) is not str for item in payload["case_ids"]):
        return None, "acceptance_protocol_invalid"
    for item in payload["cases"].values():
        if type(item) is not dict or set(item) != {"actual", "error"}:
            return None, "acceptance_protocol_invalid"
        if item["error"] is not None and type(item["error"]) is not str:
            return None, "acceptance_protocol_invalid"
        actual = item["actual"]
        if actual is not None and (type(actual) is not list
                                   or any(type(value) is not str for value in actual)):
            return None, "acceptance_protocol_invalid"
    return payload, None


def verify(root: Path, backend: str, baseline: Record,
           cancel: threading.Event) -> Record:
    root = Path(root).absolute()
    if (type(baseline) is not dict or baseline.get("schema_version") != 1
            or type(baseline.get("protected_files")) is not dict):
        raise ValueError("invalid_baseline")
    before = workspace_manifest(root)
    protected_changes = _protected_changes(before, baseline)
    tests = backends.run_preset(root, "candidate_tests", backend, 20, 65536, cancel)
    tests_ok = (tests.get("returncode") == 0 and not tests.get("timed_out")
                and not tests.get("cancelled") and not tests.get("truncated")
                and type(tests.get("discovered")) is int
                and tests["discovered"] > 0 and tests.get("diagnostic") == "passed")
    if not tests_ok:
        after = workspace_manifest(root)
        stable = before == after
        return {"passed": False, "reason": "candidate_tests_failed",
                "failed_cases": [], "candidate_tests": tests,
                "acceptance": {"case_count": 0},
                "protected_ok": not protected_changes,
                "protected_changes": protected_changes, "stable": stable,
                "before_hash": manifest_hash(before), "after_hash": manifest_hash(after)}

    raw_acceptance = backends.run_preset(root, "acceptance", backend, 20, 65536, cancel)
    payload, protocol_error = _parse_acceptance(raw_acceptance)
    expected_doc = json.loads(CASES.read_text(encoding="utf-8"))
    expected = {case["id"]: case["expected"] for case in expected_doc["cases"]}
    failed: list[str] = []
    if payload is None:
        failed = sorted(expected)
    else:
        if payload["case_ids"] != list(expected) or set(payload["cases"]) != set(expected):
            protocol_error = "acceptance_case_set_invalid"
            failed = sorted(expected)
        else:
            for case_id, wanted in expected.items():
                item = payload["cases"][case_id]
                if item["error"] is not None or item["actual"] != wanted:
                    failed.append(case_id)

    after = workspace_manifest(root)
    stable = before == after
    final_protected_changes = sorted(set(protected_changes)
                                     | set(_protected_changes(after, baseline)))
    if not stable:
        reason = "workspace_changed_during_verification"
    elif final_protected_changes:
        reason = "protected_files_changed"
    elif protocol_error:
        reason = protocol_error
    elif failed:
        reason = "acceptance_failed"
    else:
        reason = None
    passed = reason is None
    return {"passed": passed, "reason": reason, "failed_cases": failed,
            "candidate_tests": tests,
            "acceptance": {"case_count": len(expected), "raw": raw_acceptance},
            "protected_ok": not final_protected_changes,
            "protected_changes": final_protected_changes, "stable": stable,
            "before_hash": manifest_hash(before), "after_hash": manifest_hash(after)}
