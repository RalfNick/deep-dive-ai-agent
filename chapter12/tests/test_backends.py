"""Bounded host execution for generated fixtures, plus a fixed container command."""
from __future__ import annotations

from pathlib import Path
import threading
import time

import pytest

from chapter12 import backends
from chapter12.prepare import create_workspace


def fixture(tmp_path: Path) -> Path:
    return create_workspace(tmp_path / 'repo')


def test_utf8_output_budget_keeps_whole_characters():
    got = backends.bounded_decode([b'\xe4', b'\xb8\xad', b'x' * 100], 3)
    assert got == {'text': '中', 'truncated': True}


def test_invalid_utf8_is_replaced_without_exceeding_budget():
    got = backends.bounded_decode([b'ok\xffmore'], 5)
    assert got['text'] == 'ok�'
    assert len(got['text'].encode('utf-8')) <= 5
    assert got['truncated'] is True


def test_long_output_is_drained_without_deadlock(tmp_path):
    result = backends.run_preset(fixture(tmp_path), 'probe_output', 'trusted_local',
                                 timeout_seconds=5, output_bytes=1024,
                                 cancel=threading.Event())
    assert result['returncode'] == 0
    assert result['truncated'] is True
    assert len((result['stdout'] + result['stderr']).encode()) <= 1024
    assert result['timed_out'] is False and result['cancelled'] is False


def test_timeout_stops_process(tmp_path):
    result = backends.run_preset(fixture(tmp_path), 'probe_sleep', 'trusted_local',
                                 timeout_seconds=.1, output_bytes=1024,
                                 cancel=threading.Event())
    assert result['timed_out'] is True
    assert result['cancelled'] is False
    assert result['duration_seconds'] < 3


def test_cancel_has_priority_when_observed_with_deadline(tmp_path):
    cancel = threading.Event()
    cancel.set()
    result = backends.run_preset(fixture(tmp_path), 'probe_sleep', 'trusted_local',
                                 timeout_seconds=0, output_bytes=1024, cancel=cancel)
    assert result['cancelled'] is True
    assert result['timed_out'] is True


def test_cancellation_kills_child_process_tree(tmp_path):
    root = fixture(tmp_path)
    cancel = threading.Event()
    timer = threading.Timer(.15, cancel.set)
    timer.start()
    try:
        result = backends.run_preset(root, 'probe_child', 'trusted_local', 5, 1024, cancel)
    finally:
        timer.cancel()
    time.sleep(.8)
    assert result['cancelled'] is True
    assert not (root / 'child-survived.txt').exists()


def test_host_credentials_are_not_inherited(tmp_path, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-' + 'EXAMPLE_NOT_REAL' * 2)
    result = backends.run_preset(fixture(tmp_path), 'probe_env', 'trusted_local',
                                 5, 1024, threading.Event())
    assert result['stdout'].strip() == 'False'


def test_candidate_tests_are_a_fixed_preset(tmp_path):
    result = backends.run_preset(fixture(tmp_path), 'candidate_tests', 'trusted_local',
                                 10, 4096, threading.Event())
    assert result['returncode'] == 0
    assert result['discovered'] == 2
    assert result['diagnostic'] == 'passed'


def test_trusted_local_rejects_arbitrary_directory(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    with pytest.raises(ValueError, match='trusted_fixture_required'):
        backends.run_preset(root, 'candidate_tests', 'trusted_local', 5, 100,
                            threading.Event())


@pytest.mark.parametrize('preset', ['shell', '../candidate_tests', ''])
def test_arbitrary_commands_are_not_presets(tmp_path, preset):
    with pytest.raises(ValueError, match='unknown_preset'):
        backends.run_preset(fixture(tmp_path), preset, 'trusted_local', 5, 100,
                            threading.Event())


def test_container_command_has_the_required_static_boundaries(tmp_path):
    root = fixture(tmp_path)
    command = backends.container_command(root, 'candidate_tests', 'chapter12-test')
    joined = ' '.join(command)
    assert '--network none' in joined
    assert '--read-only' in command
    assert '--user 65534:65534' in joined
    assert '--cap-drop ALL' in joined
    assert '--security-opt no-new-privileges' in joined
    assert '--pids-limit 64' in joined and '--memory 256m' in joined
    assert '--cpus 1' in joined and '--workdir /work' in joined
    assert '/var/run/docker.sock' not in joined
    assert 'OPENAI_API_KEY' not in joined and '--env' not in command
    assert command[-7:] == ['python', '-B', '-m', 'unittest', 'discover', '-s', 'tests']
