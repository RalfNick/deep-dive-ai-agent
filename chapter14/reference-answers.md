# 第 14 章练习参考答案

这些答案给的是“怎样形成结论”的参考路径，而不是需要背诵的标准句式。第 2、3、5、6、14 题直接调用本章实现；其余设计题输出明确验收条件。先从仓库根目录运行：

```powershell
.\.venv\Scripts\Activate.ps1
python -B -m chapter14.exercise_solutions --all
```

运行单题使用 `--number 5`。要保存机器可检查结果，可添加 `--output chapter14/.runs/exercise-results.json`；目标存在时命令返回 3，不覆盖旧证据。

## 1. 四个概念的边界

- Benchmark：问“系统在固定题目和规则下能做到什么”；不能单独说明真实用户体验。
- Evaluation：问“Outcome 与 Trajectory 是否满足成功标准”；不能单独解释内部哪个步骤耗时。
- Observability：问“能否从 Metrics、Logs 和 Traces 推断内部状态”；不能自动定义什么是业务正确。
- Production diagnosis：问“哪个候选原因最能解释退化，干预后症状是否消失”；证据不足时应返回 `inconclusive`。

四者会共享数据，但不能互相替代。Benchmark 是一种受控 Evaluation；生产 Eval 可以成为观测信号；诊断会使用所有信号，却还需要假设、反证和干预。

## 2. 审计 Benchmark Card

先遮住 `score`。`control-a` 与 `control-b` 的任务、系统、资源和指标合同一致，比较器返回 `comparable`。`same-score-a` 与 `same-score-b` 虽然都是 72 分，却至少有三处关键变化：

1. Harness 从 `harness-a` 变成 `harness-b`；
2. 步数预算从 40 变成 80；
3. 重试策略从 `bounded-1` 变成 `bounded-3`。

因此只能说“在不同运行条件下得到相同聚合分”，不能说两个系统能力相同，也不能把差异归因于模型。

## 3. nearest-rank 分位数

排序后的十个值为：

```text
100, 105, 108, 110, 111, 113, 116, 118, 120, 900
```

nearest-rank 使用 `ceil(p × n)`：

```text
p50: ceil(0.50 × 10) = 5  → 111 ms
p95: ceil(0.95 × 10) = 10 → 900 ms
mean: 1801 / 10 = 180.1 ms
```

平均值 180.1 毫秒无法表达一个用户等待 900 毫秒的慢尾。小样本中的 p95 等于最大值并不“错误”，但报告必须注明算法与样本量，避免读者把它当成稳定总体估计。

## 4. 父子树与依赖图

结构父子边可以画成：

```text
agent.run
├─ model.plan
├─ retrieval.a
├─ retrieval.b
└─ verifier
```

工作依赖边则是：

```text
model.plan → retrieval.a ─┐
                         ├→ verifier
model.plan → retrieval.b ─┘
```

`retrieval.a` 与 `retrieval.b` 同属 `agent.run`，却彼此不等待；`verifier` 同时依赖二者。父子树回答结构包含，依赖图回答执行等待。将两者合成一棵树会丢掉并行信息。

## 5. 关键路径与重试放大

手算示例的工作量是：

```text
80 + 120 + 200 + 40 = 440 ms
```

关键路径是：

```text
plan 80 + max(retrieval 120, retrieval 200) + verify 40 = 320 ms
```

若只把检索 A 从 120 降到 20 毫秒，关键路径仍经过 200 毫秒的检索 B，端到端仍为 320 毫秒。因此“优化了 100 毫秒 Span”不等于用户少等 100 毫秒。

这个手算例子没有放入排队空档。规范夹具 `trace-stable-retrieval-02` 的端到端耗时为 331 毫秒，已观测工作关键路径为 296 毫秒，另有 35 毫秒未归因时间。它可以提示继续检查队列、调度和插桩缺口，却不能单凭差值断言根因。

参考脚本还从 24 条 incident Trace 重新计算重试放大率 `1.4375`。公式是“模型/检索/工具等可计费尝试数 ÷ 声明的逻辑操作数”。比值只能说明额外尝试，不单独证明重试错误。

## 6. 采样分母

规范实验给出：

```text
总请求       = 72
最终失败请求 = 3
保留 Trace   = 49
含错误 Span 的保留 Trace = 12
```

所以：

```text
Trace Coverage          = 49 / 72 = 0.680555...
Telemetry Completeness  = 69 / 72 = 0.958333...
总体请求失败率           = 3 / 72  = 0.041666...
```

`12 / 49` 不能当请求失败率。首先，Tail 策略主动偏向带错误 Span 的 Trace；其次，某个请求可以先有错误 Span，再重试成功。总体率必须来自采样前计数器。

## 7. 部分用量怎样报告

100 次模型调用中只有 80 次带用量，已知成本为 40 单位。可以报告：

> 已知的 80 次调用合计 40 成本单位，用量字段覆盖率为 80%。

不能报告：

> 全部 100 次调用总成本为 40 单位。

更不能在不知道缺失机制时直接外推 50 单位。若缺失集中在超时、大请求或某个 Provider，缺失并非随机。先修遥测或按切片披露缺失，再决定是否估计。

## 8. 薪酬查询的隐私分层

一种合理设计：

- 必须保留：`release_id`、有限枚举的场景切片；
- 带盐哈希：员工 ID、内部文档 ID，用于受控关联；
- 必须删除：Authorization、Cookie、原始 API Key；
- 仅限受控存储：薪酬查询原文、权限文档摘录，并设置短留存和访问审计。

Head 决策只需要 `trace_id`，可以在完整载荷形成前执行：`trace_id → deterministic bucket → keep/drop`。它不读取 Prompt，也不意味着原始载荷可以提前进入观测管线。

完整载荷的处理顺序是 `record → redact → validate → tail decision/buffer → export`。这里的 `record` 指在进程内形成事件，不代表先把原文写入外部日志。字段白名单与 Export Gate 应在数据离开信任边界前生效。

## 9. 千万级请求下的采样组合

可采用三条通道：

1. Head：按 `trace_id` 做低比例确定性采样，保留近似无偏基础样本；
2. Tail：补充错误、慢请求、新发布、审批和一般安全事件；
3. 独立审计：越权尝试与高风险副作用不可由概率丢弃，进入权限更严、留存规则独立的审计通道。

请求数、最终失败数等低基数 Metrics 在采样前聚合。这样既能控制明细容量，又不会因 Tail 偏置误算总体比例。

## 10. 为四类故障选择信号

- 模型生成慢：看 model Span、Provider 延迟/用量，以及按 release 和场景切片的 p95；
- 工具超时后重跑整条 Loop：看依赖感知 Trace、重试放大、成本与 p95 的共同变化；
- Exporter 丢 Span：看 Telemetry Completeness、Exporter 队列/错误 Metrics，而不是只看业务 Trace；
- 用户不喜欢正确答案：Outcome Eval 说明“事实正确”，反馈与 Session 上下文解释“是否有用”，二者都需要。

这道题的重点是：没有一种信号能单独确认所有故障。

## 11. 检索质量下降的消融

固定同一批任务、索引输入和指标，依次做五个对照：

1. 固定模型，只替换 Query rewrite；
2. 固定 Query，只替换索引快照；
3. 固定候选集，只替换 Reranker；
4. 固定排序结果，只替换文档内容版本；
5. 固定其余四项，只替换模型。

同时观察检索 Recall、最终 Outcome、延迟与用量覆盖。只有某个单变量干预稳定消除目标症状，且没有竞争解释时，才把它升级为根因；否则结论保持 `inconclusive`。

## 12. 用反证挑战“新模型让所有请求变慢”

如果假设为真，至少应预测：

1. 多个场景切片的 model Span 都系统性变慢；
2. 不走恢复路径的 simple 请求也变慢；
3. 固定工具和重试策略后，退化仍然存在。

本章证据恰好提供反例：只有 recovery 切片退化；四条 incident/simple Trace 保持稳定；固定 retry policy 后延迟、成本和重试三个症状一起消失。因此“模型导致所有请求变慢”被当前夹具反驳。

## 13. 映射 OpenTelemetry

可把 `trace_id` 映射为 Trace ID，`span_id/parent_span_id` 映射为 Span/Parent，release 与 environment 放入 Resource 或稳定 Attribute。

至少有两处不能机械一一对应：

1. 本章 `depends_on` 是计算工作关键路径的 DAG，不能简单等同 Parent；某些关联可以考虑 Link 或领域属性，但要按真实语义设计；
2. `IncidentReport`、业务 Outcome 与回归任务不由 Trace 协议自动定义，仍由产品和评估系统负责。

映射核对日期为 2026-09-26。接入时应重新检查 OpenTelemetry GenAI 语义的稳定状态。

## 14. 可审计 Incident Report

参考脚本使用真实 Trace 和消融结果生成报告，并应用一个最小接收门禁：必须有数值型 `data_completeness`，也必须有非空 `counterevidence_trace_ids`。

规范报告通过；删除完整率得到：

```json
{"accepted": false, "reason_codes": ["missing_data_completeness"]}
```

清空反证得到：

```json
{"accepted": false, "reason_codes": ["missing_counterevidence"]}
```

真实团队还应要求查询窗口、环境、支持证据、未知项、责任人和动作。门禁拒绝缺失字段不是为了追求文档完整，而是防止“只展示支持自己结论的 Trace”或在遥测严重缺失时给出确定根因。
