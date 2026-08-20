# 第 6 章资料台账：长任务中的上下文架构

核对日期：2026-08-17。产品行为、API 字段、默认阈值、命令可用范围和版本号属于快变事实；出版前必须按每条记录的复核标记重新打开原页面。研究论文与本地实验只支持各自声明的任务、实现和指标，不能外推为模型或产品排名。

## 使用原则

- 产品事实只引用厂商官方文档、官方工程博客或官方开源仓库；技术研究结论使用原始论文；
- 每条记录同时写“事实使用”和“明确不声称”，把证据范围与外推边界放在一起；
- OpenAI 的 opaque compaction item、Claude Code 的产品摘要、LangGraph graph state 与本书可检查的 `CompactionArtifact` 不是同一种制品；
- 官方文档描述公开行为，不授权推断未公开的摘要 Prompt、内部字段或模型能力；
- 本章确定性实验度量规范化 UTF-8 `serialized_bytes`，不把它写成 Provider Token；
- 用户 PDF 与参考开源书仅用于术语、读者难度和编排校准，不作为快变产品事实的最终依据。

## Task 11 官方页面复核记录

2026-08-17 四视角 Review 期间重新打开 S01—S10 的官方页面，并逐项核对正文产品映射。复核结果如下：

- S01 仍把 Codex Harness 描述为组装输入、执行工具并把结果加入后续调用的 Agent Loop 责任方；
- S02 仍区分 server-side compaction 与 standalone `/responses/compact`，两条路径都包含不可供人类解释的 opaque compaction item，standalone 返回值应作为 canonical next context 原样续传；
- S04 仍把 `OpenAIResponsesCompactionSession` 描述为底层 Session 的包装器，并公开自动触发、显式压缩和 clear-and-rewrite 恢复边界；
- S05—S06 仍公开 Claude Code 的结构化摘要、自动/手动 compact、规则重载、Resume、Fork 与隔离 Context 行为；
- S09—S10 仍区分 thread-scoped Checkpointer 与跨 thread Store，并把 trim、delete、summarize 作为应用可选的短期历史策略。

本次复核没有把页面新出现的模型名、窗口大小、默认阈值或命令版本固化进正文；这些仍按各记录的“出版前复核”标记处理。

## OpenAI 与 Codex 官方资料

### [S01] Unrolling the Codex agent loop
- 类型：OpenAI 官方工程博客，一手资料
- URL / 本地路径：https://openai.com/index/unrolling-the-codex-agent-loop/
- 事实使用：Codex Harness 组装初始输入，把工具调用结果追加到后续输入，并在输入持续增长时管理上下文；文章还回顾了早期手动 `/compact` 与后来的自动原生 compaction 路径。
- 明确不声称：不据此推断当前每个 Codex 表面都提供同一条手动命令，也不把 Harness 行为解释为模型能力。
- 最后核对：2026-08-17
- 出版前复核：是

### [S02] Compaction - OpenAI API
- 类型：OpenAI 官方 API 文档，一手资料
- URL / 本地路径：https://developers.openai.com/api/docs/guides/compaction
- 事实使用：Responses API 同时公开 server-side compaction 与显式的 standalone `/responses/compact`；返回的 compaction item 是 opaque 的 canonical continuation input，独立端点返回值应原样用于下一次调用。
- 明确不声称：不把 opaque item 等同于本书字段可见的 `CompactionArtifact`，不声称它可供人类审计或能恢复业务副作用。
- 最后核对：2026-08-17
- 出版前复核：是

### [S03] Codex compact handoff prompt template
- 类型：OpenAI 官方开源仓库，一手实现证据
- URL / 本地路径：https://github.com/openai/codex/blob/main/codex-rs/prompts/templates/compact/prompt.md
- 事实使用：当前主分支的 compact 模板把压缩描述为交接，要求保留进度、决定、约束、剩余工作与关键引用；只用于说明“交接信息有结构需求”。
- 明确不声称：`main` 不是固定发布版本；不声称模板文件等于所有 Codex 客户端、服务端或模型内部使用的完整实现。
- 最后核对：2026-08-17
- 出版前复核：是

### [S04] Sessions - OpenAI Agents SDK for Python
- 类型：OpenAI 官方 SDK 文档，一手资料
- URL / 本地路径：https://openai.github.io/openai-agents-python/sessions/
- 事实使用：SDK Session 在运行前取回历史、运行后保存新项；`OpenAIResponsesCompactionSession` 包装底层 Session，可按阈值自动压缩，也可显式运行压缩；文档区分客户端 Session 与 server-managed continuation。
- 明确不声称：Session 不等于长期 Memory 或业务 Checkpoint；clear-and-rewrite 的恢复说明也不构成 exactly-once 保证。
- 最后核对：2026-08-17
- 出版前复核：是

## Anthropic 与 Claude Code 官方资料

### [S05] Explore the context window - Claude Code Docs
- 类型：Anthropic 官方产品文档，一手资料
- URL / 本地路径：https://code.claude.com/docs/en/context-window
- 事实使用：Claude Code 的 Context 包含会话与启动内容；`/compact` 用结构化摘要替换历史；文档逐项公开 project-root `CLAUDE.md`、auto memory、路径规则、嵌套规则、Skill body 和 Hook 在压缩后的保留或重载行为。
- 明确不声称：不固化页面中的版本号、Token 上限或重注入限额；不推断未公开摘要字段与内部 Prompt。
- 最后核对：2026-08-17
- 出版前复核：是

### [S06] How Claude Code works
- 类型：Anthropic 官方产品文档，一手资料
- URL / 本地路径：https://code.claude.com/docs/en/how-claude-code-works
- 事实使用：产品会先清理旧工具输出，再在需要时总结历史；早期会话指令可能丢失，持久规则应文件化；Resume 保持 Session，Fork 复制历史到新 Session，Subagent 使用隔离 Context。
- 明确不声称：不把文件 checkpoint 与对话 compaction、执行 Checkpoint 或远程副作用回滚混为一谈，也不据此评价模型优劣。
- 最后核对：2026-08-17
- 出版前复核：是

### [S07] Effective harnesses for long-running agents
- 类型：Anthropic 官方工程博客，一手案例
- URL / 本地路径：https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- 事实使用：文章在特定 Coding Agent 实验中用 initializer、增量任务、进度文件与 Git 历史跨 Context 交接，并明确观察到 compaction 单独使用仍可能留下不清晰的下一步。
- 明确不声称：不把案例转写成任意模型、任务或生产环境的因果定律，也不移植文章结果为本章实验数字。
- 最后核对：2026-08-17
- 出版前复核：是

### [S08] Harness design for long-running application development
- 类型：Anthropic 官方工程博客，一手案例
- URL / 本地路径：https://www.anthropic.com/engineering/harness-design-long-running-apps
- 事实使用：文章区分 compaction 与 context reset，说明 reset 需要更完整的结构化 handoff，并讨论任务分解、生成/评估分离以及额外编排成本。
- 明确不声称：不把文章中特定模型和前端任务的观察外推到所有 Agent；不声称多 Agent 或 Reset 总优于单 Agent 与连续 Session。
- 最后核对：2026-08-17
- 出版前复核：是

## LangGraph 与 LangChain 官方资料

### [S09] LangGraph Persistence
- 类型：LangChain 官方文档，一手资料
- URL / 本地路径：https://docs.langchain.com/oss/python/langgraph/persistence
- 事实使用：Checkpointer 持久化单个 thread 的 graph state，用于连续性、人工介入、time travel 与容错；Store 保存 graph state 外的跨 thread 应用数据；二者是互补系统。
- 明确不声称：不把 Checkpointer 写成长期 Memory Store，也不声称内存 Checkpointer 能跨进程重启持久化。
- 最后核对：2026-08-17
- 出版前复核：是

### [S10] LangChain Short-term memory
- 类型：LangChain 官方文档，一手资料
- URL / 本地路径：https://docs.langchain.com/oss/python/langchain/short-term-memory
- 事实使用：AgentState 的消息历史可由 Checkpointer 持久化；长会话可采用 trim、delete、summarize 或自定义策略，且删除与摘要对 graph state 的语义不同。
- 明确不声称：不把文档示例策略当作本章贯穿任务的最佳阈值，也不把消息摘要视为执行 Checkpoint。
- 最后核对：2026-08-17
- 出版前复核：是

## 原始研究

### [S11] Lost in the Middle: How Language Models Use Long Contexts
- 类型：TACL 原始同行评审论文
- URL / 本地路径：https://aclanthology.org/2024.tacl-1.9/
- 事实使用：论文在 multi-document question answering 与 key-value retrieval 上改变相关信息位置，观察到受测模型通常在相关信息位于输入开头或结尾时表现更好、位于中部时下降。
- 明确不声称：不外推为所有当前模型、所有任务或任意长度 Context 都必然呈 U 形；本章不复用论文结果作为自己的实验数据。
- 最后核对：2026-08-17
- 出版前复核：否

## 本书前章与本地可复验证据

### [S12] 第 4 章 Harness Engineering 正文与实验
- 类型：本地一手实现与写作基线
- URL / 本地路径：book/chapter4.md；chapter4/harness/；chapter4/tests/；chapter4/reports/harness-boundary-matrix.json
- 事实使用：用于冻结 Harness、权限、沙箱、审批、幂等、Verifier 与 Trace 的既有边界，避免第 6 章重写 Durable Loop；本章只新增 Context 生命周期责任。
- 明确不声称：Chapter 4 的单机教学实验不证明分布式事务、OS 沙箱完备性或生产 exactly-once。
- 最后核对：2026-08-17
- 出版前复核：是

### [S13] 第 5 章 Context Engineering 正文与实验
- 类型：本地一手实现与写作基线
- URL / 本地路径：book/chapter5.md；book/sources/chapter5-sources.md；chapter5/context/；chapter5/tests/；chapter5/reports/context-experiments.json
- 事实使用：复用 `ContextPacket`、`ContextBuildTrace`、SourcePolicy 与单次调用装配边界；第 6 章只解释未来 Packet 如何跨压缩、重启和恢复被重新构造。
- 明确不声称：不把第 5 章 UTF-8 字节预算称为 Token，不把静态 Packet 构建结果当成长任务连续性证明。
- 最后核对：2026-08-17
- 出版前复核：是

## 作者既有工程文章

### [S14] Agent 记忆系统：为什么 RAG 不等于 Memory
- 类型：本地工程文章，作者既有资料
- URL / 本地路径：docs/author-sources/phase-4/03-agent-memory-system.md
- 事实使用：用于校准 RAG、thread checkpoint 与跨任务 Memory 的中文概念边界，并保留“临时执行状态不自动升级为长期事实”的工程警示。
- 明确不声称：文章中的规则型 Memory demo 不是本章 Context compaction 实现，也不是生产 Memory 系统。
- 最后核对：2026-08-17
- 出版前复核：否

### [S15] Phase4 收口：把 MCP、Memory 和 Multi-Agent 串成一个 Runtime
- 类型：本地工程文章，作者既有资料
- URL / 本地路径：docs/author-sources/phase-4/05-agent-runtime-integration.md
- 事实使用：用于校准 Runtime 中 Memory、工具、Reviewer 与 Trace 的责任顺序，以及“模块单独成立不等于系统成立”的叙事方式。
- 明确不声称：该确定性 Runtime 没有实现第 6 章的压缩提交边界、Artifact 或 Rehydrator，也不证明真实模型能力。
- 最后核对：2026-08-17
- 出版前复核：否

### [S16] 从 AI Coding 到数字员工：一条系统学习 AI Agent 的路线
- 类型：本地工程与学习路线文章，作者既有资料
- URL / 本地路径：docs/author-sources/codex-tutorial/2026-08-12-from-ai-coding-to-digital-employee.md
- 事实使用：用于保持全书从 Model、Context、Harness、Tools 到 Agent Runtime 的读者路线，并校准第 5—7 章的章节衔接。
- 明确不声称：文章中的个人使用比例与经验不外推为行业统计，也不作为产品能力比较证据。
- 最后核对：2026-08-17
- 出版前复核：否

## 编排参考与用户资料

### [S17] 《深入理解 AI Agent：设计原理与工程实践》开源仓库
- 类型：第三方开源书与配套实验，编排参考
- URL / 本地路径：https://github.com/bojieli/ai-agent-book
- 事实使用：参考“章节正文 + 原创图 + 配套实验 + 可复现说明”的组织密度，以及先概念、后机制、再实验与边界的阅读节奏。
- 明确不声称：不复制其正文、图片、案例或实验数字；不把其当前目录、项目数和产品事实作为本章结论。
- 最后核对：2026-08-17
- 出版前复核：是

### [S18] 用户提供《AI学习资料.pdf》
- 类型：用户提供的二手资料，仅作可读性与术语校准
- URL / 本地路径：用户提供资料《AI学习资料.pdf》（未入库）
- 事实使用：本地文件共 23 页，PDF 元数据标记为 Microsoft Print To PDF 生成；当前文件无书签且无可提取文本层，因此本章只记录其存在与版面资料属性，不从中提取技术事实。
- 明确不声称：不用于产品事实、API 行为、论文结论或实验数字；在没有 OCR 与逐页人工核对前，不声称其中包含任何具体术语或观点。
- 最后核对：2026-08-17
- 出版前复核：是

## 第 6 章本地实验事实源

### [S19] Chapter 6 deterministic context-continuity lab
- 类型：本地一手实现、固定报告与 Trace
- URL / 本地路径：chapter6/context_continuity/；chapter6/experiments/；chapter6/reports/context-continuity.json；chapter6/reports/context-continuity-trace.jsonl
- 事实使用：支持五组策略与失败矩阵的字段保留、恢复决策、重复工作、误报完成、Trace 合同和 `serialized_bytes` 观察值；所有案例声明 `sample_count=1`。
- 明确不声称：不证明真实模型平均成功率、产品排名、生产压缩阈值、摘要事实保真度或业务副作用 exactly-once。
- 最后核对：2026-08-17
- 出版前复核：是

## 出版前复核清单

1. 重新打开 S01—S10，核对页面标题、URL、公开字段、默认行为与命令适用表面；
2. 对 OpenAI API compaction 明确区分 server-side 与 standalone 路径，并再次确认 opaque 输出处理规则；
3. 对 OpenAI Agents SDK 再次核对 Session、server-managed continuation、自动/手动 compaction 与恢复边界；
4. 对 Claude Code 再次核对 `/compact`、`/context`、Resume、Fork、Subagent 及压缩后重载表；
5. 对 LangGraph 再次核对 Checkpointer 与 Store 的作用域，不把框架术语投影成本书自定义 Artifact；
6. 重新运行 Chapter 4—6 测试与 Chapter 6 固定报告，确认正文数字和图表只来自当前 JSON；
7. 检查全章未出现密钥、本机绝对路径、产品排名句式或把 `serialized_bytes` 标成 Token 的表述；
8. 如需使用用户 PDF 的具体术语，先完成 OCR、逐页核对与页码记录；未完成前继续保持“只作二手版面资料”的限制。
