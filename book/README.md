# 《深入浅出 AI Agent》书稿

> 从大模型原理到手写 Coding Agent

这不是一本“框架 API 百科”，也不是把 Prompt、RAG、MCP、Multi-Agent 等流行词依次解释一遍。全书围绕一个持续演进的工程问题展开：**怎样把一个只负责生成下一个 Token 的模型，逐步构造成能理解任务、使用工具、修改环境、检查结果并持续工作的 Agent？**

书稿沿用参考项目 `bojieli/ai-agent-book` 的核心组织方式：先建立概念边界，再解释系统结构，通过可运行实验观察真实行为，最后讨论失败模式与工程取舍。章节顺序与参考项目保持高度对应，同时补充 2026 年已经成为主流的 Coding Agent、Harness Engineering、Claude Code、Codex、Agent SDK、MCP、Skills、上下文压缩与安全隔离等内容。

## 目标读者

- 会写一点 Python，希望系统理解 LLM 与 Agent 的开发者；
- 已经使用 ChatGPT、Claude、Claude Code 或 Codex，但想知道它们为什么有效、何时失效的人；
- 用过 LangChain、LangGraph、CrewAI，却希望摆脱“只会调用框架 API”的工程师；
- 准备把 Agent 从演示原型推进到可评估、可观测、可部署系统的团队。

## 每章固定结构

1. 一个真实问题或反直觉现象；
2. 概念边界与最小心智模型；
3. 架构图和执行流程；
4. 从零实现的最小实验；
5. 主流框架或产品中的对应实现；
6. 失败案例、成本和安全边界；
7. 小结、练习与思考题。

## 已发布阅读顺序

1. [全书介绍](./introduction.md)
2. [第 1 章：大模型入门——从 Token 到 Transformer](./chapter1.md)
3. [第 2 章：大模型的训练、对齐与推理](./chapter2.md)
4. [第 3 章：AI Agent——从一次生成到闭环执行](./chapter3.md)
5. [第 4 章：Harness Engineering](./chapter4.md)
6. [第 5 章：上下文工程——Agent 真正看到的世界](./chapter5.md)
7. [第 6 章：长任务中的上下文架构](./chapter6.md)
8. [第 7 章：记忆——不是把聊天记录全部塞回去](./chapter7.md)
9. [第 8 章：RAG 与知识库——让 Agent 先查证，再回答](./chapter8.md)
10. [第 9 章：工具调用与 MCP——从“模型想做”到“系统真的做了”](./chapter9.md)

每章末尾都连接正文、配套实验、参考答案和下一阅读位置。第 10–18 章只有[写作规划](./OUTLINE.md)，不把规划标题计为已发布章节。

## 阅读路径

全书分为六部分，十八章。详细目录见 [OUTLINE.md](./OUTLINE.md)。

- 第一部分：先理解模型，再理解 Agent；
- 第二部分：上下文、记忆与知识；
- 第三部分：工具、MCP 与 Coding Agent；
- 第四部分：评估、可观测与模型选择；
- 第五部分：训练、反馈与持续进化；
- 第六部分：多模态、Multi-Agent 与生产系统。

## 书稿状态

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| [introduction.md](./introduction.md) | 初稿 | 写作动机、核心主线和实验方法 |
| [chapter1.md](./chapter1.md) | 二审稿 | 约 1.8 万中文字符、6 张图、5 个可运行实验、14 道分级练习及参考答案 |
| [chapter2.md](./chapter2.md) | 二审稿 | 约 3.4 万中文字符、7 张图、7 个无 API Key 实验、17 道分级练习及参考答案；含两种微型神经语言模型的真实训练曲线 |
| [chapter3.md](./chapter3.md) | 复审修订稿 | 约 1.07 万汉字 / 2.28 万非空字符、7 张图、5 个编号实验与 1 个 Trace 补充实验、18 道分级练习及参考答案；包含真实文件、测试进程、结构化 Verifier、循环门槛与 Trace 审计回放 |
| [chapter4.md](./chapter4.md) | 复审稿 | 约 2.7 万中文字符、8 张图、5 组无 API Key 实验、15 道分层练习与 3 道扩展实验；包含过期审批、Receipt 崩溃恢复与单案例边界故障矩阵 |
| [chapter5.md](./chapter5.md) | 复审修订稿 | 上下文装配、权限与来源身份、冲突消解、预算、注入边界，以及 63 项离线测试 |
| [chapter6.md](./chapter6.md) | v1.0.1 书稿 | 长任务压缩、Artifact、Checkpoint、Rehydration、恢复与漂移；公共仓库保留 143 项非 PDF 测试 |
| [chapter7.md](./chapter7.md) | Review 通过稿 | 约 2.6 万有效中文字符、7 张图、5 组无 API Key 实验、14 道分层练习与 65 项测试 |
| [chapter8.md](./chapter8.md) | v1.1 复审优化稿 | 约 2.56 万有效中文字符、8 张图、5 组 20 个无 API Key 案例、14 道分层练习与 60 项测试；区分 10 个符合性案例与 3 个失败探针，统一文档级固定 K 指标口径 |
| [chapter9.md](./chapter9.md) | v1.0.2 复审优化稿 | 约 2.6 万有效中文字符、8 幅原创手绘图、5 组 21 个无 API Key Case（20 个运行观察 + 1 个规范 Fixture）、14 道分层练习与 47 项测试；实现三份调用合同、写操作回执、输入/输出门禁、确定性 Tool Loop 与官方 MCP SDK 映射 |
| [sources/chapter1-sources.md](./sources/chapter1-sources.md) | 已建立 | 第 1 章资料台账与更新策略 |
| [sources/chapter2-sources.md](./sources/chapter2-sources.md) | 已建立 | 作者资料页级映射、论文、官方文档、书籍与前沿信息核对台账 |
| [sources/chapter3-sources.md](./sources/chapter3-sources.md) | 已建立 | Agent 经典论文、OpenAI/Anthropic/LangChain 官方文档与出版前复核清单 |
| [sources/chapter4-sources.md](./sources/chapter4-sources.md) | 已建立 | Harness、权限、沙箱、检查点、Claude Code 与 Codex 的官方资料台账 |
| [sources/chapter7-sources.md](./sources/chapter7-sources.md) | 已建立 | Memory 研究、评估与 LangGraph、Claude Code、OpenAI Agents SDK、Codex 官方事实台账 |
| [sources/chapter8-sources.md](./sources/chapter8-sources.md) | 已建立 | RAG 原始研究、检索算法、LangChain/LangGraph、OpenAI、Anthropic 与 Ragas 官方资料台账 |
| [sources/chapter9-sources.md](./sources/chapter9-sources.md) | 已建立 | MCP 2026-07-28 规范、官方 Python SDK、Provider Tool Use 与本地工程证据台账 |
| [reviews/chapter4-review.md](./reviews/chapter4-review.md) | 已完成 | 普通读者与 AI 工程专家双视角问题清单、修订记录和证据边界 |
| [reviews/chapter7-review-codex.md](./reviews/chapter7-review-codex.md) | 已完成 | 读者、AI Agent 专家、实验与资料时效四视角 Review 及修订证据 |
| [reviews/chapter8-review-codex.md](./reviews/chapter8-review-codex.md) | 已完成 | 读者、AI 专家、工程证据与资料时效四视角 Review，包含发现处置与报告哈希 |
| [reviews/chapter9-review-codex-v2.md](./reviews/chapter9-review-codex-v2.md) | 已完成 | v1.0.2 复审：修正协议时序与边界图，落实 Output Schema 门禁，统一证据口径；没有未处理的 P0 或 P1 |
| [reviews/chapter9-review-codex.md](./reviews/chapter9-review-codex.md) | 历史版本 | v1.0 首轮 Review，保留用于版本比较 |
| [WRITING_GUIDE.md](./WRITING_GUIDE.md) | 已建立 | 后续章节的篇幅、图表、实验和失败案例标准 |

本目录中的插图均为本书重新绘制或生成的 SVG/PNG，便于后续导出 PDF、EPUB 和网页版本；用户提供的旧资料只作为知识线索和结构素材，不直接复用原图或原文。

后续核心章节的篇幅、插图、实验和失败案例密度统一遵守 [WRITING_GUIDE.md](./WRITING_GUIDE.md)。
