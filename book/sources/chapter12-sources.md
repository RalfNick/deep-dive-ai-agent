# 第 12 章来源与版本台账

核对日期：2026-09-20。

这份台账把四类证据分开记录：固定提交的源码阅读、当前网页的官方文档、本地已安装版本的运行测试，以及本章自己的可复现实验。网页文档用于解释概念；一旦网页示例与本地依赖的真实接口不一致，以锁定版本的源码和本地测试为实现依据。

## 版本合同

本章使用独立的 Python 3.11.15 虚拟环境，`pip check` 无依赖冲突。

| 组件 | 锁定版本 | 本地证据 |
| --- | --- | --- |
| OpenAI Python | 2.54.0 | 包元数据；没有真实模型请求 |
| OpenAI Agents SDK | 0.20.0 | 9 个原生 Runner、function tool、RunState 与审批恢复测试通过 |
| LangGraph | 1.2.11 | 7 个真实 StateGraph、interrupt 与跨进程恢复测试通过 |
| SQLite checkpointer | 3.1.1 | 与 LangGraph 适配器共同测试；只用于同步、轻量场景 |
| pytest | 9.1.1 | 本章行为测试 |
| pip-tools | 7.6.1 | 依赖工具版本记录 |
| uv | 0.11.15 | 三套 universal/hash 锁与项目环境安装 |

依赖输入和锁位于 `chapter12/requirements*.in` 与 `chapter12/requirements*.txt`。Pi 是 TypeScript 项目的源码研究对象，不进入本章 Python 依赖树。

## 接口复核结论

- LangGraph 1.2.11 的 `interrupt()` 会在恢复时从节点开头重放，因此写操作不能放在 interrupt 之前；本章把提议、审批、执行、观察拆成独立节点，并用宿主持久化账本防止重复副作用。
- `SqliteSaver` 3.1.1 适合演示与轻量同步工作负载，不把它包装成生产级多线程存储。
- OpenAI Agents SDK 0.20.0 的 `RunState` 是 SDK 运行快照，不是本章可信状态的唯一来源；恢复前仍由宿主检查 action、审批和工作区 manifest。
- 当前在线文档展示的 API 可能先于或晚于锁定包。本章不因网页出现新接口而升级依赖，也不把“文档写了”当成“本地行为已经验证”。

## 资料记录

### PI-README
- id: `PI-README`
- title: Pi Agent Harness 项目总览
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/README.md
- checked_at: 2026-09-20
- commit_or_version: 19451accdeec671c1f4da9eafac8fc270f510ef4
- local_claim: Pi 将 provider API、通用 Agent runtime 与 coding-agent CLI 分成独立包，并明确默认继承启动进程的权限。
- evidence_kind: source_reading

### PI-PACKAGES
- id: `PI-PACKAGES`
- title: Pi Agent Core 与 Coding Agent 包元数据
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/package.json
- checked_at: 2026-09-20
- commit_or_version: 0.86.1@19451accdeec671c1f4da9eafac8fc270f510ef4
- local_claim: 当前包名是 @earendil-works/pi-agent-core 与 @earendil-works/pi-coding-agent，二者在该提交均为 0.86.1。
- evidence_kind: source_reading

### PI-NAMESPACE
- id: `PI-NAMESPACE`
- title: Pi npm scope 迁移记录
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/CHANGELOG.md#0740---2026-05-07
- checked_at: 2026-09-20
- commit_or_version: changelog 0.73.1-0.74.0
- local_claim: 旧资料可能仍使用 @mariozechner 命名；0.73.1 至 0.74.0 记录了向 @earendil-works 包作用域的迁移。
- evidence_kind: source_reading

### PI-AGENT-CORE
- id: `PI-AGENT-CORE`
- title: Pi Agent Core README
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/agent/README.md
- checked_at: 2026-09-20
- commit_or_version: 0.86.1@19451accdeec671c1f4da9eafac8fc270f510ef4
- local_claim: Agent Core 提供有状态工具循环和事件流，模型流函数由调用方注入，核心层并不等于完整 coding product。
- evidence_kind: source_reading

### PI-AGENT-LOOP
- id: `PI-AGENT-LOOP`
- title: Pi Agent Loop 实现
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/agent/src/agent-loop.ts
- checked_at: 2026-09-20
- commit_or_version: 19451accdeec671c1f4da9eafac8fc270f510ef4
- local_claim: 循环在模型边界前转换上下文，校验工具参数，发出消息与工具生命周期事件，并把执行异常转为模型可见的错误结果。
- evidence_kind: source_reading

### PI-SDK
- id: `PI-SDK`
- title: Pi Coding Agent SDK
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/sdk.md
- checked_at: 2026-09-20
- commit_or_version: 0.86.1@19451accdeec671c1f4da9eafac8fc270f510ef4
- local_claim: SDK 把 AgentSession、SessionManager、ResourceLoader 和工具选择暴露给宿主；默认内置工具是 read、bash、edit、write。
- evidence_kind: source_reading

### PI-SESSIONS
- id: `PI-SESSIONS`
- title: Pi 会话格式与恢复语义
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/session-format.md
- checked_at: 2026-09-20
- commit_or_version: session format v3 in package 0.86.1
- local_claim: 会话以 JSONL 树记录消息、工具装载变化、压缩与分支摘要；系统消息按顺序重放后恢复当前提示词和工具集合。
- evidence_kind: source_reading

### PI-SECURITY
- id: `PI-SECURITY`
- title: Pi 安全边界
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/security.md
- checked_at: 2026-09-20
- commit_or_version: 0.86.1@19451accdeec671c1f4da9eafac8fc270f510ef4
- local_claim: 项目信任是资源加载门禁而非沙箱；内置工具和扩展默认拥有 Pi 进程本身的权限。
- evidence_kind: source_reading

### PI-CONTAINER
- id: `PI-CONTAINER`
- title: Pi 外部隔离方案
- official_url: https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/containerization.md
- checked_at: 2026-09-20
- commit_or_version: 0.86.1@19451accdeec671c1f4da9eafac8fc270f510ef4
- local_claim: 文档列出 Gondolin、Plain Docker、OpenShell 与 Docker Sandboxes 等外部边界，并提醒可写 bind mount 仍会改变宿主文件。
- evidence_kind: source_reading

### LANGGRAPH-INSTALLED
- id: `LANGGRAPH-INSTALLED`
- title: 本章锁定的 LangGraph 包
- official_url: https://pypi.org/project/langgraph/1.2.11/
- checked_at: 2026-09-20
- commit_or_version: 1.2.11
- local_claim: 本地适配器使用真实 StateGraph 和 interrupt，7 个框架测试验证暂停、审批、重启与完成路径。
- evidence_kind: installed_runtime

### LANGGRAPH-SQLITE-INSTALLED
- id: `LANGGRAPH-SQLITE-INSTALLED`
- title: 本章锁定的 LangGraph SQLite checkpointer
- official_url: https://pypi.org/project/langgraph-checkpoint-sqlite/3.1.1/
- checked_at: 2026-09-20
- commit_or_version: 3.1.1
- local_claim: 本地 LangGraph 适配器以 SqliteSaver 持久化 checkpoint，并用同一 run_id 作为 thread_id 跨进程恢复。
- evidence_kind: installed_runtime

### LANGGRAPH-INTERRUPTS
- id: `LANGGRAPH-INTERRUPTS`
- title: LangGraph Interrupts 官方文档
- official_url: https://docs.langchain.com/oss/python/langgraph/interrupts
- checked_at: 2026-09-20
- commit_or_version: online documentation checked 2026-09-20
- local_claim: interrupt 依赖 checkpointer 与 thread_id，恢复会从包含 interrupt 的节点开头重新执行，因此副作用必须幂等或移到可控边界。
- evidence_kind: official_docs

### LANGGRAPH-SQLITE
- id: `LANGGRAPH-SQLITE`
- title: LangGraph SqliteSaver 3.1.1 官方参考
- official_url: https://reference.langchain.com/python/langgraph.checkpoint.sqlite/SqliteSaver
- checked_at: 2026-09-20
- commit_or_version: 3.1.1
- local_claim: SqliteSaver 是同步 SQLite checkpointer，官方将其定位为演示和小型项目，而非多线程生产存储。
- evidence_kind: official_docs

### OPENAI-AGENTS-INSTALLED
- id: `OPENAI-AGENTS-INSTALLED`
- title: 本章锁定的 OpenAI Agents SDK
- official_url: https://pypi.org/project/openai-agents/0.20.0/
- checked_at: 2026-09-20
- commit_or_version: 0.20.0
- local_claim: 本地适配器用真实 Model、Runner、function_tool 与 RunState，9 个测试验证逐调用审批、序列化恢复和宿主二次校验。
- evidence_kind: installed_runtime

### OPENAI-AGENTS-HITL
- id: `OPENAI-AGENTS-HITL`
- title: OpenAI Agents SDK Human-in-the-loop 官方文档
- official_url: https://openai.github.io/openai-agents-python/human_in_the_loop/
- checked_at: 2026-09-20
- commit_or_version: online documentation checked 2026-09-20; local package 0.20.0
- local_claim: 工具可声明 needs_approval，Runner 暂停后可把结果转为 RunState，逐项 approve 或 reject，再交回原顶层 Agent 恢复。
- evidence_kind: official_docs

### OPENAI-RUNSTATE
- id: `OPENAI-RUNSTATE`
- title: OpenAI Agents SDK 0.20.0 RunState 源码
- official_url: https://github.com/openai/openai-agents-python/blob/v0.20.0/src/agents/run_state.py
- checked_at: 2026-09-20
- commit_or_version: v0.20.0
- local_claim: RunState 序列化包含审批、usage、工具输入与上下文等运行元数据；应用必须避免把凭据放入可持久化 context。
- evidence_kind: source_reading
