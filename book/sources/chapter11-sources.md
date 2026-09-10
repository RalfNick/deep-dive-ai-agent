# 第 11 章资料来源与事实边界

版本：v1.0-rc1；核对日期：2026-09-10。正文为原创教学解释，资料用于核对事实，不复刻其他书籍的原文、插图或案例。

## 来源与用途

| 来源 | 用于核对 | 不据此声称 |
| --- | --- | --- |
| [SWE-agent，2024](https://arxiv.org/abs/2405.15793) | 软件工程 Agent 的交互接口设计有独立研究价值 | 本章复现了论文分数或证明某模型更强 |
| [OpenAI Best practices](https://learn.chatgpt.com/guides/best-practices) | 任务上下文、项目指导、验证与交付工作流 | 通用成功率或每次都会遵循 |
| [OpenAI AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | 项目指令发现、范围和配置边界 | 任意名称文件都会加载，所有目录一开始全部读入 |
| [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills) | 复用任务方法与按需资源 | Skill 等同模型训练或强制安全策略 |
| [OpenAI Hooks](https://learn.chatgpt.com/docs/hooks) | 事件、匹配、信任和返回语义需明确 | 本章已安装产品 Hook 或所有事件均能阻断 |
| [OpenAI Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees) | 独立工作现场及文件环境核对 | 会话恢复必然恢复依赖、未提交文件或外部副作用 |
| [Claude Code 工作原理](https://code.claude.com/docs/en/how-claude-code-works) | 仓库读取、工具行动与反馈的产品流程 | 本次运行了真实产品修复 |
| [Claude Code Memory](https://code.claude.com/docs/en/memory) | CLAUDE.md 与 @AGENTS.md 导入、加载与指导边界 | AGENTS.md 被原生自动读取，说明文件具有沙箱效力 |
| [Claude Code Skills](https://code.claude.com/docs/en/skills) | 技能作为任务方法和资源载体 | 两家产品的配置可以无条件互换 |
| [Claude Code Hooks](https://code.claude.com/docs/en/hooks) | 指定事件上的操作与返回合同 | Git 提交检查等同 Agent 工具调用门禁 |
| [Claude Code Permissions](https://code.claude.com/docs/en/permissions) | 动作授权的职责 | 授权通过等于业务正确或自动获得系统级隔离 |
| [Claude Code Sandboxing](https://code.claude.com/docs/en/sandboxing) | 工具执行环境的隔离范围 | 受信任 Python 子进程就是恶意仓库沙箱 |
| [Claude Code Checkpointing](https://code.claude.com/docs/en/checkpointing) | 文件恢复的捕获范围与限制 | Bash 命令副作用、其他进程与远端写入都可回滚 |
| [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents) | 专门子任务与结果交接 | 本次实测并发性能或证明多 Agent 更强 |
| [Python 3.11 unittest](https://docs.python.org/3.11/library/unittest.html) | 测试发现、执行与结果 | 退出码 0 自动代表覆盖充分 |
| [Git diff](https://git-scm.com/docs/git-diff) | 工作区、暂存区和提交的差异关系 | diff 自身能够证明业务正确 |

OpenAI 资料通过本次下载的官方 Codex 手册及其来源入口核对；Anthropic、Python 与 Git 使用官方页面。产品网页是滚动文档，日期不是长期兼容承诺。为保持可移植性，不提交作者本机缓存路径。发布前应重新核对有变化的产品事实，尤其指令加载、Hook 事件、检查点范围与权限。

## 本地证据

| 结论 | 实现与可复现结果 |
| --- | --- |
| 旧测试通过仍可能漏掉嵌套路径错误 | [repair](../../chapter11/experiments.py)、[规范报告](../../chapter11/reports/repository-work.json) |
| 新回归先失败、修复后通过 | repair 的 red 与 final；[quickstart](../../chapter11/quickstart.py) |
| 旧摘要补丁被拒绝，用户文件保留 | conflict；[工作台测试](../../chapter11/tests/test_workbench.py) |
| 空目录、覆盖不足与移除断言不能验收 | verification；独立 ACCEPTANCE 与测试摘要 |
| 保存的历史成功不代表当前成功 | resume；evidence_is_current |
| 指令文件仅完成清单和命令观察 | instructions；product_adherence=not_measured |
| 输出来自运行且可复现 | [报告复现测试](../../chapter11/tests/test_experiments.py)，两次生成与规范文件逐字节比较 |

源码、文档、Git 和测试子进程确实运行；选择步骤与补丁内容固定，模型调用为零。实验样本每场景一个，不计算成功率、Token 节省、厂商排名或生产安全等级。

## 本次产品观察边界

只执行本地版本检查，发现 Codex CLI 0.146.0；Claude Code 未出现在当前 PATH。这只说明当前命令环境，不证明机器上所有位置都未安装。未使用用户历史消息中提供的 API Key；没有调用外部模型，没有启动子 Agent，也没有产品端任务 Trace。

[产品观察指南](../../chapter11/product-walkthrough.md) 是待执行步骤，所有产品结果留作“待实际运行”。后续如实测，需另存脱敏观察报告，不改写本章固定序列的证据来源。

## 阅读与表达取向

沿用全书“从具体输入出发，逐步建立工作部件，再看失败”的写作约定；以讲清本章为目标，不要求所有章节共用同一任务。用户推荐的《从零构建大模型》用于明确这种教学偏好；本次没有新增该书的页级引用，不声称核对了其完整内容。相关背景可回看 [全书写作标准](../WRITING_GUIDE.md)。

图示为本次原创生成，7 幅在用图采用米白纸感与蓝绿紫橙分区。图中代码和结果是教学缩写，不是产品截图。修订记录与提示词见 [插图说明](../images/chapter11-prompts.md)。
