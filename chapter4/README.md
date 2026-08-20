# 第 4 章实验：固定决策，观察 Harness 边界

本目录为《深入浅出 AI Agent》第 4 章提供五组可观察实验。所有实验都使用确定性的 `ScriptedModel`，不比较模型能力。贯穿实验固定任务、初始仓库、决策序列、工具参数和验收条件；最后一组“边界故障矩阵”由多个独立固定案例组成，不冒充严格单变量消融。

实验范围必须准确表述为：

> separate deterministic boundary cases; not a single-variable ablation, statistical rate, model quality, or SDK ranking

也就是说，这些实验可以验证权限、应用层路径守卫、检查点、审批、回执、Verifier 和 Trace 是否按合同工作，不能用于判断真实模型质量，也不能用于比较 Claude Code、Codex、SDK 或框架的强弱。

## 环境

- Python 3.11 或更高版本；
- 只使用 Python 标准库；
- 不需要模型 API Key；
- 不访问外部网络；
- 无随机性；
- 所有文件副作用都发生在系统临时目录，实验结束后自动清理。

## 一次运行全部测试

~~~powershell
python -m unittest discover -s chapter4/tests -v
~~~

当前 24 项回归测试覆盖契约序列化、策略顺序、路径守卫、检查点恢复、过期审批、Receipt 崩溃窗口、因果 Trace、完成验收、错误重试、取消、预算停止和边界故障矩阵。

## 五组实验

### 1. 能闭环的内联 Loop 为什么仍会误报完成

~~~powershell
python chapter4/experiments/inline_loop_demo.py
~~~

固定决策只有一句“问题已经修复，测试已经通过”。内联 Loop 把最终文本直接映射为 `completed`；组件化 Harness 把它视为完成候选，运行独立测试后进入 `failed_verification`。

### 2. 权限策略与执行边界不是同一层

~~~powershell
python chapter4/experiments/permissions_path_guard_demo.py
~~~

实验故意使用放宽的软策略，让 `../secret.txt` 写入提议得到 `allow`。随后应用层 `WorkspacePathGuard` 独立解析目标，结果为 `blocked`。它证明策略与路径执行守卫可以独立失败，但不等价于进程、网络和凭据均受限的 OS Sandbox。

### 3. 审批、退出、恢复与单次副作用

~~~powershell
python chapter4/experiments/approval_resume_demo.py
~~~

观察以下事件顺序：

~~~text
checkpoint_saved
approval_requested
waiting_approval
run_resumed
approval_granted
action_deduplicated
verification_started
verification
completed
~~~

实验先在 Receipt 落盘后、终态 Checkpoint 更新前注入崩溃，再创建新的 `HarnessRuntime` 从旧的 `WAITING_APPROVAL` 检查点恢复。恢复路径确实查询已有回执并发出 `action_deduplicated`，`patch-price` 的副作用计数仍为 1。第二个案例会在等待期间修改仓库，验证旧审批进入 `approval_stale` 且不会写入。

### 4. 超时、暂时错误、永久错误、取消与预算耗尽

~~~powershell
python chapter4/experiments/failure_semantics_demo.py
~~~

暂时错误和只读超时带有 `retryable=true`，各执行两次后继续；永久错误只执行一次并进入 `failed`；拒绝审批进入 `cancelled`；达到步数预算进入 `stopped`。这些状态不能压缩为一条“执行失败”。

### 5. 边界故障实验矩阵

~~~powershell
python chapter4/experiments/boundary_matrix_demo.py --output chapter4/reports/harness-boundary-matrix.json
~~~

报告分别给出：

- `accepted`：该案例是否被独立 Verifier 接受；
- `false_completed`：该案例是否声称完成但验收失败；
- `policy_violations`：敏感动作越过策略边界的次数；
- `duplicate_side_effects`：同一稳定动作重复提交的次数；
- `recovery_succeeded`：该案例是否从持久状态恢复；
- `trace_contract_passed`：该案例的事件序列是否满足本章 Trace 合同；
- `steps`：模型决策步数；
- `simulated_cost_units`：决策步数与工具尝试次数之和，只能解释案例内部；
- `sample_count`：每行固定为 1，明确这些结果不是统计率。

JSON 中的 `null` 表示该边界案例没有测量这个观察值，不代表 0。例如 Checkpoint 缺失案例测量能否恢复，并不同时声称测量了策略违规。图表用“—”显示这些不适用项。

不要把这些不同量纲重新平均成一个“总成功率”。某个变体可能通过测试，却同时发生重复副作用；单一分数会隐藏这种风险。

## 实验、结论与边界

| 实验 | 能支持的结论 | 不能支持的结论 |
| --- | --- | --- |
| 内联 Loop | 完成文本与外部验收是两个事件 | 真实模型一定会过早完成 |
| 权限与路径守卫 | 软策略和应用层执行守卫可以独立失败 | 教学路径检查等价于容器或 OS Sandbox |
| 审批与恢复 | 检查点、状态摘要和回执可覆盖本例的过期审批与 Receipt 崩溃窗口 | 文件回执等价于分布式 exactly-once |
| 故障语义 | 结构化错误决定重试和终态 | 所有超时都可以安全重试 |
| 边界故障矩阵 | 不同责任保护不同观察值 | 各行是同一轨迹的严格消融，或结果代表生产成功率 |

## 代码地图

| 文件 | 责任 |
| --- | --- |
| `harness/contracts.py` | 决策、调用、结果、事件、状态与验收证据 |
| `harness/policy.py` | 无隐藏内存的确定性决策脚本 |
| `harness/gateway.py` | 最小必填字段检查与 `deny -> ask -> allow` 策略 |
| `harness/path_guard.py` | 应用层路径规范化与工作区包含关系 |
| `harness/state.py` | JSON 检查点和稳定动作回执 |
| `harness/recorder.py` | 单调事件 ID、因果关系和 Trace 合同 |
| `harness/environment.py` | 临时仓库、真实测试进程、故障注入和副作用计数 |
| `harness/verifier.py` | 与模型自我报告独立的完成验收 |
| `harness/runtime.py` | 内联控制组与组件化可恢复 Harness |
| `harness/reporting.py` | 故障案例与单案例边界故障矩阵 |

## 已知限制

- `WorkspacePathGuard` 不是 Sandbox，不覆盖子进程、网络、凭据、Windows junction、符号链接竞态、挂载点和完整 TOCTOU；
- 检查点与回执是单机文件实现，不提供跨进程锁、分布式事务或业务系统幂等保证；
- 检查点提交与外部审批投递没有使用事务型 outbox，本章只验证进程内事件顺序；
- 状态摘要只覆盖教学仓库中的 Python 文件，不是完整 Git 树或外部依赖版本；
- 超时故障在工具执行前注入，没有模拟“副作用已经发生但响应丢失”的未知结果；
- `simulated_cost_units` 不是 Token、延迟或货币成本；
- `ScriptedModel` 隔离了模型随机性，因此不能证明真实模型是否会选择正确工具。

## 返回正文

- [第 4 章正文](../book/chapter4.md)
- [第 4 章参考答案](./reference-answers.md)
