from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping


def write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def write_markdown(path: Path, report: Mapping[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    groups = report["groups"]
    lines = [
        "# 第 9 章工具调用与 MCP 实验证据",
        "",
        "> 这是固定决策与固定 Fixture 的边界一致性实验，不是模型或产品能力比较。",
        "",
        f"- 固定时钟：`{report['fixed_clock']}`",
        f"- MCP 协议基线：`{report['protocol_revision']}`",
        f"- 教学 SDK：`{report['sdk']}`",
        "- 样本：20 个确定性单样本案例",
        "",
    ]
    for group_name, group in groups.items():
        lines.extend(
            [
                f"## {group_name}",
                "",
                "| 案例 | 版本 | 观察结果 | 证据类型 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for case in group["cases"]:
            versions = ", ".join(f"v{version}" for version in case["versions"])
            lines.append(
                f"| `{case['case_id']}` | {versions} | {case['observed']} | {case['evidence_kind']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 本实验没有测量什么",
            "",
            "真实模型质量、Provider Token、成本和网络延迟均未测量，对应机器字段保持 `null`。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda row: int(row["event_id"]))
    text = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in ordered
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    return path

