"""Trace is evidence to inspect, not a replay command or a credential dump."""
import importlib.util

from chapter12.contracts import new_state


def modules():
    assert importlib.util.find_spec('chapter12.trace'), 'trace export is missing'
    from chapter12.state import Store
    from chapter12.trace import export
    return Store, export


def test_export_is_stable_and_does_not_change_state(tmp_path):
    Store, export = modules()
    db = Store(tmp_path / 'state.sqlite')
    state = new_state('r1', 'repair', 'trusted_local', 0)
    db.save(state)
    db.append_event('r1', 'tool_result', {'ok': False, 'error': 'stale_version'}, call_id='c1')
    left = export(db, 'r1')
    assert left == export(db, 'r1')
    assert db.load('r1') == state
    assert len(db.events('r1')) == 1
    assert left[0]['call_id'] == 'c1' and left[0]['payload']['error'] == 'stale_version'


def test_secrets_and_hidden_reasoning_are_not_persisted_in_events(tmp_path):
    Store, export = modules()
    db = Store(tmp_path / 'state.sqlite')
    db.save(new_state('r1', 'repair', 'trusted_local', 0))
    fake = 'sk-' + 'EXAMPLE_CREDENTIAL_NOT_REAL' * 2
    db.append_event('r1', 'model_message', {'text': 'value ' + fake,
        'api_key': fake, 'headers': {'Authorization': fake},
        'reasoning': 'private reasoning', 'unknown_field': 'discard this'})
    raw = str(db.events('r1'))
    assert fake not in raw and 'private reasoning' not in raw
    assert 'discard this' not in raw
    assert '[REDACTED]' in str(export(db, 'r1'))
