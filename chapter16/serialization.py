"""Canonical finite JSON; hashes never depend on machine or wall clock."""
import dataclasses
import hashlib
import json
import math
from collections.abc import Mapping
from types import MappingProxyType

def freeze(value):
    if dataclasses.is_dataclass(value):
        return value
    if isinstance(value, Mapping):
        if not all(isinstance(k, str) for k in value):
            raise ValueError("JSON keys must be strings")
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze(v) for v in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite JSON")
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise ValueError("unsupported JSON value")

def plain(value):
    if dataclasses.is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(plain(v) for v in value)
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value

def canonical_bytes(value: object) -> bytes:
    return (json.dumps(plain(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")

def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def body_hash(value, field):
    data = plain(value)
    data.pop(field)
    return digest(data)
