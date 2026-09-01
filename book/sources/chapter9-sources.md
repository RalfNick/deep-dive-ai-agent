# 第 9 章来源台账：工具调用与 MCP

本台账只记录本章实际使用的一手来源和本地工程证据。网页事实最后核对日期统一为 2026-09-01；协议、SDK 与产品接口在出版前仍需再次复核。

### [S01] MCP 2026-07-28 规范首页

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28
- 用于：确认 MCP 使用 JSON-RPC 2.0、现代请求自包含，以及 Tool、Resource、Prompt 的定义边界。
- 不用于证明：不证明任何具体 SDK 已实现规范的全部可选能力。
- 最后核对：2026-09-01
- 出版前复核：是

### [S02] MCP 2026-07-28 发布说明

- 类型：官方博客
- 地址：https://blog.modelcontextprotocol.io/posts/2026-07-28/
- 用于：确认现代版本移除 `initialize`/`initialized` 握手与协议级 Session，并引入 `server/discover`。
- 不用于证明：不证明旧客户端已经消失，也不把无 Session 等同于应用无状态。
- 最后核对：2026-09-01
- 出版前复核：是

### [S03] MCP 架构

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/architecture
- 用于：确认 Host、Client、Server 的职责、1:1 Client–Server 关系，以及 Host 的授权和隔离责任。
- 不用于证明：不证明 Host 一定采用某种 UI 或审批实现。
- 最后核对：2026-09-01
- 出版前复核：是

### [S04] MCP 基础协议概览

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/basic
- 用于：说明请求、响应、错误、通知与 `_meta` 的基础位置。
- 不用于证明：不替代 JSON-RPC 2.0 原始规范。
- 最后核对：2026-09-01
- 出版前复核：是

### [S05] MCP 版本与兼容性

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
- 用于：区分现代 `2026-07-28` 与 `2025-11-25` 及更早握手模式。
- 不用于证明：不保证任意第三方 Client 与 Server 都能自动降级成功。
- 最后核对：2026-09-01
- 出版前复核：是

### [S06] MCP Server Discovery

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/server/discovery
- 用于：说明现代客户端如何发现服务器版本与能力。
- 不用于证明：不把发现等同于调用授权。
- 最后核对：2026-09-01
- 出版前复核：是

### [S07] MCP Prompts

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/server/prompts
- 用于：说明 Prompt 是用户选择的模板消息，而不是可以产生副作用的 Tool。
- 不用于证明：不证明 Prompt 内容天然可信或安全。
- 最后核对：2026-09-01
- 出版前复核：是

### [S08] MCP Resources

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/server/resources
- 用于：说明 Resource 以 URI 标识可读取上下文，本章 Runbook 因而建模为 Resource。
- 不用于证明：不证明 Resource 可以绕开访问控制或直接执行动作。
- 最后核对：2026-09-01
- 出版前复核：是

### [S09] MCP Tools

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- 用于：确认 `tools/list`、`tools/call`、输入输出 Schema、Tool Error 与人类同意建议。
- 不用于证明：不把 Tool 描述和 annotation 当成可信的强制安全边界。
- 最后核对：2026-09-01
- 出版前复核：是

### [S10] MCP stdio 传输

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/basic/transports#stdio
- 用于：说明本地进程通过标准输入输出传递 MCP 消息的边界。
- 不用于证明：不证明 stdio 天然安全或无需进程权限隔离。
- 最后核对：2026-09-01
- 出版前复核：是

### [S11] MCP Streamable HTTP 传输

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/basic/transports#streamable-http
- 用于：说明远程部署的 HTTP 传输、协议版本头与路由边界。
- 不用于证明：不提供生产网关、WAF、TLS 与容量规划的完整方案。
- 最后核对：2026-09-01
- 出版前复核：是

### [S12] MCP Authorization

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
- 用于：说明 HTTP 授权、资源服务器与授权服务器的协议责任。
- 不用于证明：不把 OAuth 登录成功等同于某个具体 Tool 已获业务授权。
- 最后核对：2026-09-01
- 出版前复核：是

### [S13] MCP 安全最佳实践

- 类型：官方规范
- 地址：https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices
- 用于：讨论 confused deputy、Token 透传、SSRF 与最小权限等风险。
- 不用于证明：不构成某个部署已经通过安全审计的结论。
- 最后核对：2026-09-01
- 出版前复核：是

### [S14] MCP Python SDK v2

- 类型：官方 SDK 仓库
- 地址：https://github.com/modelcontextprotocol/python-sdk
- 用于：锁定本章教学依赖 `mcp==2.1.1`，使用 `MCPServer` 与 `Client` 的官方 API。
- 不用于证明：不声称 2.1.1 会永久保持最新。
- 最后核对：2026-09-01
- 出版前复核：是

### [S15] MCP Python SDK v2 变更说明

- 类型：官方 SDK 文档
- 地址：https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md
- 用于：确认 v2 默认协商 `2026-07-28`，并保留 `mode="legacy"` 兼容测试路径。
- 不用于证明：不保证所有 v1 私有行为都能无修改迁移。
- 最后核对：2026-09-01
- 出版前复核：是

### [S16] MCP Python SDK Client 指南

- 类型：官方 SDK 文档
- 地址：https://py.sdk.modelcontextprotocol.io/client/
- 用于：核对 `list_tools`、`call_tool`、`list_resources`、`read_resource`、`list_prompts` 与 `get_prompt`。
- 不用于证明：不把 SDK 便利 API 当作 MCP 协议本身。
- 最后核对：2026-09-01
- 出版前复核：是

### [S17] MCP Python SDK 测试指南

- 类型：官方 SDK 文档
- 地址：https://py.sdk.modelcontextprotocol.io/testing/
- 用于：支持本章使用进程内官方 Server/Client 进行确定性测试。
- 不用于证明：不替代真实 stdio、HTTP、网络故障与鉴权集成测试。
- 最后核对：2026-09-01
- 出版前复核：是

### [S18] JSON Schema 2020-12

- 类型：正式规范
- 地址：https://json-schema.org/draft/2020-12
- 用于：界定 Tool 输入 Schema 的标准背景，并说明本章验证器只是八个关键字的教学子集。
- 不用于证明：不声称 `chapter9/tool_runtime/schema.py` 完整实现 JSON Schema 2020-12。
- 最后核对：2026-09-01
- 出版前复核：是

### [S19] JSON-RPC 2.0

- 类型：正式规范
- 地址：https://www.jsonrpc.org/specification
- 用于：解释 MCP 消息底座中的 Request、Response、Error、Notification 和 ID 关联。
- 不用于证明：不把 JSON-RPC 2.0 本身等同于 MCP。
- 最后核对：2026-09-01
- 出版前复核：是

### [S20] OpenAI Function Calling

- 类型：官方产品文档
- 地址：https://platform.openai.com/docs/guides/function-calling
- 用于：说明模型返回函数名、`call_id` 与 JSON 字符串参数，应用负责真正执行并回传结果。
- 不用于证明：不保证所有模型、接口与 Provider 返回完全相同的事件形态。
- 最后核对：2026-09-01
- 出版前复核：是

### [S21] OpenAI Remote MCP 与 Connectors

- 类型：官方产品文档
- 地址：https://platform.openai.com/docs/guides/tools-connectors-mcp
- 用于：说明 Responses API 可连接远程 MCP Server，并支持工具过滤与授权信息。
- 不用于证明：不把 Provider 托管调用等同于本章 Host 适配器实现。
- 最后核对：2026-09-01
- 出版前复核：是

### [S22] Anthropic Tool Use

- 类型：官方产品文档
- 地址：https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview
- 用于：说明 `tool_use`、`tool_result` 与 object 形式的 `input`。
- 不用于证明：不保证未来 Claude API 的所有工具类型都沿用同一字段集合。
- 最后核对：2026-09-01
- 出版前复核：是

### [S23] Anthropic MCP

- 类型：官方产品文档
- 地址：https://docs.anthropic.com/en/docs/mcp
- 用于：说明 MCP 与 Anthropic 产品、Messages API 和 Claude Code 的连接关系。
- 不用于证明：不把 MCP 视为只属于 Anthropic 的私有协议。
- 最后核对：2026-09-01
- 出版前复核：是

### [S24] LangChain Tools

- 类型：官方框架文档
- 地址：https://docs.langchain.com/oss/python/langchain/tools
- 用于：映射 `@tool`、结构化返回、错误处理和 LangGraph `ToolNode`。
- 不用于证明：不声称框架默认策略等同于本章自建 Runtime 的全部门禁。
- 最后核对：2026-09-01
- 出版前复核：是

### [S25] LangGraph 概览

- 类型：官方框架文档
- 地址：https://docs.langchain.com/oss/python/langgraph/overview
- 用于：区分低层编排 Runtime、Agent Framework 与 Harness 的职责。
- 不用于证明：不在本章展开持久执行与复杂图状态实现。
- 最后核对：2026-09-01
- 出版前复核：是

### [S26] Build a Large Language Model (From Scratch) 官方代码

- 类型：官方书籍配套仓库
- 地址：https://github.com/rasbt/LLMs-from-scratch
- 用于：借鉴“从最小实现逐步增加机制、图解与实验”的教学组织方法。
- 不用于证明：不复制该书文字、图片、代码或章节结构。
- 最后核对：2026-09-01
- 出版前复核：是

### [S27] 本章 Tool Runtime 与规范报告

- 类型：本地工程证据
- 地址：../../chapter9/reports/tool-mcp-evidence.json
- 用于：支持 5 组、20 个单样本边界实验及未测量字段为 `null` 的声明。
- 不用于证明：不证明真实模型质量、Provider Token、成本、延迟或产品优劣。
- 最后核对：2026-09-01
- 出版前复核：是

### [S28] 本章脱敏 Trace

- 类型：本地工程证据
- 地址：../../chapter9/reports/tool-mcp-trace.jsonl
- 用于：证明调用、结果、回执与最终状态之间的因果 ID 可以重放。
- 不用于证明：不包含原始参数、Runbook 正文、调用者身份或授权集合。
- 最后核对：2026-09-01
- 出版前复核：是

