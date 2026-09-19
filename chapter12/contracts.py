"""One schema source for model tool descriptions and local validation.

Validation is deliberately a small JSON-schema subset, not a general validator.
Paths are syntactically bounded here; the filesystem policy checks them again.
"""
from __future__ import annotations

import copy
import math
import re
from typing import Any

Record = dict[str, Any]
BACKENDS = {'trusted_local', 'container'}
TERMINAL = {'completed', 'failed', 'cancelled', 'budget_exhausted'}
STATUSES = TERMINAL | {'ready', 'awaiting_approval', 'executing', 'verifying'}


def _string(minimum: int = 1, maximum: int = 240, **extra: Any) -> Record:
    return dict(type='string', minLength=minimum, maxLength=maximum, **extra)


def _object(properties: Record, required: list[str]) -> Record:
    return dict(type='object', properties=properties, required=required,
                additionalProperties=False)


TOOL_SCHEMAS = {
    'read_file': _object({'path': _string(),
        'start': {'type': 'integer', 'minimum': 1, 'maximum': 100000},
        'end': {'type': 'integer', 'minimum': 1, 'maximum': 100000}}, ['path']),
    'search': _object({'query': _string(maximum=256), 'directory': _string()}, ['query']),
    'apply_patch': _object({'path': _string(),
        'version': _string(pattern=r'(?:[0-9a-f]{64}|absent)'),
        'old': _string(0, 65536), 'new': _string(0, 65536)}, ['path', 'version', 'old', 'new']),
    'run_tests': _object({'preset': _string(enum=['candidate_tests'])}, ['preset']),
    'show_diff': _object({}, []),
}


def _validate(value: Any, schema: Record) -> None:
    kind = schema['type']
    expected = {'object': dict, 'integer': int, 'string': str}[kind]
    if type(value) is not expected:
        raise ValueError('invalid_type')
    if kind == 'object':
        if set(value) - schema['properties'].keys() or not set(schema['required']) <= value.keys():
            raise ValueError('invalid_fields')
        for key, item in value.items():
            _validate(item, schema['properties'][key])
    elif kind == 'integer':
        if not schema['minimum'] <= value <= schema['maximum']:
            raise ValueError('out_of_range')
    else:
        if not schema['minLength'] <= len(value) <= schema['maxLength']:
            raise ValueError('invalid_length')
        try:
            value.encode('utf-8')
        except UnicodeEncodeError as error:
            raise ValueError('invalid_unicode') from error
        if 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
            raise ValueError('invalid_pattern')
        if 'enum' in schema and value not in schema['enum']:
            raise ValueError('invalid_enum')


def validate_call(value: Record) -> Record:
    if type(value) is not dict or set(value) != {'call_id', 'name', 'arguments'}:
        raise ValueError('invalid_fields')
    if not isinstance(value['call_id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', value['call_id']):
        raise ValueError('invalid_call_id')
    if not isinstance(value['name'], str) or value['name'] not in TOOL_SCHEMAS:
        raise ValueError('unknown_tool')
    _validate(value['arguments'], TOOL_SCHEMAS[value['name']])
    args = value['arguments']
    if value['name'] == 'read_file' and args.get('end', max(200, args.get('start', 1))) < args.get('start', 1):
        raise ValueError('invalid_line_range')
    return copy.deepcopy(value)


def new_state(run_id: str, goal: str, backend: str, now: float) -> Record:
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', run_id):
        raise ValueError('invalid_run_id')
    if backend not in BACKENDS:
        raise ValueError('unknown_backend')
    if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
        raise ValueError('invalid_time')
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError('invalid_goal')
    return dict(schema_version=1, run_id=run_id, status='ready', goal=goal,
        constraints=['Only modify src/linkcheck.py and tests/test_agent_*.py.',
                     'Preserve notes, legacy examples and independent acceptance assets.'],
        messages=[], plan='', pending=None, evidence={},
        counters={'model_turns': 0, 'tool_calls': 0}, deadline=now + 300,
        backend=backend, workspace_hash='', reason=None, provider_state={})
