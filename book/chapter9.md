# 第 9 章 工具调用与 MCP：从“模型想做”到“系统真的做了”

> 模型提出工具调用，只代表它想做一件事；只有 Runtime 校验、授权、执行并返回可关联的结果，这件事才真正发生。

## 开场：一句“故障单已创建”，为什么可能什么都没发生

本章使用虚构的“星舟支付服务”值班事件，从一句没有证据的完成声明出发，逐步构造可靠的工具合同、执行循环与 MCP Server。

## 阅读提示：先抓住一条主线

阅读时反复追问四件事：谁提出动作、谁允许动作、谁执行动作、谁证明动作完成。

## 先给短答案：Tool Calling 与 MCP 分别解决什么

Tool Calling 约定模型如何提出结构化动作；Tool Runtime 决定动作是否执行；MCP 让 Host 以标准协议发现和调用外部能力。

## 一张边界地图：Model、Runtime、Host、Client 与 Server

本节建立全章角色地图，后续所有代码都回到这张图定位。

## 从零构建：七个版本只改变一个关键边界

### v0：自由文本为什么会误报完成

模型可以写出“已创建”，但系统没有工具调用、外部 ID 或执行回执。

### v1：有 JSON 还不等于有合同

JSON 解决可解析性，却没有自动解决字段缺失、额外字段、类型错误和枚举越界。

### v2：ToolDefinition、ToolCall 与 ToolResult

我们把“工具是什么”“模型提议了什么”“系统执行出了什么”拆成三个不可混淆的对象。

### v3：把单次调用接成 Tool Loop

每个结果必须通过 `call_id` 回到对应提议，成为下一步决策可见的新事实。

### v4：授权与回执让副作用可证明

写工具需要 Host 授权；成功返回必须携带由 Runtime 构造的可信回执，模型不能自报完成。

### v5：把同一能力暴露为 MCP Server

三个 Tool、一个 Runbook Resource 和一个 Prompt 使用官方 `MCPServer` 注册。

### v6：MCP Client、现代协议与旧版兼容

官方 `Client` 默认协商 `2026-07-28`，`mode="legacy"` 只用于验证较早握手路径。

## 进阶阅读：协议不是工具函数的另一种写法

### Tool、Resource、Prompt 为什么不能混在一起

三种原语分别代表模型动作、上下文读取与用户选择的模板消息。

### JSON-RPC 是消息底座，MCP 是能力协议

JSON-RPC 提供请求、响应和 ID；MCP 在其上定义角色、能力、原语、版本、传输与安全语义。

### 2026-07-28：无握手不等于无状态

现代协议请求自包含；应用需要状态时，应使用显式 Handle、数据库或扩展，而不是把状态藏进传输 Session。

### stdio 与 Streamable HTTP 如何选择

本地子进程与远程服务面对不同的部署、权限、网络和审计边界。

### Host 授权与 Server 授权为什么要同时存在

Host 保护用户意图，Server 保护资源；任何一层都不能假设另一层永远正确。

### LangChain、LangGraph 把哪些代码替你写了

框架可以提供工具包装、ToolNode、路由与错误处理，但业务权限、数据边界和验收证据仍由应用定义。

## 实验复现：固定模型决策，只比较系统边界

配套实验入口见 [chapter9/README.md](../chapter9/README.md)。三份规范证据分别为 [JSON 报告](../chapter9/reports/tool-mcp-evidence.json)、[可读报告](../chapter9/reports/tool-mcp-evidence.md) 与 [脱敏 Trace](../chapter9/reports/tool-mcp-trace.jsonl)。

## 本章小结

工具调用是一项提议，执行是一条受控管道，MCP 是跨 Host 与 Server 的能力协议。

## Claims：本章已经证明什么

- 固定 Tool Runtime 可以拒绝无效参数、未授权写入和伪造回执。
- 官方 MCP SDK 可以发现并调用 Tool、Resource 与 Prompt。

## Non-claims：本章没有证明什么

- 没有比较真实模型或产品能力。
- 没有测量 Provider Token、成本和网络延迟。
- 没有完成生产级 OAuth、远程部署或长任务调度。

## 分层练习

本章安排 14 道练习，参考答案见 [reference-answers.md](../chapter9/reference-answers.md)。

## 与第 10 章“工具系统进阶”的衔接

当单个工具合同和 MCP 边界清晰之后，下一章再讨论大规模工具发现、并发、异步、取消、超时和结果治理。
