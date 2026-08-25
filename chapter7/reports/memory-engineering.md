# 第 7 章记忆工程固定实验

- Schema：`1.0`
- 实验类型：`deterministic_boundary_conformance`
- 每案例样本数：`1`

## baseline

保存更多历史是否等于拥有更好的记忆？

| 变体 | 指标 | 证据 |
| --- | --- | --- |
| `no-memory` | language="JavaScript", confirm_public_api=false, unsafe_temporary_rule_used=false, task_accepted=false | decision:no-context |
| `full-transcript` | language="Python", confirm_public_api=true, unsafe_temporary_rule_used=true, task_accepted=false | transcript:item-count:4 |
| `structured-memory` | language="Python", confirm_public_api=true, unsafe_temporary_rule_used=false, task_accepted=true | recall:hit-count:2 |

## write

哪些候选信息值得跨任务保存？

| 变体 | 指标 | 证据 |
| --- | --- | --- |
| `write-everything` | write_precision=0.5, write_recall=1.0, sensitive_write_count=1, written_count=6 | write-gate:bypassed |
| `policy-gated` | write_precision=1.0, write_recall=0.666667, sensitive_write_count=0, written_count=2 | write:accepted:2 |
| `policy-plus-review` | write_precision=1.0, write_recall=1.0, sensitive_write_count=0, written_count=3 | review:approved:1 |

## recall

相似内容是否应该直接进入模型上下文？

| 变体 | 指标 | 证据 |
| --- | --- | --- |
| `global-scan` | recall_precision=0.4, cross_scope_leak_count=2, returned_count=5 | scope-filter:off, top-k:5 |
| `scoped-unranked` | recall_precision=0.5, cross_scope_leak_count=0, returned_count=4 | scope-filter:on, ranking:off |
| `scoped-ranked` | recall_precision=1.0, cross_scope_leak_count=0, returned_count=2 | scope-filter:on, ranking:on, top-k:2 |

## correct

新偏好与旧记忆冲突时能否解释变化过程？

| 变体 | 指标 | 证据 |
| --- | --- | --- |
| `overwrite` | audit_chain_complete=false, correction_converged=true | versions:retained:1 |
| `versioned` | audit_chain_complete=true, correction_converged=true | versions:retained:2, supersedes:linked |
| `stale-writer` | stale_write_rejected=true, duplicate_active_count=0 | compare-and-set:expected-record |

## forget

删除后陈旧索引和其他租户记录会不会重新进入上下文？

| 变体 | 指标 | 证据 |
| --- | --- | --- |
| `stale-index` | post_delete_leak_count=1, cross_scope_leak_count=0 | index:stale, store-resolution:off |
| `store-resolved` | post_delete_leak_count=0, cross_scope_leak_count=0 | index:stale, store-resolution:on, tombstone:present |
| `cross-tenant-probe` | post_delete_leak_count=0, cross_scope_leak_count=0 | tenant-filter:before-score |

## Non-claims

- 固定夹具不代表真实模型表现或生产成功率
- serialized_bytes 不是 Token 数
- 实验不比较 Claude Code、Codex、LangGraph 或 OpenAI Agents SDK 的整体能力
- 内存 Store 与单进程锁不等于分布式事务或合规删除系统
