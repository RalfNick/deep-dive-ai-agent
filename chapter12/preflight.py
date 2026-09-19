"""Fail closed before a live model is given an execution surface."""
from collections.abc import Callable

from .contracts import BACKENDS, Record


def check(backend: str, live: bool, probe: Callable[[], Record]) -> Record:
    if backend not in BACKENDS:
        raise ValueError('unknown_backend')
    if backend == 'trusted_local':
        return dict(backend=backend, ready=not live, reason='trusted_fixtures_only')
    try:
        facts = probe()
        ready = isinstance(facts, dict) and all(facts.get(key) is True for key in
            ('available', 'image_pinned', 'isolation_passed'))
    except (OSError, ValueError, RuntimeError):
        ready = False
    return dict(backend=backend, ready=ready,
                reason='ready' if ready else 'isolation_unverified')
