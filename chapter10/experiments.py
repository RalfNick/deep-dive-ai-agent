"""Five reproducible experiments. Run from repository root."""
import argparse
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import tempfile

from .catalog import Catalog, CatalogError, byte_size, fixture_tools
from .concurrency import bounded_reads
from .jobs import JobError, JobStore

GRANTS = {"orders:read", "reports:write", "archive:read"}
SALES = [{"order_id": "A", "month": "2026-08", "amount_cents": 1000},
         {"order_id": "B", "month": "2026-08", "amount_cents": 2000},
         {"order_id": "C", "month": "2026-08", "amount_cents": 3000},
         {"order_id": "D", "month": "2026-07", "amount_cents": 9900}]


def error_of(function):
    try:
        function()
    except (CatalogError, JobError) as error:
        return str(error)
    raise AssertionError("the injected failure did not fire")


def catalog_experiment():
    catalog = Catalog(fixture_tools())
    hits = catalog.search("查询 订单 状态", GRANTS, limit=2)
    loaded = catalog.load(hits, GRANTS)
    # Include the bootstrap discovery interface, not just selected schemas.
    bootstrap = {"name": "tools.search", "description": "按空格分隔的关键词搜索授权工具目录",
                 "parameters": {"query": "string", "limit": "positive integer"}}
    full = [tool.definition() for tool in catalog.tools.values() if tool.permission in GRANTS]
    return {"registered": len(catalog.tools), "discoverable": len(full), "loaded": len(loaded),
            "hits": [{"name": hit["name"], "score": hit["score"]} for hit in hits],
            "full_definitions_bytes": byte_size(full),
            "bootstrap_bytes": byte_size(bootstrap), "hit_summaries_bytes": byte_size(hits),
            "loaded_definitions_bytes": byte_size(loaded),
            "deferred_visible_payload_bytes": byte_size(bootstrap) + byte_size(hits) + byte_size(loaded)}


def boundaries_experiment():
    catalog = Catalog(fixture_tools())
    hit = catalog.search("订单", GRANTS)[0]
    loaded = catalog.load([hit], GRANTS)[0]
    budget = error_of(lambda: catalog.load([hit], GRANTS, budget_bytes=1))
    revoked = error_of(lambda: catalog.authorize(loaded, set()))
    catalog.tools[hit["name"]] = replace(catalog.tools[hit["name"]], version="2")
    stale = error_of(lambda: catalog.load([hit], GRANTS))
    return {"unknown_query": catalog.search("火星 着陆", GRANTS),
            "ambiguous_query": [{"name": h["name"], "score": h["score"]} for h in catalog.search("状态", GRANTS)],
            "budget": budget, "revoked": revoked, "stale": stale}


async def concurrency_experiment():
    active, peak = 0, 0
    both_started = asyncio.Event()
    async def read(value):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        if active == 2:
            both_started.set()
        try:
            await both_started.wait()
            await asyncio.sleep(0)
            if value == "C":
                raise LookupError("synthetic unavailable order")
            return {"order_id": value, "status": "paid"}
        finally:
            active -= 1
    results = await asyncio.wait_for(bounded_reads([(f"call-{x}", x) for x in "ABC"], read, limit=2), 2)
    return {"limit": 2, "peak_in_flight": peak, "results": results,
            "measured_network_latency_ms": None}


def lifecycle_experiment(directory: Path):
    path = directory / "lifecycle.sqlite"
    store = JobStore(path)
    job = store.submit("alice", "august-report", {"month": "2026-08"}, now=0)
    submitted = store.get("alice", job)
    store.close()
    # A fresh connection stands for a restarted host process. The job is durable.
    store = JobStore(path)
    try:
        attempt = store.claim(job, now=1)
        rows = [row for row in SALES if row["month"] == "2026-08"]
        total = 0
        for index, row in enumerate(rows, 1):
            total += row["amount_cents"]
            store.progress(job, attempt, index, len(rows), now=index + 1)
        cursor = store.events("alice", job)[-1]["seq"]
        store.finish(job, attempt, {"month": "2026-08", "row_count": len(rows), "total_cents": total}, now=5)
        return {"submitted": submitted, "resumed_with_same_job_id": job,
                "result": store.result("alice", job), "cursor": cursor,
                "new_events_after_cursor": store.events("alice", job, after=cursor),
                "events": store.events("alice", job)}
    finally:
        store.close()


def failures_experiment(directory: Path):
    store = JobStore(directory / "failures.sqlite")
    args = {"month": "2026-08"}
    def submit(key, **kwargs):
        return store.submit("alice", key, args, now=0, **kwargs)
    try:
        job = submit("recover")
        repeated = submit("recover")
        conflict = error_of(lambda: store.submit("alice", "recover", {"month": "2026-07"}, now=0))
        old = store.claim(job, now=1, lease=2)
        # The previous worker disappears; another worker claims after lease expiry.
        new = store.claim(job, now=3, lease=5)
        stale = error_of(lambda: store.finish(job, old, {}, now=4))
        store.finish(job, new, {"row_count": 3, "total_cents": 6000}, now=4)
        replay = store.finish(job, new, {"row_count": 3, "total_cents": 6000}, now=5)

        cancelled = submit("cancel")
        attempt = store.claim(cancelled, now=1)
        acknowledgement = store.cancel("alice", cancelled)
        store.finish(cancelled, attempt, {}, now=2)

        late = submit("late", deadline=3)
        attempt = store.claim(late, now=1)
        store.finish(late, attempt, {}, now=3)

        retry = submit("retry", max_attempts=2)
        attempt = store.claim(retry, now=1)
        store.fail(retry, attempt, "temporary", now=2, retry_after=3)
        early = store.claim(retry, now=4)
        second = store.claim(retry, now=5)
        store.fail(retry, second, "temporary", now=6, retry_after=3)

        permanent = submit("permanent")
        attempt = store.claim(permanent, now=1)
        store.fail(permanent, attempt, "bad_input", now=2)

        waiting = submit("wait-only")
        store.claim(waiting, now=1)
        # A reader merely stops polling. It makes no state-changing call.
        wait_state = store.get("alice", waiting)["state"]
        unauthorised = error_of(lambda: store.result("bob", job))
        return {"same_submission_same_job": job == repeated, "key_conflict": conflict,
                "recovery_attempts": [old, new], "stale_worker": stale,
                "recovered_receipts": store.receipt_count(job), "repeated_finish_created_receipt": replay,
                "cancel_acknowledgement": acknowledgement,
                "cancel_before_commit": store.get("alice", cancelled)["state"],
                "cancelled_receipts": store.receipt_count(cancelled),
                "cancel_after_commit": store.cancel("alice", job),
                "deadline_error": store.get("alice", late)["error"],
                "early_retry": early, "retry_final": store.get("alice", retry),
                "permanent_final": store.get("alice", permanent),
                "stopped_polling_job_state": wait_state, "cross_owner_result": unauthorised}
    finally:
        store.close()


def run_all():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        return {"contract": "deterministic tool-discovery and local-job boundary evidence",
                "model_quality": None, "provider_tokens": None, "external_exactly_once": False,
                "groups": {"catalog": catalog_experiment(), "boundaries": boundaries_experiment(),
                           "concurrency": asyncio.run(concurrency_experiment()),
                           "lifecycle": lifecycle_experiment(root), "failures": failures_experiment(root)}}


def write_reports(directory: Path):
    report = run_all()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "tool-jobs-evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = ["# 第十章固定实验报告", "", "这是离线边界实验；字节不是 Token，不测模型质量或外部服务吞吐。", ""]
    for name, result in report["groups"].items():
        lines += [f"## {name}", "", "```json", json.dumps(result, ensure_ascii=False, indent=2), "```", ""]
    (directory / "tool-jobs-evidence.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    events = report["groups"]["lifecycle"]["events"]
    (directory / "job-events.jsonl").write_text("".join(json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n" for e in events), encoding="utf-8", newline="\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=["catalog", "boundaries", "concurrency", "lifecycle", "failures"])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = write_reports(Path(__file__).parent / "reports") if args.write else run_all()
    print(json.dumps(report["groups"][args.group] if args.group else report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
