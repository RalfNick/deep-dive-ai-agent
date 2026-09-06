# 第 9 章补充问答：工具合同与 MCP 边界

这是从正文移出的 22 个完整问答，供实现和排错时按需查阅。首次学习请先阅读[第 9 章正文](../book/chapter9.md)。保留原有编号，便于对照旧版笔记。

**1. 模型选择了正确 Tool，为什么还要 Registry？**

因为“名字正确”只是模型提议。Registry 是执行方维护的可信映射，它决定当前进程真正提供哪些能力，以及每个名字绑定哪个 Handler。没有 Registry，代码可能用动态反射调用任意函数；工具名一旦受模型控制，就扩大了执行面。Registry 还应拒绝重复注册，避免加载顺序改变行为。

**2. Provider 已经支持 Strict Function Calling，还要本地验证吗？**

Strict 模式能显著提高模型输出符合所声明 Schema 的概率，但应用仍应在信任边界验证。调用可能来自缓存、重放、旧 Client、测试 Fixture 或被篡改的中间层；Provider 支持的 Schema 子集也不一定等于业务全部约束。防御性验证成本低，失败语义更清楚。

**3. 所有读 Tool 都可以自动允许吗？**

不一定。“读”也可能泄露工资、客户数据、密钥、医疗信息或私人文件。本章把固定服务快照设为自动 Allow，只是案例策略。生产系统应同时考虑数据敏感度、调用者身份、Resource 范围、输出去向和请求频率。只读描述也可能是恶意 Server 的谎言。

**4. 为什么 `approval_required` 不设成可重试？**

因为自动重放相同请求不会产生用户同意。这里的不可重试是对当前自动策略而言，不是永久禁止。Host 收到真实同意后，应构造新的授权上下文和新的 Call ID。若把等待同意当作暂时网络错误，Agent 可能在后台不断弹窗或绕过用户意图。

**5. Receipt 能证明一切吗？**

不能。Receipt 的可信度取决于生成边界和后端语义。本章内存 Store 在创建后立即返回外部 ID，因此 `committed` 很清楚。分布式系统里，写请求可能已提交但响应丢失，也可能返回排队 ID 而非最终完成。生产 Receipt 应说明状态含义，并与幂等键、查询接口和审计记录配合。

**6. 参数摘要会保护敏感数据吗？**

摘要主要用于一致性关联，不等同于加密或匿名化。低熵字段可以被枚举，大对象的结构也可能通过旁路推断。不要因为有 SHA-256 就把任意敏感参数写入公共日志。先最小化字段，再根据威胁模型决定摘要、加密、访问控制和保留周期。

**7. Tool Result 应该全部发回模型吗？**

不应。模型只需要下一步决策所需的安全信息。数据库原始行、内部堆栈、访问 Token、用户身份和巨量文档可能既敏感又浪费上下文。可以在受保护存储保存完整结果，在模型可见 Result 中提供筛选后的结构、引用 Handle 和错误码。

**8. MCP Server 能读取完整对话吗？**

协议架构不自动把完整对话交给 Server。Host 决定给某次 Tool Call 哪些参数、读哪些 Resource、取哪个 Prompt。Server 只收到请求提供的数据和协议元数据。若 Host 主动把完整历史放入参数，Server 当然会看到；隔离责任仍在 Host。

**9. MCP 与普通 REST API 谁更安全？**

没有脱离实现的统一答案。REST 可以有成熟网关、OAuth、审计和 Schema，也可能完全无鉴权；MCP 提供 AI Host 需要的发现与原语语义，也仍需要授权、隔离和安全部署。协议选择不替代威胁建模。比较时应看身份、Scope、输入验证、数据去向和副作用，而不是看名称。

**10. MCP 会不会让工具列表无限占用上下文？**

小列表可以直接放入模型上下文，大列表需要发现、过滤、搜索、分组或按需加载。现代 MCP 列表支持缓存语义，但“哪些工具此刻给模型看”仍是 Host 的上下文工程问题。第 10 章会专门讨论描述预算和大规模 Tool Discovery。

**11. 为什么本章不用真实 DeepSeek、OpenAI 或 Anthropic 做主实验？**

因为主实验要隔离 Runtime 边界。若同时更换模型，结果变化可能来自模型决策、采样、服务版本或网络。固定策略让每一步提议相同，差异只能来自外围系统。可选 Live Probe 只观察 Provider 形态映射，不写入规范报告，也不产生产品比较。

**12. 什么时候应该从自建 Runtime 迁移到框架？**

当你已经理解合同、错误、权限和完成证据后，框架能减少重复代码。迁移时先列责任表：哪些由 Provider Adapter 负责，哪些由 LangChain Tool 或 LangGraph ToolNode 负责，哪些必须保留在业务授权和审计层。不要因为框架能自动循环，就删除写入门禁和 Receipt。

**13. 有输入 Schema，为什么还要 Output Schema？**

输入 Schema 保护 Handler，输出 Schema 保护调用者。若状态 Tool 某次把 `error_rate` 从数字改成字符串，模型可能仍能读懂，确定性策略却会失败。写 Tool 若不保证返回外部 ID，Runtime 无法安全构造 Receipt。本章三个 Tool 都声明了 Output Schema，Runtime 会在结果进入 Loop 前验证；`contract-output-schema-violation` 则专门证明这道门确实生效。Output Schema 仍不能证明数据真实，只能证明形状符合约定；真实性需要领域查询或 Verifier。

**14. DomainError 与普通 Exception 为什么分开？**

DomainError 表达预期业务状态，例如服务不存在、窗口不支持、记录缺失。它的 Code、Message 和 Retryable 可以安全进入 Tool Result。普通 Exception 可能包含程序缺陷和内部细节，应转换成通用 Execution Error并记录到受保护日志。若全部吞成业务错误，监控看不到 Bug；若全部原样返回，模型会看到堆栈和隐私信息。

**15. 重复 Call ID 检查是不是已经实现幂等？**

不是。它只在一个 ToolRuntime 实例内阻止同一 ID 再执行，适合解释关联纪律。进程重启、多个 Worker、新 Call ID 重试都能绕过。业务幂等需要持久、原子、跨实例的键，并让后端写入参与。第 10 章会把 Call ID、Action ID、幂等键和外部对象 ID 分开讨论。

**16. MCP 的 Input Required 能否替代 Host 审批？**

Input Required 是多轮请求机制，允许 Server 在一次 Tool Call 中请求更多输入。它可以承载确认问题，但是否向用户展示、怎样验证回答、哪些动作仍需 Server 授权，仍由 Host 与 Server 设计。协议机制不是同意本身。一个恶意 Server 也可以请求敏感字段，Host 必须决定是否允许及如何展示。

**17. Resource 是应用控制还是模型控制？**

规范把 Resource 设计为可由应用选择和读取的上下文，产品也可以让模型建议读取某个 URI。关键是 Host 最终控制是否读取、是否把内容放入模型上下文。即使模型提出 URI，也不应绕过 Resource allowlist 和权限。控制权可以协作，但不能因为“模型建议”就消失。

**18. MCP Prompt 是否比本地 Prompt 更可信？**

不一定。它只是来自 Server 的可发现模板。可信度取决于 Server 来源、签名、组织策略和用户选择。Host 应显示 Prompt 来源，必要时在使用前预览。Server Prompt 也不能覆盖 Host 的安全策略或系统指令，更不能给自己授予 Tool 权限。

**19. `server/discover` 与 `tools/list` 有什么区别？**

`server/discover` 用于了解 Server 支持的协议版本和总体能力；`tools/list` 在已经按相应版本发出请求后，列出具体 Tool 定义。知道 Server 具有 Tools 能力，不等于知道有哪些 Tool；拿到工具列表也不等于获准调用。现代协议允许每个请求自描述，因此 Discover 是可选的预先发现，不是旧式 Session 初始化。

**20. Tool annotation 能不能直接驱动自动授权？**

只有在可信 Server 与额外策略条件下才可作为提示，不能普遍当作强制事实。Annotation 可能声称只读、幂等或无副作用，但协议规范明确要求不可信来源的 annotation 被视为不可信。Host 可以把它用于 UI 分类，再结合 Server 信任、组织策略和本地 allowlist 决定是否自动允许。

**21. stdio Server 为什么不能随便 print？**

因为标准输出承载协议帧。一行调试文本可能被 Client 当成协议消息，导致解析失败或错位。日志应写标准错误或专用日志 Sink。更深一层，日志内容仍要脱敏；从 stdout 换到 stderr 只解决通道冲突，不解决密钥、路径和用户数据泄露。

**22. 怎样判断本章实验结论有没有被夸大？**

先看输入是否固定，再看样本是什么，再看未测量字段。二十一个 Case 由二十个 Runtime Observation 和一个 Specification Fixture 组成，不是二十一次模型采样；SDK 进程内测试不是远程生产测试；Specification Fixture 不是实现互操作；Null 不是零。只要结论严格落在证据能支持的范围内，实验就有价值。超出范围的产品优劣、成本和模型成功率都必须另做测量。

[返回第 9 章](../book/chapter9.md)
