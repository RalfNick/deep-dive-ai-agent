# 第 9 章“工具调用与 MCP”设计说明

状态：已由作者于 2026-08-31 确认。

## 目标

第 9 章回答一个具体问题：当模型已经能够输出一个看似正确的工具调用时，怎样把“模型提出动作”升级成“系统按照明确合同、安全地执行动作，并把可核验结果返回给模型”。

本章采用从零构建、逐步加能力的教学路径。读者先看到模型声称“故障单已经创建”但真实系统没有任何记录，再依次加入结构化调用、JSON Schema、工具注册表、运行循环、结构化结果、权限边界和 MCP。每增加一种抽象，都必须由前一个版本的可观察失败引出。

目标读者已经完成第 1–8 章，但不要求了解 JSON Schema、JSON-RPC、MCP 或运维系统。正文先用值班案例建立直觉，再显示协议字段和代码；框架映射、协议兼容和扩展能力放在主线之后。

## 写作方法

教学节奏参考 Sebastian Raschka 的《Build a Large Language Model (From Scratch)》（中文版《从零构建大模型》）及其官方代码仓库所采用的渐进实现方法：

1. 先用一个小而完整的实现建立机制直觉；
2. 每一步只增加一个核心能力，并展示加入前后的差异；
3. 同时提供解释、图、短代码、运行结果和练习；
4. 先手写核心机制，理解以后再映射成熟 SDK；
5. 主线代码、汇总代码、扩展实验和参考答案分开组织。

本章只借鉴教学方法，不复制原书文字、代码、图或版式。书稿保持《深入浅出 AI Agent》已有的工程证据、Claims/Non-claims 和版本台账规范。

## 核心判断

全章围绕一句话展开：

> 模型负责提出下一步动作，运行时负责让动作安全发生，MCP 负责让能力以统一协议被发现和调用。

这句话包含三个不能混淆的责任层：

1. 模型根据上下文选择工具并生成参数，但不会因为输出了 Tool Call 就自动产生现实副作用；
2. Harness 或应用运行时校验、授权、执行、回传并决定是否继续循环；
3. MCP 规范 Host、Client 和 Server 之间怎样发现及调用能力，不替代业务 API、权限系统、沙箱、审批或验收。

## 当前协议基线

截至 2026-08-31，本章以 MCP 协议修订版 `2026-07-28` 为事实基线，并使用当前稳定的官方 Python SDK `v2.1.1` 设计实验。

现代 MCP 是无状态协议：每个请求携带协议版本、身份和能力元数据；客户端可以使用 `server/discover` 发现服务器支持的版本和能力。`2025-11-25` 及更早版本采用 `initialize` 握手，属于本章需要解释的兼容路径，而不是现代主线。

正文必须明确核对日期，不把 SDK API 与协议规范混为一谈。发布前再次检查：

- MCP 最新规范、变更记录和弃用清单；
- 官方 Python SDK 最新稳定版本及迁移说明；
- OpenAI Function Calling 与 Remote MCP 文档；
- Anthropic Tool Use 与 MCP 文档；
- LangChain、LangGraph 的当前工具抽象。

## 与相邻章节的边界

- 第 3 章已经解释 Agent Loop；本章把工具合同、结果关联和 MCP 连接展开，不重新定义 Agent。
- 第 4 章已经建立 Harness、权限、沙箱、状态、审批、幂等和 Trace 的系统地图；本章只实现支撑工具调用所需的最小策略接口，不重写完整可靠性 Harness。
- 第 5–6 章负责上下文装配和长任务状态；MCP Resource 可以成为上下文来源，但 MCP Server 不应自动获得完整对话。
- 第 8 章负责 RAG 证据供应链；本章说明检索可以作为 Tool 或 Resource 暴露，但不重新实现检索质量与知识治理。
- 第 10 章负责大量工具、工具检索、延迟加载、后台任务、并发、取消和大规模幂等；本章只处理少量直接工具和基本错误。
- 第 11 章负责 Claude Code、Codex 等 Coding Agent 的仓库工具、Skills、Hooks 和 MCP 集成；本章不做产品功能百科。
- 第 12 章再把工具运行时组合成完整 Mini Coding Agent；本章实验保持领域无关和可独立验证。
- 第 13–14 章系统讲评估、Tracing 与生产诊断；本章只记录解释工具合同和失败所需的最小 Trace。

Sampling、Elicitation、Roots、MCP Apps、Tasks、Skills over MCP、Registry、完整 OAuth 和生产部署只进入进阶地图，不在本章实现完整系统。

## 贯穿案例：研发值班 Agent

贯穿案例是一套完全虚构的“星舟支付服务”值班系统。读者不需要运维背景；正文第一次出现值班、服务状态、部署和故障工单时均用日常语言解释。

用户提出：

> 支付服务从刚才开始大量超时。请确认当前状态和最近是否发布过版本；如果达到严重故障条件，就创建一张 P1 故障单。

系统提供：

- 当前服务状态和固定时间窗内的错误率；
- 最近部署记录；
- 当前有效的故障处理手册；
- 故障单存储；
- 创建高优先级故障单所需的审批策略。

正确处理需要先查询状态和部署，再根据手册判断严重级别；创建工单是副作用，必须经过校验和授权，并返回真实工单 ID。模型不能只凭一段自然语言宣布动作已经完成。

语料、服务指标、部署记录和工单系统都由固定 Fixture 提供，不调用真实生产系统，不冒充真实事故数据，也不需要 API Key。

## 教学主线：v0–v6

### v0：自然语言中的伪调用

固定决策策略输出“我已经创建 P1 故障单”，但工单存储为空。这个版本建立本章最重要的张力：语言上的完成不等于环境状态已经改变。

### v1：有 JSON 还不够

决策策略输出工具名和 JSON 参数。实验分别注入缺失必填字段、错误类型、多余字段和逻辑上不可能的参数，说明“能解析”不等于“符合工具合同”。

### v2：工具定义、注册与结构化结果

加入 `ToolDefinition`、JSON Schema、`ToolRegistry`、`ToolCall` 和 `ToolResult`。工具名只有经过注册才能派发；结果必须保留 `call_id`，并区分成功、参数错误、业务错误、权限错误和执行错误。

### v3：形成可观察的 Tool Loop

运行时执行“模型提议—Schema 校验—策略判断—工具执行—结果回传—模型继续”的最小闭环。固定策略依次查询服务状态、查询部署并提出创建工单。Trace 显示每一步输入、输出和因果关系。

### v4：副作用、授权与执行回执

查询工具可以直接执行；创建故障单需要审批令牌和明确的动作摘要。执行成功必须返回不可由模型伪造的 `ExecutionReceipt`。这里只建立工具合同所需的接口，检查点、恢复和完整幂等账本仍属于第 4、10 章。

### v5：把能力封装成 MCP Server

使用官方 Python SDK 暴露：

- Tool：`get_service_status`、`list_recent_deployments`、`create_incident_ticket`；
- Resource：`runbook://payments/current`；
- Prompt：`triage-incident`。

读者通过实际发现结果理解 Tool、Resource 和 Prompt 不是三种命名风格，而是控制关系不同的协议原语。

### v6：MCP Client、兼容与失败

实现最小 MCP Client，完成服务器发现、工具列表、Resource 读取、Prompt 获取和 Tool 调用；随后注入不支持的协议版本、未知工具、输入错误、权限拒绝、暂时执行错误和伪造回执。

现代 `2026-07-28` 请求是主线；旧版 `initialize` 仅用于解释兼容性。实验不要求读者手写 JSON-RPC Server，也不把一个自制的 “MCP-like” 协议当成 MCP。

## 核心合同

`ToolDefinition` 至少包含：

- `name`、`description`；
- `input_schema`；
- 可选 `output_schema`；
- `risk_level` 与是否产生副作用；
- 供 Host 使用的策略元数据。

`ToolCall` 至少包含：

- 稳定 `call_id`；
- `tool_name`；
- `arguments`；
- 产生调用的步骤标识。

`ToolResult` 至少包含：

- 与请求对应的 `call_id`；
- `status`；
- 成功时的结构化 `data`；
- 失败时的 `error_code`、`message` 和 `retryable`；
- 可选 `receipt`。

`ExecutionReceipt` 至少包含：

- 由执行器产生的 `action_id`；
- 被执行的工具与参数摘要；
- 外部系统返回的实体 ID；
- 结果状态和固定实验时钟；
- 可验证的 Fixture 状态摘要。

模型输出不能直接构造可信执行回执；回执必须来自执行边界。

## 实现边界与文件职责

`chapter9/` 采用渐进主线与模块化汇总并存的结构：

```text
chapter9/
├─ README.md
├─ requirements.txt
├─ reference-answers.md
├─ fixtures/
│  ├─ service-status.json
│  ├─ recent-deployments.json
│  └─ runbooks/
├─ tool_runtime/
│  ├─ contracts.py
│  ├─ schema.py
│  ├─ registry.py
│  ├─ policy.py
│  ├─ runtime.py
│  └─ trace.py
├─ incident_domain/
│  ├─ queries.py
│  └─ tickets.py
├─ mcp_app/
│  ├─ server.py
│  ├─ client.py
│  └─ adapter.py
├─ experiments/
│  ├─ run_v0_free_text.py
│  ├─ run_v1_schema.py
│  ├─ run_v2_tool_loop.py
│  ├─ run_v3_mcp.py
│  ├─ run_v4_failures.py
│  └─ run_all.py
├─ reports/
└─ tests/
```

基础 Tool Runtime 只使用 Python 标准库。MCP 层使用固定版本的官方 SDK。SDK 缺失时，基础实验仍可运行；MCP 测试必须显式报告跳过或给出安装命令，不能静默伪造成功。

`experiments/` 为读者保留逐步构建路径，`tool_runtime/` 与 `mcp_app/` 保存最终可复用实现。README 提供一条从零运行路径和一条只看最终版本的快速路径。

## 五组实验

### 实验一：自由文本、可解析 JSON 与合法 Tool Call

固定相同意图，比较自然语言、语法正确但合同错误的 JSON 和通过 Schema 的调用。记录解析状态、Schema 错误路径和工具是否进入执行边界。

### 实验二：Tool Loop 与结果关联

固定决策策略依次查询状态和部署，再根据结果决定是否创建工单。实验显示 `call_id` 如何把调用与结果对应起来，以及缺失或错配结果怎样阻止继续执行。

### 实验三：权限、错误与执行回执

分别注入无审批、错误严重级别、暂时执行失败、永久业务失败和模型伪造成功。记录策略拒绝数、真实副作用数、结构化错误和回执完整性。

### 实验四：MCP 三原语与 Host 边界

使用官方 SDK 发现并调用 Tool、读取 Resource、获取 Prompt。检查 Server 是否只收到当前请求所需的信息，以及 Host 是否保留上下文装配、用户同意和跨 Server 协调责任。

### 实验五：协议版本与兼容性

比较现代 `2026-07-28` 请求、旧版初始化路径和不支持版本错误。展示 `server/discover` 与每请求能力声明，不将 SDK 内部行为冒充协议强制要求。

所有规范实验固定 Fixture、决策策略、时钟、调用 ID、动作 ID、排序、错误注入和序列化格式。JSON、Markdown 和脱敏 JSONL 连续生成必须字节一致。没有真实 Provider 时，Token、成本、模型延迟和模型质量字段使用 `null`。

## 可选真实实验

Live Probe 可使用环境变量提供的 DeepSeek、OpenAI 或 Anthropic 凭据，验证不同 Provider 的 Tool Call 适配层：

- 将 Provider 原生 Tool Call 转换成统一 `ToolCall`；
- 将统一 `ToolResult` 转换成 Provider 所需的结果消息；
- 记录模型是否选择正确工具、参数是否通过校验和循环次数；
- 比较协议形状，不进行厂商能力排名。

Live Probe 缺少依赖或凭据时必须显式跳过；输出写入 Git 忽略目录，不覆盖规范报告。仓库不提交 Key、请求收据、完整请求头或不可复现的模型生成基准。

## 图表与视觉规范

计划 8 幅原创图：

1. 竖版主信息图：一次工具调用如何真正发生；
2. 自然语言、结构化输出、Function Calling、API 与 MCP 的边界；
3. Tool Definition、Tool Call、Tool Result 与 Execution Receipt 合同拆解；
4. 模型、Harness 和工具之间的 Tool Loop；
5. MCP Host、Client、Server 架构与信任边界；
6. Tools、Resources、Prompts 的控制关系；
7. 现代 MCP 与旧版握手协议对照；
8. 参数错误、权限拒绝、执行失败和伪造回执故障地图。

视觉参考作者提供的中文手绘教学信息图：

- 米白纸张背景、深蓝手绘线框；
- 蓝、绿、紫、橙低饱和分区；
- 大号步骤数字、清晰箭头、少量易懂图标；
- 中文解释为主，必要技术词保留英文；
- 每张图底部用一句话收束结论；
- 保持纸张纹理和轻微手绘不规则感，但不得降低可读性。

主信息图使用竖版 `2:3`、`linear-progression + hand-drawn-edu`；正文支持图使用横版 `16:9`，按内容选择 `linear-progression`、`structural-breakdown`、`binary-comparison` 或 `dense-modules`，统一使用 `hand-drawn-edu` 风格。

生成式图只承担概念、关系和流程。精确 JSON、Schema、协议字段、版本号和错误码由正文代码块承载，避免图片文字错误损害技术准确性。每张图保存独立提示词和参考图记录，生成错误时重新生成，不在位图上覆盖修字。

## 正文章节结构

正文目标 2.5 万至 3 万有效中文字符、20–35 个二三级标题。第一次阅读只沿 v0–v6 前进；协议兼容、框架映射、安全细节和扩展能力放在进阶层。

正文顺序：

1. 模型说“故障单已创建”，系统为什么查不到；
2. 阅读提示、全章短答案和中文术语表；
3. Tool、结构化输出、Function Calling、API 与 MCP 边界；
4. v0–v4 手写工具合同与 Tool Loop；
5. MCP 为什么出现，以及 Host、Client、Server 架构；
6. v5–v6 MCP Server、Client、三原语与协议兼容；
7. Function Calling、MCP、Skills 和插件对照；
8. OpenAI、Anthropic、LangChain 和 LangGraph 责任映射；
9. 失败、安全、成本和什么时候不需要 MCP；
10. 实验复现、本章小结、Claims 与 Non-claims；
11. 14 道分层练习、参考答案和第 10 章衔接。

## 可读性门禁

- 每个抽象名词第一次出现前给出值班案例中的具体动作；
- 每次只引入一个核心抽象，并显示加入前后的输入、关键中间状态和输出；
- 先给生活化或工程化解释，再显示 Schema 和 JSON-RPC 字段；
- Tool 与 API、Schema 校验与业务校验、Tool Result 与最终回答、MCP 与 Function Calling 等易混概念使用对照表；
- 正文代码片段保持一屏可读，完整代码留在 `chapter9/`；
- 每个实验同时写明支持的结论和不支持的结论；
- 第一次阅读可在完成 v6 后直接进入小结，不必先读所有协议扩展；
- 不使用“显而易见”“只需”“简单地”等贬低读者疑问的表达；
- 首次出现 SRE、P1、Runbook 等领域词时立即给中文解释。

每个主要小节优先遵循以下节奏：失败或问题—直觉图—最小代码—中间输出—边界与限制—下一步。

## 安全与信任边界

工具名称、描述、Schema、注解、Resource 内容和 Server 返回值都可能来自不可信服务器。Host 不能因为协议格式合法就默认内容可信。

至少覆盖：

- 最小权限和显式用户同意；
- 读操作与副作用操作分级；
- Host 策略与 Server 业务授权的双重边界；
- Resource 或 Tool Result 中的 Prompt Injection；
- 恶意工具描述、同名工具和结果欺骗；
- 本地 `stdio` Server 的进程权限与环境变量；
- 远程 HTTP Server 的认证、来源和数据外发风险；
- 日志脱敏和错误信息最小暴露。

MCP 规定通信合同，但不能代替沙箱、审批、授权、供应链验证和业务验收。

## 练习与答案

设计 14 道练习，覆盖：

- 工具边界与责任判断；
- JSON Schema 修改；
- 输入错误定位；
- `call_id` 关联；
- 结构化错误设计；
- 副作用审批；
- Tool、Resource、Prompt 分类；
- Host、Client、Server 责任；
- 现代与旧版协议兼容；
- `stdio` 与 Streamable HTTP 选择；
- 恶意 MCP Server 威胁建模；
- Function Calling、MCP、Skills 和插件选型；
- 为新领域设计 MCP Server；
- 为第 10 章设计大规模工具发现接口。

`chapter9/reference-answers.md` 对每题给出预期推理、常见错误和可检查验收。涉及代码修改的题先要求添加失败测试。

## 资料台账

`book/sources/chapter9-sources.md` 至少记录：

- MCP `2026-07-28` 规范、架构、版本兼容、Server 原语、传输和安全文档；
- 官方 MCP Python SDK、版本说明和测试文档；
- OpenAI Function Calling、Remote MCP 与 Skills 官方文档；
- Anthropic Tool Use、MCP 和 Agent Skills 官方文档；
- JSON Schema 与 JSON-RPC 规范；
- LangChain 与 LangGraph 官方工具文档；
- 《Build a Large Language Model (From Scratch)》只用于记录教学方法参考。

快变事实必须标注核对日期。博客数据、产品示例和实验结果不得外推为普遍性能结论。

## 发布物与仓库同步

实现完成时新增或修改：

- `book/chapter9.md`；
- `book/images/fig9-1-*` 至 `fig9-8-*`；
- `book/sources/chapter9-sources.md`；
- `book/reviews/chapter9-review-codex.md`；
- `chapter9/README.md`、`requirements.txt`、`reference-answers.md`；
- `chapter9/tool_runtime/`、`incident_domain/`、`mcp_app/`、`fixtures/`、`experiments/`、`reports/`、`tests/`；
- 图片分析、结构化内容、生成提示和参考图记录；
- `README.md`、`book/README.md`、`book/manifest.json`、`docs/EXPERIMENT_STATUS.md`；
- `scripts/build_site.py`、`mkdocs.yml`、仓库合同测试和第 8 章下一章链接。

Manifest 更新为 9 章已发布、9 章规划中，版本更新为 `0.9.0`。不创建英文翻译或繁体中文目录。

## 测试与完成条件

实现遵循 TDD：先让仓库合同接受第 9 章文件，再为每个 Runtime 边界写失败测试，最后写正文和发布接入。至少验证：

- JSON Schema 必填字段、类型、额外字段和错误路径；
- 未注册工具、重复 `call_id` 和结果错配；
- 查询工具与副作用工具的策略差异；
- 参数错误、业务错误、权限错误、暂时错误和永久错误；
- 执行回执不能由模型结果替代；
- Tool Loop 的步骤、停止条件和因果 Trace；
- MCP Tools、Resources、Prompts 的发现与调用；
- 现代协议版本、能力元数据、`server/discover` 和兼容错误；
- Server 不接收完整对话，Host 保留安全和上下文责任；
- 5 组实验、规范报告复现和 Trace 脱敏；
- 正文字数、8 幅图、14 道练习、14 份答案和来源字段；
- 第 1–8 章回归、渲染器、严格 MkDocs 构建和 Git 历史安全扫描。

完成标准是正文、实验、报告、图、练习、答案、来源、Review、导航和状态台账全部一致；规范报告连续生成字节一致；所有公开测试与 GitHub CI 通过；Pages 页面能读取正文、实验和答案；工作树无 Secret、作者绝对路径、缓存、Live 输出和构建物。

## Non-goals

本章不声称确定性决策策略代表真实模型能力，不使用小案例比较 Provider 或框架，不声称 JSON Schema 能保证业务安全，不把 MCP 当成权限系统或沙箱，不把 Tool Result 等同于事实正确，不实现生产级 OAuth、服务发现或分布式任务，也不证明教学 Server 已具备生产可靠性。
