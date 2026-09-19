"""Persistent action identity and cross-process ownership, not just object roundtrips."""
import copy
import importlib.util
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from chapter12.contracts import new_state
from chapter12.prepare import create_workspace
from chapter12.tools import prepare_patch, read_file


def state_module():
    assert importlib.util.find_spec('chapter12.state'), 'persistent store is missing'
    from chapter12 import state
    return state


def make_action(tmp_path, run_id='r1'):
    root = create_workspace(tmp_path / 'repo')
    call = dict(call_id='c1', name='apply_patch', arguments=dict(path='src/linkcheck.py',
        version=read_file(root, 'src/linkcheck.py')['version'],
        old='root / target', new='document.parent / target'))
    db = state_module().Store(tmp_path / 'state.sqlite')
    db.save(new_state(run_id, 'repair', 'trusted_local', 0))
    action = db.intent(run_id, call, prepare_patch(root, call))
    return db, call, action


def test_events_and_state_survive_reopen(tmp_path):
    Store = state_module().Store
    db = Store(tmp_path / 'state.sqlite')
    state = new_state('r1', 'repair', 'trusted_local', 0)
    state['provider_state'] = {'cursor': 3}
    db.save_with_event(state, 'started', {'message': 'visible'})
    reopened = Store(tmp_path / 'state.sqlite')
    assert reopened.load('r1')['provider_state'] == {'cursor': 3}
    assert reopened.events('r1')[0]['seq'] == 1


@pytest.mark.parametrize('data', [b'broken sqlite', b'', b'SQLite format 3\x00'])
def test_corrupt_database_is_preserved_not_recreated(tmp_path, data):
    path = tmp_path / 'state.sqlite'
    path.write_bytes(data)
    with pytest.raises(RuntimeError, match='state_corrupt'):
        state_module().Store(path).load('r1')
    assert path.read_bytes() == data


def test_corrupt_saved_json_is_explicit(tmp_path):
    Store = state_module().Store
    path = tmp_path / 'state.sqlite'
    db = Store(path)
    db.save(new_state('r1', 'repair', 'trusted_local', 0))
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE runs SET payload='{' WHERE run_id='r1'")
    with pytest.raises(RuntimeError, match='state_corrupt'):
        db.load('r1')


def test_state_and_event_roll_back_together(tmp_path):
    db = state_module().Store(tmp_path / 'state.sqlite')
    state = new_state('r1', 'repair', 'trusted_local', 0)
    db.save(state)
    state['plan'] = 'uncommitted'
    with pytest.raises(ValueError):
        db.save_with_event(state, 'planned', {'value': float('nan')})
    assert db.load('r1')['plan'] == ''
    assert db.events('r1') == []


def test_same_intent_is_idempotent_but_changed_arguments_conflict(tmp_path):
    db, call, action = make_action(tmp_path)
    assert db.intent('r1', call, action['patch'])['action_id'] == action['action_id']
    changed = copy.deepcopy(call)
    changed['arguments']['new'] = 'None'
    with pytest.raises(ValueError, match='call_id_conflict'):
        db.intent('r1', changed, action['patch'])
    assert len([e for e in db.events('r1') if e['kind'] == 'action_intent']) == 1


def test_readonly_call_id_conflicts_are_also_rejected(tmp_path):
    db = state_module().Store(tmp_path / 'state.sqlite')
    db.save(new_state('r1', 'repair', 'trusted_local', 0))
    call = dict(call_id='c1', name='read_file', arguments={'path': 'notes.txt'})
    db.register_call('r1', call)
    with pytest.raises(ValueError, match='call_id_conflict'):
        db.register_call('r1', dict(call, arguments={'path': 'src/linkcheck.py'}))


def test_same_call_in_another_run_gets_another_action(tmp_path):
    db, call, action = make_action(tmp_path)
    db.save(new_state('r2', 'repair', 'trusted_local', 0))
    other = db.intent('r2', call, action['patch'])
    assert other['action_id'] != action['action_id']
    assert other['run_id'] == 'r2'


def test_intent_cannot_approve_different_patch_than_tool_arguments(tmp_path):
    root = create_workspace(tmp_path / 'repo')
    call = dict(call_id='c1', name='apply_patch', arguments=dict(path='src/linkcheck.py',
        version=read_file(root, 'src/linkcheck.py')['version'],
        old='root / target', new='document.parent / target'))
    prepared = prepare_patch(root, call)
    prepared['new'] = 'another replacement'
    db = state_module().Store(tmp_path / 'state.sqlite')
    db.save(new_state('r1', 'repair', 'trusted_local', 0))
    with pytest.raises(ValueError, match='intent_mismatch'):
        db.intent('r1', call, prepared)
    assert db.events('r1') == []


def test_repeated_intent_cannot_replace_a_different_patch(tmp_path):
    db, call, action = make_action(tmp_path)
    changed = copy.deepcopy(action['patch'])
    changed['after_hash'] = '0' * 64
    with pytest.raises(ValueError, match='intent_mismatch'):
        db.intent('r1', call, changed)


def test_receipt_cannot_be_replaced_by_conflicting_success(tmp_path):
    db, call, action = make_action(tmp_path)
    result = dict(call_id='c1', ok=False, data={}, error='execution_failed', truncated=False)
    db.receipt(action['action_id'], result)
    db.receipt(action['action_id'], result)
    with pytest.raises(ValueError, match='receipt_conflict'):
        db.receipt(action['action_id'], dict(result, ok=True, error=None))
    assert db.action(action['action_id'])['result']['ok'] is False
    assert len([e for e in db.events('r1') if e['kind'] == 'action_receipt']) == 1


@pytest.mark.parametrize('field', ['run_id', 'action_id', 'arguments_hash', 'workspace_hash'])
def test_approval_binds_every_identity_field(tmp_path, field):
    db, call, action = make_action(tmp_path)
    approval = {key: action[key] for key in ('run_id', 'action_id', 'arguments_hash', 'workspace_hash')}
    approval['approved'] = True
    altered = dict(approval, **{field: 'different'})
    with pytest.raises(ValueError, match='approval_mismatch'):
        db.approve(altered)
    assert db.approval(action['action_id']) is None
    db.approve(approval)
    assert db.approval(action['action_id']) == approval


def test_two_processes_cannot_hold_workspace_lock(tmp_path):
    root = create_workspace(tmp_path / 'repo')
    source = ('from pathlib import Path; from chapter12.state import workspace_lock; '
              'import sys;\nwith workspace_lock(Path(sys.argv[1])): print("acquired")')
    with state_module().workspace_lock(root):
        result = subprocess.run([sys.executable, '-B', '-c', source, str(root)],
                                capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'workspace_locked' in result.stderr
    result = subprocess.run([sys.executable, '-B', '-c', source, str(root)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and result.stdout.strip() == 'acquired'


def test_process_crash_releases_os_lock(tmp_path):
    state_module()
    root = create_workspace(tmp_path / 'repo')
    source = ('from pathlib import Path; from chapter12.state import workspace_lock; '
              'import os,sys;\nwith workspace_lock(Path(sys.argv[1])): os._exit(9)')
    result = subprocess.run([sys.executable, '-B', '-c', source, str(root)], timeout=10)
    assert result.returncode == 9
    with state_module().workspace_lock(root):
        assert (root / 'notes.txt').is_file()
