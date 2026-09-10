# 同一项任务，怎样观察 Claude Code 与 Codex

版本 v1.0-rc2；资料核对日期：2026-09-10。作者环境核对了 Codex CLI 版本 0.146.0 及本地命令帮助；Claude Code 未在当前 PATH 中发现。**本候选稿没有执行真实产品修复任务**。下面是可手动执行的指南，不是已完成的产品成绩；标准实验中的指令清单不能填进产品遵循记录。

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

请按当前官方入口安装和登录：[Codex CLI](https://learn.chatgpt.com/docs/codex/cli)、[Claude Code Quickstart](https://code.claude.com/docs/en/quickstart)。模型 API Key 不等于产品登录凭据。本章不要求更改全局配置、关闭审批或连接生产系统。

## 先用 Codex 跑通一条完整路线

以下命令从刚才的**本书仓库根目录**开始。若还停在其他教学目录，先回到本书根目录；不要重复执行 prepare 去覆盖现场。

```bash
cd chapter11/live-reports/codex-repo
git status --short
python -m unittest discover -s tests -v
codex --version
codex
```

首次启动如要求登录，按官方界面操作，不把凭据粘贴进任务文本。进入 Codex 交互界面后使用 `/status` 查看会话信息，用 `/permissions` 查看并按需要选择权限。这两个是**交互命令，不是终端命令**。保持审批，不开启跳过保护的模式。先给出：

> 先只读调查，不修改文件。报告当前工作目录、项目约定、测试命令，以及 tests/test_links.py 实际导入哪个实现。指出哪些信息来自启动时加载的指令，哪些来自你这次主动读取；不能确定的请明确说明。

同时检查产品可见的指令加载信息；让模型读出文件只证明这次读取，不证明启动时自动加载。fixture 中的 AGENTS.md 说明活动源码与约束，CLAUDE.md 的内容为 @AGENTS.md，后者用于下一条 Claude 路线。

第二步提交下一节的共同任务，但追加阶段限制：

> 本轮先不要修复源码。只增加覆盖 docs/guide/start.md 中 ../faq.md 的回归测试，运行测试，给出失败测试名、期望值和实际值，然后停下来等我检查。

在**另一个终端**进入同一 codex-repo，独立检查：

```bash
python -m unittest discover -s tests -v
git diff -- tests/test_links.py
git diff -- linkcheck.py
```

应发现 4 项测试，新增嵌套链接测试失败；检查器误报 ../faq.md，源码此时不应有修复。如果只有 3 项，先调查测试发现；如果是导入错误，先修复环境；如果测试全绿，先确认回归是否真的覆盖问题。不要把任何非零退出都叫作“成功复现”。

确认失败原因后，在 Codex 中继续：

> 回归已确认。现在只做必要的源码修复，保留刚确认的测试和其他工作区文件。运行全部测试，检查最终 diff；不要提交或推送。交付时分别说明改了什么、用什么命令验证、哪些边界还没有覆盖。

产品说完成后，执行下文“人工验收”的命令。目标是 4 项通过、嵌套有效链接不再误报、真正缺失的文件仍报错；人还要阅读新增断言。不要仅凭一句“测试通过”接受修复。

需要中断时，先记录工作目录、Git 状态和阶段。之后从同一目录运行 `codex resume`，在会话选择器中核对任务；恢复后重新检查文件与证据，而不是假定磁盘回到旧状态。本机只检查过该命令帮助，没有执行本次会话恢复实验。

最后的交付可以采用以下**填写模板**，方括号内容应换成实际观察，不复制标准实验数值冒充产品结果：

```text
修改：[活动文件与原因；新增哪条回归]
验证：[工作目录、命令、修复前后的测试数量与结果]
保护：[notes.txt、legacy/ 和已有修改的核对结果]
差异：[最终 diff 的关键内容]
状态：[是否存在未提交修改；未提交、未推送]
限制：[尚未覆盖的语法、路径、平台或权限条件]
```

## Claude Code 的对应入口

从本书根目录进入另一个夹具，不沿用已修好的 Codex 工作区：

```bash
cd chapter11/live-reports/claude-repo
git status --short
python -m unittest discover -s tests -v
claude --version
claude
```

使用同样的阶段提示和人工验收。Claude Code 的项目说明入口是 CLAUDE.md；本夹具通过 @AGENTS.md 导入共同约定，不声称它原生自动读取 AGENTS.md。可在交互界面的 `/context` 中查看 Memory files，并核对导入是否生效；具体表现以当前版本为准。[官方 Memory 说明](https://code.claude.com/docs/en/memory)解释了导入和上下文查看方式。权限设置按 Claude Code 当前合同检查，不机械照搬 Codex 的交互命令。

## 可选：把方法写成一份最小 Skill

先跑通上面的手动路线，再在**教学仓库**中另行创建 `.agents/skills/link-repair/SKILL.md`，内容采用正文中的最小示例：YAML 的 name、description，加上“确认入口—复现—回归失败—修复—验收”的步骤。Codex 的 `/skills` 或 `$link-repair` 是显式选择入口，见 [官方 Build skills](https://learn.chatgpt.com/docs/build-skills)。这份 Skill 文件本次没有安装或执行。

如果要比较有无 Skill，先声明新增条件，为新一轮准备独立目录，并把文件列入初始状态；不能运行到一半增加帮助后，仍声称条件完全相同。Claude Code 的技能目录和发现规则应另查其官方文档，不把 Codex 的路径当成通用协议。

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
