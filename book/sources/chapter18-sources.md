# 第18章来源台账

外部来源解释概念与产品责任，本地证据证明本章实际发生的操作。核对日期2026-10-01；没有以文档示例代替运行实验，没有复制特定系统收益作为本章成绩。

## 官方与研究资料

1. **Anthropic / Jeremy Hadfield等**：[How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)，发布2025-06-13，核对2026-10-01。重点：Benefits、Architecture、Prompting、Production reliability。用途：主研究者分工、子任务边界、协调成本的工程启发。不能支持：所有领域多Agent优于单Agent、通用加速比，或本地实现拥有生产恢复能力。正文只使用概念层转述。
2. **OpenAI Agents SDK维护者**：[Agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/)，动态Python SDK文档，核对2026-10-01；本章没有锁定或安装该SDK。重点：Core SDK patterns中的Agents as tools与Handoffs。用途：主控保留与控制接管的责任区别。不能支持：本地Runtime等价SDK、安全隔离或性能排名。
3. **OpenAI**：[官方SDK迁移验收检查表](https://developers.openai.com/cookbook/examples/agents_sdk/migrate-from-claude-agent-sdk/readme#final-validation-checklist)，动态Cookbook，核对2026-10-01。经官方Docs MCP搜索后获取具体段落。用途：所有权、工具边界与业务验收分别检查。不能支持：本文已经实施SDK迁移，或所有Guardrails等价业务授权。
4. **LangChain团队**：[Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)，当前OSS Python文档，核对2026-10-01。重点：Why multi-agent、Patterns、Custom workflow。用途：单Agent/Skills/Subagents/Handoffs/Router与图编排的边界。不能支持：示例模型调用数或Token百分比在本章成立，或LangGraph已经接入实验包。
5. **Anthropic**：[Create custom subagents](https://code.claude.com/docs/en/sub-agents)，Claude Code动态文档，核对2026-10-01。重点：总览、Frontmatter、Permission modes、Manage subagent context。用途：独立上下文、专门指令、工具与权限配置的责任映射。不能支持：所有子代理默认权限相同、跨版本功能完全不变、实际产品安全性已全面验证。核对页提及多个v2.1.x行为变化，正文不搬运版本功能清单。
6. **OpenAI**：[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)，当前动态手册，核对2026-10-01。先运行官方文档技能的手册缓存助手，再读Multi-agent operations与Why subagent workflows help；Docs MCP获取针对段落。旧入口`https://developers.openai.com/codex/multi-agent`经浏览核对重定向到上述当前页。用途：独立探索后返回摘要、主任务汇总及并行写入的协调风险。不能支持：多Agent低成本、跨所有产品表面权限相同，或本章运行了真实Codex子代理评测。
7. **Yubin Kim等**：[Towards a Science of Scaling Agent Systems，arXiv:2512.08296v3](https://arxiv.org/abs/2512.08296v3)，v1发布2025-12-09，当前引用v3修订2026-04-08；核对2026-10-01。核对摘要、作者、Submission history。用途：任务结构与协调架构的匹配作为研究问题。不能支持：普遍多Agent收益阈值、本文23/16为实测性能，或固定策略案例测量了真实模型能力。正文不引用跨基准百分比作为通用结论。

## 本地证据

- [任务与运行合同](../../chapter18/contracts.py)：默认16工具总额度内含2验证保留；深度2、在途3、handoff4、Worker决策4。
- [五组二十案](../../chapter18/cases.py)：固定策略测试边界；第一组同目标单控制器对照保持3项查询、3次工具调用与相同证据。
- [系统](../../chapter18/system.py)：工具观察构造结果；实际上下文传递；验收重新加载来源；接纳补丁ID才进入业务提交路径。
- [集成](../../chapter18/integration.py)与[验证](../../chapter18/verifier.py)：真实文件副作用、基线拒绝与可信测试/行为探针，不是罐装成功。
- [规范总报告](../../chapter18/reports/reference-rc1/team-report.json)、[摘要](../../chapter18/reports/reference-rc1/summary.md)、[manifest](../../chapter18/reports/reference-rc1/manifest.json)：稳定字节与派生指标；实际工作区另在忽略目录，不进入规范包。
- [练习](../../chapter18/reference-answers.md)与[可复算入口](../../chapter18/exercise_solutions.py)：13题、计算与实际代码题证据。

本地规范记录不会引入绝对机器路径、时钟、UUID、API Key或真实Provider响应。模型选择、价格和平台可用性不是本章实验变量。未实现项集中见[实现说明](../../chapter18/IMPLEMENTATION.md)，不将理论生产清单写成已完成交付。
