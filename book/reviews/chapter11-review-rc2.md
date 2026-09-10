# 第 11 章 v1.0-rc2 修订复核

日期：2026-09-10。基线：v1.0-rc1，提交 2ad0791235fd6b368887533a64e82f6d404c6bec。范围：正文、工作台、五组报告、练习与答案、产品指南、来源和预览。同一 Agent 执行修订与自查，不冒充独立读者试读。

## 本轮结论

保留原有章节主线、七幅图和十四道练习，不另换案例。修订集中解决“知道原则，但不知道具体怎么做”的落差：先展示真实断言差异，再解释结果通道；补齐产品阶段提示和交付模板，让读者可以从书面说明走到操作。

## Review 意见与处理

| 原问题 | 本轮处理 | 可复核依据 |
| --- | --- | --- |
| 普通 print 混入 stdout，导致整段 JSON 解析失败；断言诊断丢失 | 子进程结果写入仓库外临时 JSON；stdout、stderr 单列，details 保留测试名、failure/error 和异常消息；没有有效报告时 count=null | [工作台](../../chapter11/workbench.py)、[回归检查](../../chapter11/tests/test_review_regressions.py) |
| 文中说先确认红灯再冻结，代码顺序不一致，也没有阻止假红灯 | repair 确认 4 项、1 个目标失败、0 error、对应差异与退出码之后，才冻结并修复；其他情况 unexpected_red | [repair](../../chapter11/experiments.py)；全绿、导入错误、无关断言三个反例均在源码修改前停止 |
| 产品部分偏原则，读者缺少完整操作路线 | 正文与指南提供 Codex 启动、状态和权限查看、只读调查、回归暂停、修复、人工验收、恢复入口；Claude Code 简要映射；增加最小 Skill 文本示例 | [操作指南](../../chapter11/product-walkthrough.md)、[官方来源](../sources/chapter11-sources.md)；未声称已执行产品修复 |
| 练习 6–10 缺少完整变量和独立入口；第 9 题验收预期难以扩展 | exercise_solutions 为各题建立独立临时现场；第 9 题在修复前声明 nested_missing，再验证真实缺失与“恒空返回”反例 | [程序](../../chapter11/exercise_solutions.py)、[五项 CLI 检查](../../chapter11/tests/test_exercise_solutions.py)、[答案](../../chapter11/reference-answers.md) |
| 重复边界声明挤占具体讲解 | 合并部分重复说明，用失败输出阅读、完整阶段操作和交付示例替换；仍保留必要的可信夹具与产品证据边界 | [正文](../chapter11.md) |
| 重写产品段落后遗留无引用脚注，生成一个失效返回链接 | 从 Markdown 源删除孤立定义；加强引用/定义双向比较及预览 fragment 检查 | [文稿检查](../../chapter11/tests/test_artifacts.py)；先复现两项断言失败，修复后通过 |

## 验证记录

环境：Python 3.11.15、Windows。本轮先增加失败回归，再修实现。四项工作台回归在修复前失败；练习 CLI 检查在入口不存在时失败，补齐后通过。这里记录的是实际子进程与临时 Git 夹具，不是外部模型成绩。

- `python -B -m unittest discover -s chapter11/tests -v`：最终重跑 26 项通过，包含脚注修订、五组规范报告的两次生成与仓库文件逐字节比较。
- `python -B -m unittest discover -s tests -v`：43 项仓库合同通过；发布安全检查与 MkDocs strict 构建通过。构建仍仅组装已发布的前十章，不表示第 11 章上线。
- `npm test --prefix book`：4 项渲染合同通过。
- `node book/check_chapter11_preview.mjs`：1280px 与 390px 均为 7 图加载、7 figure、16 个脚注、0 失效片段、无整页横向溢出。检查过手机首屏；插图仍需放大阅读小字，不把“无溢出”当作“缩略图中所有文字清晰”。
- 当前规范 JSON SHA-256：135ed5792a6577e567b7e826b7b710272c7a652d67ea71b39917317374f44422。
- 当前规范 Markdown SHA-256：375d0b8d9a75266648c2c32594b53862861b549cf10c2c83c45ffb4cebd0bb50。

诊断文字来自 Python unittest；可复现检查支持本次固定环境，不承诺任意 Python 版本、扩展测试或调试输出都逐字节相同。结构化结果与日志分流解决普通输出污染，不构成恶意结果伪造防护。

## 仍然保留的限制

1. 未运行真实 Codex 或 Claude Code 修复，Skill、Hook、子 Agent 均未安装或实测。产品工作流依据官方文档，本地只检查 CLI 版本与帮助。
2. 工作台只接受可信教学代码，没有恶意仓库隔离、跨进程写锁或生产级输出容量限制；超时仍中止实验，不伪装成验收成功。
3. 文件摘要不包含解释器、依赖和外部状态；单个固定场景不能推出产品成功率、模型能力或成本结论。
4. 红灯门禁识别的是本章指定回归与断言差异，不是能够理解任意失败根因的通用诊断系统。第 9 题的预期由实验作者事先配置，不由待验收候选自行重定。

## 历史与发布边界

rc2 分支为 codex/chapter11-review-rc2。rc1 分支、提交、[旧 Review](chapter11-review-codex.md)均保留；旧报告另存于 [v1.0-rc1](../../chapter11/reports/versions/v1.0-rc1/repository-work.md)，其 JSON 摘要仍为 fb37f030388c2b08306a5363aa4c79b9545341157e990a53cab70ddc59a7fabe，Markdown 摘要仍为 3baffe4de8d2b3a74a232b616666389cf031a4341ba9038c36efae3fc82e5f5c。

本轮仅优化本地候选，不推送、不发布、不改公开 manifest 或网站导航，不改写前十章正文、旧图或 tag。未生成 PDF/EPUB。
