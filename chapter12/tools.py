"""Small filesystem tools; all external data is rechecked at the write boundary.

This is cooperative single-writer protection, not a hostile-host filesystem
sandbox. Model-produced code must run in the container execution backend.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from .contracts import Record, validate_call
from .prepare import control_path

MAX_FILE_BYTES = 262144
MAX_OUTPUT_BYTES = 8192
MAX_FILES = 512
MAX_WORKSPACE_BYTES = 4194304
IGNORED = {'.git', '__pycache__', '.pytest_cache'}
WINDOWS_DEVICES = {'con', 'prn', 'aux', 'nul'} | {f'{p}{i}' for p in ('com', 'lpt') for i in range(1, 10)}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_hash(files: Record) -> str:
    return digest(json.dumps(files, sort_keys=True, separators=(',', ':')).encode())


def _check_node(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise ValueError('path_denied')
    if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
        raise ValueError('path_denied')
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
        raise ValueError('path_denied')


def safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or len(relative) > 240:
        raise ValueError('path_denied')
    if any(c in relative for c in ('\\', ':', '\x00')) or relative.startswith('/'):
        raise ValueError('path_denied')
    parts = [] if relative == '.' else relative.split('/')
    for part in parts:
        if (not part or part.startswith('.') or part != part.strip() or part.endswith('.')
                or part.split('.')[0].casefold() in WINDOWS_DEVICES):
            raise ValueError('path_denied')
    root = root.absolute()
    # Check root as supplied, before resolve() can erase a symlink/reparse point.
    for ancestor in (*reversed(root.parents), root):
        _check_node(ancestor)
    candidate = root
    for part in parts:
        candidate = candidate / part
        _check_node(candidate)
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('path_denied')
    return candidate


def _read(root: Path, relative: str) -> bytes:
    path = safe_path(root, relative)
    if not path.is_file():
        raise ValueError('file_missing')
    with path.open('rb') as handle:
        value = handle.read(MAX_FILE_BYTES + 1)
    if len(value) > MAX_FILE_BYTES:
        raise ValueError('file_too_large')
    return value


def _clip(text: str, limit: int = MAX_OUTPUT_BYTES) -> tuple[str, bool]:
    raw = text.encode('utf-8')
    return raw[:limit].decode('utf-8', errors='ignore'), len(raw) > limit


def _files(root: Path, directory: str = '.') -> list[str]:
    start = safe_path(root, directory)
    if not start.is_dir():
        raise ValueError('directory_missing')
    result = []
    for parent, dirs, names in os.walk(start, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in IGNORED)
        for name in dirs:
            safe_path(root, (Path(parent) / name).relative_to(root).as_posix())
        for name in sorted(names):
            relative = (Path(parent) / name).relative_to(root).as_posix()
            safe_path(root, relative)
            result.append(relative)
            if len(result) > MAX_FILES:
                raise ValueError('workspace_too_large')
    return sorted(result)


def workspace_manifest(root: Path) -> Record:
    files = {}
    size = 0
    for path in _files(root):
        data = _read(root, path)
        size += len(data)
        if size > MAX_WORKSPACE_BYTES:
            raise ValueError('workspace_too_large')
        files[path] = digest(data)
    return files


def read_file(root: Path, path: str, start: int = 1, end: int | None = None) -> Record:
    if end is None and type(start) is int:
        end = start + 199
    if type(start) is not int or type(end) is not int or start < 1 or end < start:
        raise ValueError('invalid_line_range')
    raw = _read(root, path)
    lines = raw.decode('utf-8').splitlines(keepends=True)
    text, truncated = _clip(''.join(lines[start - 1:end]))
    return dict(text=text, start_line=start, end_line=min(end, len(lines)),
                total_lines=len(lines), version=digest(raw), truncated=truncated)


def search(root: Path, query: str, directory: str = '.') -> Record:
    if not isinstance(query, str) or not query or len(query) > 256:
        raise ValueError('invalid_query')
    result = {'matches': [], 'truncated': False}
    for path in _files(root, directory):
        try:
            text = _read(root, path).decode('utf-8')
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if query not in line:
                continue
            snippet, clipped = _clip(line, 1024)
            item = {'path': path, 'line': number, 'text': snippet}
            result['matches'].append(item)
            result['truncated'] |= clipped
            if len(json.dumps(result, ensure_ascii=False).encode()) > MAX_OUTPUT_BYTES:
                result['matches'].pop()
                result['truncated'] = True
                return result
    return result


def writable(path: str) -> bool:
    return path == 'src/linkcheck.py' or re.fullmatch(r'tests/test_agent_[A-Za-z0-9_]+\.py', path) is not None


def prepare_patch(root: Path, call: Record) -> Record:
    call = validate_call(call)
    if call['name'] != 'apply_patch':
        raise ValueError('not_a_patch')
    args = call['arguments']
    name = args['path']
    target = safe_path(root, name)
    if not writable(name):
        raise ValueError('write_denied')
    files = workspace_manifest(root)
    before_hash = files.get(name, 'absent')
    if args['version'] != before_hash:
        raise ValueError('stale_version')
    if before_hash == 'absent':
        if not name.startswith('tests/test_agent_') or args['old'] or not target.parent.is_dir():
            raise ValueError('write_denied')
        replacement = args['new'].encode('utf-8')
    else:
        current = _read(root, name)
        old = args['old'].encode('utf-8')
        if not old or current.count(old) != 1:
            raise ValueError('non_unique_match')
        replacement = current.replace(old, args['new'].encode('utf-8'), 1)
    if len(replacement) > MAX_FILE_BYTES:
        raise ValueError('file_too_large')
    after_hash = digest(replacement)
    if before_hash == after_hash:
        raise ValueError('no_op_patch')
    after_files = dict(files, **{name: after_hash})
    return dict(path=name, before_hash=before_hash, after_hash=after_hash,
        old=args['old'], new=args['new'], workspace_hash=manifest_hash(files),
        before_files=files, after_files=after_files,
        action_id=digest(json.dumps(call, sort_keys=True).encode()))


def write_patch(root: Path, patch: Record) -> Record:
    """Low-level operation. Caller owns the lock and exact-action approval."""
    name = patch['path']
    if not writable(name):
        raise ValueError('write_denied')
    target = safe_path(root, name)
    files = workspace_manifest(root)
    if files != patch['before_files'] or manifest_hash(files) != patch['workspace_hash']:
        raise ValueError('workspace_changed')
    current = _read(root, name) if patch['before_hash'] != 'absent' else b''
    if patch['before_hash'] == 'absent':
        data = patch['new'].encode('utf-8')
    else:
        old = patch['old'].encode('utf-8')
        if not old or current.count(old) != 1:
            raise ValueError('non_unique_match')
        data = current.replace(old, patch['new'].encode('utf-8'), 1)
    if digest(data) != patch['after_hash'] or len(data) > MAX_FILE_BYTES:
        raise ValueError('intent_mismatch')
    # Stage outside candidate directory; model tools cannot see control data.
    control = control_path(root)
    control.mkdir(exist_ok=True)
    descriptor, staged_name = tempfile.mkstemp(prefix='patch-', dir=control)
    staged = Path(staged_name)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        safe_path(root, name)
        if workspace_manifest(root) != files:
            raise ValueError('workspace_changed')
        os.replace(staged, target)
    finally:
        staged.unlink(missing_ok=True)
    return dict(path=name, version=patch['after_hash'],
                workspace_hash=manifest_hash(workspace_manifest(root)),
                diff=''.join(difflib.unified_diff(current.decode().splitlines(keepends=True),
                    data.decode().splitlines(keepends=True), f'a/{name}', f'b/{name}')))


def show_diff(root: Path) -> Record:
    baseline = json.loads((control_path(root) / 'baseline.json').read_text(encoding='utf-8'))
    files = workspace_manifest(root)
    paths = [name for name in sorted(files.keys() | baseline['files'].keys())
             if writable(name) and files.get(name) != baseline['files'].get(name)]
    chunks = []
    for name in paths:
        before = baseline['text'].get(name, '')
        after = _read(root, name).decode('utf-8') if name in files else ''
        chunks.extend(difflib.unified_diff(before.splitlines(keepends=True),
            after.splitlines(keepends=True), f'a/{name}', f'b/{name}'))
    text, truncated = _clip(''.join(chunks))
    return dict(paths=paths, text=text, truncated=truncated)
