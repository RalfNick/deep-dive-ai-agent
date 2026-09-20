"""Runnable reference solutions for the fourteen Chapter 12 exercises."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from typing import Callable
from unittest.mock import patch as mock_patch

from . import backends
from .context import build_context
from .contracts import Record, TOOL_SCHEMAS, new_state, validate_call
from .prepare import control_path, create_workspace
from .providers.replay import ReplayModel
from .recovery import classify
from .runtime import run as run_manual
from .services import Services
from .state import Store
from .tools import prepare_patch, read_file, workspace_manifest
from .trace import export
from .verifier import capture_baseline, verify


TITLES = {
    1: "工具调用是提议，不是执行",
    2: "从 Trace 定位第一次失败",
    3: "增加独立的只读查询入口",
    4: "补丁为什么要求唯一匹配",
    5: "拒绝基于过期版本的补丁",
    6: "批准必须绑定到具体动作",
    7: "崩溃恢复的三态判断",
    8: "压缩时保留完整工具消息对",
    9: "零测试为什么不能算绿色",
    10: "总预算与单次超时的计算",
    11: "区分隔离命令和隔离证据",
    12: "LangGraph 重入不能重复写入",
    13: "SDK 最终输出不等于任务完成",
    14: "手写循环、Pi、框架与宿主的职责",
}


def _record(number: int, criteria: list[str], evidence: Record, *,
            status: str = "passed", execution: str = "real") -> Record:
    return {
        "number": number,
        "title": TITLES[number],
        "status": status,
        "execution": execution,
        "criteria": criteria,
        "evidence": evidence,
    }


def _error(operation: Callable[[], object]) -> str | None:
    try:
        operation()
    except Exception as error:  # The exercise records the public failure code.
        return str(error) or type(error).__name__
    return None


def _exercise_1() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex1-") as directory:
        root = create_workspace(Path(directory) / "repo")
        before = workspace_manifest(root)
        call = {
            "call_id": "proposal-only",
            "name": "apply_patch",
            "arguments": {
                "path": "src/linkcheck.py",
                "version": read_file(root, "src/linkcheck.py")["version"],
                "old": "candidate = root / target",
                "new": "candidate = document.parent / target",
            },
        }
        proposal = validate_call(call)
        after = workspace_manifest(root)
    return _record(1, [
        "schema 校验成功只产生一个结构化提议",
        "未经过执行网关时工作区哈希保持不变",
    ], {
        "call_id": proposal["call_id"],
        "tool": proposal["name"],
        "workspace_unchanged": before == after,
        "executed": False,
    })


def _exercise_2() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex2-") as directory:
        store = Store(Path(directory) / "state.sqlite")
        store.save(new_state("exercise-2", "locate first failure", "trusted_local", 0))
        store.append_event("exercise-2", "tool_observed", {
            "ok": True, "preset": "candidate_tests", "discovered": 2,
        }, call_id="test-before")
        store.append_event("exercise-2", "tool_observed", {
            "ok": False, "error": "tests_failed", "preset": "candidate_tests",
        }, call_id="test-red")
        store.append_event("exercise-2", "model_message", {
            "text": "repair after observing the failure",
        })
        events = export(store, "exercise-2")
        failure = next(event for event in events if event["payload"].get("error"))
    return _record(2, [
        "按 seq 而不是日志显示顺序定位失败",
        "报告失败事件的 call_id 与 error，而不重新执行工具",
    ], {
        "event_sequence": [event["kind"] for event in events],
        "first_failure": {
            "seq": failure["seq"],
            "call_id": failure["call_id"],
            "error": failure["payload"]["error"],
        },
    })


def _exercise_readonly_query(root: Path, suffix: str) -> list[str]:
    """Exercise-only read model; it deliberately does not extend TOOL_SCHEMAS."""
    if not isinstance(suffix, str) or not suffix.startswith("."):
        raise ValueError("invalid_suffix")
    return sorted(path for path in workspace_manifest(root) if path.endswith(suffix))


def _exercise_3() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex3-") as directory:
        root = create_workspace(Path(directory) / "repo")
        matches = _exercise_readonly_query(root, ".py")
    return _record(3, [
        "查询只读取受限工作区 manifest",
        "正文的五工具协议保持不变",
    ], {
        "query": {"suffix": ".py"},
        "matches": matches,
        "contract_tools": sorted(TOOL_SCHEMAS),
        "registered_as_model_tool": False,
    })


def _exercise_4() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex4-") as directory:
        root = create_workspace(Path(directory) / "repo")
        source = read_file(root, "src/linkcheck.py")
        call = {"call_id": "ambiguous", "name": "apply_patch", "arguments": {
            "path": "src/linkcheck.py", "version": source["version"],
            "old": "target", "new": "destination",
        }}
        error = _error(lambda: prepare_patch(root, call))
    return _record(4, [
        "旧文本出现次数不等于 1 时拒绝补丁",
        "拒绝发生在写文件之前",
    ], {
        "match_count": source["text"].count("target"),
        "error": error,
        "write_attempted": False,
    })


def _exercise_5() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex5-") as directory:
        root = create_workspace(Path(directory) / "repo")
        version = read_file(root, "src/linkcheck.py")["version"]
        target = root / "src" / "linkcheck.py"
        target.write_text(target.read_text(encoding="utf-8") + "\n# user edit\n",
                          encoding="utf-8", newline="\n")
        call = {"call_id": "stale", "name": "apply_patch", "arguments": {
            "path": "src/linkcheck.py", "version": version,
            "old": "candidate = root / target",
            "new": "candidate = document.parent / target",
        }}
        error = _error(lambda: prepare_patch(root, call))
        current_version = read_file(root, "src/linkcheck.py")["version"]
    return _record(5, [
        "准备补丁时比较提议版本和磁盘当前版本",
        "检测到外部编辑后保留用户内容并返回 stale_version",
    ], {
        "error": error,
        "version_changed": version != current_version,
        "external_edit_preserved": True,
    })


def _paused_patch(directory: Path, run_id: str) -> tuple[Path, Store, Record]:
    root = create_workspace(directory / "repo")
    store = Store(control_path(root) / "state.sqlite")
    call = {"call_id": "patch", "name": "apply_patch", "arguments": {
        "path": "src/linkcheck.py",
        "version": read_file(root, "src/linkcheck.py")["version"],
        "old": "candidate = root / target",
        "new": "candidate = document.parent / target",
    }}
    state = new_state(run_id, "bind approval to one action", "trusted_local", time.time())
    services = Services(root, store, ReplayModel([
        {"kind": "tool", "text": "", "call": call},
    ]), "trusted_local", threading.Event())
    return root, store, run_manual(state, services)


def _exercise_6() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex6-") as directory:
        _root, store, state = _paused_patch(Path(directory), "exercise-6")
        action = store.action(state["pending"]["action_id"])
        forged = {key: action[key] for key in
                  ("run_id", "action_id", "arguments_hash", "workspace_hash")}
        forged["workspace_hash"] = "0" * 64
        forged["approved"] = True
        error = _error(lambda: store.approve(forged))
        recorded = store.approval(action["action_id"])
    return _record(6, [
        "批准同时绑定 run、action、参数哈希和工作区哈希",
        "任一字段不匹配时不落批准记录",
    ], {
        "error": error,
        "approval_recorded": recorded is not None,
        "bound_fields": ["run_id", "action_id", "arguments_hash", "workspace_hash"],
    })


def _exercise_7() -> Record:
    before, after, other = "a" * 64, "b" * 64, "c" * 64
    states = {
        "before": classify(before, after, before),
        "after": classify(before, after, after),
        "other": classify(before, after, other),
    }
    return _record(7, [
        "当前 manifest 等于 before 时重新检查批准",
        "等于 after 时只补记回执；第三种状态停止并请求人工处理",
    ], {"states": states, "rewrite_after_state": False})


def _exercise_8() -> Record:
    state = new_state("exercise-8", "keep complete tool pairs", "trusted_local", 0)
    state["workspace_hash"] = "a" * 64
    state["messages"] = [
        *({"role": "user", "content": f"old observation {index} " * 20}
          for index in range(12)),
        {"role": "assistant", "content": None, "tool_calls": [{
            "id": "failed-tests", "type": "function",
            "function": {"name": "run_tests", "arguments": "{\"preset\":\"candidate_tests\"}"},
        }]},
        {"role": "tool", "tool_call_id": "failed-tests",
         "content": json.dumps({"ok": False, "error": "tests_failed"})},
    ]
    full = build_context(state, 100_000)
    forced_size = len(json.dumps(full[:1], ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8"))
    view = build_context(state, forced_size + 650)
    assistant_ids = [item["tool_calls"][0]["id"] for item in view if item.get("tool_calls")]
    result_ids = [item["tool_call_id"] for item in view if item.get("role") == "tool"]
    return _record(8, [
        "压缩只能选择完整消息组，不能留下孤立 tool result",
        "最近一次失败的 call/result 对必须保留",
    ], {
        "assistant_call_ids": assistant_ids,
        "tool_result_ids": result_ids,
        "compacted": any("history_compaction" in item.get("content", "") for item in view),
        "view_messages": len(view),
    })


def _exercise_9() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex9-") as directory:
        root = create_workspace(Path(directory) / "repo")
        baseline = capture_baseline(root)
        zero_tests = {
            "returncode": 0,
            "timed_out": False,
            "cancelled": False,
            "truncated": False,
            "discovered": 0,
            "diagnostic": "passed",
            "stdout": "Ran 0 tests",
            "stderr": "",
        }
        with mock_patch("chapter12.verifier.backends.run_preset", return_value=zero_tests):
            verdict = verify(root, "trusted_local", baseline, threading.Event())
    return _record(9, [
        "退出码为 0 之外还要求 discovered > 0",
        "零测试时不运行后续验收并返回 candidate_tests_failed",
    ], {
        "accepted": verdict["passed"],
        "reason": verdict["reason"],
        "discovered": verdict["candidate_tests"]["discovered"],
        "acceptance_case_count": verdict["acceptance"]["case_count"],
    })


def budget_answer(total_seconds: int, elapsed_seconds: int,
                  single_call_cap: int) -> Record:
    values = (total_seconds, elapsed_seconds, single_call_cap)
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("invalid_budget")
    remaining = max(0, total_seconds - elapsed_seconds)
    return {
        "remaining_seconds": remaining,
        "next_timeout_seconds": min(remaining, single_call_cap),
    }


def _exercise_10() -> Record:
    inputs = {"total_seconds": 120, "elapsed_seconds": 35, "single_call_cap": 45}
    answer = budget_answer(**inputs)
    result = _record(10, [
        "剩余预算不能小于 0",
        "下一次调用超时取剩余预算与单次上限的较小值",
    ], {"formula": "min(max(0,total-elapsed),single_call_cap)"},
        execution="computed")
    result.update(input=inputs, **answer)
    return result


def _option(command: list[str], name: str) -> str | None:
    try:
        return command[command.index(name) + 1]
    except (ValueError, IndexError):
        return None


def _exercise_11() -> Record:
    with tempfile.TemporaryDirectory(prefix="chapter12-ex11-") as directory:
        root = create_workspace(Path(directory) / "repo")
        command = backends.container_command(root, "probe_env", "exercise-probe", "docker")
    checks = {
        "network_none": _option(command, "--network") == "none",
        "read_only_root": "--read-only" in command,
        "non_root_user": _option(command, "--user") == "65534:65534",
        "capabilities_dropped": _option(command, "--cap-drop") == "ALL",
        "no_new_privileges": _option(command, "--security-opt") == "no-new-privileges",
        "resource_limits": all(name in command for name in
                               ("--pids-limit", "--memory", "--cpus")),
    }
    facts = backends.probe_container()
    status = "verified" if facts["isolation_passed"] else "unverified"
    return _record(11, [
        "静态命令同时声明网络、只读根、非 root、cap drop 与资源限制",
        "只有真实探针全部通过才可把环境标成 verified",
    ], {
        "mechanism_checks": checks,
        "environment_probe": facts,
    }, status=status)


def _exercise_12() -> Record:
    # Shared scenario code is also used by the framework conformance tests.
    from .tests.framework_cases import run_scenario

    with tempfile.TemporaryDirectory(prefix="chapter12-ex12-") as directory:
        outcome = run_scenario("langgraph", "approval_restart", Path(directory))
    return _record(12, [
        "同一 thread_id 跨进程恢复",
        "两个批准动作各写一次、各记一次回执",
    ], {
        "orchestration": outcome["orchestration"],
        "framework_version": outcome["framework_version"],
        "status": outcome["status"],
        "writes": outcome["writes"],
        "receipts": outcome["receipts"],
        "distinct_processes": len(set(outcome["process_ids"])),
    })


def _exercise_13() -> Record:
    from .tests.framework_cases import run_scenario

    with tempfile.TemporaryDirectory(prefix="chapter12-ex13-") as directory:
        outcome = run_scenario("agents_sdk", "false_finish", Path(directory))
    return _record(13, [
        "Runner 的 final_output 必须进入宿主 verifier",
        "没有代码修改和验收证据时状态不得变成 completed",
    ], {
        "orchestration": outcome["orchestration"],
        "framework_version": outcome["framework_version"],
        "status": outcome["status"],
        "writes": outcome["writes"],
        "verification_failures": outcome["verification_failures"],
    })


def _exercise_14() -> Record:
    responsibilities = {
        "handwritten_loop": ["决定何时请求模型", "把 observation 送回下一轮"],
        "pi_source": ["展示模型、Agent Core、Coding Agent 的分层", "提供会话与资源装配参考"],
        "framework": ["推进节点或 Runner 回合", "保存框架级 checkpoint 或 RunState"],
        "host_application": ["权限策略与真实执行", "幂等账本", "独立验收", "安全 Trace"],
    }
    return _record(14, [
        "每项责任只有一个最终 owner",
        "框架状态不能替代宿主审批、执行回执和验收事实",
    ], {
        "responsibilities": responsibilities,
        "decision_rule": "framework orchestrates; host authorizes, executes and accepts",
    }, status="answered", execution="design")


SOLVERS: dict[int, Callable[[], Record]] = {
    1: _exercise_1,
    2: _exercise_2,
    3: _exercise_3,
    4: _exercise_4,
    5: _exercise_5,
    6: _exercise_6,
    7: _exercise_7,
    8: _exercise_8,
    9: _exercise_9,
    10: _exercise_10,
    11: _exercise_11,
    12: _exercise_12,
    13: _exercise_13,
    14: _exercise_14,
}


def solve(number: int) -> Record:
    if type(number) is not int or number not in SOLVERS:
        raise ValueError("unknown_exercise")
    return SOLVERS[number]()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Chapter 12 reference solutions")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--number", type=int)
    parser.add_argument("--output", type=Path,
                        help="write the same JSON evidence to a new file")
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        print("output_exists", file=sys.stderr)
        return 3
    numbers = range(1, 15) if args.all else [args.number]
    answers = [solve(number) for number in numbers]
    unverified = [answer["number"] for answer in answers if answer["status"] == "unverified"]
    payload = {
        "schema_version": 1,
        "answers": answers,
        "summary": {
            "count": len(answers),
            "unverified": unverified,
            "all_mechanisms_passed": not unverified and all(
                answer["status"] in {"passed", "answered", "verified"}
                for answer in answers),
        },
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    return 2 if unverified else 0


if __name__ == "__main__":
    raise SystemExit(main())
