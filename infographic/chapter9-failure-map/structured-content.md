# 工具调用失败地图

模型输出 → JSON 解析 → Schema → Registry → Host Policy → Server Policy → Executor → Result / Receipt → 模型上下文。

对应风险：格式错误；参数注入；未知 Tool；未同意；越权；业务错误 / 执行异常 / 超时未知；错配 / 伪造；结果注入 / 数据外泄。

底部结论：格式正确只是起点，安全执行需要多道边界。
