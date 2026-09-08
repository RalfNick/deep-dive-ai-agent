# 第 10 章来源与事实边界

版本：v1.0；核对日期：2026-09-07；发布日期：2026-09-08。正文由本地实验组织，官方资料用于产品机制与标准语义，未复制书籍文字、原图或厂商评测结论。

## 官方来源

| ID | 来源 | 支持的具体陈述 | 不支持的延伸 |
| --- | --- | --- | --- |
| S01 | [OpenAI Tool search](https://developers.openai.com/api/docs/guides/tools-tool-search) | 托管/客户端执行搜索、延迟定义、命名空间与单函数初始可见信息不同 | 不声称所有模型与 SDK 支持一致，不用本地字节推算 API usage |
| S02 | [Anthropic Tool search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) | `defer_loading` 控制模型上下文；完整定义仍按当前合同传入请求；搜索入口保持可用 | 不等于无需网络上传或无需执行授权 |
| S03 | [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) | 用程序编排工具与筛选中间结果的思路 | 不引用宣传百分比，不把本章可信固定代码称为模型生成代码沙箱 |
| S04 | [Python 3.11 Coroutines and Tasks](https://docs.python.org/3.11/library/asyncio-task.html) | 协作调度、TaskGroup、CancelledError 与 wait_for 的取消行为 | 不把协程理解为多核加速或持久作业 |
| S05 | [SQLite Atomic Commit](https://www.sqlite.org/atomiccommit.html) | 本地数据库原子提交的背景及明确存储边界 | 不声称抵御全部硬件故障，也不延伸为外部 API 事务 |
| S06 | [AWS：Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) | 调用方意图标识、同键不同参数、原子记录与副作用边界 | 不把参数哈希当作业务意图，不承诺无限幂等保留窗口 |
| S07 | [LangChain Prebuilt middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) | LLMToolSelectorMiddleware 与 ProviderToolSearchMiddleware 的责任区别；always_include 不计入 max_tools | 不把文档中的模型支持范围当作本地已验证 SDK 集成 |
| S08 | [OpenAI Background mode](https://developers.openai.com/api/docs/guides/background) | 后台模型响应、轮询、取消、临时数据保留 | 不等于本地业务工具自动执行，也不固定快速变化的数据保留配置 |
| S09 | [MCP Tasks extension](https://modelcontextprotocol.io/extensions/tasks/overview) | 当前 Tasks 为需要双方支持的扩展，持久句柄、状态查询与合作取消 | 不把旧协议示例与当前扩展混用，不声称所有 MCP 客户端已支持 |
| S10 | [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | checkpointer 保存图状态；持久后端与内存后端不同 | 不从 checkpoint 推出外部副作用 exactly-once |

## 核对中避免的旧口径

- 没有把“延迟加载”写成“不向 API 发送定义”；请求平面与上下文平面分别解释。
- 没有照抄旧示例中关于 Background mode 必须 `store=true` 的断言。当前官方页面已给出不同保留行为，正文只保留机制与复核提醒。
- 没有把 MCP Tasks 写成所有客户端默认具备的核心协议功能，也没有依照旧任务 API 字段实现一份声称兼容当前协议的适配器。
- 框架与提供方文档里的支持模型下限并不总一致；正文不列快速变化的最低模型名单，不以某一层文档覆盖另一层的实际限制。

## 本地证据

| 证据 | 用途 | 主要限制 |
| --- | --- | --- |
| [catalog.py](../../chapter10/catalog.py) | 硬权限过滤、关键词检索、加载预算、版本与定义指纹 | 非中文自然语言分词；296 项是合成定义；不是真实连接器集合 |
| [concurrency.py](../../chapter10/concurrency.py) | 有限列表的固定 worker 并发、ID 归属与取消传播 | 不含无限输入流背压、不测网络吞吐 |
| [jobs.py](../../chapter10/jobs.py) | SQLite 作业状态、提交键、租约代次、取消、事务结果 | 可信调用者身份、逻辑时间；无外部 exactly-once、无自动调度守护进程 |
| [固定报告](../../chapter10/reports/tool-jobs-evidence.json) | 300/299/2、93,644/1,412 字节、6,000 分汇总与故障输出 | 不测模型质量、Token、成本、真实服务时延 |
| [事件流](../../chapter10/reports/job-events.jsonl) | 排队、领取、进度、提交与游标补读 | 只有状态事件，不是全业务 Trace |
| [行为测试](../../chapter10/tests) | 真实双连接竞争、事务中断回滚、结果授权、取消竞争 | 不是独立外部审计或生产安全证明 |

## 写作衔接

总纲以 [OUTLINE.md](../OUTLINE.md) 为准：本章不重写第九章 Schema/MCP 入门，不展开第十一章 Coding Agent 产品使用手册。沿用已确认的“从最小例子增加机制”的教学方法；没有从用户旧 PDF 取新引文，也不冒称本轮对旧 PDF 做过页级核查。

首次正式发布前需要复核 S01、S02、S07、S08、S09 的具体接入字段与产品可用性。候选稿没有 Live SDK 集成，不能只升级一个版本号就宣称真实接口已测。
