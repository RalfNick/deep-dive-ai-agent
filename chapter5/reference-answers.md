# 第 5 章练习参考答案

这些答案给出判断依据、代码入口和验收方式，不要求逐字照抄。涉及实现的题目应先增加失败测试，再修改代码。

## 基础题 1：概念边界

- Prompt 解决“怎样表达目标、约束和输出格式”；它是 Context 的一部分。
- Context 解决“本次模型调用实际能看见什么”；它包含指令、任务、证据、历史、工具描述等瞬时输入。
- Context Window 是输入与输出共享的容量上限，不是内容选择策略。
- Context Engineering 解决“谁在何时从哪些来源，以什么策略构造 Context”。
- Memory 解决跨轮或跨会话保存什么；保存后仍需 Loader/Builder 决定是否进入当前 Context。
- RAG 解决从外部知识中召回候选证据；召回不等于自动加载，更不等于事实已经验证。

验收：六个定义都要指出各自回答的问题；不能用“Context 就是更大的 Prompt”或“Memory 就是 RAG”循环解释。

## 基础题 2：身份与正文

网页正文中的 `SYSTEM:` 只是字符。`SourcePolicy` 信任的是 Loader 提供的受控 `channel`，而不是正文的自我声明。`web_content` 或 `hostile_fixture` 即使写着“最高权限”，仍应被分类为无指令权威的数据；否则第三方网页、代码注释或工具输出可以给自己提权，形成间接提示注入。

代码入口：`chapter5/context/source_policy.py` 的 `CHANNEL_RULES` 和 `classify()`。验收测试应构造正文相同、加载通道不同的来源，证明 authority 由通道映射决定，恶意正文不能把自己变成 SYSTEM。

## 基础题 3：权威与信任

Authority 回答“谁有权改变任务或约束”，Trust 回答“这条陈述作为事实有多可信”。例如仓库规则有较高 authority，可以要求完成前运行测试；真实 pytest 输出有较高 trust，却没有权把用户任务改成另一个目标。反过来，用户指令可能有 USER authority，但用户对运行时版本的猜测不应覆盖已经观测到的事实。

对应实现：`InstructionAuthority` 与 `TrustLevel` 是两个独立枚举，非指令 ContextItem 的 authority 必须为 `NONE`。验收：答案必须分别给出“高权威、非事实”和“高可信、无指令权”的例子。

## 基础题 4：缺失状态

`missing_requirements` 不能只从当前候选项的 `required_for` 汇总，因为 Loader 可能根本没加载某项必需证据。任务合同应通过 `BuildConfig.expected_requirements` 独立声明预期条件，再与选中条目满足的 requirement 对账。

以 `test_pricing.py` 为例：如果 Loader 漏掉它，候选池里就没有 `currency-test` 标签；若只看候选池，系统会误以为没有缺失。当前实验把 `currency-test` 写进任务合同，因此 Builder 会返回 `needs_context`。

运行：`python -m chapter5.experiments.assembly_ablation`。验收：`missing_required` 必须列出 `currency-test`，Probe 决策为 `needs_context`。

## 实验题 5：去重 Trace

先运行 `python -m chapter5.experiments.assembly_ablation`，在 `duplicate` 变体中找到 `test_pricing-copy.py` 对应的 Trace 条目；它应被记录为 `duplicate`，Packet 只保留一份相同类型、相同内容摘要的测试证据。

然后把副本正文改动一个字符再运行。内容摘要变化后，去重原因应消失，Packet Digest 应变化。是否同时保留两份仍取决于场景：普通上下文可以节省预算；审计或多来源确认需要保留 provenance 集合，不能假装第二个来源从未存在。

代码入口：`chapter5/context/builder.py` 的 dedup 阶段。验收：同时报告保留项、丢弃项、reason code 与变更前后 Packet Digest。

## 实验题 6：预算曲线

把 `BuildConfig.budget_units` 从 100 到 1400 每次增加 100，记录 `selected_item_ids`、`missing_requirements`、`budget_used` 和 Probe 决策。可以使用 `canonical_sources()` 与 `ContextBuilder.build()` 编写一个小实验，不要直接修改生产常量。

预期曲线应出现若干离散恢复点：预算不足时先保留高保留优先级条目，但 task requirement 仍可能缺失；当对应证据进入 Packet 后，`missing_requirements` 才减少。横轴必须标为“UTF-8 字节估算单位”，不能写成 Token。

验收：图或表明确标出每个 requirement 首次恢复的预算值，并说明不同 Tokenizer 下阈值可能变化。

## 实验题 7：作用域

新增 `backend/AGENTS.md` 与 `frontend/AGENTS.md` 两条 repository rule，目标仍为根目录 `pricing.py`。Builder 应根据路径作用域排除两条不适用规则，并在 Trace 中记录 `out_of_scope`；改变候选输入顺序不应改变结果。

测试入口：`chapter5/tests/test_builder.py` 中已有嵌套规则和输入排列稳定性案例，可扩展为双目录夹具。

验收：两个目录规则都未进入 Packet；Trace 能解释排除原因；两种候选顺序得到相同 selected IDs 与 Packet Digest。

## 实验题 8：工具描述

为功能重叠的 `write_file` 先写一个失败样本，例如描述只写“Write a file”。此时模型或教学 Probe 无法区分它与 `apply_patch` 的使用时机。改进描述至少说明：什么时候使用、什么时候不用、每个参数的语义、前置条件、返回值和仍由执行侧控制的风险。

本章实验是“文本化工具合同实验”：它把描述作为 Context 文本交给固定 Probe，并没有使用 Provider 原生 `tools/tool_calls`。完整 Function Calling 协议留到第 9 章。

验收：先保留模糊描述导致的失败证据，再展示两个工具在名称、用途、负面边界和参数合同上的可区分性；不能只比较字节长度。

## 实验题 9：位置探针

在允许的真实模型环境中固定模型、参数、ContextItem 集合和序列化模板，只移动关键证据到前、中、后三个位置，每个位置至少重复 5 次。报告必须分别记录 requested model、returned model、有效决策数、Provider 故障、请求摘要和每个模板结果。

行为比例只能以 valid decisions 为分母；429、超时和非法响应属于基础设施状态。样本量不足时只能报告观察，不能声称“所有模型都存在 Lost in the Middle”，也不能进行供应商排名。

代码入口：`chapter5/experiments/information_position.py` 与 `DeepSeekAdapter`。验收：三组 Packet 的选中集合相同、顺序摘要不同，报告清楚区分行为结果和 Provider 故障。

## 设计与批判题 10：多租户 Context

把规则作用域设计成 `tenant → organization/team → user → task/path`。低层规则可以覆盖同一租户内允许覆盖的偏好，但不能跨越组织安全规则；任何检索和 Builder 过滤都必须先执行租户硬隔离。

审计记录至少包含租户 ID、规则来源、版本、有效期、覆盖关系和操作者；删除租户数据后，Context Store、缓存、Trace 索引与派生向量都要遵循删除合同。

验收：两个正文完全相同但 tenant 不同的 ContextItem 不能进入同一 Packet；跨租户条目记录 `out_of_scope`，且 Trace 不复制其正文。

## 设计与批判题 11：Secret 工具

模型只生成业务参数，例如数据库查询和资源 ID；Runtime 在工具真正执行前，根据租户、用户和工具身份从 Secret Store 解析凭据，再注入仅供执行器使用的连接对象。API Key 不属于 Tool Schema，也不进入模型参数。

接口可以分成 `ModelToolArguments` 与 `RuntimeExecutionContext`：前者可序列化进 Context，后者只能在受信执行侧创建。错误信息返回稳定原因码，不回显连接串、Header 或凭据摘要。

验收：Key 不出现在 Context、Provider Payload、Trace、异常、工具返回和模型生成参数中；缺 Key 时返回 `credential_unavailable`，而不是要求模型补写 Key。

## 设计与批判题 12：事实冲突

两份政策应作为两个带 provenance 的 Fact 保留，字段至少包括部门、文档 ID、版本、生效/失效时间、签名或审批状态、抓取时间和内容摘要。系统不能仅凭输入顺序覆盖其中一份。

冲突记录应指出冲突字段、候选值、各自来源与当前解析状态。只有在明确的有效期、签名优先级或组织政策能够裁决时才自动选择；否则两边保持可见并升级给人工或上游 Policy Resolver。

验收：改变输入顺序不改变冲突记录；过期或未签名版本被排除时 Trace 有明确 reason；无法裁决时 Packet/Trace 保留双方 provenance。

## 设计与批判题 13：安全反例

“系统 Prompt 写上不要修改 `.env`”不足以构成安全边界：不可信网页或代码注释仍可能诱导模型；模型输出是概率性的；工具调用只是待审提议；Gateway 必须重新校验工具、参数和资源范围；最终还需要文件权限、容器或 OS 沙箱限制真实副作用。

五层答案分别是：来源分类与隔离、模型风险、Tool Proposal、Action Gateway、OS/运行时隔离。任意一层都不能被描述为完整防御。

验收：能够解释本章 `injection_path` 为什么允许危险提议出现、又为什么必须由第 4 章 Gateway 拒绝；同时明确当前实验没有证明 OS Sandbox。

## 设计与批判题 14：评估设计

为自己的 Agent 建立至少 20 条固定 Context Fixture，覆盖正常、缺失、过期、冲突、噪声、Secret、注入和 Provider 故障。每条夹具冻结来源、任务合同、预期选中/排除项、预期 Decision，以及允许或禁止的 Action。

分别定义三层指标：Build 检查 requirement 召回、无关保留、冲突与预算；Decision 检查状态、工具和参数；Safety 检查提权、泄漏、越界提议与 Gateway 结果。Provider 超时、429 和非法响应不进入行为分母。

验收：先运行基线并保存逐案例证据，再做消融；报告不得用一个总分掩盖 Build、Decision、Safety 的不同失败，也不得把 fixture safety passed 写成系统安全认证。

## 扩展挑战

### 扩展挑战 A：类型化事实时效性

新增仅对 Fact 生效的有效期合同。不要给所有 ContextItem 添加一个通用排序分。测试同一事实的新旧版本、无法比较的时间以及历史审计保留。

### 扩展挑战 B：替换预算估算器

定义可注入 `BudgetEstimator`，保留 UTF-8 字节估算作为离线基线，再接入目标模型 Tokenizer。比较选择结果和耗时，不能把供应商 Token 数反向写成 ContextItem 的永久属性。

### 扩展挑战 C：接入第二个模型供应商

实现另一个 `ModelProbe`，复用同一个 Packet 和 Grader。记录请求/返回模型、参数和请求摘要，供应商错误仍与行为分母分开。不要用少量调用做供应商排名。

### 扩展挑战 D：建立注入回归集

增加代码注释、README、网页、工具输出和检索文档中的不同注入方式。分别测量是否被提升、是否泄漏 Secret、是否产生越界提议，以及 Gateway 是否漏判；不要只记录“最终任务成功”。
