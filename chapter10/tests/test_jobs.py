import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path

from chapter10.jobs import JobError, JobStore


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "jobs.sqlite"
        self.store = JobStore(self.path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def submit(self, key="export-1", owner="alice", **kwargs):
        return self.store.submit(owner, key, {"month": "2026-08"}, now=0, **kwargs)

    def test_same_key_same_intent_reuses_job_even_when_full(self):
        a = self.submit(capacity=1)
        self.assertEqual(a, self.submit(capacity=1))
        with self.assertRaisesRegex(JobError, "queue_full"):
            self.submit("export-2", capacity=1)

    def test_same_key_different_args_is_conflict(self):
        self.submit()
        with self.assertRaisesRegex(JobError, "key_conflict"):
            self.store.submit("alice", "export-1", {"month": "2026-07"}, now=0)

    def test_replay_after_deadline_recovers_existing_terminal_job(self):
        for terminal in ("succeeded", "failed", "cancelled"):
            with self.subTest(terminal=terminal):
                job = self.submit(key=terminal, deadline=3)
                if terminal == "cancelled":
                    self.store.cancel("alice", job)
                else:
                    attempt = self.store.claim(job, now=1)
                    if terminal == "succeeded":
                        self.store.finish(job, attempt, {"total_cents": 6000}, now=2)
                    else:
                        self.store.fail(job, attempt, "bad_input", now=2)
                before = self.store.events("alice", job)
                try:
                    replay = self.store.submit("alice", terminal, {"month": "2026-08"},
                                               now=4, deadline=3)
                except JobError as error:
                    self.fail(f"Existing intent must remain recoverable: {error}")
                self.assertEqual(job, replay)
                self.assertEqual(terminal, self.store.get("alice", job)["state"])
                self.assertEqual(before, self.store.events("alice", job))

    def test_replay_conflict_is_detected_even_after_deadline(self):
        self.submit(deadline=3)
        with self.assertRaisesRegex(JobError, "key_conflict"):
            self.store.submit("alice", "export-1", {"month": "2026-07"}, now=4, deadline=3)

    def test_new_intent_with_expired_deadline_is_not_accepted(self):
        with self.assertRaisesRegex(JobError, "invalid_submission"):
            self.store.submit("alice", "new", {"month": "2026-08"}, now=3, deadline=3)
        self.assertEqual(0, self.store.db.execute("SELECT count(*) FROM jobs").fetchone()[0])

    def test_replay_does_not_replace_original_execution_budget(self):
        job = self.submit(deadline=3, max_attempts=1)
        self.assertEqual(job, self.store.submit("alice", "export-1", {"month": "2026-08"},
                                              now=2, deadline=30, max_attempts=9))
        self.assertIsNone(self.store.claim(job, now=3))
        self.assertEqual("deadline_exceeded", self.store.get("alice", job)["error"])

    def test_keys_are_scoped_to_owner(self):
        self.assertNotEqual(self.submit(), self.submit(owner="bob"))

    def test_resume_after_reopen_and_one_receipt(self):
        job = self.submit()
        attempt = self.store.claim(job, now=1, lease=5)
        self.store.close()
        self.store = JobStore(self.path)
        self.store.finish(job, attempt, {"total_cents": 6000}, now=2)
        self.assertEqual("succeeded", self.store.get("alice", job)["state"])
        self.assertFalse(self.store.finish(job, attempt, {"total_cents": 6000}, now=3))
        self.assertEqual(1, self.store.receipt_count(job))

    def test_lease_recovery_fences_old_worker(self):
        job = self.submit()
        old = self.store.claim(job, now=1, lease=2)
        new = self.store.claim(job, now=3, lease=5)
        self.assertNotEqual(old, new)
        with self.assertRaisesRegex(JobError, "stale_attempt"):
            self.store.finish(job, old, {}, now=4)
        self.store.finish(job, new, {"total_cents": 6000}, now=4)

    def test_expired_worker_cannot_finish_before_reclaim(self):
        job = self.submit()
        attempt = self.store.claim(job, now=1, lease=2)
        with self.assertRaisesRegex(JobError, "lease_expired"):
            self.store.finish(job, attempt, {}, now=3)

    def test_queued_cancel_is_terminal(self):
        job = self.submit()
        self.assertEqual("cancelled", self.store.cancel("alice", job))
        self.assertIsNone(self.store.claim(job, now=1))

    def test_running_cancel_requires_worker_ack(self):
        job = self.submit()
        attempt = self.store.claim(job, now=1)
        self.assertEqual("cancel_requested", self.store.cancel("alice", job))
        self.assertFalse(self.store.finish(job, attempt, {}, now=2))
        self.assertEqual("cancelled", self.store.get("alice", job)["state"])
        self.assertEqual(0, self.store.receipt_count(job))

    def test_cancel_after_completion_cannot_undo_receipt(self):
        job = self.submit()
        attempt = self.store.claim(job, now=1)
        self.store.finish(job, attempt, {}, now=2)
        self.assertEqual("succeeded", self.store.cancel("alice", job))

    def test_deadline_prevents_late_commit(self):
        job = self.submit(deadline=3)
        attempt = self.store.claim(job, now=1, lease=10)
        self.assertFalse(self.store.finish(job, attempt, {}, now=3))
        self.assertEqual("deadline_exceeded", self.store.get("alice", job)["error"])
        self.assertEqual(0, self.store.receipt_count(job))

    def test_retry_requires_backoff_and_is_bounded(self):
        job = self.submit(max_attempts=2)
        attempt = self.store.claim(job, now=1)
        self.store.fail(job, attempt, "temporary", now=2, retry_after=3)
        self.assertIsNone(self.store.claim(job, now=4))
        second = self.store.claim(job, now=5)
        self.store.fail(job, second, "temporary", now=6, retry_after=3)
        self.assertEqual("failed", self.store.get("alice", job)["state"])

    def test_permanent_error_does_not_retry(self):
        job = self.submit()
        attempt = self.store.claim(job, now=1)
        self.store.fail(job, attempt, "bad_input", now=2)
        self.assertIsNone(self.store.claim(job, now=3))

    def test_all_public_reads_and_cancel_check_owner(self):
        job = self.submit()
        for action in (self.store.get, self.store.cancel, self.store.events, self.store.result):
            with self.subTest(action=action.__name__):
                with self.assertRaisesRegex(JobError, "not_found"):
                    action("bob", job)

    def test_progress_is_monotonic_and_cursor_is_resumable(self):
        job = self.submit()
        attempt = self.store.claim(job, now=1)
        self.store.progress(job, attempt, 2, 3, now=2)
        with self.assertRaisesRegex(JobError, "progress"):
            self.store.progress(job, attempt, 1, 3, now=2)
        events = self.store.events("alice", job)
        self.assertEqual([], self.store.events("alice", job, after=events[-1]["seq"]))

    def test_result_not_available_until_success(self):
        job = self.submit()
        with self.assertRaisesRegex(JobError, "not_ready"):
            self.store.result("alice", job)

    def test_two_connections_race_for_one_lease(self):
        job = self.submit()
        gate = Barrier(2)
        def compete():
            other = JobStore(self.path)
            try:
                gate.wait(timeout=3)
                return other.claim(job, now=1)
            finally:
                other.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(compete) for _ in range(2)]
            results = [future.result(timeout=5) for future in futures]
        self.assertEqual(1, results.count(1))
        self.assertEqual(1, results.count(None))
        self.assertEqual(2, self.store.claim(job, now=11))

    def test_receipt_and_state_roll_back_together(self):
        job = self.submit()
        attempt = self.store.claim(job, now=1)
        self.store.db.execute("""CREATE TRIGGER inject_state_failure BEFORE UPDATE OF state ON jobs
                                 WHEN NEW.state='succeeded' BEGIN SELECT RAISE(ABORT,'injected'); END""")
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.finish(job, attempt, {"total_cents": 6000}, now=2)
        self.assertEqual(0, self.store.receipt_count(job))
        self.assertEqual("running", self.store.get("alice", job)["state"])
        self.store.db.execute("DROP TRIGGER inject_state_failure")
        self.assertTrue(self.store.finish(job, attempt, {"total_cents": 6000}, now=3))

    def test_expired_cancel_request_is_finalized_without_new_attempt(self):
        job = self.submit()
        self.store.claim(job, now=1, lease=2)
        self.store.cancel("alice", job)
        self.assertIsNone(self.store.claim(job, now=3))
        self.assertEqual("cancelled", self.store.get("alice", job)["state"])
        self.assertEqual(1, self.store.get("alice", job)["attempt"])

    def test_deadline_before_claim_does_not_consume_attempt(self):
        job = self.submit(deadline=3)
        self.assertIsNone(self.store.claim(job, now=3))
        self.assertEqual("failed", self.store.get("alice", job)["state"])
        self.assertEqual(0, self.store.get("alice", job)["attempt"])


if __name__ == "__main__":
    unittest.main()
