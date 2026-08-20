"""A minimal, observable Agent loop built only with Python's standard library.

The "model" is a deterministic policy so the experiment is reproducible and
requires no API key.  Replace ``RepairPolicy.decide`` with a model API call and
the model/runtime boundary remains the same.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


BROKEN_SOURCE = '''def parse_price(value: str) -> float:
    """Parse a decimal price."""
    return float(value)
'''

FIXED_SOURCE = '''def parse_price(value: str) -> float:
    """Parse a decimal price with an optional yuan symbol."""
    normalized = value.strip()
    if normalized.startswith(("\\uffe5", "\\u00a5")):
        normalized = normalized[1:]
    return float(normalized)
'''

TEST_SOURCE = '''import unittest

from pricing import parse_price


class ParsePriceTest(unittest.TestCase):
    def test_plain_decimal(self) -> None:
        self.assertEqual(parse_price("12.50"), 12.5)

    def test_full_width_yuan_symbol(self) -> None:
        self.assertEqual(parse_price("\\uffe519.90"), 19.9)


if __name__ == "__main__":
    unittest.main()
'''


@dataclass(frozen=True)
class ToolCall:
    """A model-proposed action. It has no side effect by itself."""

    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """The harness-owned observation linked to exactly one tool call."""

    call_id: str
    ok: bool
    content: str
    error_type: str | None = None
    retryable: bool = False
    state_changed: bool = False


@dataclass(frozen=True)
class VerificationResult:
    """Environment-owned evidence for accepting or rejecting completion."""

    accepted: bool
    rules: tuple[str, ...]
    command: tuple[str, ...]
    exit_code: int
    state_digest: str
    protected_files_unchanged: bool


@dataclass(frozen=True)
class Decision:
    """One policy decision: request a tool, propose final, or stop."""

    kind: str
    reason: str
    call: ToolCall | None = None
    final: str | None = None


@dataclass(frozen=True)
class Event:
    step: int
    kind: str
    data: dict[str, Any]


@dataclass
class RunResult:
    status: str
    final: str | None
    events: list[Event] = field(default_factory=list)

    @property
    def tool_calls(self) -> int:
        return sum(event.kind == "tool_call" for event in self.events)


class Policy(Protocol):
    def decide(self, events: list[Event]) -> Decision:
        """Choose the next action from the observable trajectory."""


class PriceRepo:
    """An isolated repository fixture with a real Python test process."""

    def __init__(
        self,
        *,
        pricing_source: str = BROKEN_SOURCE,
        test_source: str = TEST_SOURCE,
    ) -> None:
        self._temp = tempfile.TemporaryDirectory(prefix="chapter3-agent-")
        # Normalize once. On Windows, comparing an unresolved TemporaryDirectory
        # path with a resolved child path can reject an otherwise valid child.
        self.root = Path(self._temp.name).resolve()
        (self.root / "pricing.py").write_text(pricing_source, encoding="utf-8")
        (self.root / "test_pricing.py").write_text(test_source, encoding="utf-8")
        self._protected_hashes = {
            "test_pricing.py": self._file_digest(self.root / "test_pricing.py")
        }

    def close(self) -> None:
        self._temp.cleanup()

    def __enter__(self) -> "PriceRepo":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def state_digest(self) -> str:
        payload = "".join(
            path.name + "\0" + path.read_text(encoding="utf-8")
            for path in sorted(self.root.glob("*.py"))
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]

    def read_file(self, path: str) -> ToolResult:
        target = self._resolve(path)
        if not target.exists():
            return ToolResult("", False, f"not found: {path}", "not_found")
        return ToolResult("", True, target.read_text(encoding="utf-8"))

    def apply_patch(self, path: str, old: str, new: str) -> ToolResult:
        target = self._resolve(path)
        if not target.exists():
            return ToolResult("", False, f"not found: {path}", "not_found")
        source = target.read_text(encoding="utf-8")
        if source.count(old) != 1:
            return ToolResult(
                "", False, "old text must occur exactly once", "patch_conflict"
            )
        target.write_text(source.replace(old, new), encoding="utf-8")
        return ToolResult("", True, f"updated {path}", state_changed=True)

    @property
    def test_command(self) -> tuple[str, ...]:
        return (sys.executable, "-m", "unittest", "-v")

    def _run_test_process(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(self.test_command),
            cwd=self.root,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=10,
        )

    def run_tests(self) -> ToolResult:
        completed = self._run_test_process()
        output = (completed.stdout + completed.stderr).strip()
        return ToolResult(
            "",
            completed.returncode == 0,
            f"exit_code={completed.returncode}\n{output}",
            None if completed.returncode == 0 else "test_failure",
        )

    def execute(self, call: ToolCall) -> ToolResult:
        """Validate a call, execute it, and preserve the model's call_id."""
        before = self.state_digest()
        try:
            if call.name == "read_file":
                result = self.read_file(**call.arguments)
            elif call.name == "apply_patch":
                result = self.apply_patch(**call.arguments)
            elif call.name == "run_tests":
                if call.arguments:
                    raise TypeError("run_tests takes no arguments")
                result = self.run_tests()
            else:
                result = ToolResult(
                    "", False, f"unknown tool: {call.name}", "tool_not_found"
                )
        except subprocess.TimeoutExpired as error:
            result = ToolResult(
                "",
                False,
                f"tool exceeded {error.timeout}s timeout",
                "tool_timeout",
                retryable=True,
            )
        except (TypeError, ValueError) as error:
            result = ToolResult("", False, str(error), "invalid_arguments")
        after = self.state_digest()
        return ToolResult(
            call_id=call.call_id,
            ok=result.ok,
            content=result.content,
            error_type=result.error_type,
            retryable=result.retryable,
            state_changed=before != after,
        )

    def tests_pass(self) -> bool:
        """Convenience probe for examples that display a simple boolean."""
        return self.run_tests().ok

    def verify_completion(self) -> VerificationResult:
        """Run trusted tests and bind their result to the verified repo state."""
        completed = self._run_test_process()
        protected_files_unchanged = all(
            self._file_digest(self.root / name) == expected
            for name, expected in self._protected_hashes.items()
        )
        tests_passed = completed.returncode == 0
        rules = (
            "tests_passed" if tests_passed else "tests_failed",
            (
                "protected_files_unchanged"
                if protected_files_unchanged
                else "protected_files_changed"
            ),
        )
        return VerificationResult(
            accepted=tests_passed and protected_files_unchanged,
            rules=rules,
            command=self.test_command,
            exit_code=completed.returncode,
            state_digest=self.state_digest(),
            protected_files_unchanged=protected_files_unchanged,
        )

    @staticmethod
    def _file_digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate.parent != self.root:
            raise ValueError("path escapes the isolated workspace")
        return candidate


class RepairPolicy:
    """A deterministic stand-in that advances from structured observations."""

    @staticmethod
    def _call(
        events: list[Event], name: str, arguments: dict[str, Any]
    ) -> ToolCall:
        ordinal = 1 + sum(event.kind == "tool_call" for event in events)
        return ToolCall(f"call-{ordinal:02d}-{name}", name, arguments)

    @staticmethod
    def _is_only_target_failure(content: str) -> bool:
        if "test_full_width_yuan_symbol" not in content:
            return False
        summary = next(
            (
                line
                for line in reversed(content.splitlines())
                if line.startswith("FAILED")
            ),
            "",
        )
        failure_counts = [
            int(count)
            for _, count in re.findall(r"(failures|errors)=(\d+)", summary)
        ]
        return sum(failure_counts) == 1

    def decide(self, events: list[Event]) -> Decision:
        results = [event for event in events if event.kind == "tool_result"]
        if not results:
            return Decision(
                "tool",
                "先读取真实实现，避免按记忆猜测。",
                self._call(events, "read_file", {"path": "pricing.py"}),
            )

        latest = results[-1]
        latest_tool = latest.data.get("tool_name")

        if latest_tool == "read_file":
            if not latest.data["ok"]:
                return Decision("stop", "无法读取目标文件，停止自动修改。")
            test_results = [
                event
                for event in results
                if event.data.get("tool_name") == "run_tests"
            ]
            if test_results and self._is_only_target_failure(
                test_results[-1].data["content"]
            ):
                return Decision(
                    "tool",
                    "重新读取后按最新内容构造补丁。",
                    self._call(
                        events,
                        "apply_patch",
                        {
                            "path": "pricing.py",
                            "old": latest.data["content"],
                            "new": FIXED_SOURCE,
                        },
                    ),
                )
            return Decision(
                "tool",
                "先复现失败，获得环境证据。",
                self._call(events, "run_tests", {}),
            )

        if latest_tool == "run_tests":
            if latest.data["ok"]:
                return Decision(
                    "final",
                    "外部测试已通过。",
                    final="修复完成，2 项测试通过。",
                )
            if not self._is_only_target_failure(latest.data["content"]):
                return Decision(
                    "stop", "测试证据不只包含目标缺陷，停止自动修改。"
                )
            reads = [
                event
                for event in results
                if event.data.get("tool_name") == "read_file"
                and event.data["ok"]
            ]
            if not reads:
                return Decision(
                    "tool",
                    "缺少真实源码观察，重新读取。",
                    self._call(events, "read_file", {"path": "pricing.py"}),
                )
            return Decision(
                "tool",
                "失败与目标缺陷一致，按已读取内容修复。",
                self._call(
                    events,
                    "apply_patch",
                    {
                        "path": "pricing.py",
                        "old": reads[-1].data["content"],
                        "new": FIXED_SOURCE,
                    },
                ),
            )

        if latest_tool == "apply_patch":
            if latest.data["ok"]:
                return Decision(
                    "tool",
                    "修改后必须用同一验收方式复测。",
                    self._call(events, "run_tests", {}),
                )
            if latest.data["error_type"] == "patch_conflict":
                return Decision(
                    "tool",
                    "补丁前置条件失效，重新读取后再规划。",
                    self._call(events, "read_file", {"path": "pricing.py"}),
                )
            return Decision("stop", "补丁执行失败且不可恢复。")

        return Decision("stop", "收到无法解释的工具观察，停止自动执行。")


class AgentLoop:
    """The harness: it owns execution, budgets, verification, and trace data."""

    def __init__(
        self,
        environment: PriceRepo,
        *,
        max_steps: int = 8,
        max_same_action: int = 2,
        completion_verifier: Callable[[], VerificationResult] | None = None,
    ) -> None:
        self.environment = environment
        self.max_steps = max_steps
        self.max_same_action = max_same_action
        self.completion_verifier = completion_verifier

    def run(self, policy: Policy) -> RunResult:
        events: list[Event] = []
        signatures: Counter[str] = Counter()
        seen_call_ids: set[str] = set()

        for step in range(1, self.max_steps + 1):
            decision = policy.decide(events)
            events.append(Event(step, "decision", asdict(decision)))

            if decision.kind == "final":
                verification = (
                    VerificationResult(
                        accepted=True,
                        rules=("verifier_not_configured",),
                        command=(),
                        exit_code=0,
                        state_digest=self.environment.state_digest(),
                        protected_files_unchanged=True,
                    )
                    if self.completion_verifier is None
                    else self.completion_verifier()
                )
                state_unchanged = (
                    verification.state_digest == self.environment.state_digest()
                )
                verified = verification.accepted and state_unchanged
                events.append(
                    Event(
                        step,
                        "verification",
                        {
                            **asdict(verification),
                            "accepted": verified,
                            "state_unchanged_since_verification": state_unchanged,
                        },
                    )
                )
                if verified:
                    events.append(
                        Event(step, "run_finished", {"status": "completed"})
                    )
                    return RunResult("completed", decision.final, events)
                continue

            if decision.kind == "stop":
                events.append(Event(step, "run_finished", {"status": "failed"}))
                return RunResult("failed", None, events)

            if decision.kind != "tool" or decision.call is None:
                return RunResult("invalid_decision", None, events)

            call = decision.call
            signature = json.dumps(
                {"name": call.name, "arguments": call.arguments},
                ensure_ascii=False,
                sort_keys=True,
            )
            signatures[signature] += 1
            events.append(
                Event(
                    step,
                    "tool_call",
                    {"call_id": call.call_id, "name": call.name, "arguments": call.arguments},
                )
            )
            if call.call_id in seen_call_ids:
                duplicate_result = ToolResult(
                    call_id=call.call_id,
                    ok=False,
                    content="call_id must be unique within one run",
                    error_type="duplicate_call_id",
                    retryable=False,
                    state_changed=False,
                )
                events.append(
                    Event(
                        step,
                        "tool_result",
                        {**asdict(duplicate_result), "tool_name": call.name},
                    )
                )
                events.append(
                    Event(step, "guard_stop", {"reason": "duplicate_call_id"})
                )
                events.append(
                    Event(step, "run_finished", {"status": "duplicate_call_id"})
                )
                return RunResult("duplicate_call_id", None, events)
            seen_call_ids.add(call.call_id)
            if signatures[signature] > self.max_same_action:
                events.append(
                    Event(step, "guard_stop", {"reason": "repeated_action"})
                )
                return RunResult("repeated_action", None, events)

            result = self.environment.execute(call)
            events.append(
                Event(
                    step,
                    "tool_result",
                    {**asdict(result), "tool_name": call.name},
                )
            )

        events.append(Event(self.max_steps, "guard_stop", {"reason": "max_steps"}))
        return RunResult("max_steps", None, events)


def print_trace(result: RunResult) -> None:
    for event in result.events:
        if event.kind == "decision":
            print(f"[{event.step}] decide: {event.data['reason']}")
        elif event.kind == "tool_call":
            print(
                f"[{event.step}] call: {event.data['name']} "
                f"id={event.data['call_id']}"
            )
        elif event.kind == "tool_result":
            first_line = event.data["content"].splitlines()[0]
            print(
                f"[{event.step}] result: ok={event.data['ok']} "
                f"changed={event.data['state_changed']} {first_line}"
            )
        elif event.kind == "verification":
            print(
                f"[{event.step}] verify: accepted={event.data['accepted']} "
                f"rules={event.data['rules']}"
            )
        elif event.kind == "guard_stop":
            print(f"[{event.step}] stop: {event.data['reason']}")
    print(
        f"[run] status={result.status} calls={result.tool_calls} "
        f"final={result.final!r}"
    )


def main() -> None:
    with PriceRepo() as repo:
        print(f"[fixture] state_before={repo.state_digest()}")
        result = AgentLoop(
            repo, completion_verifier=repo.verify_completion
        ).run(RepairPolicy())
        print_trace(result)
        print(f"[fixture] state_after={repo.state_digest()}")
        assert result.status == "completed"
        assert repo.verify_completion().accepted


if __name__ == "__main__":
    main()
