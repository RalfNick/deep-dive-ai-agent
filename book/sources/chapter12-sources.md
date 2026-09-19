# 第 12 章来源与版本台账

核对日期：2026-09-19。状态：实现中；以下是实际安装和读取的接口证据，不是框架对照实验已经通过的声明。

## 版本合同

项目独立 Python 3.11.15 虚拟环境，`pip check` 无依赖冲突。

| 组件 | 实装版本 | 当前证据 |
| --- | --- | --- |
| OpenAI Python | 2.54.0 | 包元数据，尚未真实调用模型 |
| OpenAI Agents SDK | 0.20.0 | Model、Runner、RunState 签名检查 |
| LangGraph | 1.2.11 | 包元数据，编排测试尚未执行 |
| SQLite checkpointer | 3.1.1 | 包元数据 |
| pytest | 9.1.1 | 本章行为测试 |
| pip-tools | 7.6.1 | 核心锁解析完成；框架解析延迟后切换统一锁工具 |
| uv | 0.11.15 | 三套 universal/hash 锁与项目环境安装 |

依赖输入和锁分别在 `chapter12/requirements*.in`、`chapter12/requirements*.txt`。`uv pip compile --universal --generate-hashes --no-header` 生成锁，安装前以 hash 校验；“解析到最新版本”本身不是功能验证。

### SDK 实装接口

- `Model.get_response` 接收 system_instructions、input、model_settings、tools、output_schema、handoffs、tracing，以及关键字 previous_response_id、conversation_id、prompt，返回 ModelResponse。
- `Runner.run` 接收 Agent 和消息或 RunState，支持 context、max_turns、hooks、run_config、session 等参数。
- `RunState.to_json` 返回字典；`include_tracing_api_key` 默认 False。应用仍需控制 context_serializer，不能因该默认值就断言上下文没有凭据。
- `RunState.from_json(initial_agent, state_json, ...)` 支持 context_override 和 context_deserializer。恢复时要重建真实工具与宿主服务，不能把 Services 实例任意序列化进快照。

这些记录来自已安装包的 inspect.signature；功能行为由后续适配器测试验证。Pi 提交级源码及逐项事实引用在源码研究任务完成后追加，不能将尚未进行的研究写成既成事实。
