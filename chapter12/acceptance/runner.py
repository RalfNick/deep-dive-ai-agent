"""Execute host-owned acceptance inputs and emit raw candidate observations."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile

CASES = Path(__file__).with_name("cases.json")


def _load_candidate(workspace: Path):
    candidate = workspace / "src" / "linkcheck.py"
    spec = importlib.util.spec_from_file_location("chapter12_candidate_linkcheck", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError("candidate_import_failed")
    module = importlib.util.module_from_spec(spec)
    # Candidate print output is never allowed to become the result protocol.
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        spec.loader.exec_module(module)
    return module


def run(workspace: Path) -> dict[str, object]:
    document = json.loads(CASES.read_text(encoding="utf-8"))
    module = _load_candidate(workspace)
    observations: dict[str, object] = {}
    control = workspace.parent / f".{workspace.name}.agent"
    scratch = control / "acceptance-runs"
    scratch.mkdir(parents=True, exist_ok=True)
    for case in document["cases"]:
        with tempfile.TemporaryDirectory(prefix="case-", dir=scratch) as name:
            root = Path(name)
            for relative, text in case["files"].items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8", newline="\n")
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    actual = module.broken_links(root / case["document"], root)
                json.dumps(actual, ensure_ascii=False)
                observations[case["id"]] = {"actual": actual, "error": None}
            except Exception as error:  # raw exception class, not a claimed match
                observations[case["id"]] = {
                    "actual": None, "error": type(error).__name__}
    return {"schema_version": 1,
            "case_ids": [case["id"] for case in document["cases"]],
            "cases": observations}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().workspace.absolute()),
                     ensure_ascii=False, sort_keys=True, separators=(",", ":")))
