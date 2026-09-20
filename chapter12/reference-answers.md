# 第 12 章练习参考答案

这些答案不是“看起来合理”的文字解答。除第 10 题的纯计算和第 14 题的职责设计外，其余题目都会调用本章真实实现；第 12、13 题还会运行已安装的 LangGraph 1.2.11 与 OpenAI Agents SDK 0.20.0。

从仓库根目录运行全部答案：

```bash
python -B -m chapter12.exercise_solutions --all
```

当前机器没有可用容器运行时，因此第 11 题会得到 `unverified`，整个命令仍输出完整 JSON，但退出码为 `2`。这不是运行失败被吞掉，而是明确表示“机制检查通过，环境隔离尚未验证”。运行单题可使用：

```bash
python -B -m chapter12.exercise_solutions --number 6
```

若要保存机器生成、且不含工作目录和凭据的固定记录：

```bash
python -B -m chapter12.exercise_solutions --all --output chapter12/reports/exercise-results.json
```

输出文件已存在时命令会拒绝覆盖并返回 `3`。要重新生成，应先明确归档旧记录，而不是静默改写证据。

## 1. 工具调用是提议，不是执行

运行：

```bash
python -B -m chapter12.exercise_solutions --number 1
```

关键输出：

```json
{
  "call_id": "proposal-only",
  "tool": "apply_patch",
  "executed": false,
  "workspace_unchanged": true
}
```

`validate_call()` 只检查调用结构、工具名和参数约束，并返回防御性副本。它没有权限直接写文件。真正的写入还要依次经过补丁准备、策略判断、批准绑定、执行网关和回执记录。

错误答案是“模型生成了合法 `apply_patch`，所以补丁已经执行”。合法只说明提议可以进入下一道边界。它既不代表被允许，也不代表磁盘已改变。

本题只证明 schema 层不会产生副作用，不证明后续执行器安全。

## 2. 从 Trace 定位第一次失败

运行：

```bash
python -B -m chapter12.exercise_solutions --number 2
```

关键输出应包含：

```json
{
  "event_sequence": ["tool_observed", "tool_observed", "model_message"],
  "first_failure": {
    "seq": 2,
    "call_id": "test-red",
    "error": "tests_failed"
  }
}
```

定位故障时先按 `seq` 恢复因果顺序，再找第一条带显式 `error` 的 observation。这里失败属于 `test-red`，后面的模型消息只是对失败的反应，不能倒过来当成根因。

Trace 是观察接口，不是重放脚本。读取 Trace 不应再次执行测试或工具，否则“排查问题”本身会制造新副作用。

## 3. 增加独立的只读查询入口

运行：

```bash
python -B -m chapter12.exercise_solutions --number 3
```

练习入口按照后缀查询工作区 manifest，返回 Python 文件；同时输出正文合同中的五个工具：

```text
apply_patch, read_file, run_tests, search, show_diff
```

这里没有把临时练习能力塞进 `TOOL_SCHEMAS`。原因是“读者练习需要一个查询函数”和“模型长期拥有一个新工具”是两件事。后一项会改变协议、提示词、权限面和全部适配器测试，不能作为练习的隐式副作用。

如果要把它升级为正式模型工具，应新增 schema、结果合同、路径限制、输出上限、Trace 字段和框架适配测试，而不是只在 dispatcher 里加一个分支。

## 4. 补丁为什么要求唯一匹配

运行：

```bash
python -B -m chapter12.exercise_solutions --number 4
```

固定 fixture 中 `target` 出现 6 次。用它作为 `old` 文本准备补丁，会返回：

```json
{
  "match_count": 6,
  "error": "non_unique_match",
  "write_attempted": false
}
```

如果补丁只说“把 `target` 改成 `destination`”，执行器无法知道模型指的是变量、参数还是字符串处理逻辑。自动选择第一次出现会让偶然的文本顺序决定语义。

唯一匹配不是万能补丁算法，却是一个可解释的最小安全合同：零次说明上下文过期，多次说明意图有歧义，恰好一次才允许进入准备阶段。

## 5. 拒绝基于过期版本的补丁

运行：

```bash
python -B -m chapter12.exercise_solutions --number 5
```

解答先读取 `src/linkcheck.py` 的 SHA-256 版本，再模拟用户添加一行，最后用旧版本准备补丁。关键输出是：

```json
{
  "error": "stale_version",
  "version_changed": true,
  "external_edit_preserved": true
}
```

正确行为不是覆盖用户的新内容，也不是偷偷重新读取后套用旧补丁。旧版本证明模型的提议基于已经失效的事实，必须回到“重新观察—重新提议”。

版本比较解决的是失效观察，不解决语义合并。真正需要合并时，应生成新的差异、再次检查并重新批准。

## 6. 批准必须绑定到具体动作

运行：

```bash
python -B -m chapter12.exercise_solutions --number 6
```

本题先让真实手写 runtime 运行到 `awaiting_approval`，再把批准中的 `workspace_hash` 换成伪造值。结果是：

```json
{
  "error": "approval_mismatch",
  "approval_recorded": false,
  "bound_fields": ["run_id", "action_id", "arguments_hash", "workspace_hash"]
}
```

“允许写文件”过于宽泛。一个批准只能授权某次运行中、某组参数、针对某个工作区快照的具体动作。路径相同但内容或参数变化后，旧批准都应失效。

这也是为什么不能设计“本轮全部允许”作为默认恢复策略：进程退出后，模型可能提出了另一个看似相同但实际不同的调用。

## 7. 崩溃恢复的三态判断

运行：

```bash
python -B -m chapter12.exercise_solutions --number 7
```

对持久化动作的 `before_hash`、预期 `after_hash` 和恢复时 `current_hash`，只有三种结论：

| 当前状态 | 结论 | 下一步 |
| --- | --- | --- |
| 等于 before | `recheck_approval` | 确认批准仍有效，再执行一次 |
| 等于 after | `record_receipt` | 不再写文件，只补记回执 |
| 两者都不等 | `uncertain` | 停止，标记批准过期并请求人工处理 |

第三种状态不能“尽量重放”。它可能来自用户编辑、另一个进程、部分外部操作或未经记录的变化。自动覆盖会把恢复机制变成数据破坏机制。

本章覆盖的是合作式单写者和命名崩溃窗口，不宣称能抵抗恶意进程在检查之间反复修改文件。

## 8. 压缩时保留完整工具消息对

运行：

```bash
python -B -m chapter12.exercise_solutions --number 8
```

关键输出：

```json
{
  "assistant_call_ids": ["failed-tests"],
  "tool_result_ids": ["failed-tests"],
  "compacted": true
}
```

上下文压缩的单位不是任意单条消息，而是完整语义组。assistant 提出 tool call 后，对应 tool result 必须一起保留或一起移除。否则模型会看到“调用却没有结果”或“结果找不到调用”的非法历史。

本题还保留最近一次失败的完整消息对，因为失败说明下一步修复最需要它。权威目标、审批和验证事实则由强制状态摘要单独提供，不依赖聊天历史是否被压缩。

这里采用字节预算，不等同于任一模型的 tokenizer 精确计数。

## 9. 零测试为什么不能算绿色

运行：

```bash
python -B -m chapter12.exercise_solutions --number 9
```

本题把候选测试结果设为“退出码 0、诊断 passed、发现 0 个测试”，再交给真实 verifier。输出为：

```json
{
  "accepted": false,
  "reason": "candidate_tests_failed",
  "discovered": 0,
  "acceptance_case_count": 0
}
```

没有测试失败，可能只是没有收集到测试。Verifier 因而同时要求：进程正常退出、没有超时/取消/截断、诊断为 passed，并且 `discovered > 0`。前置条件不满足时，独立验收不会继续运行。

这道题防止的是“空测试集假绿”，不保证已有测试覆盖全部需求。

## 10. 总预算与单次超时的计算

题目输入：总预算 120 秒，已用 35 秒，单次调用上限 45 秒。

```text
remaining = max(0, 120 - 35) = 85
next_timeout = min(85, 45) = 45
```

运行：

```bash
python -B -m chapter12.exercise_solutions --number 10
```

输出中的 `remaining_seconds` 应为 85，`next_timeout_seconds` 应为 45。若已用时间为 50 秒、总预算只有 30 秒，两者都应归零，不能得到负超时。

单次超时不能替代总预算：每次调用都在 45 秒内完成，仍可能通过无限重试耗尽整台机器。

## 11. 区分隔离命令和隔离证据

运行：

```bash
python -B -m chapter12.exercise_solutions --number 11
```

解答分两部分：

1. 机制检查确认命令声明了 `--network none`、只读根文件系统、非 root 用户、`cap-drop ALL`、`no-new-privileges`、进程/内存/CPU 限制；
2. 环境探针检查本机是否存在运行时，以及真实隔离探针是否执行并全部通过。

当前固定输出为：

```json
{
  "available": false,
  "image_pinned": true,
  "isolation_passed": false,
  "reason": "runtime_unavailable"
}
```

所以本题状态必须是 `unverified`，`--all` 返回 2。一个看起来正确的 Docker 命令只能证明设计意图，不能证明镜像实际以非 root 运行、网络确实不可达或取消后没有残留容器。

用户已决定暂不安装容器运行时，因此正确做法是保留未验证状态，不改用 `trusted_local` 冒充隔离实验。

## 12. LangGraph 重入不能重复写入

运行：

```bash
python -B -m chapter12.exercise_solutions --number 12
```

这不是模拟图。解答使用真实 `StateGraph`、`interrupt()` 与 `SqliteSaver`，并在多个新 Python 进程中完成两次批准和一次完成后重入检查。固定判据是：

```json
{
  "orchestration": "langgraph",
  "framework_version": "1.2.11",
  "status": "completed",
  "writes": 2,
  "receipts": 2,
  "distinct_processes": 4
}
```

LangGraph 恢复包含 `interrupt()` 的节点时会从节点开头重新执行。因此图节点必须把“提议/审批”和“真实执行”分开；宿主还要用 action id、manifest 和回执判断副作用是否已经发生。

SQLite checkpointer 保存图的推进位置，但不替代宿主的副作用账本。两者解决的是不同问题。

## 13. SDK 最终输出不等于任务完成

运行：

```bash
python -B -m chapter12.exercise_solutions --number 13
```

真实 Agents SDK Runner 收到的脚本化模型输出只有一句“已经完成”。SDK 正常产生 `final_output`，但宿主 verifier 找不到修改和验收证据，因此结果是：

```json
{
  "orchestration": "agents_sdk",
  "framework_version": "0.20.0",
  "status": "failed",
  "writes": 0,
  "verification_failures": 1
}
```

`final_output` 的含义是“Runner 这一轮得到了最终文本”，不是“软件任务满足验收条件”。完成状态只能由宿主基于独立证据决定。

同理，`RunState` 负责保存 SDK 的暂停/恢复信息，也不能替代工作区版本、批准绑定和写入回执。

## 14. 手写循环、Pi、框架与宿主的职责

运行：

```bash
python -B -m chapter12.exercise_solutions --number 14
```

一个可执行的职责划分如下：

| 层 | 应负责 | 不应被默认赋予 |
| --- | --- | --- |
| 手写 Loop | 何时请求模型、怎样把 observation 送回下一轮 | 自动获得持久化、安全和验收能力 |
| Pi 源码参考 | 展示 model API、Agent Core、Coding Agent 的分层，以及会话和资源装配方式 | 因为读过源码就声称运行过 Pi 或验证过产品效果 |
| LangGraph / Agents SDK | 推进图节点或 Runner 回合，保存 framework checkpoint / RunState | 成为权限、操作系统隔离或最终验收的唯一权威 |
| 宿主应用 | 权限策略、真实执行、批准绑定、幂等账本、独立验收和安全 Trace | 把模型文本当成完成证据 |

最短的判断规则是：

> 框架负责编排；宿主负责授权、执行和验收。

如果同一项关键责任同时由两层“都负责”，恢复时通常会发生重复执行；如果没有任何一层负责，则错误会被聊天文本掩盖。设计评审时应给每项关键事实指定唯一 owner 和持久化位置。

## 自检

运行答案测试：

```bash
python -B -m pytest chapter12/tests/test_exercises.py -q
```

它检查 14 个编号和判据、预算可复算、五工具合同未被练习污染、上下文消息成对、零测试不假绿、隔离未验证不假装成功，以及两个真实框架的关键边界。测试通过仍不补足被用户暂缓的容器实测和真实模型运行。
