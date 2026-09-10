# 第 11 章插图提示词与修订记录

使用内置 imagegen 生成原创中文图，非产品截图；所有图已逐张检查。统一提示：米白纸张、手绘墨线与轻水彩、深蓝文字、蓝绿紫橙分区；纵向知识图，中文清晰，避免无关装饰、品牌标志和过多文字。

## 图 11-1：一次代码修改，怎样变成可检查的结果

初稿：fig11-1-workflow.png。

Seven numbered blocks connected in a clear reading flow top to bottom with compact icons: 1 复现问题; 2 搜索与阅读; 3 补回归测试; 4 修改源码; 5 运行验证; 6 检查差异; 7 交付证据. From step 5 add one clearly labeled orange return arrow to step 2, label 失败后继续定位. Footer 目标、源码、测试与差异，必须指向同一次修改.

## 图 11-2：代码库就是 Agent 的环境

初稿：fig11-2-environment.png。

Center a workstation labeled Coding Agent surrounded by six clearly separated cards with icons: 源码 / 实现行为; 测试 / 检查样本; 文档 / 解释约定; 配置 / 决定入口; 终端 / 产生观察; Git / 标记改动. Clear small arrows from these six cards into center. Footer 文件存在，不代表已经进入模型上下文.

## 图 11-3：从一个报错，找到需要读的几行

初稿：fig11-3-search.png。

Four vertically stacked panels: 1 目录：先找入口 icon folder tree; 2 搜索：找到候选 icon magnifying glass; 3 精读：核对调用 icon code with selected lines; 4 复现：检验猜想 icon terminal. Highlight in blue path docs/guide/start.md and green ../faq.md resolving to docs/faq.md as tiny example at bottom. Put orange crossed out candidate legacy/ as a small side branch from search labeled 旧实现：核对是否运行. Footer 搜索结果是线索，运行结果才检验假设.

## 图 11-4：应用补丁前，确认文件还是刚才那一份

初稿：fig11-4-patch.png。

Three horizontal stages drawn vertically for mobile: 1 读取当前文件 with fingerprint A; 2 提出最小修改 with patch card; 3 再核对文件 with two clear branches: A 未变化 → 应用补丁, B 已变化 → 停下重读. Separate bottom inset showing notes.txt labeled 用户已有改动 stays unchanged, no connection into patch. Footer 小补丁便于审阅；前置检查不能替代并发写锁.

## 图 11-5：测试绿了，还需要哪些证据

初稿：fig11-5-evidence.png。

Three stacked large cards: 1 命令执行：退出码为 0; 2 检查有效：发现了预期测试，覆盖了目标问题; 3 修改可交付：差异符合范围，验收针对当前版本. Put small warning orange on first card: 零项测试也可能返回 0. Bottom four evidence icons labels 命令, 测试范围, 版本, 差异. Footer 通过了哪些检查，比一句“全部通过”更有用.

## 图 11-6：项目约定和扩展能力，各管哪一段

初稿：fig11-6-extension.png。

Five clean separate rows each with icon and question: 项目指令 → 在这个仓库怎样工作; Skill → 这类任务按什么步骤做; Hook → 在指定事件上执行什么检查; CLI → 本机怎样调用现有工具; MCP → 怎样连接外部数据与动作. Footer 指令提供指导；实际约束取决于执行路径与权限. Avoid hierarchy arrows implying MCP supersedes CLI.

## 图 11-7：继续会话前，先核对工作现场

初稿：fig11-7-resume.png。

Top left card 昨天：测试通过 / 文件版本 A; top right card 今天：会话恢复 / 文件可能已变化. Arrow both into middle diamond 当前文件还是 A 吗？. Green branch 是 → 核对命令与环境 → 继续工作; orange branch 否 → 旧证据失效 → 重新验证. Bottom separate note 会话历史、文件状态、外部副作用，恢复范围各不相同. Footer 记得上次做过什么，不等于现在仍然成立.

## 技术复核与在用版本

- 图 11-1 使用 fig11-1-workflow-v2.png：将“无新增问题”改为“已覆盖场景通过”，不把有限测试画成完备保证。
- 图 11-3 使用 fig11-3-search-v3.png：移除生成器虚构的模块/命令；使用正文真实的搜索符号、代码和测试命令；纠正目录树中重复的 docs/ 前缀。终端内容是回归失败阶段的教学缩写，不是原样终端截图。
- 图 11-6 使用 fig11-6-extension-v2.png：将 Git 提交、推送、合并事件示例改为工具调用前、调用后和一轮结束，并注明以产品支持事件为准。
- 图 11-2、11-4、11-5、11-7 使用初稿；补丁图保留并发写锁限制，恢复图区分文件与会话。

未修订初稿文件保留，但正文不引用已知不准确的初稿；不要单独发布这些旧图。生成后的原始资源也保留，不覆盖生成器原件。图示用于建立关系，正文与可运行代码负责精确合同。
