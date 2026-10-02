# 第18章协作机制报告

固定策略教学案例，不是模型或SDK排名。

| 案例 | 状态 | 覆盖 | 工具调用 |
| --- | --- | --- | --- |
| single-sufficient | answer | 1/1 | 1 |
| parallel-separated | answer | 3/3 | 3 |
| serial-dependency | answer | 2/2 | 2 |
| duplicate-research | answer | 1/1 | 2 |
| delegation-return | answer | 1/1 | 1 |
| handoff-transfer | answer | 1/1 | 1 |
| context-not-forwarded | unknown | 0/1 | 1 |
| scope-escalation | blocked | 0/1 | 0 |
| source-version-conflict | conflict | 0/1 | 2 |
| same-source-three-votes | unknown | 1/2 | 3 |
| stale-patch | conflict | 0/1 | 5 |
| disjoint-patches | verified | 1/1 | 8 |
| one-worker-timeout | unknown | 1/2 | 2 |
| global-budget-exhausted | stopped | 0/1 | 6 |
| cancel-late-result | stopped | 0/1 | 3 |
| handoff-cycle | stopped | 0/1 | 0 |
| kb-verified-answer | answer | 1/1 | 1 |
| kb-permission-denied | blocked | 0/1 | 1 |
| repair-verified | verified | 1/1 | 5 |
| repair-needs-approval | needs_approval | 0/1 | 2 |

状态、覆盖、冲突、拒绝、写入与验收分别统计；不提供成功率总分。
