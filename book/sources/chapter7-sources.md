# 第 7 章资料台账：记忆工程

核对日期：2026-08-25。长期 Memory 的产品接口、默认加载方式、存储位置、阈值和 Beta 状态变化很快；出版前必须重新打开标记为“是”的官方页面。本章的固定实验只验证声明的写入、召回、修正、遗忘与隔离边界，不用于比较模型或产品能力。

## 使用原则

- 产品事实只使用厂商官方文档、官方工程博客或官方开源仓库；研究观点优先引用原始论文；
- “人类记忆”只作为有限分类类比，不暗示 Agent 具有人的主观体验、自然遗忘机制或同等认知结构；
- Semantic Memory 是事实或概念的存储类型，semantic search 是一种检索方法，二者不能混写；
- Session 历史、Checkpoint、Memory、RAG、规则文件与模型参数是不同状态表面；
- 本章只实现元数据过滤与确定性关键词排序，Embedding、向量库、混合召回和 RAGAS 留给第 8 章；
- 本地报告中的 UTF-8 字节数不是 Token 数；每案例 `sample_count=1`，不报告统计成功率；
- 官方产品行为只支持责任映射，不授权推断未公开的 Prompt、内部存储格式或模型能力。

## 教学编排参考

### [S01] Build a Large Language Model (From Scratch) companion hub
- 类型：作者官方图书配套站与官方代码仓库，教学编排参考
- URL / 本地路径：https://sebastianraschka.com/llms-from-scratch/；https://github.com/rasbt/LLMs-from-scratch
- 事实使用：官方学习路线采用先阅读、再按需观看、随后运行章节代码、最后用练习自检；代码仓库按章节提供主实现、补充材料和练习答案。本章借鉴“从最小部件逐层搭建”的学习顺序。
- 明确不声称：不复制该书文字、代码、插图或章节结构；该书讨论 LLM 构建，不是 Agent Memory 技术事实来源。
- 最后核对：2026-08-25
- 出版前复核：否

## 原始研究与评估

### [S02] Cognitive Architectures for Language Agents (CoALA)
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2309.02427
- 事实使用：论文提出包含模块化 Memory、内部/外部动作空间和决策过程的语言 Agent 认知架构，用于校准 working、episodic、semantic 与 procedural Memory 的分类来源。
- 明确不声称：分类是分析框架，不是唯一标准；本章教学实现不等同于论文完整架构，也不据此类比人的意识。
- 最后核对：2026-08-25
- 出版前复核：否

### [S03] Generative Agents: Interactive Simulacra of Human Behavior
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2304.03442
- 事实使用：论文系统保存自然语言经历、生成更高层 Reflection，并按需检索支持计划；消融覆盖 observation、planning 与 reflection 对其特定“可信行为”评价的贡献。
- 明确不声称：不把 25 个模拟角色的结果外推到 Coding Agent、企业助手或本章固定实验；不把 Reflection 自动生成的内容视为已验证事实。
- 最后核对：2026-08-25
- 出版前复核：否

### [S04] MemGPT: Towards LLMs as Operating Systems
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2310.08560
- 事实使用：论文用操作系统虚拟内存类比设计多层 Context/Memory 管理，并在文档分析与多会话对话任务中评估跨有限窗口搬运信息。
- 明确不声称：OS 类比不意味着文本 Memory 具备操作系统页表、隔离或事务保证；本章不复现其模型实验数字。
- 最后核对：2026-08-25
- 出版前复核：否

### [S05] LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory
- 类型：原始研究与公开 Benchmark
- URL / 本地路径：https://arxiv.org/abs/2410.10813
- 事实使用：Benchmark 将长期交互记忆拆成信息提取、跨 Session 推理、时间推理、知识更新和拒答，并公开 500 个问题的任务设计；用于提醒评估不能只看“有没有召回”。
- 明确不声称：不把论文对当时系统的聚合结果写成 2026 年产品排名，也不声称本章 15 个确定性案例复现了该 Benchmark。
- 最后核对：2026-08-25
- 出版前复核：否

### [S06] AMemGym: Interactive Memory Benchmarking for Assistants in Long-Horizon Conversations
- 类型：2026 年原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2603.01966
- 事实使用：论文提出带状态演进的交互式 Memory 环境和结构化指标，用于补充静态离线历史难以覆盖 on-policy 交互的问题；本章据此把修正与时间变化列为独立指标。
- 明确不声称：论文仍是特定生成环境与受测系统的研究结果；本章不移植其分数，也不证明自己的固定夹具具有相同覆盖率。
- 最后核对：2026-08-25
- 出版前复核：是

## LangGraph 与 LangChain 官方资料

### [S07] LangChain Memory overview
- 类型：LangChain 官方概念文档，一手资料
- URL / 本地路径：https://docs.langchain.com/oss/python/concepts/memory
- 事实使用：官方区分 thread-scoped short-term memory 与跨 thread 的 long-term memory；长期部分按 semantic、episodic、procedural 分类，并讨论 hot path 与后台写入。
- 明确不声称：不把人类记忆类比写成严格同构，不把文档当前类名和默认行为当作永久 API；本章先讲原理再做框架映射。
- 最后核对：2026-08-25
- 出版前复核：是

### [S08] LangGraph Persistence
- 类型：LangChain 官方文档，一手资料
- URL / 本地路径：https://docs.langchain.com/oss/python/langgraph/persistence
- 事实使用：Checkpointer 持久化 thread 的 graph state，Store 保存 graph state 之外、可跨 thread 访问的应用数据；二者可组合但作用域不同。
- 明确不声称：不把 Checkpointer 称为长期事实库，不声称内存实现可跨进程恢复，也不把 Store 本身等同于完善的 Memory Policy。
- 最后核对：2026-08-25
- 出版前复核：是

## Anthropic 与 Claude Code 官方资料

### [S09] How Claude remembers your project
- 类型：Anthropic 官方 Claude Code 文档，一手资料
- URL / 本地路径：https://code.claude.com/docs/en/memory
- 事实使用：官方当前区分由用户维护的 `CLAUDE.md` 与 Claude 自动维护的 auto memory；两者进入会话 Context，auto memory 使用项目级普通 Markdown 文件，可由用户审计、编辑或删除。
- 明确不声称：不把当前版本号、默认开关、目录、行数或字节阈值固化为长期契约；这些内容是 Context，不是强制权限边界。
- 最后核对：2026-08-25
- 出版前复核：是

### [S10] Explore the context window - Claude Code Docs
- 类型：Anthropic 官方 Claude Code 文档，一手资料
- URL / 本地路径：https://code.claude.com/docs/en/context-window
- 事实使用：官方公开 Context 可包含 `CLAUDE.md`、auto memory、工具名、Skill 描述、历史、文件与命令输出；压缩与 Memory 加载是不同生命周期动作。
- 明确不声称：不固化 Context 上限、清理阈值和版本行为；不把 auto memory 当作模型参数更新，也不推断内部选择算法。
- 最后核对：2026-08-25
- 出版前复核：是

## OpenAI、Agents SDK 与 Codex 官方资料

### [S11] Agent memory - OpenAI Agents SDK
- 类型：OpenAI 官方 SDK 文档，一手资料，当前为 Beta
- URL / 本地路径：https://openai.github.io/openai-agents-python/sandbox/memory/
- 事实使用：官方把 sandbox agent memory 与保存消息历史的 Session memory 明确分开；前者把未来运行可复用的经验提炼成 Workspace 文件，并支持不同 Agent 的 Memory layout 隔离。
- 明确不声称：Beta API、默认能力和目录可能变化；不把文件 Memory 写成所有 Codex 产品的内部实现，也不声称它自动保证事实正确或安全删除。
- 最后核对：2026-08-25
- 出版前复核：是

### [S12] Sessions - OpenAI Agents SDK for Python
- 类型：OpenAI 官方 SDK 文档，一手资料
- URL / 本地路径：https://openai.github.io/openai-agents-python/sessions/
- 事实使用：Session 在运行前取回对话历史、运行后保存新项；可使用不同后端和 compaction 包装器，解决的是会话连续性。
- 明确不声称：Session 不等于跨任务 Memory、业务 Checkpoint 或事实源；server-managed continuation 也不等于应用删除证明。
- 最后核对：2026-08-25
- 出版前复核：是

### [S13] Dreaming: Better memory for a more helpful ChatGPT
- 类型：OpenAI 官方产品/研究发布，一手资料
- URL / 本地路径：https://openai.com/index/chatgpt-memory-dreaming/
- 事实使用：OpenAI 当前把 Memory 评价目标公开为跨对话保留有用 Context、遵循偏好/约束和随时间保持最新，并说明后台综合需要处理陈旧、正确性和规模问题。
- 明确不声称：这是 ChatGPT 产品说明，不是公开的 Agents SDK 实现规范；官方图表结果不外推到本章 Runtime、其他模型或 Coding Agent。
- 最后核对：2026-08-25
- 出版前复核：是

### [S14] Inside OpenAI's in-house data agent
- 类型：OpenAI 官方工程案例，一手资料
- URL / 本地路径：https://openai.com/index/inside-our-in-house-data-agent/
- 事实使用：案例把历史查询、人工注释、机构知识、Memory 与实时查询分层；Memory 用于保留难以从其他层推断的修正、过滤条件和约束，并允许人工创建、编辑与作用域管理。
- 明确不声称：不移植内部规模和效果数字，不把案例架构当作所有组织的最佳方案；RAG 与数据平台部分留到第 8 章。
- 最后核对：2026-08-25
- 出版前复核：是

### [S15] Custom instructions with AGENTS.md - Codex
- 类型：OpenAI 官方 Codex 文档，一手资料
- URL / 本地路径：https://developers.openai.com/codex/guides/agents-md/
- 事实使用：`AGENTS.md` 是由人和仓库版本控制的持久项目指令表面，Codex 按公开发现规则把它装入任务 Context；用于与自动生成的长期 Memory 划清所有者边界。
- 明确不声称：不把 `AGENTS.md` 称为 Codex 自动 Memory，不推断 Codex 未公开的跨任务学习机制；发现顺序和限制需出版前复核。
- 最后核对：2026-08-25
- 出版前复核：是

## 本书前章、本章实现与作者既有资料

### [S16] 第 5—6 章 Context 与连续性边界
- 类型：本地一手正文、实现与固定报告
- URL / 本地路径：book/chapter5.md；book/chapter6.md；chapter5/context/；chapter6/context_continuity/；chapter6/reports/context-continuity.json
- 事实使用：冻结 Context、Session、RunState、Checkpoint、Artifact 与 Memory candidate 的既有分工；第 7 章从第 6 章停止的位置实现 Write、Recall、Correct 和 Forget。
- 明确不声称：前章压缩实验不证明长期 Memory；本章也不重写 Checkpoint、Artifact、Verifier 或副作用 exactly-once。
- 最后核对：2026-08-25
- 出版前复核：是

### [S17] Chapter 7 deterministic memory-engineering lab
- 类型：本地一手实现、固定报告和脱敏 Trace
- URL / 本地路径：chapter7/memory_runtime/；chapter7/fixtures/；chapter7/experiments/；chapter7/reports/memory-engineering.json；chapter7/reports/memory-engineering-trace.jsonl
- 事实使用：支持五组 15 个固定案例中的写入闸门、作用域硬过滤、可分解排序、连续版本、陈旧写入拒绝、Tombstone 与删除后解析行为；每案例 `sample_count=1`。
- 明确不声称：不证明真实模型质量、生产成功率、Embedding 召回、分布式事务、合规删除或产品排名；报告中的序列化字节不是 Token。
- 最后核对：2026-08-25
- 出版前复核：是

### [S18] Agent 记忆系统：为什么 RAG 不等于 Memory
- 类型：本地工程文章，作者既有资料
- URL / 本地路径：docs/author-sources/phase-4/03-agent-memory-system.md
- 事实使用：提供早期标准库 Memory demo、`MemoryPolicy`、中文 ID 冲突和 typed search 写回数据丢失案例；本章重新设计版本链、删除和隔离合同，并保留真实踩坑的叙事线索。
- 明确不声称：旧规则型 Demo 不是本章 Runtime，也不是生产 Memory 服务；原文测试数和输出不直接移植到本章报告。
- 最后核对：2026-08-25
- 出版前复核：否

### [S19] Phase4 收口：把 MCP、Memory 和 Multi-Agent 串成一个 Runtime
- 类型：本地工程文章，作者既有资料
- URL / 本地路径：docs/author-sources/phase-4/05-agent-runtime-integration.md
- 事实使用：用于校准“先 Recall、再计划，行动后才产生 Write candidate”的 Runtime 顺序，并使用其中一次疑问句误写 Memory 的真实 Bug 说明静默污染。
- 明确不声称：旧集成 Runtime 没有本章版本、删除与租户隔离合同，也不证明真实模型或 Multi-Agent 能力。
- 最后核对：2026-08-25
- 出版前复核：否

### [S20] 《深入理解 AI Agent：设计原理与工程实践》开源仓库
- 类型：第三方开源书与配套实验，编排参考
- URL / 本地路径：https://github.com/bojieli/ai-agent-book
- 事实使用：参考“正文、图、代码、练习”并行组织和概念—机制—实验—边界的章节密度；本章结合作者反馈进一步采用递进式最小实现。
- 明确不声称：不复制其文字、图片、案例、代码或实验结果；快变产品事实仍以本台账官方来源为准。
- 最后核对：2026-08-25
- 出版前复核：是

## 出版前复核清单

1. 重新打开 S07—S15，核对页面标题、Beta 状态、作用域、加载行为与当前 API；
2. 明确区分 Claude Code `CLAUDE.md`、auto memory 和 Session Context，不把任一表面写成权限强制；
3. 明确区分 OpenAI Agents SDK Session 与 sandbox agent memory，并保留 Beta 标记；
4. 对 Codex 只陈述 `AGENTS.md` 和仓库文件的公开持久表面，不推断自动长期 Memory；
5. 检查 Semantic Memory 与 semantic search 没有混写，第 8 章 RAG 内容没有提前展开；
6. 重新运行 Chapter 5—7 测试并连续生成 Chapter 7 三份报告，确认字节一致；
7. 检查每个正文实验数字都能回到 `memory-engineering.json`，未测字段继续使用 `null`；
8. 检查全章没有 Secret、作者机器绝对路径、产品排名、单案例“成功率”或 byte-as-Token 表述；
9. 核对删除段落没有把 Tombstone 夸大为物理删除、备份清除或合规证明；
10. 核对人类记忆类比始终有边界说明，没有把 Agent 写成具有人类主观记忆。
