"""Runnable solutions 6-10. Creates only disposable trusted fixture repositories."""
import argparse
import json
from pathlib import Path
import tempfile

from .experiments import repair
from .workbench import (BUG_LINE, FIX_LINE, REGRESSION, create_workspace,
                        evidence_is_current, fingerprint, patch_file, run_tests, verify)


def fix(root: Path) -> None:
    patch_file(root, "linkcheck.py", fingerprint(root / "linkcheck.py"), BUG_LINE, FIX_LINE)


def exercise7(root: Path) -> dict:
    create_workspace(root)
    note = root / "notes.txt"
    note.write_text("My unfinished note.\n", encoding="utf-8", newline="\n")
    before = note.read_bytes()
    fix(root)
    preserved = before == note.read_bytes()
    source = root / "linkcheck.py"
    expected = fingerprint(source)
    source.write_text(source.read_text(encoding="utf-8") + "\n# Collaborator note\n",
                      encoding="utf-8", newline="\n")
    collaborator = source.read_bytes()
    error = None
    try:
        patch_file(root, "linkcheck.py", expected, FIX_LINE, BUG_LINE)
    except ValueError as failure:
        error = str(failure)
    return {"notes_preserved": preserved, "conflict_error": error,
            "collaborator_preserved": collaborator == source.read_bytes()}


def exercise8(root: Path) -> dict:
    create_workspace(root)
    return verify(root, fingerprint(root / "tests"), "empty_tests")


def exercise9(root: Path) -> dict:
    # Declare the changed contract before constructing tests or editing source.
    expected_nested = ("../absent.md",)
    create_workspace(root)
    document = root / "docs/guide/start.md"
    document.write_text(document.read_text(encoding="utf-8") + "[Missing](../absent.md)\n",
                        encoding="utf-8", newline="\n")
    regression = REGRESSION.replace("self.assertEqual([],", "self.assertEqual(['../absent.md'],")
    test = root / "tests/test_links.py"
    test.write_text(test.read_text(encoding="utf-8") + regression, encoding="utf-8", newline="\n")
    red = run_tests(root)
    if not (red["count"] == 4 and red["failures"] == 1 and red["errors"] == 0
            and red["exit_code"] == 1 and len(red["details"]) == 1
            and red["details"][0]["test"].endswith(".test_nested_document")
            and "['../absent.md'] != ['../faq.md', '../absent.md']" in red["details"][0]["message"]):
        raise ValueError("unexpected_red: nested missing-link exercise")
    expected_tests = fingerprint(root / "tests")
    fix(root)
    final = verify(root, expected_tests, nested_missing=expected_nested)
    # A deliberately wrong candidate: treating every link as valid.
    source = root / "linkcheck.py"
    source.write_text(source.read_text(encoding="utf-8") +
                      "\ndef broken_links(root, document):\n    return []\n",
                      encoding="utf-8", newline="\n")
    always_empty = verify(root, expected_tests, nested_missing=expected_nested)
    return {"expected_nested_missing": list(expected_nested), "red": red,
            "final": final, "always_empty": always_empty}


def exercise10(root: Path) -> dict:
    create_workspace(root)
    fix(root)
    expected_tests = fingerprint(root / "tests")
    receipt = verify(root, expected_tests)
    document = root / "docs/faq.md"
    document.write_text(document.read_text(encoding="utf-8") + "\nExtra explanation.\n",
                        encoding="utf-8", newline="\n")
    return {"historical_accepted": receipt["accepted"],
            "current_after_document_edit": evidence_is_current(root, receipt),
            "revalidation": verify(root, expected_tests)}


EXERCISES = {6: repair, 7: exercise7, 8: exercise8, 9: exercise9, 10: exercise10}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("number", type=int, choices=tuple(EXERCISES))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="book-ch11-exercise-") as folder:
        result = EXERCISES[args.number](Path(folder) / "repo")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
