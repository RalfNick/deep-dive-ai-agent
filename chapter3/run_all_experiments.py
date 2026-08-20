"""Run all Chapter 3 experiments and publish bounded, local evidence."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


CHAPTER_DIR = Path(__file__).resolve().parent
REPORT_PATH = CHAPTER_DIR / "reports" / "experiment-results.json"
MAX_STDOUT_CHARS = 12_000
CANONICAL_GENERATED_AT = "2026-08-14T00:00:00Z"

EXPERIMENTS = {
    "one_shot_vs_loop": {
        "script": "one_shot_vs_loop.py",
        "proves": "生成候选与环境验收是两个不同事件。",
        "does_not_prove": "所有任务都必须使用 Agent Loop。",
    },
    "agent_loop": {
        "script": "agent_loop.py",
        "proves": "确定性策略可在受控运行时中完成观察、行动和验证闭环。",
        "does_not_prove": "该策略代表真实语言模型的任务能力。",
    },
    "loop_guards": {
        "script": "loop_guards_demo.py",
        "proves": "重复动作检测可以在步数耗尽前终止停滞。",
        "does_not_prove": "重复工具调用必然是错误。",
    },
    "tool_errors": {
        "script": "tool_error_demo.py",
        "proves": "同一幂等键可消解本地先提交后超时的不确定结果。",
        "does_not_prove": "本地字典等价于跨服务支付事务。",
    },
    "verifier": {
        "script": "verifier_demo.py",
        "proves": "外部验证可以拒绝没有环境证据的完成声明。",
        "does_not_prove": "单元测试覆盖全部用户意图。",
    },
    "trace_replay": {
        "script": "trace_replay_demo.py",
        "proves": "有序事件可审计调用关联并回放本地确定性状态变化。",
        "does_not_prove": "任意外部副作用都可安全回放。",
    },
}


def run_all(
    *,
    generated_at: str | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": generated_at or CANONICAL_GENERATED_AT,
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "experiments": {},
    }

    for name, contract in EXPERIMENTS.items():
        command = [sys.executable, contract["script"]]
        completed = subprocess.run(
            command,
            cwd=CHAPTER_DIR,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=30,
        )
        combined = (completed.stdout + completed.stderr).strip()
        report["experiments"][name] = {
            "command": ["python", contract["script"]],
            "exit_code": completed.returncode,
            "stdout": combined[-MAX_STDOUT_CHARS:],
            "proves": contract["proves"],
            "does_not_prove": contract["does_not_prove"],
        }

    if write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def main() -> None:
    report = run_all()
    failures = {
        name: item["exit_code"]
        for name, item in report["experiments"].items()
        if item["exit_code"] != 0
    }
    print(f"report={REPORT_PATH}")
    print(f"experiments={len(report['experiments'])} failures={failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
