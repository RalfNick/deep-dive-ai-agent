"""Unavailable isolation must never lead to host execution of model code."""
import importlib.util

import pytest


def check(*args):
    assert importlib.util.find_spec('chapter12.preflight'), 'preflight is missing'
    from chapter12.preflight import check as actual
    return actual(*args)


@pytest.mark.parametrize('facts', [{}, {'available': False},
    {'available': True, 'image_pinned': True, 'isolation_passed': False},
    {'available': True, 'image_pinned': True, 'isolation_passed': 'yes'}])
def test_unverified_container_never_falls_back(facts):
    result = check('container', True, lambda: facts)
    assert result['ready'] is False
    assert result['backend'] == 'container'


def test_verified_container_is_available():
    result = check('container', True, lambda: dict(
        available=True, image_pinned=True, isolation_passed=True))
    assert result['ready'] is True


def test_probe_error_fails_closed_without_exception_details():
    def broken():
        raise OSError('private machine diagnostic')
    result = check('container', True, broken)
    assert result['ready'] is False
    assert 'private machine diagnostic' not in str(result)


def test_local_is_only_for_offline_fixtures():
    assert check('trusted_local', False, lambda: {})['ready'] is True
    assert check('trusted_local', True, lambda: {})['ready'] is False


def test_unknown_backend_is_rejected():
    with pytest.raises(ValueError, match='unknown_backend'):
        check('automatic', False, lambda: {})
