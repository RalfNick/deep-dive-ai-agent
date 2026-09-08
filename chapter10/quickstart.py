"""One complete local report flow: python -m chapter10.quickstart."""
import json
from pathlib import Path
import tempfile

from .experiments import SALES
from .jobs import JobStore


def run_demo(directory: Path) -> dict:
    # A dedicated database in the caller's temporary directory.
    store = JobStore(directory / "quickstart.sqlite")
    try:
        month = "2026-08"
        job = store.submit("alice", "august-report", {"month": month}, now=0)
        states = [store.get("alice", job)["state"]]
        attempt = store.claim(job, now=1)
        if attempt is None:
            raise RuntimeError("No execution lease acquired")
        states.append(store.get("alice", job)["state"])
        rows = [row for row in SALES if row["month"] == month]
        total = 0
        for index, row in enumerate(rows, 1):
            total += row["amount_cents"]
            store.progress(job, attempt, index, len(rows), now=index + 1)
        report = {"month": month, "row_count": len(rows), "total_cents": total}
        if not store.finish(job, attempt, report, now=5):
            raise RuntimeError("Result was not committed")
        states.append(store.get("alice", job)["state"])
        return {"states": states, "result": store.result("alice", job),
                "events": store.events("alice", job),
                "receipt_count": store.receipt_count(job)}
    finally:
        store.close()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as directory:
        print(json.dumps(run_demo(Path(directory)), ensure_ascii=True, indent=2))
