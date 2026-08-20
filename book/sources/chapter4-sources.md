# 第 4 章资料台账：Harness Engineering

核对日期：2026-08-12。产品命令、默认权限、协议字段、Beta 状态和版本号属于快速变化信息，出版前必须再次核验。

## 使用原则

- 产品行为只使用厂商官方文档、官方工程博客或官方开源仓库；
- 系统原则优先使用经典论文、官方技术文档和本章本地可执行证据；
- 不把厂商案例中的速度、规模或成功率外推为普遍结论；
- 不把确定性 `ScriptedModel` 实验解释为真实模型评测；
- Claude Code 与 Codex 只做 Model、Context、Tools、Runtime、Safety、Evaluation 六维责任映射，不排名；
- 正文回答职责、接口和失败状态，机制内部优化留给第 5、6、9、10、13、14 章。

## OpenAI 官方资料

| 来源 | 本章核对的事实 | 边界与快变项 |
| --- | --- | --- |
| OpenAI, [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/), 2026-01-23 | Codex Harness 组装初始输入、执行工具、把结果加入下一轮输入、管理不断增长的上下文；最终助手消息结束一轮，但代码与文件才可能是主要产物 | Responses API 输入项、缓存策略、压缩阈值和具体模型指令会变化 |
| OpenAI, [Unlocking the Codex harness: how we built the App Server](https://openai.com/index/unlocking-the-codex-harness/), 2026-02-04 | 同一 Codex Harness 服务 CLI、IDE、Web 等表面；Codex Core 负责线程生命周期、持久事件、配置认证、工具执行、沙箱、MCP 与 Skills；App Server 用双向事件和服务端请求支持审批暂停 | App Server 协议、推荐集成方式、客户端覆盖面和协议版本需出版前复核 |
| OpenAI, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/), 2026-02-11 | Agent-first 仓库需要清晰结构、可机械执行的约束、反馈循环、仓库知识和可观测环境；“仓库 Harness”比单次运行时更广 | 文章中的代码量、PR 数和速度是特定团队案例，不作为本章实验基准 |
| OpenAI, [Codex App Server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md) | 审批通过服务端发起请求交给客户端；请求与 thread/turn 关联；客户端响应后运行继续或终止 | 决策枚举、JSON-RPC 字段、experimental permissions 和审批模式会变化 |
| OpenAI, [Codex open-source repository](https://github.com/openai/codex) | 官方实现可用于核对 Agent Loop、工具、配置、沙箱和 App Server 的实际边界 | 只引用固定提交才能支持精确代码行；出版前记录最终引用 commit |

## Anthropic 与 Claude Code 官方资料

| 来源 | 本章核对的事实 | 边界与快变项 |
| --- | --- | --- |
| Anthropic, [Beyond permission prompts: making Claude Code more secure](https://www.anthropic.com/engineering/claude-code-sandboxing), 2025-10-20 | 权限提示与沙箱是互补层；沙箱同时约束文件系统和网络，可在边界内减少逐条审批 | 文中的内部“减少 84% 权限提示”是 Anthropic 特定环境结果，不外推 |
| Claude Code Docs, [Configure permissions](https://code.claude.com/docs/en/permissions) | 权限规则有 allow/ask/deny，文档当前说明 deny 优先；权限适用于工具，沙箱对 Bash 及子进程提供 OS 级文件和网络强制约束 | 权限模式、规则语法、默认值和研究预览功能变化快 |
| Claude Code Docs, [Sandboxing](https://code.claude.com/docs/en/sandboxing) | Auto-allow 与常规权限模式共享同一隔离边界；沙箱不可用时的回退行为可配置；存在受审批控制的逃逸路径 | OS 支持、依赖、默认 `failIfUnavailable` 和逃逸配置需复核 |
| Claude Code Docs, [Hooks reference](https://code.claude.com/docs/en/hooks) | PreToolUse 等生命周期事件可在工具执行前做确定性拦截；多个决定有明确优先级；`defer` 可用于稍后恢复 | Hook 事件、输出 Schema、HTTP Hook 错误策略和超时默认值会变化 |
| Claude Code Docs, [Security](https://code.claude.com/docs/en/security) | 默认权限、项目写边界、沙箱和用户审批共同形成安全模型 | 默认权限与平台差异需出版前验证 |
| Claude Code Docs, [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) | 上下文包含历史、文件、命令输出、CLAUDE.md、记忆、Skills 与系统指令；接近窗口限制时由产品管理上下文 | 自动压缩流程和界面命令可能变化，本章不展开优化算法 |
| Claude Code Docs, [Explore the context window](https://code.claude.com/docs/en/context-window) | 压缩会用结构化摘要替换历史；不同类型的启动内容、规则和 Skills 在压缩后的保留/重载行为不同 | 具体 Token 数、Skills 上限和重载规则是快变项 |
| Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), 2025-11-26 | 单有 compaction 不足以保证长任务；初始化环境、增量推进、进度文件和 Git 历史可帮助跨上下文接力；文中观察到“一次做太多”和过早完成 | 文章使用当时模型与 Agent SDK，经验不能直接转成所有任务的因果结论 |
| Anthropic, [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps), 2026-03-24 | 长任务可通过任务分解、结构化交接、规划/生成/评估责任和可评分合同改善；文章仍诚实记录成品缺陷 | 多 Agent 结构不是本章默认方案，也不能证明角色越多越好 |

## LangGraph 官方资料

| 来源 | 本章核对的事实 | 边界与快变项 |
| --- | --- | --- |
| LangChain Docs, [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | Checkpointer 按 thread 保存图状态，支持 human-in-the-loop、恢复、历史和容错；Store 用于跨 thread 数据，二者不是同一概念 | `DeltaChannel`、集成包、类名和版本要求会变化 |
| LangChain Docs, [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | Interrupt 保存状态并等待外部输入；恢复要使用同一 thread ID；节点从头重启，因此 interrupt 之前的副作用必须幂等 | `Command`、stream v1/v2 输出结构和具体 API 会变化 |

## 经典系统资料与进一步阅读

| 来源 | 本章使用内容 | 边界 |
| --- | --- | --- |
| Saltzer & Schroeder, [The Protection of Information in Computer Systems](https://web.mit.edu/Saltzer/www/publications/protection/), 1975 | 最小权限、完全仲裁、机制简化等安全设计原则 | 论文早于 LLM Agent，本章只迁移通用系统原则 |
| Lamport, [Time, Clocks, and the Ordering of Events in a Distributed System](https://lamport.azurewebsites.net/pubs/time-clocks.pdf), 1978 | 事件顺序与因果关系的基本思想，帮助解释 Trace 不能只收集无序日志 | 本章没有实现分布式逻辑时钟或共识 |
| Kleppmann, *Designing Data-Intensive Applications* | 重试、幂等、日志、故障与分布式系统语义的进一步阅读 | 教学文件回执不具备书中分布式数据系统保证 |
| Google, [Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/) | 超时、重试、监控、事故与可靠性工程的进一步阅读 | SRE 实践不能直接替代 Agent 任务级评估 |

## 本地实现与可复验证据

| 来源 | 本章使用内容 |
| --- | --- |
| `chapter3/agent_loop.py` | 第 3 章已有能读写文件、运行测试、分类错误和验收的闭环；第 4 章控制组不是“没有 Loop” |
| `chapter3/tests/test_agent_loop.py` | 6 项上一章回归，确保本章没有通过改写第三章结论制造对比 |
| `chapter4/harness/` | Context 以外的运行时契约、策略、沙箱、状态、Verifier 与 Recorder 的教学实现 |
| `chapter4/tests/` | 契约、路径、检查点、回执、审批顺序、验收、重试、取消、预算与报告回归 |
| `chapter4/reports/harness-ablation.json` | 分指标消融结果；明确限定为 deterministic boundary conformance |
| `docs/codex-tutorial/2026-07-31-harness-engineering.md` | 作者先前 Harness 专题的状态机、审批恢复和失败注入线索；本章重新组织、重新实现和重新验证，不直接复制成书稿 |

## 证据外推限制

1. 本章固定了决策策略，因此没有评估模型规划、工具选择、代码生成或自我纠错能力；
2. 单机 JSON 检查点和回执不能证明跨进程互斥、分布式事务或业务系统 exactly-once；
3. 教学路径解析不能替代容器、虚拟机、OS 沙箱、网络代理或凭据代理；
4. 本地任务规模很小，不能推断长任务的真实 Token、延迟、费用或成功率；
5. 产品对照说明责任映射，不对 Claude Code、Codex、LangGraph 或任何模型排序；
6. 厂商工程博客中的内部数字只作为案例背景，不进入本章消融图。

## 出版前更新检查

1. 重新核对 OpenAI 三篇 2026 工程文章的日期、术语和链接；
2. 记录引用时的 OpenAI Codex 仓库 commit，并复核 App Server 审批字段；
3. 复核 Claude Code allow/ask/deny 顺序、权限模式、沙箱回退、Hooks 事件和 compaction 保留规则；
4. 复核 LangGraph checkpointer/store、interrupt/Command 和 stream 版本说明；
5. 重新运行 Chapter 3 与 Chapter 4 全部测试，确认报告由当前代码生成；
6. 在 Windows 与至少一个类 Unix 系统验证路径、符号链接和临时目录行为；
7. 把产品快变内容的最终核对日期写入正文，不在正文固化不必要的版本号；
8. 检查所有外链可访问，并为长期出版保存必要的标题、作者、日期与 commit 元数据。
