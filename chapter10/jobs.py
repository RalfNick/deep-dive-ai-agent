"""Durable local jobs. All write effects in this lab live in one SQLite DB.

Owner strings are supplied by a trusted caller, not authenticated here. Worker
methods are internal-only. Logical time is explicitly injected for experiments.
Lease fencing cannot fence an external API which does not honor the same token.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3

from .catalog import canonical

TERMINAL = {"succeeded", "failed", "cancelled"}


class JobError(ValueError):
    pass


class JobStore:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY, owner TEXT NOT NULL, action_key TEXT NOT NULL,
                intent TEXT NOT NULL, state TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0,
                lease_until INTEGER NOT NULL DEFAULT 0, not_before INTEGER NOT NULL,
                deadline INTEGER NOT NULL, max_attempts INTEGER NOT NULL,
                done INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 0,
                error TEXT, UNIQUE(owner, action_key));
            CREATE TABLE IF NOT EXISTS receipts (
                job_id INTEGER PRIMARY KEY REFERENCES jobs(id), body TEXT NOT NULL,
                digest TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id),
                kind TEXT NOT NULL, attempt INTEGER NOT NULL, detail TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def _row(self, job: int):
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
        if row is None:
            raise JobError("not_found")
        return row

    def _owned(self, owner: str, job: int):
        row = self._row(job)
        if row["owner"] != owner:
            raise JobError("not_found")
        return row

    def _event(self, job: int, kind: str, detail=None):
        self.db.execute("INSERT INTO events(job_id,kind,attempt,detail) VALUES(?,?,?,?)",
                        (job, kind, self._row(job)["attempt"], canonical(detail or {})))

    def _state(self, job: int, state: str, error=None):
        self.db.execute("UPDATE jobs SET state=?,error=? WHERE id=?", (state, error, job))
        self._event(job, state, {"error": error} if error else {})

    def submit(self, owner: str, action_key: str, args: dict, *, now: int,
               deadline: int = 100, max_attempts: int = 3, capacity: int = 20) -> int:
        if not owner or not action_key or capacity < 1 or max_attempts < 1 or deadline <= now:
            raise JobError("invalid_submission")
        # This lab implements one business operation, frozen at version 1.
        if set(args) != {"month"} or not isinstance(args["month"], str):
            raise JobError("bad_input")
        intent = canonical({"tool": "reports.export", "version": "1", "args": args})
        with self.transaction():
            existing = self.db.execute("SELECT id,intent FROM jobs WHERE owner=? AND action_key=?",
                                       (owner, action_key)).fetchone()
            if existing:
                if existing["intent"] != intent:
                    raise JobError("key_conflict")
                return existing["id"]
            count = self.db.execute("SELECT count(*) FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled')").fetchone()[0]
            if count >= capacity:
                raise JobError("queue_full")
            job = self.db.execute("""INSERT INTO jobs(owner,action_key,intent,state,not_before,deadline,max_attempts)
                                     VALUES(?,?,?,'queued',?,?,?)""",
                                  (owner, action_key, intent, now, deadline, max_attempts)).lastrowid
            self._event(job, "queued")
            return job

    def get(self, owner: str, job: int) -> dict:
        row = self._owned(owner, job)
        return {key: row[key] for key in ("id", "state", "attempt", "done", "total", "error")}

    def claim(self, job: int, *, now: int, lease: int = 10) -> int | None:
        if lease < 1:
            raise ValueError("lease must be positive")
        with self.transaction():
            row = self._row(job)
            if row["state"] in TERMINAL:
                return None
            if row["state"] == "cancel_requested":
                if now >= row["lease_until"]:
                    self._state(job, "cancelled")
                return None
            if now >= row["deadline"]:
                self._state(job, "failed", "deadline_exceeded")
                return None
            if row["state"] == "running" and now < row["lease_until"]:
                return None
            if now < row["not_before"]:
                return None
            if row["attempt"] >= row["max_attempts"]:
                self._state(job, "failed", "attempts_exhausted")
                return None
            self.db.execute("""UPDATE jobs SET state='running',attempt=attempt+1,lease_until=?,
                               done=0,total=0,error=NULL WHERE id=?""", (now + lease, job))
            self._event(job, "running")
            return self._row(job)["attempt"]

    def _worker_row(self, job: int, attempt: int, now: int):
        row = self._row(job)
        if row["attempt"] != attempt:
            raise JobError("stale_attempt")
        if row["state"] in TERMINAL:
            return row
        if row["state"] not in {"running", "cancel_requested"}:
            raise JobError("not_running")
        if now >= row["lease_until"]:
            raise JobError("lease_expired")
        return row

    def progress(self, job: int, attempt: int, done: int, total: int, *, now: int):
        with self.transaction():
            row = self._worker_row(job, attempt, now)
            if row["state"] != "running":
                raise JobError("not_running")
            if not 0 <= row["done"] <= done <= total or (row["total"] and total != row["total"]):
                raise JobError("invalid_progress")
            self.db.execute("UPDATE jobs SET done=?,total=? WHERE id=?", (done, total, job))
            self._event(job, "progress", {"done": done, "total": total})

    def finish(self, job: int, attempt: int, result: dict, *, now: int) -> bool:
        body = canonical(result)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        with self.transaction():
            row = self._worker_row(job, attempt, now)
            if row["state"] in TERMINAL:
                return False
            if row["state"] == "cancel_requested":
                self._state(job, "cancelled")
                return False
            if now >= row["deadline"]:
                self._state(job, "failed", "deadline_exceeded")
                return False
            self.db.execute("INSERT INTO receipts(job_id,body,digest) VALUES(?,?,?)", (job, body, digest))
            self._state(job, "succeeded")
            return True

    def fail(self, job: int, attempt: int, code: str, *, now: int, retry_after: int | None = None):
        if retry_after is not None and retry_after < 1:
            raise ValueError("retry_after must be positive")
        with self.transaction():
            row = self._worker_row(job, attempt, now)
            if row["state"] in TERMINAL:
                return
            if row["state"] == "cancel_requested":
                self._state(job, "cancelled")
            elif now >= row["deadline"]:
                self._state(job, "failed", "deadline_exceeded")
            elif retry_after is not None and row["attempt"] < row["max_attempts"] and now + retry_after < row["deadline"]:
                self.db.execute("UPDATE jobs SET not_before=? WHERE id=?", (now + retry_after, job))
                self._state(job, "queued", code)
            else:
                self._state(job, "failed", code)

    def cancel(self, owner: str, job: int) -> str:
        with self.transaction():
            row = self._owned(owner, job)
            if row["state"] == "queued":
                self._state(job, "cancelled")
            elif row["state"] == "running":
                self._state(job, "cancel_requested")
            return self._row(job)["state"]

    def events(self, owner: str, job: int, after: int = 0) -> list[dict]:
        self._owned(owner, job)
        return [{"seq": row["seq"], "kind": row["kind"], "attempt": row["attempt"],
                 "detail": json.loads(row["detail"])} for row in self.db.execute(
                     "SELECT * FROM events WHERE job_id=? AND seq>? ORDER BY seq", (job, after))]

    def result(self, owner: str, job: int) -> dict:
        row = self._owned(owner, job)
        if row["state"] != "succeeded":
            raise JobError("not_ready")
        result = self.db.execute("SELECT body,digest FROM receipts WHERE job_id=?", (job,)).fetchone()
        return {"artifact_id": f"report-{job}", "sha256": result["digest"], "data": json.loads(result["body"])}

    def receipt_count(self, job: int) -> int:
        """Internal evidence check, not an unauthenticated public endpoint."""
        return self.db.execute("SELECT count(*) FROM receipts WHERE job_id=?", (job,)).fetchone()[0]
