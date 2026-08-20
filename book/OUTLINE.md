# 《深入浅出 AI Agent》目录与写作地图

副标题：从大模型原理到手写 Coding Agent

## 第一部分：模型是怎样变成 Agent 的

### 第 1 章 大模型入门：从 Token 到 Transformer

从“模型以预测下一个 Token 为核心，为什么却能表现出复杂能力”这一矛盾出发，讲清 AI、机器学习、深度学习、LLM、Workflow 与 Agent 的边界；解释 Token、Embedding、自注意力、Transformer、预训练与自回归生成。实验包括分词观察、微型注意力计算、Bigram 字符模型、温度采样和 Coding Agent 验证循环。

### 第 2 章 大模型的训练、对齐与推理

说明预训练、监督微调、偏好优化、推理时计算与模型 API；讨论温度、采样、结构化输出、成本、延迟和模型选择。实验比较不同采样参数与推理预算对结果的影响。

### 第 3 章 AI Agent：从一次生成到闭环执行

定义模型、增强型 LLM、Workflow 与 Agent；手写最小 ReAct / Tool Calling 循环，解释“观察 - 决策 - 行动 - 验证”。对照 OpenAI Responses/Agents SDK、Claude Agent SDK 和 LangChain 的基本抽象。

### 第 4 章 Harness Engineering：模型之外，谁在让 Agent 真正工作

解释为什么同一模型放进不同产品会表现得像不同智能体。拆解提示词、工具、权限、沙箱、文件系统、状态、重试、压缩、人工审批和可观测性；以 Claude Code 与 Codex 为主案例，建立现代 Coding Agent 的系统视图。

## 第二部分：上下文、记忆与知识

### 第 5 章 上下文工程：Agent 真正看到的世界

从 Prompt Engineering 走向 Context Engineering；解释 system/user/tool 消息、上下文窗口、工具描述、工作目录与隐式状态。实验观察指令冲突、信息位置和上下文噪声。

### 第 6 章 长任务中的上下文架构

讲解滑动窗口、摘要、压缩、检查点、文件化状态和按需加载；分析“上下文越长不等于效果越好”。对照 Claude Code 的会话机制、Codex 的 compaction 与 LangGraph checkpoint。

### 第 7 章 记忆：不是把聊天记录全部塞回去

区分工作记忆、情景记忆、语义记忆、程序性记忆与用户画像；比较内存、数据库、向量库和文件系统。实现一个会写入、检索、遗忘和修正的记忆模块。

### 第 8 章 RAG 与知识库：给 Agent 可更新的外部知识

完成切分、向量检索、关键词检索、混合召回、重排、引用和 RAGAS 评估；讨论 RAG 与记忆的边界、检索失败与知识污染。与项目 `phase-2-rag/` 和最终知识库系统对应。

## 第三部分：工具、MCP 与 Coding Agent

### 第 9 章 工具调用与 MCP

从 JSON Schema 和函数调用开始，解释模型只会“提出调用”，真正的副作用由 Harness 执行。手写工具循环，再实现 MCP Server；比较 Function Calling、MCP、Skills 和插件。

### 第 10 章 大规模工具集与异步任务

解决工具过多、描述占满上下文、工具选择歧义、长任务超时和并发调用问题；介绍工具检索、延迟加载、后台任务、事件流、取消与幂等。

### 第 11 章 Coding Agent：代码库就是它的环境

拆解 Claude Code、Codex 等 Coding Agent 的读文件、搜索、编辑、执行测试、查看差异、权限控制和会话恢复机制；讨论 AGENTS.md、CLAUDE.md、Skills、Hooks、MCP 与子 Agent。

### 第 12 章 手写一个 Mini Coding Agent

从模型 API 与五个基础工具开始，实现可在沙箱中完成小型代码任务的 Agent；加入计划、补丁编辑、测试验证、上下文压缩、审批边界和执行轨迹。最后分别用 LangGraph 与 Agent SDK 重构，并比较抽象成本。

## 第四部分：评估、可观测与模型选择

### 第 13 章 Agent 评估：答案正确还不够

建立任务集、环境、评分器和可复现实验；区分最终结果、轨迹、工具调用、安全和成本指标。覆盖确定性测试、LLM-as-a-Judge、人工评审与回归测试。

### 第 14 章 Benchmark、Tracing 与生产诊断

接入 Langfuse 等观测工具，记录 Token、延迟、成本、错误和轨迹；进行模型、提示词、工具集与框架的消融实验。解释如何读 SWE-bench 等公开基准而不被单一分数误导。

## 第五部分：训练、反馈与持续进化

### 第 15 章 Agent 的后训练

说明什么时候 Prompt/RAG 已经不够，需要 SFT、偏好优化或强化学习；设计轨迹数据、工具调用数据和拒绝样本。强调数据质量、奖励投机与评估隔离。

### 第 16 章 从失败中学习：持续改进系统

把生产失败转成回放样本、回归测试、规则、Skill、记忆或训练数据；建立“发现 - 归因 - 修复 - 验证 - 发布”的闭环，区分在线自适应与离线改进。

## 第六部分：多模态、多 Agent 与生产系统

### 第 17 章 多模态与实时 Agent

处理图像、语音、屏幕和文档；解释 Computer Use、视觉定位、实时语音、事件流和跨模态上下文。实现一个能读图表并调用代码验证结论的 Agent。

### 第 18 章 Multi-Agent 与最终系统

讨论什么时候拆分 Agent，什么时候单 Agent 更好；实现委派、并行研究、共享状态、交接、冲突处理与停止条件。最终汇总为企业知识库问答与 Coding Agent 综合项目，并完成安全、评估、部署和成本复盘。

## 附录规划

- 附录 A：Python、TypeScript 与模型 API 快速准备；
- 附录 B：LangChain / LangGraph / CrewAI / OpenAI Agents SDK / Claude Agent SDK 对照表；
- 附录 C：Claude Code 与 Codex 常用配置、项目指令和权限模型；
- 附录 D：MCP、Agent Skills 与工具协议速查；
- 附录 E：实验环境、依赖锁定与全书评估集；
- 后记：从“会调用模型”到“会设计智能系统”。

## 与参考项目的对应关系

| 参考项目主线 | 本书对应章节 | 新增或强化内容 |
| --- | --- | --- |
| Agent 基础 | 第 1-4 章 | 大模型入门、Harness Engineering、Claude Code、Codex |
| 上下文 | 第 5-6 章 | 上下文压缩、文件化状态、长任务会话 |
| 记忆与知识库 | 第 7-8 章 | 混合检索、重排、RAGAS、记忆边界 |
| 工具 | 第 9-10 章 | MCP、Skills、工具发现、异步与并发 |
| Coding Agent | 第 11-12 章 | 产品拆解与从零实现并行推进 |
| 评估 | 第 13-14 章 | Trace、回归、成本、公开基准解读 |
| 后训练与进化 | 第 15-16 章 | 轨迹数据、失败回放、持续改进闭环 |
| 多模态与多 Agent | 第 17-18 章 | Computer Use、实时交互、委派与安全边界 |
