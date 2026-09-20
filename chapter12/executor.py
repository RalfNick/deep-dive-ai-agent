"""The only gateway from validated model calls to workspace operations."""
from __future__ import annotations

from pathlib import Path
import threading

from . import backends
from .contracts import Record, validate_call
from .tools import read_file, search, show_diff


def _result(call_id: str, ok: bool, data: Record | None = None,
            error: str | None = None, truncated: bool = False) -> Record:
    return {"call_id": call_id, "ok": ok, "data": data or {},
            "error": error, "truncated": truncated}


def dispatch(root: Path, call: Record, backend: str,
             cancel: threading.Event) -> Record:
    try:
        call = validate_call(call)
        name, arguments = call["name"], call["arguments"]
        if name == "read_file":
            data = read_file(root, **arguments)
            return _result(call["call_id"], True, data,
                           truncated=bool(data.get("truncated")))
        if name == "search":
            data = search(root, **arguments)
            return _result(call["call_id"], True, data,
                           truncated=bool(data.get("truncated")))
        if name == "show_diff":
            data = show_diff(root)
            return _result(call["call_id"], True, data,
                           truncated=bool(data.get("truncated")))
        if name == "run_tests":
            execution = backends.run_preset(root, arguments["preset"], backend,
                                             20, 65536, cancel)
            ok = (execution["returncode"] == 0 and not execution["timed_out"]
                  and not execution["cancelled"] and execution["diagnostic"] == "passed")
            return _result(call["call_id"], ok, execution,
                           None if ok else execution.get("reason") or "tests_failed",
                           bool(execution.get("truncated")))
        # Writes are prepared and approved by Services, never dispatched raw.
        return _result(call["call_id"], False, error="approval_required")
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        call_id = call.get("call_id") if isinstance(call, dict) else "invalid"
        return _result(call_id if isinstance(call_id, str) and call_id else "invalid",
                       False, error=str(error) or type(error).__name__)
