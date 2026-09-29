# 第16章来源台账

核对日期：2026-09-29。正文产品映射以此日期读取的官方原文为准；不做功能、价格或模型排行榜。论文链接固定版本。以下“本地实现”是本书设计对照，不表示运行了来源中的 SDK 或完整算法。

| 一手来源及日期/版本 | 支持的有限结论与正文位置 | 不支持的结论 | 本地实现 |
| --- | --- | --- | --- |
| [OpenAI Harness engineering](https://openai.com/index/harness-engineering/)，2026-02-11 | §7/12：把经验变成仓库知识与可机械检查的约束，维护过期资料 | 本实验达到其吞吐，或所有团队可不审查合并 | artifacts.py、evaluation.py |
| [OpenAI Run long horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)，2026-02-23 | §2：错误、日志、外部化状态支持当前任务纠错 | 当前循环等于权重训练；文中时长/Token可复制 | replay.py、agent.py |
| [Anthropic Improving skill-creator](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills)，2026-03-03 | §7/12：版本/无Skill对照、回归、触发准确性需要测试 | 本章安装了插件、复现产品收益或输出真实Token费用 | artifacts.py、reports/group-3.json |
| [Anthropic质量复盘](https://www.anthropic.com/engineering/april-23-postmortem)，2026-04-23；原文指问题已于4月20日v2.1.116解决 | §5：默认推理配置、会话历史处理、系统提示可分别影响体验，应分切片诊断 | 2026-09-29仍存在原事件；问题由模型权重下降造成 | replay.py、evaluation.py |
| [LangGraph Add memory](https://docs.langchain.com/oss/python/langgraph/add-memory)，动态文档，未声明固定SDK版本 | §2/8：线程状态检查点与跨会话store有不同职责 | Store自动提供权限、TTL、安全治理或学习保证 | contracts.py、artifacts.py |
| [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)，动态文档，未声明固定SDK版本 | §10：持久化中断/恢复是审批编排的可用机制 | 中断本身验证候选、签署批准或撤销副作用 | governance.py |
| [LangChain How to give your agent memory](https://www.langchain.com/blog/how-to-give-your-agent-memory)，2026-06-24 | §2：轨迹是证据，只有转为可读取并影响后续运行的上下文才成为记忆 | 存所有日志就是学习；产品链路已被本章复现 | feedback.py→artifacts.py→agent.py |
| [Reflexion](https://arxiv.org/abs/2303.11366v4)，v4，2023-10-10 | §13：语言反馈、情景反思记忆影响后续试验，不更新权重 | 无错误反思、生产安全性或本书能力指标 | lessons.py是作者规则，不是Reflexion复现 |
| [Self-Refine](https://arxiv.org/abs/2303.17651v2)，v2，2023-05-25 | §13：同一LLM生成、反馈、迭代修订，无额外训练 | 自动跨任务持久学习；自评等于独立正确性 | replay.py的固定干预只是教学对照 |
| [GEPA](https://arxiv.org/abs/2507.19457v2)，v2，2026-02-14 | §13：轨迹反思、提出和测试Prompt候选的搜索 | 本章实现完整优化器或论文收益；无需留出集 | prompt提案只导出，不进入可执行资产 |

检索先检查了本仓库第4/5章来源与设计稿，再重新打开上述原文。OpenAI Docs 检索另核对官方开发者长任务文章。没有读取密钥、调用真实Provider、下载训练数据或引用搜索摘要作为证据。

本地证据入口：[规范报告](../../chapter16/reports/improvement-report.json)、[报告manifest](../../chapter16/reports/manifest.json)、[实验入口](../../chapter16/experiments.py)、[夹具](../../chapter16/fixtures/)。人工编写的发现/留出样本不是真实模型盲测。
