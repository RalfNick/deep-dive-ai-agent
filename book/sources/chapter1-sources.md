# 第 1 章资料台账

稳定原理与正文引文映射复核：2026-08-13。

快变产品信息最后网络核对：2026-08-09。

本台账将“稳定原理”和“快速变化的产品信息”分开维护。正文中的模型名、功能状态和 API 建议在出版前必须再次核对；数学定义与原始论文则按版本固定引用。

## 作者提供资料

| 资料 | 用途 | 处理方式 |
| --- | --- | --- |
| 用户提供资料《大模型入门.pdf》，40 页（未入库） | AI/ML/DL 边界、机器学习范式、Transformer、Token、Embedding、Attention、Prompt、CoT、RAG 等选题线索 | 图片型 PDF，已逐页渲染检查；不复制原文与原图。第 1 章吸收模型基础线索，Prompt/CoT 移至第 5 章，RAG 移至第 8 章，数据分析案例移至工具与 Coding Agent 章节 |

## 稳定原理来源

| 来源 | 支撑内容 | 备注 |
| --- | --- | --- |
| Vaswani et al., [Attention Is All You Need](https://arxiv.org/abs/1706.03762), 2017 | Transformer、缩放点积注意力、多头注意力 | 原始论文；正文公式按通用形式重新表述 |
| Sennrich et al., [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909), 2015 | 子词切分与 BPE 背景 | 用于后续扩充 Tokenizer 小节 |
| OpenAI, [tiktoken](https://github.com/openai/tiktoken) | 实验中的真实 Tokenizer | 第 1 章锁定 `tiktoken==0.13.0` 与 `o200k_base`；具体编码与模型映射仍可能变化 |
| Bengio et al., [Scheduled Sampling for Sequence Prediction with Recurrent Neural Networks](https://arxiv.org/abs/1506.03099), 2015 | Teacher Forcing 与生成时输入分布差异 | 正文只把 Exposure Bias 列为误差累积的一个原因 |
| Brown et al., [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165), 2020 | In-context Learning 与 Few-shot 背景 | 不把单篇论文结论外推为所有模型的稳定能力 |
| Su et al., [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864), 2021 | RoPE 的位置旋转思想 | 第 1 章只提供直觉，第 2/6 章再讨论长度扩展 |
| Dao et al., [FlashAttention](https://arxiv.org/abs/2205.14135), 2022 | 注意力计算的 IO-aware 优化 | 用于说明实现优化不等于上下文免费 |
| Ainslie et al., [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245), 2023 | GQA 与 KV Cache 效率 | 第 1 章仅做架构演进提示 |
| Kaplan et al., [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361), 2020；Hoffmann et al., [Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556), 2022 | 参数、数据与计算规模的关系 | 防止把“大”简单等同于参数量 |
| Jain and Wallace, [Attention is not Explanation](https://arxiv.org/abs/1902.10186), 2019 | 注意力权重不自动等于完整解释 | 用于约束可解释性表述，不否定注意力可视化的教学价值 |
| Wei et al., [Emergent Abilities of Large Language Models](https://arxiv.org/abs/2206.07682), 2022；Schaeffer et al., [Are Emergent Abilities of Large Language Models a Mirage?](https://arxiv.org/abs/2304.15004), 2023 | 涌现现象及评价指标争议 | 正文并列呈现两种证据，不把涌现写成规模增长的必然定律 |
| Liu et al., [Lost in the Middle](https://arxiv.org/abs/2307.03172), 2023 | 长上下文中信息位置与任务表现 | 用于否定“放得下就等于用得好”；不外推成所有模型的固定位置曲线 |

## 官方工程资料

| 来源 | 发布/核对时间 | 在本书中的用途 |
| --- | --- | --- |
| Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | 2024-12-19 | Workflow 与 Agent 的边界；增强型 LLM；简单可组合模式优先 |
| Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 2025-09-29 | Context Engineering 定义、有限注意力预算、最小高信号上下文 |
| Anthropic, [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) | 2026-08-09 核对 | Claude Code 的 Agent 循环、工具、上下文与验证机制 |
| Anthropic, [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) | 2026-08-09 核对 | 模型提出工具调用、运行时执行、结果回到模型的循环 |
| OpenAI, [From model to agent: Equipping the Responses API with a computer environment](https://openai.com/index/equip-responses-api-computer-environment/) | 2026-03-11 | 编排器、Shell、容器、Skills 与 compaction 的现代 Agent 架构 |
| OpenAI, [Model guidance](https://developers.openai.com/api/docs/guides/latest-model) | 2026-08-09 核对 | 当前模型族、Responses API、推理与工具调用建议；属于高频变化资料 |
| OpenAI, [Models](https://developers.openai.com/api/docs/models) | 2026-08-09 核对 | 当前模型目录；不把具体型号固化为长期结论 |

## 尚待补充的证据

- 在第 6 章选择公开模型复跑一组长上下文位置实验，检验 `Lost in the Middle` 结论在当前模型上的变化；
- 将第 1 章 Tokenizer 固定样本扩展成跨编码器测量表，同时避免从少量语言样本推导普遍优劣；
- 已在第 2 章加入两种源码公开、固定 seed 的微型神经语言模型训练曲线；下一步升级为固定版本开放权重模型的多随机种子实验；
- 在第 4、11 章分别建立 Claude Code 与 Codex 功能核对表，记录产品版本和抓取日期；
- 出版前对所有 2026 年产品名、API 名称、计费和功能状态做一次统一复核。

## 引用原则

1. 技术机制优先引用论文、协议或官方文档；
2. 产品能力只描述核对当日可证实的事实，不使用“永远领先”等判断；
3. 博客中的经验数字只作为该团队特定环境的观察，不外推成普遍规律；
4. 对旧资料进行重组和重新绘图，不复用来源不明的截图；
5. 每个依赖最新状态的段落都应能回到本台账找到核对日期。
