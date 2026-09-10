# 同一项任务，怎样观察 Claude Code 与 Codex

本指南不是产品排名，也不包含伪造的产品运行结果。资料核对日期：2026-09-10。作者环境只核对了 Codex CLI 版本 0.146.0；Claude Code 未在当前 PATH 中发现。**本候选稿没有执行真实产品修复任务**。标准实验中的指令清单不能填进产品遵循记录。

## 准备独立现场

在书籍仓库根目录运行两次：

```bash
python -m chapter11.prepare chapter11/live-reports/codex-repo --with-guidance
python -m chapter11.prepare chapter11/live-reports/claude-repo --with-guidance
```

如果目录已存在，选择一个新的名称，不要清理已有工作。每个目录是独立的 Git 夹具。不要让两个产品共用一个可写工作区。先分别进入目录，确认：

```bash
git status --short
python -m unittest discover -s tests -v
```

初始三个测试应该通过，但它们没有覆盖嵌套文档。AGENTS.md 和 CLAUDE.md 是未提交的任务约定文件；记录初始状态，不能把这两项误当作模型新增文件。

请按当前官方入口安装和登录：[Codex 官方指南](https://learn.chatgpt.com/guides/best-practices)、[Claude Code 官方文档](https://code.claude.com/docs/en/overview)。模型 API Key 不等于产品登录凭据。本章不要求更改全局配置、关闭审批或连接生产系统。

## 使用相同任务说明

> docs/guide/start.md 中的 ../faq.md 实际指向 docs/faq.md，但检查器把它报告为缺失。请确认活动实现和原因，在修改源码前增加一个能复现问题的回归测试，再修复。保持函数接口、已有缺失文件检测和外部链接跳过行为；保留 notes.txt 与无关改动，不修改 legacy/，不提交或推送。请报告运行目录、命令、测试数量、失败到通过的过程、最终 diff 与剩余限制。

在各自产品中选择对应工作目录。启动入口、权限模式、模型与版本需要当场记录；不要为了让结果“可比”而强行使用两个产品并不支持的同一设置。无法固定的差异必须公开。

开始前检查产品是否真的显示加载了预期项目指令。Codex 的 AGENTS.md 发现规则和 Claude Code 的 CLAUDE.md 导入规则不同，详见 [Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 与 [Claude Code](https://code.claude.com/docs/en/memory)。只有文件存在不算加载证据；模型复述约定也不等于全过程遵循。

## 记录过程，而不只记录回答

| 项目 | Codex | Claude Code |
| --- | --- | --- |
| 日期、产品版本、模型、操作系统 | 待实际运行 | 待实际运行 |
| 工作目录与起始 Git 状态 | 待实际运行 | 待实际运行 |
| 权限、联网、额外工具与项目指令 | 待实际运行 | 待实际运行 |
| 找到的活动实现及依据 | 待实际运行 | 待实际运行 |
| 回归修改前是否失败 | 待实际运行 | 待实际运行 |
| 最终命令、测试数、结果 | 待实际运行 | 待实际运行 |
| 修改文件、最终 diff | 待实际运行 | 待实际运行 |
| 人工介入、次数与内容 | 待实际运行 | 待实际运行 |
| 计时范围与中断原因 | 待实际运行 | 待实际运行 |

遇到审批按事先约定处理，并逐次记录。若需要人工提示才能找到活动文件，把提示作为介入记录，不删除这段过程后宣称独立完成。不要将未显示的 Token、缓存命中或费用估算成产品账单。

## 人工验收与下一轮观察

产品完成后，在对应教学目录重新运行：

```bash
python -m unittest discover -s tests -v
git diff --check
git diff -- linkcheck.py tests/test_links.py
git status --short
```

对照基线检查 notes.txt 和 legacy/ 是否保留，检查新增测试确实调用活动实现。检查缺失文件仍会报错，不接受“所有链接都返回空列表”的修复。

这些命令本身不构成通用验收器。产品可以改测试，所以人还要阅读 diff；可信教学工作台的冻结摘要、独立样本也不能直接作为恶意代码隔离。更高风险仓库需要隔离环境和独立测试资产。

单次结果适合分析工作过程，不能推出模型能力排名。若扩展为评估，应预先固定任务集与验收，随机或交替运行顺序，记录失败和介入，重复采样，并保留环境差异。预算不足就报告观察，不把一次成功写成 100% 成功率。

产品 Hook、Skill 和子 Agent 本次均没有安装或实测。它们在正文中用于解释职责；接入之前应核对版本、事件合同和权限，不把工作台 verify 函数称为产品 Hook。
