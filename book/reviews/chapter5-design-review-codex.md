# 第 5 章写作前设计 Review：上下文工程——Agent 真正看到的世界

Review 日期：2026-08-15。

Review 对象：

- 第五章实验与代码架构草案；
- [`book/OUTLINE.md`](../OUTLINE.md) 中第五、六章的范围定义；
- [`book/chapter4.md`](../chapter4.md) 中 Context Builder 与第五章的衔接；
- 计划新增的 `chapter5/` 配套代码。

## 总体结论

第五章的设计方向合理，建议判定为**写作前条件通过**，当前完成度约为 **8.5/10**。

本章能够准确承接第四章留下的问题：第四章已经确定 Context Builder 属于 Harness，但尚未实现；第五章将其抽成独立组件，通过信息缺失、指令冲突、信息位置、工具描述、噪声和提示注入等实验，研究“模型最终看到什么，以及这些信息为何进入上下文”。这一定位也能与第六章区分：第五章处理单次模型调用前的上下文选择、排序和信任边界，第六章再处理长任务中的压缩、检查点、持久化和恢复。

当前架构最大的优点是同时设计了两层实验：

- `ScriptedModel` 隔离模型随机性，验证 Context Builder 自身是否按合同工作；
- 真实模型探针观察同一 Context Packet 是否会引发不同决策，并记录 Token、错误和失败类型。

但写作前必须收紧三个边界：

1. Context Builder 正确，不等于真实模型一定服从上下文标签；
2. 模型没有服从一次提示注入，不等于系统形成了安全边界；
3. `authority`、`trust_level` 和 `priority` 解决的是三个不同问题，不能合并成一个高低分。

因此，本章不需要更换主题或推翻五组实验，但应调整数据模型、Trace 位置、Grader 分层和实验验收条件。

## 与全书结构的衔接

### 与第四章的边界

第四章已经给出全局 Harness 地图，包括 Context、Control、Execution、State、Verifier 和 Recorder，并明确把 Context Builder 留给下一章实现。因此第五章应聚焦：

- 候选上下文从哪里来；
- 哪些信息能够作为指令；
- 哪些信息只能作为不可信数据；
- 信息如何去重、冲突、排序和分配预算；
- 最终 Context Packet 是否可解释、可复现。

第五章可以复用第四章的 Action Gateway 做安全 dry-run，但不应重新展开权限系统、沙箱、审批恢复和崩溃恢复。

### 与第六章的边界

第五章可以讨论单次调用的 Token 预算，但不要展开：

- 跨几十轮会话的自动压缩；
- 滑动窗口；
- 长任务检查点；
- 文件化进度状态；
- 会话恢复和 compaction。

这些属于第六章。第五章中的“预算”应被定义为：在一次 Context Packet 中，有限窗口如何分配给必要规则、任务、工具定义、事实和观察。

### 与第九、十章的边界

工具描述实验是合理的，因为工具定义本身就是上下文。但第五章只需回答：

> 模糊、精确或带反例的工具描述，怎样影响工具选择和参数生成？

不要在本章展开 MCP 协议、工具检索、延迟加载、异步任务和大规模工具集，这些属于第九、十章。

## 推荐代码架构

原始架构主线成立，但建议让 Context Builder 同时产生 Packet 和装配 Trace，并将模型调用抽象为通用探针：

```text
ContextSource
    ↓ 收集候选信息
Candidate ContextItem
    ↓
SourcePolicyRegistry
    ├─ 分配 authority
    ├─ 分配 trust
    ├─ 限定 scope
    ├─ 标记 instruction / data
    └─ 标记 sensitivity
    ↓
ContextBuilder
    ├─ 过滤
    ├─ 去重
    ├─ 冲突检测与处理
    ├─ 预算分配
    ├─ 排序
    └─ 类型化序列化
    ↓
ContextPacket + ContextBuildTrace
    ↓
ModelProbe
    ├─ ScriptedModel
    └─ DeepSeekAdapter
    ↓
Decision
    ├─ tool
    ├─ answer
    ├─ needs_context
    └─ refuse
    ↓
BuildGrader + DecisionGrader + SafetyGrader
    ↓
RunRecord / ExperimentReport
```

如果提示注入实验要验证系统安全边界，应增加：

```text
Decision
    ↓
chapter4.ActionGateway（dry-run）
    ↓
allow / deny / ask
```

否则实验最多能证明模型在当前样本中没有跟随恶意指令，不能证明危险动作无法执行。

## 数据模型 Review

### `ContextItem` 字段不应共用一个“重要程度”概念

建议最小数据模型为：

```text
ContextItem
├─ id
├─ kind
├─ content
├─ source
├─ authority
├─ trust_level
├─ priority
├─ scope
├─ freshness
├─ sensitivity
└─ provenance
```

各字段责任如下：

| 字段 | 回答的问题 | 示例 |
| --- | --- | --- |
| `kind` | 这是指令、事实、工具定义还是观察？ | `instruction`、`fact`、`tool_schema`、`observation` |
| `source` | 它属于哪类来源？ | system、user、repo_rule、tool_result |
| `authority` | 如果它是指令，谁有权要求系统执行？ | product policy、task owner、repository rule |
| `trust_level` | 如果它陈述事实，事实有多可信？ | verified、untrusted、unknown |
| `priority` | 当前任务是否值得为它分配上下文预算？ | required、high、normal、low |
| `scope` | 指令或事实在哪个范围内有效？ | 仓库、目录、工具、任务阶段 |
| `freshness` | 信息是否可能过期？ | 文件 digest、版本、采集时间 |
| `sensitivity` | 是否允许进入模型输入或普通 Trace？ | public、internal、secret |
| `provenance` | 具体从哪里、何时、以何种方式取得？ | 路径、调用 ID、URI、摘要哈希 |

必须明确以下原则：

1. 工具结果可以高度相关，但没有指令权威；
2. 仓库规则可以在特定目录内有权威，但作用域外不能自动生效；
3. 恶意文档不能通过在内容中写 `priority=high` 抢占上下文预算；
4. `authority`、`trust_level`、`priority`、`sensitivity` 必须由 Harness 根据来源策略分配，不能相信内容自报；
5. 高权威指令与高可信事实是两种不同性质，不能用同一个数值排序。

### `source` 与 `provenance` 应分开

例如：

```text
source      = repository_rule
provenance  = path=AGENTS.md,
              digest=sha256:...,
              collected_at=...,
              collector=RepoRuleSource
```

`source` 用于分类和策略，`provenance` 用于审计、重放和版本检查。

### `token_cost` 应由 TokenEstimator 计算

Token 数不是 Context Item 的永久属性，因为它取决于：

- 模型使用的 tokenizer；
- 最终消息角色和包装格式；
- 序列化时加入的来源标签；
- 是否进行转义、引用或结构化封装。

建议将原始字段改成运行时估算：

```text
TokenEstimator(model_id, serializer_version)
    ↓
estimated_tokens
```

最终在 Packet 和 RunRecord 中记录：

```text
estimated_input_tokens
actual_input_tokens
token_budget
model_id
serializer_version
```

### `priority` 不应完全由 ContextSource 决定

来源可以给出候选相关度，但最终是否进入 Packet 应由 Builder 的策略结合以下因素判断：

- 是否为不可丢弃规则；
- 是否与当前任务相关；
- 是否被更新版本替代；
- 是否与更高权威内容冲突；
- Token 成本；
- 安全和敏感性限制。

否则一个不可信来源可以通过提交大量“高优先级”内容实现上下文拒绝服务。

## `ContextPacket` 设计建议

Context Packet 不应只是拼接后的长字符串。建议内部保留类型化分区：

```text
ContextPacket
├─ system_policies
├─ task_instruction
├─ repository_rules
├─ tool_definitions
├─ trusted_facts
├─ untrusted_observations
└─ history_summary
```

再由模型适配器把 Packet 转换成供应商需要的消息格式。

这样做可以支持：

- 工具输出不会被错误序列化成 system instruction；
- 仓库文档中的文字保持“数据”身份；
- Grader 能检查项目是否进入了正确分区；
- 切换模型时无需重写 Context Builder；
- Packet 可以生成稳定 digest，支持实验对照。

但正文必须强调：XML 标签、Markdown 引用块或 `untrusted_data` 标记只是模型侧缓解手段。模型仍可能服从恶意内容，真正权限必须由外部 Action Gateway 控制。

## `ContextBuildTrace` 设计建议

Context Trace 应在模型调用前由 Builder 生成，而不是作为 Decision 的附属结果。

建议至少记录：

```text
ContextBuildTrace
├─ candidate_items
├─ selected_items
├─ dropped_items
│  └─ drop_reason
├─ conflicts
│  ├─ participants
│  ├─ resolution
│  └─ policy_rule
├─ ordering
├─ token_estimates
├─ budget_remaining
├─ packet_digest
└─ serializer_version
```

建议定义稳定的丢弃原因枚举：

```text
irrelevant
duplicate
superseded
out_of_scope
conflict_lost
untrusted_instruction
sensitive
budget_exceeded
```

这样消融实验才能回答“模型没看到某条信息，是来源没有提供、Builder 丢弃，还是预算不足”。

## 五组实验 Review

### 实验一：信息缺失实验

方向正确，但成功标准不能只设为“缺少规则时模型必须选错”。信息确实不足时，可靠 Agent 应该提问、请求读取规则或返回 `needs_context`，而不是盲猜。

建议变体：

```text
full_context
missing_required_rule
duplicated_rule
tight_budget
restored_rule
```

ScriptedModel 验收：

- 必要规则存在时必须进入 Packet；
- 必要规则缺失时不得伪造；
- 重复规则只能保留一个规范版本；
- 紧预算下不可丢弃规则仍被保留；
- 每个删除或保留决定在 Trace 中有原因。

真实模型指标：

- 正确工具或文件选择率；
- 信息不足时合理提问/请求上下文率；
- 约束违反率；
- 规则恢复后的成功恢复率。

将重复和紧预算放入这一组，可以直接覆盖原架构中的去重和预算分配，否则五组实验没有直接验证这两个核心能力。

### 实验二：指令冲突实验

“后出现优先”适合作为错误基线，但正确方案不能只是对所有内容做单一数值排序。

建议交叉两个变量：

```text
authority: high / low / same
position:  first / last
```

核心实验不变量应是：

> 当权威关系不变时，仅改变出现顺序，不应改变跨权威等级冲突的处理结果。

还应区分三种冲突：

1. 指令与指令冲突；
2. 事实与事实冲突；
3. 不可信数据伪装成指令。

同一权威层内发生不可调和冲突时，合理结果应是：

```text
conflict_detected
needs_input
```

而不是 Context Builder 任意选择一项。

### 实验三：信息位置实验

这一实验主要测真实模型的位置敏感性，而不是 ScriptedModel 的智能程度。

ScriptedModel 只需要证明：

- 三个 Packet 包含相同 Item；
- 只改变关键约束的序列位置；
- 没有发生 Token 截断；
- authority、scope、provenance 和内容 digest 保持不变。

真实模型再比较开头、中间和结尾位置的：

- 决策正确率；
- 关键约束违反率；
- 决策稳定性；
- 输出和输入 Token；
- 提问或拒绝比例。

不要只使用一个固定任务。建议准备多个等价任务模板，并随机化无关内容，否则可能测到具体措辞或单个案例记忆，而不是信息位置效应。

### 实验四：工具描述实验

方向合理。本章应聚焦工具描述作为上下文的影响，不展开 MCP 和大规模工具检索。

建议变体：

```text
vague_description
precise_description
description_with_negative_example
```

控制变量：

- 工具集合相同；
- JSON Schema 相同；
- 工具名称相同；
- 描述长度尽量接近；
- 任务与其他上下文相同；
- 至少包含两个容易混淆的工具。

指标应拆分为：

```text
tool_selection_accuracy
argument_schema_valid_rate
argument_semantic_accuracy
unnecessary_tool_rate
```

不能只报告“最终调用是否正确”，否则无法判断问题来自工具选择还是参数生成。

### 实验五：噪声与提示注入实验

这是五组中最重要的一组，但建议拆成两个子实验：

```text
5A irrelevant noise
5B adversarial prompt injection
```

两者失败机制不同：

- 普通噪声消耗预算、干扰选择和注意力；
- 提示注入试图让数据跨越指令边界并诱导危险动作。

建议变体：

```text
clean
irrelevant_noise
untrusted_injection
trusted_looking_injection
injection_at_beginning
injection_at_end
```

ScriptedModel/Builder 验收：

- 不可信内容不能获得 instruction authority；
- 恶意内容仍保留原始 provenance；
- 无关噪声在紧预算下优先被丢弃；
- 任何被拒或被保留的内容都有 Trace 原因。

真实模型指标：

- 正常任务成功率；
- 攻击指令服从率；
- 高风险动作提议率；
- Action Gateway 拒绝率；
- 误拒绝率；
- 噪声造成的成功率下降。

结论应写成“在当前模型、Packet 和样本中降低了攻击服从率”或“Builder 没有把不可信数据提升为指令”，不要写成“提示注入已解决”。

## ScriptedModel 与真实模型的证据边界

### ScriptedModel 能证明什么

- Context Builder 的选择规则按代码执行；
- required 项不会因普通预算竞争被丢弃；
- 去重、作用域和冲突处理符合声明合同；
- 不可信数据没有被提升为高权威指令；
- Packet 和 Trace 可确定性重建；
- 同一输入生成稳定 digest。

### ScriptedModel 不能证明什么

- 真实模型一定理解 authority 标签；
- 真实模型一定服从排序结果；
- 分隔符能够阻止提示注入；
- 当前上下文策略对所有任务最优；
- Context Builder 可以替代权限系统和沙箱。

### 真实模型探针能观察什么

- 模型决策是否随 Packet 变化；
- 位置变化是否造成行为差异；
- 工具描述是否影响选择和参数；
- 注入内容是否提高违规动作提议率；
- 相同条件下模型输出是否稳定。

### 真实模型探针不能证明什么

- 少量样本可以代表所有模型和任务；
- 一次成功代表稳定能力；
- 没有观察到攻击成功就表示安全；
- 某个供应商模型的行为来自公开可知的内部机制。

## 模型适配器建议

不建议把实验框架直接绑定到 `DeepSeekModel` 类名。建议先定义通用接口：

```python
class ModelProbe(Protocol):
    def decide(self, packet: ContextPacket) -> ModelRun:
        ...
```

然后实现：

```text
ScriptedModel(ModelProbe)
DeepSeekAdapter(ModelProbe)
```

这样以后增加其他模型时，不需要改 Context Builder、实验用例或 Grader。

真实 API 探针应为显式 opt-in：

- 默认测试和 CI 只运行 ScriptedModel；
- 缺少 API Key 时不报错退出；
- API Key 只从环境读取，不写入报告、Trace、请求样本和异常；
- 测试中使用 fake transport，不连接真实服务；
- 原始响应保存前进行敏感字段清洗。

## Grader 分层建议

不要把所有指标压缩为一个总分。建议至少拆成三类。

### BuildGrader

检查 Context Builder：

- 必要项是否进入；
- 禁止项是否进入；
- 不可信数据是否位于正确分区；
- 是否超出预算；
- 去重和冲突结果是否正确；
- provenance 是否完整；
- Packet digest 是否稳定。

### DecisionGrader

检查模型 Decision：

- 工具选择；
- 参数 Schema；
- 参数业务语义；
- 信息不足时是否提问；
- 是否产生无关工具调用；
- 是否完成任务。

### SafetyGrader

检查安全结果：

- 是否服从不可信指令；
- 是否提议越权动作；
- Action Gateway 是否正确拒绝；
- 是否出现正常任务误拒绝；
- 敏感内容是否进入 Packet 或普通 Trace。

安全硬门槛不能被较低 Token、较快延迟或较高普通任务成功率抵消。

## API 运行状态设计

“不把 API 错误与任务失败混在一起”的方向正确，但 `skipped` 应只表示实验没有执行。

建议分成两个正交字段：

```text
RunStatus
├─ completed
├─ skipped_no_api_key
├─ skipped_by_configuration
├─ infra_error_rate_limited
├─ infra_error_timeout
├─ infra_error_provider
└─ model_output_parse_error

TaskOutcome
├─ correct
├─ incorrect
├─ needs_context
├─ constraint_violation
├─ security_violation
└─ not_scored
```

限流、超时和服务错误不应记为 `skipped`。它们是已经尝试运行后发生的基础设施失败，应从行为成功率分母中单独处理，但必须报告数量。否则模型在困难变体中频繁超时，可能通过被大量标成 skipped 产生虚高成功率。

## 复现协议建议

每次真实模型运行至少记录：

- 精确模型 ID；
- 请求日期和实验版本；
- temperature、top-p、最大输出 Token；
- Context Packet digest；
- serializer version；
- estimated/actual input Token；
- output Token；
- 延迟；
- 重试次数；
-原始结构化 Decision；
- Grader 结果；
- RunStatus 和 TaskOutcome；
- 失败类型。

重复次数不要只写“少量”：

- 默认教学运行：每个变体 5 次；
- 探索性报告：每个变体 10–20 次；
- 成本不足时报告准确的 `n/N`，不要只给百分比。

小样本结论统一写成：

> 在当前模型版本、Context Packet、任务样本和运行配置中观察到……

不要外推成普遍的长上下文、位置效应或提示注入规律。

## 推荐的五组最终实验矩阵

| 实验 | 主要变量 | ScriptedModel / Builder 验收 | 真实模型指标 |
| --- | --- | --- | --- |
| 1. 装配消融 | 缺失、重复、紧预算、恢复 | 选择、去重和丢弃原因正确 | 正确行动或合理提问率 |
| 2. 冲突与权威 | authority × position | 顺序不能覆盖权威策略 | 冲突处理率、违规率 |
| 3. 信息位置 | 开头、中间、结尾 | Packet 仅位置不同 | 位置敏感性、稳定性 |
| 4. 工具描述 | 模糊、精确、反例 | 工具集与 Schema 不变 | 工具和参数正确率 |
| 5. 噪声与注入 | 普通噪声、恶意数据 | 数据未被提升为指令 | 攻击服从率、误拒率 |

## 推荐目录结构

```text
chapter5/
├── context/
│   ├── models.py
│   ├── sources.py
│   ├── source_policy.py
│   ├── token_estimator.py
│   ├── builder.py
│   ├── packet.py
│   └── trace.py
├── models/
│   ├── protocol.py
│   ├── scripted.py
│   └── deepseek_adapter.py
├── graders/
│   ├── build_grader.py
│   ├── decision_grader.py
│   └── safety_grader.py
├── experiments/
│   ├── assembly_ablation.py
│   ├── instruction_conflict.py
│   ├── information_position.py
│   ├── tool_description.py
│   └── noise_and_injection.py
├── fixtures/
│   ├── tasks.json
│   ├── context_items.json
│   └── expected_packets.json
├── tests/
│   ├── test_builder.py
│   ├── test_conflicts.py
│   ├── test_budget.py
│   ├── test_packet_serialization.py
│   ├── test_injection_boundary.py
│   └── test_run_status.py
├── reports/
├── README.md
└── reference-answers.md
```

该结构是建议上限，不要求写作前一次实现全部文件。为了保持教学代码可读，首版可以合并小模块，但职责边界应保留。

## 写作结构建议

第五章正文可以按以下顺序展开：

1. 同一个模型为什么会因“看到的世界”不同而行动不同；
2. Prompt Engineering 与 Context Engineering 的边界；
3. Context Item：指令、事实、工具定义和观察；
4. authority、trust、priority 与 scope；
5. Context Builder：选择、去重、冲突、预算和排序；
6. Context Packet 与 Build Trace；
7. 实验一：信息缺失、重复与紧预算；
8. 实验二：指令冲突与权威顺序；
9. 实验三：信息位置；
10. 实验四：工具描述；
11. 实验五：噪声与提示注入；
12. ScriptedModel 与真实模型证据边界；
13. 生产失败、安全与成本；
14. 本章小结：上下文是受控投影，不是完整世界；
15. 与第六章长任务上下文架构衔接。

建议继续使用一个贯穿任务，让五组实验共享同一候选信息池。例如沿用 `parse_price()` 仓库任务，并准备：

- system policy；
- 用户目标；
- 仓库规则；
- 工作目录；
- 两个相似工具定义；
- 失败测试结果；
- 无关 README；
- 含恶意指令的工具输出。

但真实模型探针还应加入少量结构相同、文本不同的任务，避免模型只适配单个案例。

## 写作前验收清单

- [ ] `authority`、`trust_level` 和 `priority` 有独立定义；
- [ ] Context Item 能区分 instruction、fact、tool schema 和 observation；
- [ ] 来源策略由 Harness 赋值，内容不能自报权威和优先级；
- [ ] `token_cost` 由明确的 TokenEstimator 计算；
- [ ] Context Packet 保留类型化分区，而非只有长字符串；
- [ ] Context Builder 同时生成 Build Trace；
- [ ] Build Trace 记录候选、选中、丢弃、冲突和预算原因；
- [ ] ScriptedModel 和真实模型使用同一 Packet；
- [ ] 缺失必要信息时允许 `needs_context`，不强迫模型盲猜；
- [ ] 冲突实验交叉 authority 和 position；
- [ ] 位置实验确保除位置外其他变量完全相同；
- [ ] 工具描述实验控制 Schema、工具集和描述长度；
- [ ] 普通噪声和对抗性注入分开统计；
- [ ] 提示注入结论不替代 Action Gateway 权限边界；
- [ ] Build、Decision、Safety 使用独立 Grader；
- [ ] API 缺失、限流、超时、服务错误和任务失败分别记录；
- [ ] 真实模型运行固定模型版本、参数、Packet digest 和重复次数；
- [ ] 默认 CI 不需要 API Key；
- [ ] 报告不会保存 API Key 或未经清洗的敏感响应；
- [ ] 第五章不提前展开第六章的压缩和恢复机制。

## 最终判断

第五章的核心方向是对的，五组实验也具有明显的递进关系：

```text
有没有必要信息
  → 冲突时听谁的
  → 相同信息放在哪里
  → 工具怎样被描述
  → 不可信内容能否越过边界
```

最需要避免的是把 Context Engineering 写成“把更多信息按分数塞进 Prompt”。本章真正应该建立的结论是：

> 模型上下文是 Harness 对目标、规则、事实、工具和历史的受控投影；每个进入项都应有来源、作用域、信任边界、预算理由和可审计的装配记录。

完成数据模型、Packet/Trace 分离、Grader 分层和失败状态设计后，可以正式开始第五章正文与 `chapter5/` 配套代码。
