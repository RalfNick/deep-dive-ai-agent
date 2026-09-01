# Function Calling、Tool Runtime 与 MCP

- 左：模型 + Function Calling；工具定义 → 调用提议。
- 中：Tool Runtime；Schema → Policy → Executor → Receipt。
- 右：MCP；Host → Client → Server；连接 Tools / Resources / Prompts。
- 连接：模型提议进入 Runtime；Runtime 可调用本地 Handler 或远程 MCP Server。

底部结论：Function Calling 描述一次调用，MCP 标准化能力连接。
