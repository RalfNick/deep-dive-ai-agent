# 现代 MCP 与旧版握手模式

左：2026-07-28；请求自带协议版本、Client 身份、Client 能力；server/discover 可选；直接请求。

右：2025-11-25；initialize → initialized → 后续请求；依赖初始化生命周期。

两边底部：业务状态用显式 ID 与持久存储。

底部结论：现代 MCP 每次请求自描述，旧版靠初始化握手。
