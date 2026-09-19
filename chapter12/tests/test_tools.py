"""File tools must preserve the workspace boundary and the version read."""
import importlib.util
import json
import subprocess
import sys

import pytest


def tools():
    assert importlib.util.find_spec('chapter12.tools'), 'file tools are missing'
    from chapter12 import tools as module
    return module


def create(root):
    assert importlib.util.find_spec('chapter12.prepare'), 'fixture creator is missing'
    from chapter12.prepare import create_workspace
    return create_workspace(root)


def patch(root, old='root / target', new='document.parent / target', call_id='c1'):
    return tools().prepare_patch(root, dict(call_id=call_id, name='apply_patch', arguments=dict(
        path='src/linkcheck.py', version=tools().read_file(root, 'src/linkcheck.py')['version'],
        old=old, new=new)))


@pytest.mark.parametrize('name', ['../escape', '/etc/passwd', 'C:/secret', '//host/share',
    r'..\escape', 'src/../notes.txt', 'src/a:stream', 'src/a.', 'src/ a ',
    '.git/config', '.env', 'src/CON', 'src/a\x00b'])
def test_path_escape_is_denied(tmp_path, name):
    with pytest.raises(ValueError, match='path_denied'):
        tools().safe_path(tmp_path, name)


def test_existing_destination_is_never_replaced(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    (root / 'mine.txt').write_text('mine')
    with pytest.raises(FileExistsError):
        create(root)
    assert (root / 'mine.txt').read_text() == 'mine'


def test_read_lines_and_version(tmp_path):
    (tmp_path / 'text.txt').write_bytes('第一行\nsecond\nthird\n'.encode())
    data = tools().read_file(tmp_path, 'text.txt', 2, 2)
    assert data['text'] == 'second\n'
    assert data['start_line'] == 2 and data['end_line'] == 2
    assert data['total_lines'] == 3 and data['truncated'] is False
    assert len(data['version']) == 64


def test_read_and_search_outputs_are_bounded(tmp_path):
    (tmp_path / 'big.txt').write_bytes(('中' * 12000).encode())
    data = tools().read_file(tmp_path, 'big.txt')
    assert len(data['text'].encode()) <= 8192 and data['truncated'] is True
    results = tools().search(tmp_path, '中')
    assert len(json.dumps(results, ensure_ascii=False).encode()) <= 8192
    assert results['truncated'] is True


def test_search_separates_no_matches_from_truncation(tmp_path):
    (tmp_path / 'a.txt').write_text('one\nneedle\n', encoding='utf-8')
    data = tools().search(tmp_path, 'needle')
    assert data['matches'] == [{'path': 'a.txt', 'line': 2, 'text': 'needle'}]
    assert data['truncated'] is False
    assert tools().search(tmp_path, 'absent') == {'matches': [], 'truncated': False}


def test_stale_patch_does_not_touch_new_content(tmp_path):
    root = create(tmp_path / 'repo')
    version = tools().read_file(root, 'src/linkcheck.py')['version']
    target = root / 'src/linkcheck.py'
    target.write_text('external\n', encoding='utf-8')
    call = dict(call_id='c1', name='apply_patch', arguments=dict(
        path='src/linkcheck.py', version=version, old='root / target', new='document.parent / target'))
    with pytest.raises(ValueError, match='stale_version'):
        tools().prepare_patch(root, call)
    assert target.read_text() == 'external\n'


def test_prepare_has_no_side_effect_and_write_rechecks_manifest(tmp_path):
    root = create(tmp_path / 'repo')
    intent = patch(root)
    assert 'root / target' in (root / 'src/linkcheck.py').read_text()
    (root / 'notes.txt').write_text('user edit')
    with pytest.raises(ValueError, match='workspace_changed'):
        tools().write_patch(root, intent)
    assert 'root / target' in (root / 'src/linkcheck.py').read_text()


def test_patch_and_diff_preserve_other_files(tmp_path):
    root = create(tmp_path / 'repo')
    notes = (root / 'notes.txt').read_bytes()
    result = tools().write_patch(root, patch(root))
    assert result['version'] == tools().read_file(root, 'src/linkcheck.py')['version']
    diff = tools().show_diff(root)
    assert diff['paths'] == ['src/linkcheck.py']
    assert '+        candidate = document.parent / target' in diff['text']
    assert str(root) not in diff['text']
    assert (root / 'notes.txt').read_bytes() == notes


@pytest.mark.parametrize('old,new,error', [('missing string','x','non_unique_match'),
    ('root','newroot','non_unique_match'), ('root / target','root / target','no_op_patch')])
def test_patch_conflicts_are_explicit(tmp_path, old, new, error):
    root = create(tmp_path / 'repo')
    with pytest.raises(ValueError, match=error):
        patch(root, old, new)


@pytest.mark.parametrize('name', ['notes.txt', 'legacy/check_links.py', 'tests/test_existing.py',
    'src/new.py', 'tests/other.py'])
def test_patch_cannot_change_protected_paths(tmp_path, name):
    root = create(tmp_path / 'repo')
    with pytest.raises(ValueError, match='write_denied'):
        tools().prepare_patch(root, dict(call_id='c1', name='apply_patch', arguments=dict(
            path=name, version='absent', old='', new='bad')))


def test_new_regression_file_has_absent_precondition(tmp_path):
    root = create(tmp_path / 'repo')
    call = dict(call_id='c1', name='apply_patch', arguments=dict(path='tests/test_agent_nested.py',
        version='absent', old='', new='import unittest\n'))
    intent = tools().prepare_patch(root, call)
    assert intent['before_hash'] == 'absent'
    tools().write_patch(root, intent)
    assert (root / 'tests/test_agent_nested.py').read_text() == 'import unittest\n'
    with pytest.raises(ValueError, match='stale_version'):
        tools().prepare_patch(root, call)


def test_symlink_is_rejected(tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'secret.txt').write_text('keep')
    root = tmp_path / 'repo'
    root.mkdir()
    try:
        (root / 'linked').symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f'platform cannot create symlink; boundary not verified here: {error.errno}')
    with pytest.raises(ValueError, match='path_denied'):
        tools().read_file(root, 'linked/secret.txt')
    assert (outside / 'secret.txt').read_text() == 'keep'


def test_hardlink_is_rejected(tmp_path):
    outside = tmp_path / 'outside.txt'
    outside.write_text('keep')
    root = tmp_path / 'repo'
    root.mkdir()
    (root / 'hard.txt').hardlink_to(outside)
    with pytest.raises(ValueError, match='path_denied'):
        tools().read_file(root, 'hard.txt')
    assert outside.read_text() == 'keep'


def test_large_file_is_rejected_before_full_read(tmp_path):
    (tmp_path / 'large.txt').write_bytes(b'x' * 262145)
    with pytest.raises(ValueError, match='file_too_large'):
        tools().read_file(tmp_path, 'large.txt')


def test_read_start_without_end_uses_a_bounded_window(tmp_path):
    (tmp_path / 'many.txt').write_bytes(b'row\n' * 250)
    data = tools().read_file(tmp_path, 'many.txt', start=220)
    assert data['text'] == 'row\n' * 31


def test_tampered_patch_manifest_does_not_bypass_target_version(tmp_path):
    root = create(tmp_path / 'repo')
    intent = patch(root)
    (root / 'src/linkcheck.py').write_text('root / target\n')
    intent['before_files'] = tools().workspace_manifest(root)
    intent['workspace_hash'] = tools().manifest_hash(intent['before_files'])
    with pytest.raises(ValueError, match='intent_mismatch'):
        tools().write_patch(root, intent)


def test_fixture_original_tests_pass_but_nested_link_is_wrong(tmp_path):
    root = create(tmp_path / 'repo')
    result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests'],
        cwd=root, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    spec = importlib.util.spec_from_file_location('fixture_linkcheck', root / 'src/linkcheck.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.broken_links(root / 'docs/guide/start.md', root) == ['../target.md', 'missing.md']
