# 第 12 章 v1.0 正式发布记录

发布日期：2026-09-27。正式标签：`book-chapter12-v1.0`。发布基线：[v1.0-rc2](chapter12-v1.0-rc2.md)；rc1 与 rc2 记录不改写。

## 发布内容

- 正文《手写一个 Mini Coding Agent》、7 幅原创教学图、5 组实验、14 道练习与参考答案；
- 从确定性 Replay 和最小 Loop 逐步实现工具合同、补丁准备、审批、恢复、上下文控制、Verifier 与 Trace；
- 真实加载 LangGraph、SQLite checkpointer 与 OpenAI Agents SDK，用薄适配器比较责任边界。

## 发布验证

- `python -B -m pytest chapter12/tests -q`：`210 passed`；
- 离线规范报告两次重建一致；仓库合同、发布安全检查、Node 排版合同与 MkDocs strict 构建通过；
- `offline-canonical.json`：`AFC9AB8544C6123D9FBB087238CA5C983B6FE0AC4C11D2AAAD90B1D8A672F5DB`（SHA-256）；
- `framework-comparison.json`：`0FF34EBDA6150297DEB4B24E14DAA62441A8CFA79026E4B33A59917EFFB69057`（SHA-256）；
- `exercise-results.json`：`B445B75D8FB4612AAEFBDEF3E8558F7A90D96442E986DB183685A798BB86E9C6`（SHA-256）。

## 证据边界

真实模型运行：未执行。容器隔离：未验证。生产隔离部分是理论合同与参考配置，不提供 Docker 实测结论。单仓库、单写者和小型 fixture 不能直接外推到大型代码库、分布式执行或敌对代码。
