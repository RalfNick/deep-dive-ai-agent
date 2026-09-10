"""Deterministic real filesystem, subprocess, and Git experiments."""
import argparse
import json
from pathlib import Path
import tempfile

from .workbench import (BUG_LINE, FIX_LINE, GUIDANCE, REGRESSION, create_workspace,
                        evidence_is_current, fingerprint, git, instruction_inventory,
                        patch_file, run_tests, verify)


def repair(root: Path) -> dict:
    create_workspace(root)
    initial_tests = run_tests(root)
    missing = verify(root, fingerprint(root / "tests"))
    test = root / "tests/test_links.py"
    test.write_text(test.read_text(encoding="utf-8") + REGRESSION, encoding="utf-8", newline="\n")
    # Freeze the intentionally extended suite before code editing, not before
    # a reviewer-approved regression has been added.
    expected = fingerprint(root / "tests")
    red = run_tests(root)
    source = root / "linkcheck.py"
    patch_file(root, "linkcheck.py", fingerprint(source), BUG_LINE, FIX_LINE)
    final = verify(root, expected)
    return {"initial_tests": initial_tests, "initial_acceptance": missing["acceptance"],
            "red": red, "final": final,
            "diff": git(root, "diff", "--", "linkcheck.py", "tests/test_links.py")}


def instructions(root: Path) -> dict:
    create_workspace(root)
    before = instruction_inventory(root)
    (root / "AGENTS.md").write_text(GUIDANCE, encoding="utf-8", newline="\n")
    (root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8", newline="\n")
    return {"before": before, "after": instruction_inventory(root),
            "command_observation": run_tests(root),
            "interpretation": "file inventory and real command execution; not product instruction adherence"}


def conflict(root: Path) -> dict:
    create_workspace(root)
    source = root / "linkcheck.py"
    expected = fingerprint(source)
    source.write_text(source.read_text(encoding="utf-8") + "\n# collaborator edit\n", encoding="utf-8", newline="\n")
    note = root / "notes.txt"
    note.write_text("Unfinished user note.\n", encoding="utf-8", newline="\n")
    before = fingerprint(root)
    error = None
    try:
        patch_file(root, "linkcheck.py", expected, BUG_LINE, FIX_LINE)
    except ValueError as failure:
        error = str(failure)
    return {"error": error, "workspace_preserved": before == fingerprint(root),
            "dirty_files": git(root, "diff", "--name-only").splitlines()}


def verification(root: Path) -> dict:
    create_workspace(root)
    expected = fingerprint(root / "tests")
    false_green = verify(root, expected)
    zero = verify(root, expected, "empty_tests")
    (root / "tests/test_links.py").write_text("# assertions removed\n", encoding="utf-8", newline="\n")
    tampered = verify(root, expected)
    return {"insufficient_coverage": false_green, "zero_tests": zero, "tampered_tests": tampered}


def resume(root: Path) -> dict:
    create_workspace(root)
    expected = fingerprint(root / "tests")
    source = root / "linkcheck.py"
    patch_file(root, "linkcheck.py", fingerprint(source), BUG_LINE, FIX_LINE)
    receipt = verify(root, expected)
    unchanged = evidence_is_current(root, receipt)
    # Serialize the handoff outside the observed repository, as a new session
    # would, so the handoff itself does not mutate the measured snapshot.
    handoff = root.parent / "handoff.json"
    handoff.write_text(json.dumps(receipt), encoding="utf-8", newline="\n")
    patch_file(root, "linkcheck.py", fingerprint(source), FIX_LINE, BUG_LINE)
    reloaded = json.loads(handoff.read_text(encoding="utf-8"))
    return {"before_change_current": unchanged,
            "old_evidence_current": evidence_is_current(root, reloaded),
            "revalidation": verify(root, expected)}


GROUPS = {"repair": repair, "instructions": instructions, "conflict": conflict,
          "verification": verification, "resume": resume}


def run_all(group: str | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="book-ch11-") as folder:
        selected = {group: GROUPS[group]} if group else GROUPS
        results = {name: function(Path(folder) / name) for name, function in selected.items()}
    return {"contract": "trusted fixture repository workflow observations",
            "decision_source": "fixed teaching sequence; no model calls",
            "model_quality": None, "product_adherence": None,
            "sandbox_security": None, "sample_count_per_scenario": 1, "groups": results}


def write_reports(output: Path) -> None:
    report = run_all()
    output.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (output / "repository-work.json").write_text(payload, encoding="utf-8", newline="\n")
    text = "# 第 11 章实验记录\n\n实际执行文件修改、Git 和测试子进程；决策序列固定，未调用模型。\n\n"
    for group, data in report["groups"].items():
        text += "## " + group + "\n\n```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```\n\n"
    (output / "repository-work.md").write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=tuple(GROUPS))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        if args.group:
            parser.error("--output writes all groups; do not combine with --group")
        write_reports(args.output)
    else:
        print(json.dumps(run_all(args.group), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
