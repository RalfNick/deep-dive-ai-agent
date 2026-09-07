import asyncio
import unittest

from chapter10.concurrency import bounded_reads


class ConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_overlap_limit_and_id_binding(self):
        active = 0
        peak = 0
        gate = asyncio.Event()

        async def read(value):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            if active == 2:
                gate.set()
            await gate.wait()
            await asyncio.sleep(0)
            active -= 1
            return value * 10

        results = await asyncio.wait_for(bounded_reads([("a", 1), ("b", 2), ("c", 3)], read, limit=2), 2)
        self.assertEqual(2, peak)
        self.assertEqual({"a": {"value": 10}, "b": {"value": 20}, "c": {"value": 30}}, results)

    async def test_failure_keeps_successful_sibling(self):
        async def read(value):
            if value == 2:
                raise ValueError("private data must not leak")
            return value
        results = await bounded_reads([("a", 1), ("b", 2)], read, limit=2)
        self.assertEqual({"error": "ValueError"}, results["b"])
        self.assertEqual({"value": 1}, results["a"])

    async def test_duplicate_call_ids_rejected(self):
        async def read(value):
            return value
        with self.assertRaises(ValueError):
            await bounded_reads([("a", 1), ("a", 2)], read)

    async def test_cancellation_propagates_and_workers_exit(self):
        started = asyncio.Event()
        stopped = asyncio.Event()
        async def read(value):
            try:
                started.set()
                await asyncio.Event().wait()
            finally:
                stopped.set()
        task = asyncio.create_task(bounded_reads([("a", 1)], read))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(stopped.is_set())


if __name__ == "__main__":
    unittest.main()
