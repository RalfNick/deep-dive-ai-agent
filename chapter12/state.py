"""Transactional control-plane state; keep the database outside candidate writes."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Iterator

from .contracts import Record, STATUSES, validate_call, validate_result
from .prepare import control_path
from .tools import manifest_hash, safe_path
from .trace import sanitize


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def _decode(text: str) -> Record:
    try:
        result = json.loads(text)
        if not isinstance(result, dict):
            raise ValueError('not an object')
        return result
    except (ValueError, TypeError) as error:
        raise RuntimeError('state_corrupt') from error


class Store:
    def __init__(self, path: Path):
        self.path = path
        existing = path.exists()
        if existing and path.stat().st_size < 100:
            raise RuntimeError('state_corrupt')
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connection() as connection:
                if connection.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise RuntimeError('state_corrupt')
                version = connection.execute('PRAGMA user_version').fetchone()[0]
                if existing and version != 1:
                    raise RuntimeError('state_schema_unsupported')
                connection.execute('PRAGMA journal_mode=WAL')
                connection.executescript('''
                    CREATE TABLE IF NOT EXISTS runs (
                        run_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS calls (
                        run_id TEXT NOT NULL, call_id TEXT NOT NULL, payload TEXT NOT NULL,
                        PRIMARY KEY(run_id,call_id), FOREIGN KEY(run_id) REFERENCES runs(run_id));
                    CREATE TABLE IF NOT EXISTS actions (
                        action_id TEXT PRIMARY KEY, run_id TEXT NOT NULL,
                        call_id TEXT NOT NULL, payload TEXT NOT NULL,
                        UNIQUE(run_id,call_id), FOREIGN KEY(run_id) REFERENCES runs(run_id));
                    CREATE TABLE IF NOT EXISTS approvals (
                        action_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                        FOREIGN KEY(action_id) REFERENCES actions(action_id));
                    CREATE TABLE IF NOT EXISTS events (
                        run_id TEXT NOT NULL, seq INTEGER NOT NULL, payload TEXT NOT NULL,
                        PRIMARY KEY(run_id,seq), FOREIGN KEY(run_id) REFERENCES runs(run_id));
                    PRAGMA user_version=1;
                ''')
        except sqlite3.DatabaseError as error:
            raise RuntimeError('state_corrupt') from error

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=2)
        try:
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=2000')
            connection.execute('PRAGMA synchronous=FULL')
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _save(self, connection: sqlite3.Connection, state: Record) -> None:
        if state.get('schema_version') != 1 or state.get('status') not in STATUSES:
            raise ValueError('invalid_state')
        connection.execute('INSERT INTO runs(run_id,payload) VALUES (?,?) '
            'ON CONFLICT(run_id) DO UPDATE SET payload=excluded.payload',
            (state['run_id'], canonical_json(state)))

    def save(self, state: Record) -> None:
        with self._connection() as connection:
            self._save(connection, state)

    def save_with_event(self, state: Record, kind: str, payload: Record,
                        call_id: str | None = None,
                        action_id: str | None = None) -> None:
        # Validate raw event serializability before filtering unknown fields.
        canonical_json(payload)
        with self._connection() as connection:
            self._save(connection, state)
            self._event(connection, state['run_id'], kind, payload, call_id, action_id)

    def load(self, run_id: str) -> Record:
        with self._connection() as connection:
            row = connection.execute('SELECT payload FROM runs WHERE run_id=?', (run_id,)).fetchone()
        if row is None:
            raise ValueError('run_not_found')
        result = _decode(row[0])
        if result.get('schema_version') != 1 or result.get('status') not in STATUSES:
            raise RuntimeError('state_corrupt')
        return result

    def _event(self, connection: sqlite3.Connection, run_id: str, kind: str,
               payload: Record, call_id: str | None = None, action_id: str | None = None) -> Record:
        canonical_json(payload)
        seq = connection.execute('SELECT COALESCE(MAX(seq),0)+1 FROM events WHERE run_id=?',
                                 (run_id,)).fetchone()[0]
        record = dict(seq=seq, run_id=run_id, kind=kind, call_id=call_id,
                      action_id=action_id, payload=sanitize(payload))
        connection.execute('INSERT INTO events VALUES (?,?,?)', (run_id, seq, canonical_json(record)))
        return record

    def append_event(self, run_id: str, kind: str, payload: Record,
                     call_id: str | None = None, action_id: str | None = None) -> Record:
        with self._connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            return self._event(connection, run_id, kind, payload, call_id, action_id)

    def events(self, run_id: str) -> list[Record]:
        with self._connection() as connection:
            rows = connection.execute('SELECT payload FROM events WHERE run_id=? ORDER BY seq',
                                      (run_id,)).fetchall()
        return [_decode(row[0]) for row in rows]

    def _register(self, connection: sqlite3.Connection, run_id: str, call: Record) -> Record:
        call = validate_call(call)
        text = canonical_json(call)
        existing = connection.execute('SELECT payload FROM calls WHERE run_id=? AND call_id=?',
                                      (run_id, call['call_id'])).fetchone()
        if existing is not None:
            if existing[0] != text:
                raise ValueError('call_id_conflict')
        else:
            connection.execute('INSERT INTO calls VALUES (?,?,?)', (run_id, call['call_id'], text))
        return call

    def register_call(self, run_id: str, call: Record) -> Record:
        with self._connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            return self._register(connection, run_id, call)

    def intent(self, run_id: str, call: Record, patch: Record) -> Record:
        with self._connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            call = self._register(connection, run_id, call)
            args = call['arguments']
            if (call['name'] != 'apply_patch'
                    or patch.get('path') != args['path']
                    or patch.get('old') != args['old']
                    or patch.get('new') != args['new']
                    or patch.get('before_hash') != args['version']
                    or patch['workspace_hash'] != manifest_hash(patch['before_files'])
                    or patch['before_files'].get(patch['path'], 'absent') != patch['before_hash']
                    or patch['after_files'] != dict(patch['before_files'], **{patch['path']: patch['after_hash']})):
                raise ValueError('intent_mismatch')
            existing = connection.execute('SELECT payload FROM actions WHERE run_id=? AND call_id=?',
                                          (run_id, call['call_id'])).fetchone()
            if existing is not None:
                action = _decode(existing[0])
                comparable = {key: value for key, value in patch.items() if key != 'action_id'}
                previous = {key: value for key, value in action['patch'].items() if key != 'action_id'}
                if comparable != previous:
                    raise ValueError('intent_mismatch')
                return action
            arguments_hash = canonical_hash({'name': call['name'], 'arguments': call['arguments']})
            action_id = canonical_hash([run_id, call['call_id'], arguments_hash])
            patch = copy.deepcopy(patch)
            patch['action_id'] = action_id
            action = dict(action_id=action_id, run_id=run_id, call_id=call['call_id'],
                call=call, patch=patch, arguments_hash=arguments_hash,
                workspace_hash=patch['workspace_hash'], result=None)
            connection.execute('INSERT INTO actions VALUES (?,?,?,?)',
                               (action_id, run_id, call['call_id'], canonical_json(action)))
            self._event(connection, run_id, 'action_intent', {
                'path': patch['path'], 'before_hash': patch['before_hash'],
                'after_hash': patch['after_hash'], 'arguments_hash': arguments_hash},
                call['call_id'], action_id)
            return action

    def _action(self, connection: sqlite3.Connection, action_id: str) -> Record:
        row = connection.execute('SELECT payload FROM actions WHERE action_id=?', (action_id,)).fetchone()
        if row is None:
            raise ValueError('action_not_found')
        return _decode(row[0])

    def action(self, action_id: str) -> Record:
        with self._connection() as connection:
            return self._action(connection, action_id)

    def receipt(self, action_id: str, result: Record) -> None:
        with self._connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            action = self._action(connection, action_id)
            if result.get('call_id') != action['call_id']:
                raise ValueError('receipt_call_mismatch')
            if action['result'] is not None:
                if action['result'] != result:
                    raise ValueError('receipt_conflict')
                return
            action['result'] = copy.deepcopy(result)
            connection.execute('UPDATE actions SET payload=? WHERE action_id=?',
                               (canonical_json(action), action_id))
            self._event(connection, action['run_id'], 'action_receipt', result,
                        action['call_id'], action_id)

    def complete_action(self, state: Record, action_id: str, result: Record) -> None:
        """Atomically persist the receipt, paired observation state, and event."""
        result = validate_result(result)
        with self._connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            action = self._action(connection, action_id)
            if state.get('run_id') != action['run_id'] or result['call_id'] != action['call_id']:
                raise ValueError('receipt_call_mismatch')
            if action['result'] is not None:
                if action['result'] != result:
                    raise ValueError('receipt_conflict')
                self._save(connection, state)
                return
            action['result'] = copy.deepcopy(result)
            connection.execute('UPDATE actions SET payload=? WHERE action_id=?',
                               (canonical_json(action), action_id))
            self._save(connection, state)
            self._event(connection, action['run_id'], 'action_receipt', result,
                        action['call_id'], action_id)

    def unresolved_actions(self, run_id: str) -> list[Record]:
        with self._connection() as connection:
            rows = connection.execute('SELECT payload FROM actions WHERE run_id=? ORDER BY rowid',
                                      (run_id,)).fetchall()
        return [action for row in rows if (action := _decode(row[0]))['result'] is None]

    def approve(self, approval: Record) -> None:
        keys = {'run_id', 'action_id', 'arguments_hash', 'workspace_hash', 'approved'}
        if set(approval) != keys or type(approval['approved']) is not bool:
            raise ValueError('approval_mismatch')
        with self._connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            try:
                action = self._action(connection, approval['action_id'])
            except ValueError as error:
                raise ValueError('approval_mismatch') from error
            if any(approval[key] != action[key] for key in keys - {'approved'}):
                raise ValueError('approval_mismatch')
            if action['result'] is not None:
                raise ValueError('action_already_resolved')
            previous = connection.execute('SELECT payload FROM approvals WHERE action_id=?',
                                          (approval['action_id'],)).fetchone()
            if previous:
                if _decode(previous[0]) != approval:
                    raise ValueError('approval_conflict')
                return
            connection.execute('INSERT INTO approvals VALUES (?,?)',
                               (approval['action_id'], canonical_json(approval)))
            self._event(connection, action['run_id'], 'approval_recorded', approval,
                        action['call_id'], action['action_id'])

    def approval(self, action_id: str) -> Record | None:
        with self._connection() as connection:
            row = connection.execute('SELECT payload FROM approvals WHERE action_id=?', (action_id,)).fetchone()
        return _decode(row[0]) if row else None


@contextmanager
def workspace_lock(root: Path) -> Iterator[None]:
    safe_path(root, '.')
    control = control_path(root)
    control.mkdir(exist_ok=True)
    with (control / 'writer.lock').open('a+b') as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b'\0')
            handle.flush()
        handle.seek(0)
        acquired = False
        try:
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError as error:
                raise RuntimeError('workspace_locked') from error
            yield
        finally:
            if acquired:
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
