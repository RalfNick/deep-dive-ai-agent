"""Bounded execution backends for the chapter's deliberately small lab.

Only named presets can run.  ``trusted_local`` is reserved for the shipped
fixture and replay tests; model-directed execution must use ``container``.
"""
from __future__ import annotations

import codecs
import ctypes
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from typing import Iterable

from .contracts import Record
from .prepare import control_path

SANDBOX = Path(__file__).parent / "sandbox"
ACCEPTANCE = Path(__file__).parent / "acceptance"
IMAGE_LOCK = SANDBOX / "image-lock.json"
PRESETS = {"candidate_tests", "acceptance", "probe_output", "probe_sleep",
           "probe_child", "probe_env"}


def bounded_decode(chunks: Iterable[bytes], limit: int) -> Record:
    """Return valid UTF-8 text whose encoded form fits the byte budget."""
    if limit < 0:
        raise ValueError("invalid_output_limit")
    kept = bytearray()
    total = 0
    for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise TypeError("bytes_required")
        total += len(chunk)
        remaining = limit - len(kept)
        if remaining > 0:
            kept.extend(chunk[:remaining])
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    decoded = decoder.decode(bytes(kept), final=True)
    output: list[str] = []
    used = 0
    output_truncated = False
    for character in decoded:
        width = len(character.encode("utf-8"))
        if used + width > limit:
            output_truncated = True
            break
        output.append(character)
        used += width
    return {"text": "".join(output),
            "truncated": total > limit or output_truncated}


def _trusted_fixture(root: Path) -> None:
    if not root.is_dir() or not (control_path(root) / "baseline.json").is_file():
        raise ValueError("trusted_fixture_required")


def _preset_command(root: Path, preset: str) -> list[str]:
    if preset not in PRESETS:
        raise ValueError("unknown_preset")
    if preset == "candidate_tests":
        return [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"]
    if preset == "acceptance":
        runner = ACCEPTANCE / "runner.py"
        if not runner.is_file():
            raise RuntimeError("acceptance_unavailable")
        return [sys.executable, "-B", str(runner), "--workspace", str(root)]
    if preset == "probe_output":
        code = "import sys;sys.stdout.write('x'*200000);sys.stderr.write('y'*200000)"
    elif preset == "probe_sleep":
        code = "import time;time.sleep(5)"
    elif preset == "probe_env":
        code = "import os;print('OPENAI_API_KEY' in os.environ)"
    else:
        marker = str(root / "child-survived.txt")
        child = ("import pathlib,time;time.sleep(.5);"
                 f"pathlib.Path({marker!r}).write_text('survived',encoding='utf-8')")
        code = ("import subprocess,sys,time;"
                f"subprocess.Popen([sys.executable,'-c',{child!r}]);time.sleep(5)")
    return [sys.executable, "-B", "-c", code]


def _child_environment() -> dict[str, str]:
    env = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    # Python on Windows needs the system directory to find core DLLs.  No PATH,
    # API keys, HOME, proxy settings, or model credentials cross the boundary.
    for key in ("SystemRoot", "WINDIR"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


class _OutputCollector:
    def __init__(self, budget: int) -> None:
        self.budget = budget
        self.remaining = budget
        self.buffers: dict[str, list[bytes]] = {"stdout": [], "stderr": []}
        self.truncated = False
        self.lock = threading.Lock()

    def drain(self, name: str, stream: object) -> None:
        while True:
            chunk = stream.read(8192)  # type: ignore[attr-defined]
            if not chunk:
                return
            with self.lock:
                take = min(len(chunk), self.remaining)
                if take:
                    self.buffers[name].append(chunk[:take])
                    self.remaining -= take
                if take < len(chunk):
                    self.truncated = True


def _windows_process_tree(parent_pid: int) -> list[int]:
    """Snapshot descendants before terminating their parent (Windows only)."""
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", wintypes.LONG), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", wintypes.WCHAR * 260)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid = ctypes.c_void_p(-1).value
    if snapshot == invalid:
        return []
    relations: dict[int, list[int]] = {}
    entry = ProcessEntry()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        present = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        while present:
            relations.setdefault(int(entry.th32ParentProcessID), []).append(
                int(entry.th32ProcessID))
            present = bool(kernel32.Process32NextW(snapshot, ctypes.byref(entry)))
    finally:
        kernel32.CloseHandle(snapshot)
    descendants: list[int] = []
    pending = list(relations.get(parent_pid, []))
    while pending:
        pid = pending.pop()
        descendants.append(pid)
        pending.extend(relations.get(pid, []))
    return descendants


def _terminate_windows_pid(pid: int) -> None:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    handle = kernel32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
    if handle:
        try:
            kernel32.TerminateProcess(handle, 1)
        finally:
            kernel32.CloseHandle(handle)


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        # ``taskkill /T`` can be denied in constrained hosts even for our own
        # child.  Enumerate descendants while the parent relation still exists,
        # then terminate deepest-first with process handles we own.
        descendants = _windows_process_tree(process.pid)
        for pid in reversed(descendants):
            _terminate_windows_pid(pid)
        process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _execute(command: list[str], cwd: Path, timeout_seconds: float,
             output_bytes: int, cancel: threading.Event) -> Record:
    if timeout_seconds < 0 or output_bytes < 0:
        raise ValueError("invalid_execution_limit")
    start = time.monotonic()
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(command, cwd=cwd, env=_child_environment(),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=creationflags, start_new_session=os.name != "nt")
    collector = _OutputCollector(output_bytes)
    readers = [threading.Thread(target=collector.drain, args=(name, stream), daemon=True)
               for name, stream in (("stdout", process.stdout), ("stderr", process.stderr))]
    for reader in readers:
        reader.start()

    deadline = start + timeout_seconds
    cancelled = timed_out = False
    while process.poll() is None:
        now = time.monotonic()
        # Record both facts when they become observable together; cancellation
        # determines the terminal reason below.
        cancelled = cancelled or cancel.is_set()
        timed_out = timed_out or now >= deadline
        if cancelled or timed_out:
            _kill_tree(process)
            break
        time.sleep(min(.02, max(0.001, deadline - now)))
    process.wait()
    for reader in readers:
        reader.join(timeout=2)

    stdout = bounded_decode(collector.buffers["stdout"], output_bytes)["text"]
    stderr_budget = max(0, output_bytes - len(b"".join(collector.buffers["stdout"])))
    stderr = bounded_decode(collector.buffers["stderr"], stderr_budget)["text"]
    combined = stdout + "\n" + stderr
    found = re.search(r"Ran\s+(\d+)\s+tests?", combined)
    discovered = int(found.group(1)) if found else None
    if discovered is None:
        diagnostic = None
    elif process.returncode == 0 and discovered > 0:
        diagnostic = "passed"
    elif process.returncode == 0:
        diagnostic = "zero_tests"
    else:
        diagnostic = "failed"
    reason = "cancelled" if cancelled else "timeout" if timed_out else None
    return {"returncode": process.returncode, "stdout": stdout, "stderr": stderr,
            "truncated": collector.truncated, "timed_out": timed_out,
            "cancelled": cancelled, "duration_seconds": time.monotonic() - start,
            "discovered": discovered, "diagnostic": diagnostic, "reason": reason}


def _image() -> str:
    lock = json.loads(IMAGE_LOCK.read_text(encoding="utf-8"))
    return f"{lock['image']}@{lock['digest']}"


def container_command(root: Path, preset: str, name: str,
                      runtime: str = "docker") -> list[str]:
    command = _preset_command(root, preset)
    if preset == "acceptance":
        command = ["python", "-B", "/acceptance/runner.py", "--workspace", "/work"]
    elif preset in {"candidate_tests", "probe_output", "probe_sleep", "probe_env"}:
        # The image has the same Python minor version; replace the host path.
        command[0] = "python"
    mount = f"{root.absolute()}:/work:rw"
    return [runtime, "run", "--rm", "--name", name, "--network", "none",
            "--read-only", "--user", "65534:65534", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "64",
            "--memory", "256m", "--cpus", "1", "--workdir", "/work",
            "--mount", f"type=bind,source={root.absolute()},target=/work",
            "--mount", f"type=bind,source={ACCEPTANCE.absolute()},target=/acceptance,readonly",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=32m", _image(), *command]


def probe_container() -> Record:
    lock = json.loads(IMAGE_LOCK.read_text(encoding="utf-8"))
    pinned = bool(re.fullmatch(r"sha256:[0-9a-f]{64}", lock.get("digest", "")))
    runtime = shutil.which("docker") or shutil.which("podman")
    if runtime is None:
        return {"available": False, "image_pinned": pinned,
                "isolation_passed": False, "runtime": None,
                "reason": "runtime_unavailable"}
    # Merely finding a binary is not evidence that all isolation properties hold.
    return {"available": True, "image_pinned": pinned,
            "isolation_passed": False, "runtime": runtime,
            "reason": "probes_not_run"}


def run_preset(root: Path, preset: str, backend: str, timeout_seconds: float,
               output_bytes: int, cancel: threading.Event) -> Record:
    root = Path(root).absolute()
    if preset not in PRESETS:
        raise ValueError("unknown_preset")
    _trusted_fixture(root)
    if backend == "trusted_local":
        return _execute(_preset_command(root, preset), root, timeout_seconds,
                        output_bytes, cancel)
    if backend != "container":
        raise ValueError("unknown_backend")
    facts = probe_container()
    if not facts["available"]:
        raise RuntimeError("container_unavailable")
    name = f"chapter12-{os.getpid()}-{time.monotonic_ns()}"
    command = container_command(root, preset, name, facts["runtime"])
    return _execute(command, root, timeout_seconds, output_bytes, cancel)
