"""Runnable reference solutions for exercises 6–9; 10–11 use test_jobs.py."""
import asyncio
import unittest

from chapter10.catalog import Catalog, CatalogError, Tool, byte_size, fixture_tools
from chapter10.concurrency import bounded_reads
from chapter10.experiments import SALES


class ExerciseSolutions(unittest.TestCase):
    def test_exercise6_invoice_visibility(self):
        catalog = Catalog(fixture_tools() + [Tool("invoices.get", "只读查询发票状态。",
                          ("发票", "查询", "状态"), "invoices:read", "read")])
        self.assertEqual("invoices.get", catalog.search("发票", {"invoices:read"})[0]["name"])
        self.assertEqual([], catalog.search("发票", {"orders:read"}))

    def test_exercise7_exact_budget(self):
        catalog = Catalog(fixture_tools())
        grants = {"orders:read"}
        hits = catalog.search("查询 订单 状态", grants)
        definitions = catalog.load(hits, grants)
        size = byte_size(definitions)
        self.assertEqual(definitions, catalog.load(hits, grants, budget_bytes=size))
        with self.assertRaisesRegex(CatalogError, "budget"):
            catalog.load(hits, grants, budget_bytes=size - 1)

    def test_exercise9_month_filter(self):
        extra_august = {"order_id": "E", "month": "2026-08", "amount_cents": 4000}
        extra_july = {"order_id": "F", "month": "2026-07", "amount_cents": 8000}
        def august_total(rows):
            return sum(row["amount_cents"] for row in rows if row["month"] == "2026-08")
        self.assertEqual(10000, august_total(SALES + [extra_august]))
        self.assertEqual(10000, august_total(SALES + [extra_august, extra_july]))
        self.assertEqual(4, len(SALES))  # Never mutate the canonical fixture.


class AsyncExerciseSolutions(unittest.IsolatedAsyncioTestCase):
    async def test_exercise8_five_calls_one_failure(self):
        active, peak = 0, 0
        gate = asyncio.Event()
        async def read(value):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            if active == 2:
                gate.set()
            try:
                await gate.wait()
                await asyncio.sleep(0)
                if value == 3:
                    raise LookupError()
                return value
            finally:
                active -= 1
        results = await asyncio.wait_for(bounded_reads([(str(i), i) for i in range(5)], read, limit=2), 2)
        self.assertEqual(set("01234"), set(results))
        self.assertEqual(2, peak)
        self.assertEqual({"error": "LookupError"}, results["3"])
        self.assertEqual(4, sum("value" in result for result in results.values()))


if __name__ == "__main__":
    unittest.main()
