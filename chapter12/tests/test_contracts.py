"""Boundary tests: malformed model actions must not reach an executor."""
import copy
import importlib.util

import pytest


def contracts():
    assert importlib.util.find_spec('chapter12.contracts'), 'tool protocol is missing'
    from chapter12 import contracts as module
    return module


@pytest.mark.parametrize('name,args', [
    ('read_file', {'path': 'src/linkcheck.py'}),
    ('search', {'query': 'broken_links', 'directory': '.'}),
    ('apply_patch', {'path': 'src/linkcheck.py', 'version': 'a' * 64,
                     'old': 'old', 'new': 'new'}),
    ('run_tests', {'preset': 'candidate_tests'}),
    ('show_diff', {}),
])
def test_valid_tool_call_is_copied_not_mutated(name, args):
    value = {'call_id': 'c1', 'name': name, 'arguments': args}
    original = copy.deepcopy(value)
    result = contracts().validate_call(value)
    assert result == original
    result['arguments']['changed'] = True
    assert value == original


@pytest.mark.parametrize('value,error', [
    ({'call_id': 'c1', 'name': 'shell', 'arguments': {}}, 'unknown_tool'),
    ({'call_id': '', 'name': 'show_diff', 'arguments': {}}, 'invalid_call_id'),
    ({'call_id': 'c1', 'name': 'show_diff', 'arguments': {}, 'approved': True}, 'invalid_fields'),
    ({'call_id': 'c1', 'name': 'show_diff', 'arguments': {'command': 'echo bad'}}, 'invalid_fields'),
    ({'call_id': 'c1', 'name': 'read_file', 'arguments': {'path': 'a', 'start': True}}, 'invalid_type'),
    ({'call_id': 'c1', 'name': 'read_file', 'arguments': {'path': 'a', 'start': 0}}, 'out_of_range'),
    ({'call_id': 'c1', 'name': 'read_file', 'arguments': {'path': 'a', 'start': 5, 'end': 2}}, 'invalid_line_range'),
    ({'call_id': 'c1', 'name': 'search', 'arguments': {'query': ''}}, 'invalid_length'),
    ({'call_id': 'c1', 'name': 'apply_patch', 'arguments': {'path': 'a', 'old': 'x', 'new': 'y', 'version': 'latest'}}, 'invalid_pattern'),
    ({'call_id': 'c1', 'name': 'run_tests', 'arguments': {'preset': 'acceptance'}}, 'invalid_enum'),
    ({'call_id': 'c1', 'name': 'show_diff', 'arguments': []}, 'invalid_type'),
])
def test_invalid_actions_are_rejected(value, error):
    with pytest.raises(ValueError, match=error):
        contracts().validate_call(value)


def test_run_state_does_not_share_mutable_defaults():
    one = contracts().new_state('one', 'repair', 'trusted_local', 10)
    two = contracts().new_state('two', 'repair', 'trusted_local', 10)
    one['messages'].append({'role': 'user', 'content': 'hello'})
    one['counters']['model_turns'] = 1
    assert two['messages'] == []
    assert two['counters']['model_turns'] == 0
    assert two['deadline'] == 310
    assert two['status'] == 'ready'


@pytest.mark.parametrize('run_id,backend,now', [('../escape', 'trusted_local', 0),
    ('ok', 'fallback', 0), ('ok', 'container', float('nan'))])
def test_invalid_initial_state_is_rejected(run_id, backend, now):
    with pytest.raises(ValueError):
        contracts().new_state(run_id, 'repair', backend, now)
