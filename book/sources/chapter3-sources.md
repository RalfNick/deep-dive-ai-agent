# 第 3 章资料台账：AI Agent 与闭环执行

核对日期：2026-08-14。快速变化的 API、Beta 状态、模型名和产品能力在出版前必须再次核验。

## 使用原则

- 概念史和实验主张优先引用原论文；
- 产品行为只引用厂商官方文档；
- 框架 API 只引用当前官方文档，不凭记忆写类名；
- 用户提供资料用于建立学习线索，本章核心 Agent Loop 以公开一手资料和本地可执行证据校准；
- 不把厂商演示、单个基准或本章确定性夹具外推成普遍可靠性结论。

## 论文与经典来源

| 来源 | 本章使用内容 | 边界 |
| --- | --- | --- |
| Yao et al., [ReAct](https://arxiv.org/abs/2210.03629), ICLR 2023 | reasoning/action/observation 交错、环境反馈、原论文失败类型 | 不外推旧模型基准数字；不把公开 CoT 当内部机制全貌 |
| Sutton & Barto, *Reinforcement Learning: An Introduction* | 状态、动作、策略、转移的通用符号 | 本章没有进行强化学习或权重更新 |

## OpenAI 官方资料

| 来源 | 核对事实 | 快变项 |
| --- | --- | --- |
| [Function calling](https://developers.openai.com/api/docs/guides/function-calling) | 模型输出 function call；应用执行；用同一 call_id 回传结果 | Responses API 输出项与 SDK 示例 |
| [Using tools](https://developers.openai.com/api/docs/guides/tools) | 工具是模型访问外部能力的接口；具体托管工具集合 | 工具类型、参数和可用模型 |
| [Running agents — Agents SDK](https://openai.github.io/openai-agents-python/running_agents/)；[v0.16.0 release](https://github.com/openai/openai-agents-python/releases/tag/v0.16.0) | Runner 的 final / handoff / tool call 循环；`MaxTurnsExceeded`；`max_turns=None`；当日默认 `DEFAULT_MAX_TURNS=10`；模型并行调用与 SDK 本地执行并发分层 | SDK API、错误类型、默认值 |
| [Iterate on difficult problems](https://learn.chatgpt.com/use-cases/iterate-on-difficult-problems) | Codex scored improvement loop 的公开产品用法 | 产品功能和页面示例 |

## Anthropic 官方资料

| 来源 | 核对事实 | 快变项 |
| --- | --- | --- |
| [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Workflow / Agent 区分、增强型 LLM、环境 ground truth、停止条件、简单可组合模式 | 文章为 2024 经验总结，不是统一行业定义 |
| [Tool runner (SDK)](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner) | 自动工具循环、消息状态、错误封装、max_iterations、手写循环适用场景 | 当日为 Beta；语言支持和 API |
| [Claude Agent SDK overview](https://code.claude.com/docs/en/agent-sdk)、[Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) | SDK 是独立 Python/TypeScript 库；在用户进程运行同源 Agent Loop；程序化 Hooks 在应用进程中执行 | 包版本、能力和配置项 |
| [Claude Managed Agents quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart) | Agent、Environment、Session、Event；托管沙箱与 Agent Loop；当日请求头 `managed-agents-2026-04-01`，memory store 使用 `agent-memory-2026-07-22` | Beta header、工具集和支持模型 |
| [Trustworthy agents in practice](https://www.anthropic.com/research/trustworthy-agents) | Agent 自主循环带来误解意图、提示注入和监督风险 | 2026 产品与治理背景，非技术评测 |

## LangChain 官方资料

| 来源 | 核对事实 | 快变项 |
| --- | --- | --- |
| [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents) | `create_agent`、工具、system prompt、structured output、middleware、checkpointer；基于 LangGraph runtime | Provider 示例、模型名与具体 API |
| [LangChain short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory) | 线程级状态由 checkpointer 持久化；每步开始读取、调用或工具步骤完成后更新 | Checkpointer 实现和持久化后端 |

## 参考项目与本地证据

| 来源 | 用法 |
| --- | --- |
| [bojieli/ai-agent-book](https://github.com/bojieli/ai-agent-book/tree/main) | 参考“正文 + SVG + 按章实验 + 失败与边界”的组织密度，不复制文字与图片 |
| `chapter3/agent_loop.py` | 最小 Loop、类型、真实临时仓库和测试进程 |
| `chapter3/tests/` | 19 项回归：观察驱动修复、无关失败、受保护测试、唯一 call ID、超时、幂等、Trace 完整性和报告合同 |
| `chapter3/trace_audit.py`、`chapter3/trace_replay_demo.py` | call/result 数量、顺序、关联、完成合同与确定性状态回放 |
| `chapter3/reports/experiment-results.json` | 六个本地脚本的命令、退出码、有限输出与结论边界 |

## 出版前更新检查

1. OpenAI Agents SDK 的 Runner、`max_turns`、工具并发和错误类型是否变化；
2. Anthropic Tool Runner 是否仍为 Beta，`max_iterations` 和错误结构是否变化；
3. Claude Agent SDK 与 Managed Agents 的命名、运行位置、支持语言和 Beta header；
4. LangChain `create_agent` 与 LangGraph/checkpointer 的当前关系；
5. Codex、Claude Code 产品能力只保留官方可验证描述；
6. 所有本地实验在 Windows 与至少一个类 Unix 环境运行；
7. 路径规范化、符号链接与 junction 的安全边界增加跨平台测试。
