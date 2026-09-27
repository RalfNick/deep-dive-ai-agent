# 第 13 章 v1.0 正式发布记录

发布日期：2026-09-27。正式标签：`book-chapter13-v1.0`。发布基线：[v1.0-rc2](chapter13-v1.0-rc2.md)；rc1 与 rc2 记录不改写。

## 发布内容

- 正文《Agent 评估：答案正确还不够》、12 个教学任务、120 条计分 Trial、7 幅图、5 组实验、14 道练习与答案；
- 同时评估 Outcome、Trajectory、安全和效率，区分环境错误与 Agent 失败；
- 包含 `pass@k`、`pass^k`、任务切片、成对 Bootstrap、Judge 校准和 `pass / fail / inconclusive` 发布门禁。

## 发布验证

- `python -B -m pytest chapter13/tests -q`：38 项通过；
- 两个独立输出目录的稳定报告逐字节一致；
- Draft 2020-12 JSON Schema、仓库合同、发布安全检查、Node 排版合同与 MkDocs strict 构建通过。

## 证据边界

固定任务和确定性策略只验证 Evaluation Harness 的合同，不衡量真实模型、Claude Code、Codex、OpenAI Evals、LangSmith 或 Inspect AI 的能力。教学 Bootstrap 不能消除任务选择偏差；Live Judge 未执行。
