# Pi Agent 源码研究：一个 Coding Harness 怎样分层

> 研究边界：这是“源码阅读，不是产品运行记录”。核对时间为 2026-09-20，源码固定在提交 `19451accdeec671c1f4da9eafac8fc270f510ef4`。本章只做静态源码审读，没有安装或运行 Pi，没有调用它支持的任何模型，也不据此评价 Pi、Claude Code 或 Codex 的效果。Pi 是 TypeScript 参考实现，不是 Python 依赖。

## 先看全貌：Pi 不是一个 while 循环

项目的[总览源码](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/README.md)把系统分成三层：[PI-README]

1. `@earendil-works/pi-ai` 负责多模型、provider 与流式协议；
2. `@earendil-works/pi-agent-core` 负责 Agent 状态、工具循环和事件；
3. `@earendil-works/pi-coding-agent` 把前两层装配成 CLI、会话、资源加载与交互产品。

当前提交中的 `pi-ai`、`pi-agent-core` 和 `pi-coding-agent` 都标记为 `0.86.1`。[包元数据](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/package.json)使用 `@earendil-works/*` 作用域；旧文章中常见的 `@mariozechner/*` 已过时。项目 changelog 在 0.73.1—0.74.0 记录了 npm scope 迁移，因此阅读旧示例时不能直接复制 import。[PI-PACKAGES] [PI-NAMESPACE]

这层拆分给第 12 章的第一个启示是：模型适配、Agent Loop 和 Coding Agent 产品不是同一个东西。模型负责提出下一步；runtime 推进回合和工具协议；产品层再决定会话、资源、权限与用户交互。

## 阅读点一：模型适配和运行时怎样解耦

[Agent Core 文档](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/agent/README.md)显示，低层 `agentLoop()` 接受一个外部 `streamFn`；模型集合和 provider 注册位于 `pi-ai`，循环不需要把某一家 API 写死。[PI-AGENT-CORE]

这不是简单的“换一个模型名”。它把两种变化分开了：

- provider 差异由模型适配层吸收；
- tool call 之后是否继续、事件怎样发出、何时结束，由 Agent Core 决定；
- 会话落盘、技能发现、终端 UI 和默认工具，由 Coding Agent 决定。

本章 Python 实验采用同样的责任边界：`ChatModel` 只返回文本或一个结构化 `ToolCall`，`runtime` 和两个框架适配器负责推进状态，宿主服务负责策略、执行与验证。这样才能在保持决策脚本不变时比较外围 Harness。

## 阅读点二：上下文不是“把全部历史发给模型”

[agent-loop.ts](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/agent/src/agent-loop.ts)在每次模型请求前依次执行：

```text
AgentMessage[]
  -> transformContext（可选的裁剪、压缩或改写）
  -> convertToLlm（转成 provider 能理解的消息）
  -> normalizeContext
  -> streamFn（真正调用模型边界）
```

也就是说，持久化的会话历史、Agent 内部消息和模型本轮真正看到的输入是三件事。[PI-AGENT-LOOP] 这解释了为什么第 12 章会把“持久状态”和“上下文投影”分开：SQLite 中的事实不能因为超出模型窗口就消失；模型输入也不应包含每一条内部控制记录。

## 阅读点三：工具调用是一条协议，而不是一次函数调用

同一个 [agent-loop.ts](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/agent/src/agent-loop.ts#L434-L856)展示了较完整的工具生命周期：[PI-AGENT-LOOP]

1. 从 assistant message 中取得 tool call；
2. 在 `tool_execution_start` 事件保留 call id、工具名和原始参数；
3. 查找工具、准备参数并运行 schema 校验；
4. 让 `beforeToolCall` 决定是否阻止；
5. 按全局设置或单工具声明选择顺序/并行执行；
6. 通过 `tool_execution_update` 发送中间结果；
7. 把未知工具、参数错误、取消和异常变成显式错误结果；
8. 发出 `tool_execution_end`，再生成带 `toolCallId`、`toolName` 和 `isError` 的 tool-result message。

这里最值得借鉴的不是事件名称，而是“调用身份、完整参数、执行结果和失败语义没有被压扁成一段聊天文本”。不过，事件完整并不自动产生安全边界：`beforeToolCall` 是应用钩子，不等于操作系统强制隔离；有 tool result 也不等于任务已通过独立验收。

## 阅读点四：会话和资源加载属于 Harness

[Coding Agent SDK](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/sdk.md)把 `AgentSession`、`SessionManager` 和 `ResourceLoader` 作为独立对象暴露出来。[PI-SDK]

- `SessionManager` 可以使用内存会话，也可以创建、打开、继续或分叉落盘会话；
- `DefaultResourceLoader` 从工作目录和用户目录发现 extensions、skills、prompt templates、themes 与上下文文件；
- 默认内置工具是 `read`、`bash`、`edit`、`write`；`grep`、`find`、`ls`、`powershell` 等是可选择的内置工具，并非默认全部打开；
- 自定义 loader 后，资源发现策略由宿主接管，而工作目录仍影响路径解析和会话命名。

[会话格式](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/session-format.md)进一步说明，JSONL 会话是一棵可分支的树；消息、工具装载变化、压缩检查点和分支摘要按顺序重放后，才能得到当前上下文。[PI-SESSIONS]

这与“把 messages 数组序列化一下”有本质区别。一个可恢复 Coding Agent 至少要知道：当前运行属于哪个会话、停在哪个动作、哪些资源已装载、哪些副作用已完成，以及恢复时应该从哪一个稳定检查点继续。

## 阅读点五：项目信任不是权限系统，权限系统也不是沙箱

[安全文档](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/security.md)给出的边界很明确：[PI-SECURITY]

- project trust 决定是否加载项目本地设置、扩展、skills 和 packages；
- 它不是运行沙箱，也不会限制模型启动工具后能做什么；
- 内置工具、TypeScript 扩展以及它们启动的普通进程，默认继承 Pi 进程的用户权限；
- 对不可信仓库或无人值守任务，真正隔离应来自操作系统、容器、VM、micro-VM 或策略沙箱。

[容器化文档](https://github.com/earendil-works/pi/blob/19451accdeec671c1f4da9eafac8fc270f510ef4/packages/coding-agent/docs/containerization.md)列出了 Gondolin、Plain Docker、OpenShell 和 Docker Sandboxes 等组合方式。[PI-CONTAINER] 文档同时提醒：把宿主工作区以可写方式挂载进去，容器内写入仍会改变宿主文件；把宿主认证目录挂进去，也会把凭据和会话暴露给容器。

因此，本章不会把“工具 allowlist”“审批按钮”或“项目已信任”写成沙箱。前两者是控制平面，容器/VM 才是强制执行边界。当前机器未安装可用容器运行时，所以本章的容器隔离证据保持为 deferred，而不是悄悄退化成本地执行。

## 对第 12 章实现的影响

| Pi 源码给出的观察 | 本章采用的设计 | 本章额外强调的边界 |
| --- | --- | --- |
| provider、loop、coding product 分层 | Model、runtime/framework adapter、host services 分层 | 同一决策策略下比较 Harness，不比较模型能力 |
| 模型请求前有上下文投影 | 持久事实与模型上下文分离 | 压缩不能删除审批、执行回执和验收事实 |
| 工具有 call id、参数、错误和事件 | ToolCall、action_id、receipt、Trace 显式关联 | 写工具必须经过宿主策略、审批与幂等账本 |
| 会话与资源加载是产品能力 | SQLite RunState、恢复命令、固定工具注册 | framework checkpoint 不是唯一可信状态 |
| 默认继承用户权限，隔离在外部 | live 模式必须通过 container preflight | 不可用时失败关闭，不降级到 trusted_local |

## 这次研究没有证明什么

本研究没有运行 Pi，因此不能证明它的安装体验、模型质量、速度、成本、审批 UX 或隔离方案在本机可用。它也不能证明第 12 章的 Python 实现“等价于 Pi”。这里能支持的结论只有：一个真实开源 Coding Harness 如何划分模型、循环、上下文、工具事件、会话资源和外部隔离责任；这些边界可作为本章设计的对照材料。

LangGraph、OpenAI Agents SDK 与本章实验的来源和版本记录见 `book/sources/chapter12-sources.md`。[LANGGRAPH-INSTALLED] [LANGGRAPH-SQLITE-INSTALLED] [LANGGRAPH-INTERRUPTS] [LANGGRAPH-SQLITE] [OPENAI-AGENTS-INSTALLED] [OPENAI-AGENTS-HITL] [OPENAI-RUNSTATE]
