# 工具调用的四份合同

1. Tool Definition：名称、描述、输入 Schema、风险。
2. Tool Call：Call ID、Tool 名、Arguments、Step ID。
3. Tool Result：状态、数据或错误、Call ID。
4. Execution Receipt：Action ID、外部 ID、参数摘要、时间。

控制者：应用定义 → 模型提议 → Runtime 返回 → 执行边界签发。

底部结论：合法调用需要定义、请求、结果和回执四份合同。
