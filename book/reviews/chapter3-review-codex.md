# 第 3 章 Review：AI Agent——从一次生成到闭环执行

Review 日期：2026-08-13。

Review 对象：

- `book/chapter3.md`
- `chapter3/agent_loop.py`
- `chapter3/one_shot_vs_loop.py`
- `chapter3/loop_guards_demo.py`
- `chapter3/tool_error_demo.py`
- `chapter3/verifier_demo.py`
- `chapter3/trace_replay_demo.py`
- `chapter3/tests/test_agent_loop.py`
- `chapter3/README.md`
- `chapter3/reference-answers.md`
- `book/sources/chapter3-sources.md`
- `output/pdf/chapter3-preview.pdf`

## 总体结论

第三章的选题、主问题和总体顺序是合理的，建议判定为**条件通过**。

它完成了全书一个很重要的转折：前两章主要解释模型如何生成、后训练和返回工具协议；本章开始解释一个系统怎样把模型提议接入真实环境，形成观察、决策、行动、验证与停止的闭环。章节从“一次正确回答为什么仍未改变仓库”切入，依次建立 Agent/Workflow 边界、最小序贯定义、ReAct、Model/Harness/Environment/Verifier 四角色、工具协议、状态、停止、错误、完成合同、Trace、循环模式和现代框架映射。这条主线清楚，也能自然进入第四章 Harness Engineering，不建议拆章或大幅重排。

本章写得最好的地方是没有把 Agent 简化为“会调用工具的模型”，也没有把框架的 final output 当成业务完成。工具提议与执行、聊天历史与环境状态、协议结束与外部验收、调用 ID 与幂等键等边界，都比常见入门材料更严谨。

但是，配套代码目前还没有完全兑现正文的核心主张：

1. `RepairPolicy` 主要按照“哪些工具曾被调用”推进，没有真正消费文件内容和多数错误观察；
2. `tests_pass()` Verifier 可以通过修改测试文件被绕过，仍返回 `completed`；
3. Trace 没有把验收证据绑定到状态 digest，也没有验证 call/result 的一一对应；
4. PDF 中五个公式块均以原始 LaTeX 文本显示，没有完成数学排版。

综合评价约为 **7.9/10**。修复四项 P1 后，大纲和主要内容可以进入复审；补齐异常、测试和排版验收后，才适合标记为终稿候选。

## 规模与写作标准核对

当前正文约包含：

- 10,066 个中日韩统一表意文字字符；
- 20,554 个非空白字符；
- 19 个二级标题、33 个三级标题；
- 7 张原创 SVG；
- 5 个编号实验，加 1 个独立 Trace 回放演示；
- 18 道分级练习；
- 28 页 PDF 预览。

章节虽未达到 `book/WRITING_GUIDE.md` 中“约 1.8 万至 3 万中文字符”的字面下限，但核心概念、代码、失败边界、框架映射、生产风险和练习均已覆盖。当前不应为了字符数机械扩写，更应优先补强证据闭环。

`book/README.md` 和 PDF 封面写“约 2.2 万中文字符”，这一数字接近非空白字符数，却明显不是汉字数。建议全书统一统计口径，使用“约 1.0 万汉字 / 2.1 万非空字符”或明确“字符包含英文、代码和标点”。

## 实际验证结果

本次实际运行：

```powershell
python chapter3/agent_loop.py
python chapter3/one_shot_vs_loop.py
python chapter3/loop_guards_demo.py
python chapter3/tool_error_demo.py
python chapter3/verifier_demo.py
python chapter3/trace_replay_demo.py
python -m unittest discover -s chapter3/tests -v
python -m compileall -q chapter3
```

验证环境：

```text
Python 3.11.15
第三方运行依赖：无
```

结果：

- 六个脚本均正常退出；
- Python 编译检查通过；
- 一次生成实验得到 `answer_chars=204`、`file_changed=False`、`acceptance_tests_pass=False`；
- 最小 Loop 完成四次工具调用，第五步通过 Verifier，正文展示结果可以复现；
- 重复动作实验在第三次相同提议时停止，实际只执行前两次读取；
- 工具错误实验正确区分瞬时错误与永久参数错误，并把账本保持为一条；
- Verified Runner 拒绝第一次自然语言完成声明，修改和测试后才接受；
- Trace 回放得到相同 `final_digest=3e3b9dedc733`；
- 6 项回归测试全部通过；
- 7 个 SVG 均可通过 XML 解析；
- 正文引用的 7 个本地图片目标全部存在；
- 8 个脚注均有定义和引用；
- 28 页 PDF 没有发现裁切、重叠、破图或中文缺字，但数学公式没有渲染。

这些结果说明“当前成功路径可以复现”。本次还增加了三组不修改仓库的临时失败注入，暴露了下述 P1/P2 问题。

## P1：必须修改

### 1. `RepairPolicy` 没有真正消费多数环境观察

正文的核心论点是观察进入下一轮后会改变 Agent 决策，`book/chapter3.md:97` 还强调“每一轮只比上一轮多一份可验证事实”。但 `chapter3/agent_loop.py:208-243` 中的确定性策略主要检查工具名是否曾出现：

```python
calls = [event.data["name"] for event in events if event.kind == "tool_call"]

if "read_file" not in calls:
    ...
if "run_tests" not in calls:
    ...
if "apply_patch" not in calls:
    ...
```

它没有读取 `read_file` 的内容，没有确认第一次测试失败是否与需求一致，也没有处理补丁返回的 `patch_conflict`。只有最后阶段读取了 `run_tests` 结果的 `ok` 布尔值。因而第 3 步写出的理由“失败与需求一致，做最小替换”并不是由代码中的失败内容推导出来的。

本次把 `pricing.py` 换成一个不同的错误实现，使固定 `old` 文本不再匹配，实际轨迹为：

```text
step 2  run_tests   -> test_failure
step 3  apply_patch -> patch_conflict
step 4  run_tests   -> test_failure
step 5  run_tests   -> repeated_action
status=repeated_action
```

按照正文 `book/chapter3.md:414` 给出的策略，`patch_conflict` 后应重新读取当前文件再生成补丁；示例策略却忽略了这条观察。它也在失败重试中复用固定的 `call-test-after`，进一步破坏调用 ID 唯一性。

这不影响 `AgentLoop` 作为 Harness 骨架的教学价值，但会使“本章已经观察了一个根据新事实调整行动的 RepairPolicy”这一印象超出证据。

#### 建议修改

- 让 `RepairPolicy` 显式读取最近一次与当前 `call_id` 对应的 `ToolResult`；
- 只有读取结果确实包含预期旧实现、测试失败确实包含目标失败时，才应用补丁；
- 遇到 `patch_conflict` 时重新读取，而不是继续原样跑测试；
- 遇到 `invalid_arguments`、`tool_not_found` 和不可重试错误时进入明确失败状态；
- 每次模型提议生成唯一 `call_id`，业务重试另行复用 `idempotency_key`；
- 增加“不同初始实现”“无关测试失败”“补丁冲突”三项失败测试。

如果希望保持策略极小，也可降低正文措辞：明确它是“按固定阶段推进、只在最终测试上读取反馈的脚本策略”，真正基于观察内容的模型策略留到后续评估章节。

### 2. 当前 Verifier 可以通过修改测试文件被绕过

正文正确给出了更完整的完成谓词：

```text
tests_pass AND no_forbidden_change AND policy_ok
```

并在 `book/chapter3.md:471-487` 说明应禁止修改 `test_*.py`。然而主 Loop 和 `verifier_demo.py` 实际使用的都是：

```python
completion_verifier=repo.tests_pass
```

它只看测试进程退出码，不检查目标文件是否按要求改变，也不检查测试文件是否被修改。`PriceRepo.apply_patch()` 又允许修改工作区内任何顶层文件，包括 `test_pricing.py`。

本次失败注入让策略把 `test_pricing.py` 替换成永远通过的测试，然后提出 final。实际结果为：

```text
status=completed
pricing_still_broken=True
tests_pass=True
verification_event=[{"accepted": True}]
```

也就是说，当前代码可以在 `parse_price()` 完全未修复时返回 `completed`。正文已经口头承认公开测试并不完整，但这个问题比测试覆盖不足更严重：模型能够直接改变判定规则。

#### 建议修改

- 把 Verifier 从 `Callable[[], bool]` 升级为返回结构化 `VerificationResult`；
- 运行前记录允许修改文件和禁止修改文件的摘要；
- 验收至少检查目标测试通过、`pricing.py` 发生预期变化、`test_pricing.py` 未变化、无越界文件变化；
- 将拒绝规则和证据写入 `verification` 事件；
- 把练习 12 提升为正文中的正式失败注入和回归测试，而不只留给读者；
- 增加“删除测试”“改写测试”“只硬编码一个样例”三类反例。

这项修复会直接强化本章最重要的结论：完成权不仅要外移，还必须由 Agent 不能任意改写的验收合同控制。

### 3. Trace 尚未建立正文声称的状态证据链

正文 `book/chapter3.md:489-500` 提出两个正确要求：

1. 验收证据要绑定被检查状态的 digest；
2. `call_id` 应支持检测孤儿结果、重复回传和漏回传。

当前实现没有真正做到这两点。

#### 验收结果没有绑定 digest

`AgentLoop` 的 verification 事件只有：

```python
Event(step, "verification", {"accepted": verified})
```

位置：`chapter3/agent_loop.py:271-278`。

最终测试命令、退出码、测试前后的状态摘要、环境版本都没有记录。`trace_replay_demo.py:29` 的 `final_digest` 是 Loop 已经返回后另行读取的，并非 Verifier 在同一证据对象中产生。因此正文说这个 digest“正在建立这条证据链”并不准确；在并发修改场景下，它仍可能读取到另一个状态。

#### call/result 检查不是一一对应检查

`trace_replay_demo.py` 把调用放进按 `call_id` 索引的字典，只检查每个结果 ID 存在于调用字典。测试则把调用和结果都变成集合后比较：

```python
self.assertEqual(calls, results)
```

位置：`chapter3/tests/test_agent_loop.py:29-39`。

字典和集合都会吞掉重复项，无法检测：

- 两个工具调用复用同一 `call_id`；
- 同一调用收到两次结果；
- 有两个调用、但只有一个同 ID 结果；
- 调用顺序与结果因果关系错误。

本次注入两个同 ID 的合法读取调用，`AgentLoop` 接受了两个调用，集合仍报告 `calls == results`。这与正文“检测重复回传或漏回传”的表述相冲突。

#### 建议修改

- 在接收 Tool Call 时强制 `call_id` 在本次 Run 内唯一；
- 审计器验证每个调用恰有一个结果、每个结果恰有一个调用，保留计数和顺序，而不是使用集合；
- 验证结果返回结构化证据：`accepted`、规则结果、测试命令、退出码、`state_digest`、时间和环境版本；
- 将验证与 digest 采集放在同一受控快照或不可变工作区中；
- Trace 回放前先做完整性校验，失败时不得执行任何状态变更；
- 增加 duplicate call、duplicate result、missing result、orphan result 和乱序结果测试。

### 4. PDF 中五个数学公式均未渲染

28 页预览版的中文、表格、代码和 SVG 整体清晰，但以下公式在 PDF 中直接显示成了原始 LaTeX：

- 第 5 页：策略与状态转移两组公式；
- 第 8 页：`done(s)` 完成谓词；
- 第 24 页：延迟和成本两组公式。

读者实际看到的是：

```text
\[a_t \sim \pi(a \mid c_t), ...\]
\[done(s)=tests\_pass(s) \land ...\]
```

而不是排版后的数学表达式。正文对应位置为 `book/chapter3.md:73-82`、`174-176`、`630-638`。

`book/render_preview.mjs` 使用 CDN 加载 MathJax。当前逻辑在脚本没有加载成功时不会失败：`window.MathJax` 仍只是配置对象，`startup.promise` 不存在，构建继续生成带原始 TeX 的 PDF。这是发布阻断项，不只是美观问题。

#### 建议修改

- 将 MathJax/KaTeX 固定版本作为本地构建依赖，避免 PDF 构建依赖临时 CDN；
- PDF 生成前等待数学引擎完成，并断言页面存在预期 `mjx-container` 或 KaTeX 节点；
- 构建后扫描正文，若仍出现 `\[`、`\]`、`\land` 等原始控制序列则失败；
- 重新渲染并逐页检查第 5、8、24 页；
- 同时把正文中的 `(pi)`、`(g)`、`(a_t)` 等纯文本记号统一成可渲染的行内数学格式。

## P2：应当修改

### 5. 工具超时会逃出 Loop，而不是成为类型化观察

`PriceRepo.run_tests()` 设置了 `timeout=10`，但 `PriceRepo.execute()` 只捕获 `TypeError` 和 `ValueError`。`subprocess.TimeoutExpired` 会直接抛出，整个 Agent Loop 崩溃。

本次用受控 mock 注入超时，结果为：

```text
TimeoutExpired escaped_execute=True
```

这与正文中的 `tool_timeout`、`timeout` 终止状态及“错误是下一步策略输入”尚未对齐。练习 10 已要求读者实现超时与取消，但主代码和 README 应明确标注当前未实现；更好的做法是提供基础实现和回归测试，再让练习扩展到用户取消与可能已发生副作用的处理。

### 6. 幂等实验没有模拟最危险的“不确定结果”

正文用“服务端已经扣款、响应丢失”解释幂等性，这是正确的。但 `PaymentTool` 第一次超时时并未写入账本，第二次才真正扣款。因此实验展示的是：

- 确定未成功后的安全重试；
- 已知成功后的重复请求去重。

它没有展示最危险的“服务端已经提交、客户端却只看到超时”。正文 `book/chapter3.md:439` 已经谨慎地只声称错误分类和幂等键影响策略，所以不存在错误结论；但如果要让实验和引入案例完全对应，建议增加 `commit_then_timeout` 故障模式，并对比无幂等账本时出现两条扣款、有账本时仍为一条。

### 7. “五组实验”与实际交付数量表述不一致

正文、README 和 PDF 封面都写“五组实验”，但运行列表和证据表包含六个独立脚本：

1. `one_shot_vs_loop.py`
2. `agent_loop.py`
3. `loop_guards_demo.py`
4. `tool_error_demo.py`
5. `verifier_demo.py`
6. `trace_replay_demo.py`

正文只有实验 3-1 至 3-5，Trace 回放作为未编号演示存在。两种口径都可以，但应统一：要么把它称为“5 个编号实验 + 1 个 Trace 补充演示”，要么正式增加实验 3-6，并同步封面、README 和章节状态。

### 8. 回归测试覆盖成功路径较好，失败协议仍有明显空缺

现有 6 项测试覆盖完成、call_id 基本保留、重复动作、未知工具、路径越界和过早完成，质量明显优于前两章的无测试状态。但应增加：

1. `patch_conflict` 后必须重新读取；
2. 不相关测试失败不得套用固定补丁；
3. Verifier 拒绝测试文件修改；
4. call ID 唯一、重复结果、漏结果和孤儿结果；
5. `TimeoutExpired` 转成类型化结果；
6. Verifier 异常不会把 Run 静默标记完成；
7. `final=None` 或非法 `Decision` 不能成为 `completed`；
8. Windows 盘符、UNC、POSIX 绝对路径、符号链接/junction 的跨平台边界。

### 9. 参考答案对两道设计题的验收覆盖不足

`chapter3/reference-answers.md` 整体与题目对应较好，但两项仍不足以自检：

- 第 16 题要求收集并分类 20 条模拟轨迹；参考答案只有六类定义和主因规则，没有给出 20 条最小样本、分配方案或示例标注表。
- 第 17 题题面写“分别用 OpenAI Agents SDK、Claude Agent SDK 或 LangGraph”，语义不清楚是三者都做还是三选一；参考答案只给通用验收字段，没有展示至少一个框架的具体 `ToolCall`、`ToolResult`、状态、停止与 Verifier 映射。

建议明确第 17 题为“三选一”或“三者分别实现”，再给一份最低合格映射。第 14 题也可补上超时、取消和总预算停止状态，使退款 Agent 的控制面更完整。

### 10. 当前框架事实基本准确，但两处链接与语义应更新

本次于 2026-08-13 重新核对：

- OpenAI Agents SDK Runner 仍按照 final、handoff、tool call 循环运行，超过 `max_turns` 时抛出 `MaxTurnsExceeded`；当前文档还允许 `max_turns=None` 关闭该限制，并区分模型侧并行工具调用与 SDK 本地执行并发；
- OpenAI Function Calling 仍要求应用执行函数并用对应 `call_id` 回传结果；
- Anthropic Tool Runner 仍支持 `max_iterations`，Managed Agents 仍使用 Beta header；
- Claude Agent SDK 仍是在用户进程中运行的 Python/TypeScript 库，与托管 Managed Agents 分层；
- LangChain `create_agent` 仍构建在 LangGraph runtime 之上，线程级持久化仍通过 checkpointer 配置。

核对来源：[OpenAI Using tools](https://developers.openai.com/api/docs/guides/tools)、[OpenAI Agents SDK Running agents](https://openai.github.io/openai-agents-python/running_agents/)、[Claude Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)、[Anthropic Tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)、[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/quickstart)、[LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)、[LangChain short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory)。

建议修改两处：

- `book/chapter3.md:563` 把“超过 `max_turns` 则停止”写精确为“默认抛出 `MaxTurnsExceeded`；当前可用 `None` 关闭，因此业务仍需决定自己的硬上限”；
- 原 `https://developers.openai.com/codex/use-cases` 已重定向到新的 ChatGPT/Codex Use cases 页面，内容中仍有“scored improvement loop”，但来源台账应更新最终 URL和页面名称。

### 11. PDF 的章节分段还有两处可抛光

除公式外，PDF 整体排版良好。可继续优化：

- 第 25 页只放了本章小结的第 1 条，其余 9 条全部在第 26 页，属于明显的列表跨页孤项；
- 第 27 页练习 17 的题干在页末被截断，剩余一句和第 18 题在第 28 页。

建议对有序列表和单道练习设置合适的 `break-inside`、孤行寡行和最小保留行数。不要强制所有长列表不分页，但应避免只留一项或半道题。

## 对大纲与章节结构的判断

### 当前主线是成立的

第三章可以归纳为四段：

```text
先定义 Agent 与 Workflow 的边界
  → 再拆 Model / Harness / Environment / Verifier
  → 再实现 Tool Call、状态、停止、错误、验收与 Trace
  → 最后映射到 ReAct、状态图和现代 Agent SDK
```

这条顺序比从 LangChain 或某家 SDK 的类名开始更稳定。读者先获得不依赖厂商的责任模型，再看框架封装，不会把 `agent.invoke()` 或 `Runner.run()` 误认为完整业务验收。

### 不建议拆章，但建议合并部分标题层级

正文只有约 1 万汉字，却有 19 个二级标题和 33 个三级标题，阅读上略显碎片化。可以保持内容不变，把以下内容收进更大的二级段落：

- “状态、停止、错误、完成协议、Trace”统一归入“Loop 的五类运行时责任”；
- “生产失败、成本与性能、从 Demo 到生产”统一归入“生产边界”；
- “三种循环模式、现代框架对照”统一归入“从最小 Loop 到框架”。

这样既不牺牲微信阅读的视觉结构，也能让读者看到章节的三四个大台阶，而不是十九个并列主题。

### 与第四章的边界基本合适

第三章只需要让读者知道 Harness 拥有校验、执行、状态和停止；第四章再展开权限优先级、沙箱、审批恢复、幂等、超时、上下文压缩和可观测性。当前第三章虽多次提到这些词，但没有展开成完整实现，因此不是严重重复。

修订时应继续遵守这个边界：本章修复必要的 call ID、Verifier 和 Trace 证据问题即可，不要把审批状态机、崩溃恢复和上下文压缩全部搬进来。

## 写得好的部分

### 1. 开头冲突非常有效

“代码回答正确，但仓库没有变化”是理解 Agent 的理想入口。它把生成质量和环境完成拆开，比泛泛询问“什么是 Agent”更有工程张力。

### 2. Agent 与 Workflow 的判断问题足够稳定

用“新观察出现后，下一步路径由谁选择”代替模型调用次数，能避免把固定流水线包装成 Agent。正文也明确说这不是行业唯一命名标准，边界声明恰当。

### 3. ReAct 没有被等同于公开完整思维链

正文保留 Reason/Action/Observation 的因果思想，同时强调工程审计需要输入、动作、结果与验收，不需要保存模型每个隐含推理 Token。这一处理符合现代推理 API 的现实。

### 4. 四角色模型适合贯穿后续章节

Model 提议、Harness 执行、Environment 提供事实、Verifier 接受目标，这个拆分简单但有解释力。第四章、评估章和 Coding Agent 章都可以继续复用。

### 5. 工具协议的责任边界写得清楚

正文正确指出 Function Call 是数据，Schema 只解决语法与结构，`call_id` 不等于幂等键，并行工具调用也不等于无条件并发执行。这几组区分非常实用。

### 6. 状态与停止不是附录，而是主线

轨迹状态、环境状态和控制状态的拆分，以及 `completed`、`needs_input`、`failed`、`timeout`、`cancelled`、`policy_blocked` 等终止类型，避免了把所有结果都包装成一段自然语言。

### 7. 完成协议的三层区分有长期价值

protocol final、task accepted 和 user accepted 是本章最值得保留的概念之一。它能直接解释为什么 SDK 的 final output、CI 通过和用户满意不能默认等价。

### 8. 框架映射克制且当前仍准确

正文没有把 OpenAI Agents SDK、Claude Agent SDK 和 LangChain 写成三个完全不同的世界，而是映射到策略、循环、工具、状态、停止和业务验收。快速变化事实有日期和来源，且本次复核未发现主要错误。

### 9. 结论边界诚实

章节明确说明确定性 `RepairPolicy` 没有证明真实模型能稳定选择正确动作，也没有把教学测试外推成生产可靠性。这一边界必须保留。

## 推荐修改顺序

### 第一轮：修正文与证据的直接矛盾

1. 让 `RepairPolicy` 真正消费读取内容、测试失败和 `patch_conflict`；
2. 实现不可由模型篡改的结构化 Verifier；
3. 强制 call ID 唯一并做 call/result 一一对应审计；
4. 把 verification evidence 与同一状态 digest 绑定；
5. 重新运行全部成功和失败注入测试。

### 第二轮：补运行时异常与测试

1. 把 `TimeoutExpired` 转为 `tool_timeout`；
2. 增加取消、Verifier 异常和非法 Decision 测试；
3. 增加跨平台路径与链接边界测试；
4. 给幂等实验增加 commit-then-timeout 场景；
5. 明确“5 个编号实验 + 1 个补充演示”或增加实验 3-6。

### 第三轮：编辑与出版

1. 修复数学公式构建并让未渲染 TeX 触发构建失败；
2. 统一字符数统计；
3. 补齐参考答案；
4. 合并部分二级标题；
5. 修复 PDF 第 25-28 页列表和练习分页；
6. 更新官方资料核对日期和 Codex use cases 最终链接。

## 复审验收清单

- [ ] 不同初始实现出现 `patch_conflict` 后，策略会重新读取并改变后续参数；
- [ ] 无关测试失败不会触发固定 `parse_price()` 补丁；
- [ ] 修改或删除 `test_pricing.py` 时 Verifier 必须拒绝完成；
- [ ] `verification` 事件记录规则结果、测试命令、退出码和状态 digest；
- [ ] 验收通过的 digest 与最终交付 digest 一致；
- [ ] 每个 `call_id` 在 Run 内唯一，且恰有一个结果；
- [ ] duplicate/missing/orphan result 均在回放前失败；
- [ ] `TimeoutExpired` 返回类型化错误，不会使 Loop 直接崩溃；
- [ ] 六个现有脚本与新增失败注入全部通过；
- [ ] `python -m unittest discover -s chapter3/tests -v` 覆盖上述协议；
- [ ] PDF 第 5、8、24 页公式已正确渲染；
- [ ] PDF 构建检测到原始 TeX 时会失败；
- [ ] 实验数量、字符数和封面元数据采用统一口径；
- [ ] 第 16、17 题参考答案能够逐项对应题面；
- [ ] 发布前重新核对 OpenAI、Anthropic 与 LangChain 官方文档。

## 最终判断

第三章的大纲合适，甚至可以说是目前全书最重要的“系统边界章”之一。它已经把“一次生成”与“闭环执行”讲清，也为 Harness、状态图、评估和 Tracing 建立了统一词汇。

当前问题不是缺更多 Agent 概念，而是示例代码还没有完全达到正文自己设定的证据标准。最优修订方向是：少扩写，多做失败注入；少增加框架名，多让 Observation、Verifier、call ID 和 digest 真正形成闭环。完成 P1 后，本章可以继续保持“复审稿”定位；完成异常测试、公式排版和元数据修订后，再升级为终稿候选。

## v1.1 修订处理记录（2026-08-14）

本节追加修订事实，不改写上面的 v1.0 初审结论和 7.9/10 评分。

| Review 建议 | 处理方式 | v1.1 实现或证据 |
| --- | --- | --- |
| 策略消费 Observation | 采纳 | `RepairPolicy` 读取最近一次 ToolResult，以真实源码作为补丁前置条件；无关失败返回 `failed` |
| 结构化且防测试篡改的 Verifier | 采纳 | `VerificationResult` 记录规则、命令、退出码、状态摘要与受保护文件检查 |
| call ID 唯一与 Trace 一一对应 | 采纳 | 第二个重复 ID 在副作用前被拒绝；`trace_audit.py` 检测 duplicate、missing、orphan 和乱序 |
| 验收证据绑定状态摘要 | 调整后采纳 | 单进程实验在 Verifier 中生成摘要并在 `completed` 前立即复核；不声称具备生产原子快照 |
| `TimeoutExpired` 类型化 | 采纳 | 转成 `tool_timeout`、`retryable=True`，保留回归测试 |
| commit-then-timeout | 采纳 | 第一次先写本地账本再丢响应；同一幂等键恢复后 `side_effects=1` |
| 实验数量与统计口径 | 采纳 | 统一为“5 个编号实验 + 1 个 Trace 补充实验”；正文约 1.07 万汉字 / 2.28 万非空字符 |
| 第 16、17 题答案 | 采纳 | 补 20 条轨迹分配、指标分母和 LangGraph 逐项映射；第 17 题明确三选一 |
| 快变框架事实 | 采纳 | 2026-08-14 复核 OpenAI、Anthropic、LangChain 与 Codex 一手页面，替换 Codex 重定向旧链接 |
| 取消、Verifier 异常、跨平台链接边界 | 留作扩展 | 本章只修已复现的基础合同；持久取消与更强文件系统边界由第四章继续展开 |
| 本地公式和 PDF 分页 | 采纳并关闭 | 固定 MathJax 4.1.3 本地依赖；公式数量、残留 TeX、页面错误与失败请求进入构建门禁；30 页 PDF 全页目检无裁切、重叠、缺图或练习条目跨页 |

当前自动证据命令为：

~~~powershell
python -m unittest discover -s chapter3/tests -p "test*.py" -v
python chapter3/run_all_experiments.py
npm --prefix book test
npm --prefix book run render:chapter3
~~~

最终验收中，第一条命令发现 19 项测试并全部通过，第二条命令运行 6 个脚本且 `failures={}`，渲染门禁的 4 项测试全部通过。v1.1 PDF 共 30 页；文本层没有 `\pi`、`\sum`、`\mathbb`、`\left`、`\[` 或 `\(` 原始 TeX，也没有 Unicode 替换字符。所有页面均渲染为图片目检，公式、表格、代码、SVG、练习与注释未发现裁切、重叠或缺字。版本化 PDF 的 SHA-256 为 `3E2E6319B17B0A972FEEB4A8172E74D2EAD55FC2FCB70A91230EC882DFEEE54D`。
