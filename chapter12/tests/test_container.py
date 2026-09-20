"""Truthful container availability checks; these do not claim isolation passed."""
from pathlib import Path
import threading

import pytest

from chapter12 import backends
from chapter12.prepare import create_workspace


def test_missing_runtime_is_an_error_not_a_host_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(backends.shutil, 'which', lambda name: None)
    root = create_workspace(tmp_path / 'repo')
    with pytest.raises(RuntimeError, match='container_unavailable'):
        backends.run_preset(root, 'candidate_tests', 'container', 5, 1024,
                            threading.Event())
    assert backends.probe_container() == {
        'available': False, 'image_pinned': True, 'isolation_passed': False,
        'runtime': None, 'reason': 'runtime_unavailable'}


def test_actual_probe_never_reports_isolation_without_all_checks():
    facts = backends.probe_container()
    assert set(facts) >= {'available', 'image_pinned', 'isolation_passed', 'reason'}
    if facts['isolation_passed']:
        assert facts['available'] is True
        assert facts['image_pinned'] is True
        assert facts['checks'] == {
            'non_root': True, 'read_only_root': True, 'network_disabled': True,
            'no_host_credentials': True, 'no_control_socket': True,
            'limits': True, 'cancel_cleanup': True}
    else:
        assert facts['reason'] != 'ready'
