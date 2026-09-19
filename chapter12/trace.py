"""Store only visible, bounded evidence; exporting never re-executes a tool."""
from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .state import Store

VISIBLE_FIELDS = {
    'text', 'message', 'ok', 'error', 'reason', 'status', 'path', 'paths', 'name',
    'call_id', 'action_id', 'run_id', 'arguments_hash', 'workspace_hash', 'version',
    'before_hash', 'after_hash', 'approved', 'truncated', 'returncode', 'discovered',
    'failed_cases', 'protected_ok', 'passed', 'backend', 'decision_source',
    'model', 'model_turns', 'tool_calls', 'usage', 'input_tokens', 'output_tokens',
    'total_tokens', 'prompt_tokens', 'completion_tokens', 'duration_seconds',
    'timeout_seconds', 'cancelled', 'timed_out', 'query', 'directory', 'start', 'end',
    'old', 'new', 'preset', 'arguments', 'data', 'result', 'diff', 'stdout', 'stderr',
    'event', 'evidence', 'log_ref', 'matches', 'line', 'plan', 'cursor', 'phase',
    'orchestration', 'framework_version', 'bytes_before', 'bytes_after',
}
SECRET = re.compile(r'(?i)\b(?:sk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._~+/-]{16,})')
ASSIGNMENT = re.compile(r'(?i)((?:api[_-]?key|password|access[_-]?token)\s*[:=]\s*)\S+')


def sanitize(value: Any, depth: int = 0) -> Any:
    if depth > 12:
        return '[DEPTH_LIMIT]'
    if isinstance(value, dict):
        return {key: sanitize(item, depth + 1) for key, item in value.items()
                if key in VISIBLE_FIELDS}
    if isinstance(value, list):
        return [sanitize(item, depth + 1) for item in value[:128]]
    if isinstance(value, str):
        value = SECRET.sub('[REDACTED]', value)
        value = ASSIGNMENT.sub(r'\1[REDACTED]', value)
        return value.encode('utf-8')[:8192].decode('utf-8', errors='ignore')
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('non_finite_event')
    if value is None or type(value) in (int, float, bool):
        return value
    raise ValueError('non_json_event')


def export(store: Store, run_id: str) -> list[dict[str, Any]]:
    # A trace is an observation interface, never an instruction to execute again.
    return store.events(run_id)
