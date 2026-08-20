# 深入浅出 AI Agent

从大模型基础出发，逐步走到上下文工程、Harness、工具、MCP、Coding Agent、评估、记忆、RAG、多模态与 Multi-Agent。每一章都尽量把概念边界、系统结构、可运行实验、失败案例和工程取舍放在一起。

本书面向三类读者：刚接触 AI、缺少系统学习路径的开发者；已经在工作中使用 AI Coding、Claude Code 或 Codex，希望理解其系统边界的人；以及准备把 Agent 原型推进到可测试、可观测、可部署系统的团队。

## 当前状态

- 简体中文是唯一权威正文，已完成并复审第 1–6 章。
- 第 1–6 章都包含配套实验、测试、固定报告或结果，以及参考答案。
- 第 7–18 章已进入写作规划，尚未发布正文。
- 英文版状态为 `planned`，当前没有译文章节；暂不建立繁体中文版。
- 在线阅读地址预留为 <https://ralfnick.github.io/deep-dive-ai-agent/>，GitHub Pages 验收前不标记为已发布。
- PDF/EPUB 尚未在本仓库发布，未来只通过 GitHub Releases 提供。

## 已发布章节与实验

| 章节 | 正文 | 配套实验 | 参考答案 | 验证状态 |
| --- | --- | --- | --- | --- |
| 第 1 章 大模型入门 | [正文](book/chapter1.md) | [实验](chapter1/README.md) | [答案](chapter1/reference-answers.md) | [10 项测试通过](docs/EXPERIMENT_STATUS.md#逐章状态) |
| 第 2 章 训练、对齐与推理 | [正文](book/chapter2.md) | [实验](chapter2/README.md) | [答案](chapter2/reference-answers.md) | [7 个命令通过](docs/EXPERIMENT_STATUS.md#逐章状态) |
| 第 3 章 从一次生成到闭环执行 | [正文](book/chapter3.md) | [实验](chapter3/README.md) | [答案](chapter3/reference-answers.md) | [20 项测试通过](docs/EXPERIMENT_STATUS.md#逐章状态) |
| 第 4 章 Harness Engineering | [正文](book/chapter4.md) | [实验](chapter4/README.md) | [答案](chapter4/reference-answers.md) | [24 项测试通过](docs/EXPERIMENT_STATUS.md#逐章状态) |
| 第 5 章 上下文工程 | [正文](book/chapter5.md) | [实验](chapter5/README.md) | [答案](chapter5/reference-answers.md) | [63 项测试通过](docs/EXPERIMENT_STATUS.md#逐章状态) |
| 第 6 章 长任务中的上下文架构 | [正文](book/chapter6.md) | [实验](chapter6/README.md) | [答案](chapter6/reference-answers.md) | [142 项测试通过](docs/EXPERIMENT_STATUS.md#逐章状态) |

建议先读[全书介绍](book/introduction.md)，再按[中文阅读顺序](book/README.md)推进。详细来源、Review 和版本记录均保留在 `book/` 中。

## 18 章学习路线

全书分为六部分，共 18 章：

1. 大模型入门：从 Token 到 Transformer
2. 大模型的训练、对齐与推理
3. AI Agent：从一次生成到闭环执行
4. Harness Engineering：模型之外，谁在让 Agent 真正工作
5. 上下文工程：Agent 真正看到的世界
6. 长任务中的上下文架构
7. 记忆：不是把聊天记录全部塞回去
8. RAG 与知识库：给 Agent 可更新的外部知识
9. 工具调用与 MCP
10. 大规模工具集与异步任务
11. Coding Agent：代码库就是它的环境
12. 手写一个 Mini Coding Agent
13. Agent 评估：答案正确还不够
14. Benchmark、Tracing 与生产诊断
15. Agent 的后训练
16. 从失败中学习：持续改进系统
17. 多模态与实时 Agent
18. Multi-Agent 与最终系统

每章范围和前后依赖见[完整大纲](book/OUTLINE.md)。未发布章节的标题是规划，不代表正文或实验已经完成。

## 实验证据的四种状态

| 状态 | 含义 |
| --- | --- |
| 离线已验证 | 固定夹具或本地代码已运行，可在公共 CI 中复现 |
| Live 可选 | 需要真实 provider/API Key，只保留显式入口，不进入公共 CI |
| 发布型排除 | PDF、浏览器视觉或二进制发布验收不放入 Git 主线 |
| 规划中 | 章节或实验尚未实现，不用占位输出冒充结果 |

固定夹具只能验证所声明的边界。离线字节数不是 Token 数，单案例不是统计成功率，实验也不用于给 Claude Code、Codex 或模型厂商排名。精确命令、测试数和报告哈希见[实验状态台账](docs/EXPERIMENT_STATUS.md)。

## 快速开始

需要 Python 3.11–3.13。每章是独立实验包，可只安装自己要读的章节依赖。

~~~powershell
git clone https://github.com/RalfNick/deep-dive-ai-agent.git
cd deep-dive-ai-agent
python -m pip install -r chapter1/requirements.txt -r chapter2/requirements.txt
python -m unittest discover -s chapter1/tests -v
python chapter2/real_sft_evidence.py
~~~

其余命令见对应 `chapterN/README.md`。仓库级验证、在线阅读构建和 CI 会在后续提交中加入。

## 参与贡献

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。正文修改需要同步检查来源、图表、实验和前后章节；代码修改需要先补测试，再更新固定报告与结论边界。翻译规则见 [docs/TRANSLATION.md](docs/TRANSLATION.md)，英文版当前仍是 [planned](book-en/README.md)。

本项目采用 [Apache License 2.0](LICENSE)。
