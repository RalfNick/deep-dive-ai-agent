# 第 2 章资料台账

最后核对：2026-08-09

本台账把“可以长期复用的训练原理”“会快速变化的产品能力”和“作者提供的学习线索”分开记录。正文中的当前模型名、参数名、功能状态和价格不应脱离核对日期引用；论文结论也只在其数据与实验边界内表述。

## 作者提供资料

| 资料 | 页码与线索 | 本章处理方式 |
| --- | --- | --- |
| 用户提供资料《AI学习资料.pdf》，23 页（未入库） | 第 1–6 页：学习地图、Transformer、微调、推理加速、Agent/MCP、技术图谱 | 图片型 PDF，无文字层；已逐页渲染抽检。作为路线索引，不直接引用截图、术语释义或平台列表 |
| 同上 | 第 7 页：无标注数据预训练、标注数据微调、强化学习与行业微调流程 | 映射为本章“预训练 → SFT → 偏好/RL → 推理系统”主线；流程由原始论文重新核验并重新绘图 |
| 同上 | 第 8–10 页：AI 在 SDLC 中的应用、旧版模型演进图、截至 DeepSeek-R1 的时间线 | SDLC 线索留给 Coding Agent 章节；演进图不复用，避免把时间敏感列表写入稳定正文 |
| 同上 | 第 11–16 页：《AI 工程》《从零构建大模型》《图解大模型》《大规模语言模型：从理论到实践》等书单与课程 | 经出版社或作者官网二次核对后，纳入章末分层阅读路线 |
| 同上 | 第 17–18 页：LLMs-from-scratch、llm-course、LLaMA-Factory、LangChain、DeerFlow 等项目 | 从零构建与训练工具作为实践入口；LangChain/DeerFlow 留给后续框架与 Agent 章节 |
| 同上 | 第 19–23 页：监督/无监督/RL、Transformer、预训练、微调、RLHF、CoT、Agent、MCP、Skills、A2A 术语表 | 不直接采用定义。第 2 章重写预训练、微调、RLHF 与 CoT；Agent/MCP/Skills/A2A 留给对应章节并以协议/官方文档核验 |

## 稳定原理与论文

| 来源 | 支撑内容 | 使用边界 |
| --- | --- | --- |
| Ouyang et al., [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155), 2022 | 示范数据 SFT、输出排序、奖励模型与 RLHF；小型 InstructGPT 在论文特定提示分布上的人类偏好结果 | 不外推为所有模型、所有任务或“RLHF 自动带来事实正确” |
| Schulman et al., [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347), 2017 | PPO 的裁剪代理目标与稳定策略更新背景 | 正文不展开完整 RL 推导，只解释其在经典 RLHF 管线中的角色 |
| Rafailov et al., [Direct Preference Optimization](https://arxiv.org/abs/2305.18290), 2023 | DPO 将标准 RLHF 目标改写为简单分类式偏好损失 | “简单”指训练路径，不代表数据、评估和超参数不重要 |
| Bai et al., [Constitutional AI](https://arxiv.org/abs/2212.08073), 2022 | 自我批评/修订、AI 偏好反馈与 RLAIF | 用于说明反馈来源可从人工扩展到规则和模型；不等于消除人类价值选择 |
| Wei et al., [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903), 2022 | 生成中间步骤对特定模型和推理任务的增益 | 不把可见推理文本当成内部过程的完整、忠实解释 |
| Snell et al., [Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters](https://arxiv.org/abs/2408.03314), 2024 | 搜索、验证器与按问题难度分配测试时计算；compute-optimal 思想 | 论文中的 4× 与 14× 等结果只属于其模型、任务与 FLOPs 匹配设置，正文不作为普遍常数 |
| Shao et al., [DeepSeekMath](https://arxiv.org/abs/2402.03300), 2024 | GRPO 是 PPO 的变体；组内相对奖励用于估计 advantage，省去独立价值模型 | GRPO 是优化方法，不与 RLVR 奖励来源或 RFT 工作流混为一谈；不外推论文基准数字 |
| DeepSeek-AI, [DeepSeek-R1](https://arxiv.org/abs/2501.12948), 2025 | 大规模 RL、可验证奖励、冷启动、多阶段训练、蒸馏；R1-Zero 的可读性和语言混合失败 | 用于解释 RLVR 与“能力提高仍需行为塑形”；不据此断言 SFT 已过时 |

## OpenAI 官方工程资料

| 来源 | 核对时间 | 本章用途 |
| --- | --- | --- |
| OpenAI, [Model guidance](https://developers.openai.com/api/docs/guides/latest-model) | 2026-08-09 | GPT-5.6 模型族、Responses API、reasoning effort、pro mode、持久化推理、程序化工具调用与 multi-agent beta；全部属于高频变化信息 |
| OpenAI, [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning) | 2026-08-09 | 内部 reasoning token、effort、max output、推理摘要以及工具间推理的当前 API 心智模型 |
| OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | 2026-08-09 | JSON Schema、显式 refusal 与 SDK 类型支持；正文额外强调 Schema 不能替代语义/权限校验 |
| OpenAI, [Function calling](https://developers.openai.com/api/docs/guides/function-calling) | 2026-08-09 | 工具定义、调用、应用执行、结果回传的五步循环；模型提出动作不等于动作已执行 |
| OpenAI, [Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses) | 2026-08-09 | typed output items、`store`、`previous_response_id`、加密 reasoning item 与 API 形状差异 |
| OpenAI, [Model selection](https://developers.openai.com/api/docs/guides/model-selection) | 2026-08-09 | 先达到准确率目标，再优化成本与延迟；建立评估集和任务门槛 |
| OpenAI, [Supervised fine-tuning](https://developers.openai.com/api/docs/guides/supervised-fine-tuning) | 2026-08-09 | 托管 SFT 的数据与评估接口参考；受同一微调平台逐步下线状态影响，不能据旧教程假定新用户可用 |
| OpenAI, [Direct preference optimization](https://developers.openai.com/api/docs/guides/direct-preference-optimization) | 2026-08-09 | 托管 DPO 的工作流参考；受平台状态影响，算法原理仍以原始论文为准 |
| OpenAI, [Reinforcement fine-tuning](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning) | 2026-08-09 | RFT 的采样—grader—策略梯度工作流；页面当日说明托管微调平台正在逐步下线且不再向新用户开放，不作为新项目默认能力 |

## Anthropic 官方工程资料

| 来源 | 核对时间 | 本章用途 |
| --- | --- | --- |
| Anthropic, [Thinking](https://platform.claude.com/docs/en/about-claude/models/extended-thinking-models) | 2026-08-09 | thinking block、工具调用间推理、`max_tokens` 与多轮保留规则 |
| Anthropic, [Effort](https://platform.claude.com/docs/en/build-with-claude/effort) | 2026-08-09 | effort 是影响文本、工具调用与 thinking 的软信号；应以工作负载评估校准 |
| Anthropic, [Task budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets) | 2026-08-09 | 长时 Agent 任务的建议预算；留给后续 Harness 与长任务章节扩展 |

## 经官网核对的书籍与课程

| 读者目标 | 资料 | 为什么放在这一层 |
| --- | --- | --- |
| 从零实现模型 | Sebastian Raschka, [Build a Large Language Model (From Scratch)](https://www.manning.com/preview/build-a-large-language-model-from-scratch/chapter-1), Manning, 2024 | 从文本处理、注意力和 GPT 实现推进到预训练与指令微调；适合把第 1–2 章落实为 PyTorch 代码 |
| 直觉与实践并重 | Jay Alammar, Maarten Grootendorst, [Hands-On Large Language Models](https://www.oreilly.com/library/view/hands-on-large-language/9781098150952/titlepage01.html), O'Reilly, 2024 | 第 12 章明确覆盖预训练、SFT、PEFT、奖励模型与 DPO，图解风格适合作为第二解释路径 |
| AI 应用工程 | Chip Huyen, [AI Engineering](https://www.oreilly.com/library/view/ai-engineering/9781098166298/), O'Reilly, 2024 | 连接模型、评估、成本、延迟、适配与应用工程；本章模型选择方法的重要拓展阅读 |
| 中文理论路线 | 张奇、桂韬、郑锐、黄萱菁, [大规模语言模型：从理论到实践](https://intro-llm.github.io/), 2023；[第二版预览](https://intro-llm.github.io/chapter/LLM-TAP-v2.pdf), 2025 | 从语言模型、数据与分布式训练推进到 SFT、RL 和评估；与作者资料的书单线索一致 |
| 2026 推理模型专题 | Sebastian Raschka, [Build a Reasoning Model (From Scratch)](https://www.manning.com/books/build-a-reasoning-model-from-scratch), Manning, 2026 | 覆盖测试时方法、验证器、RLVR、GRPO、奖励和蒸馏；属于快速演进专题，出版前需检查最终版 |

## 本地工程证据

| 文件 | 证据用途 |
| --- | --- |
| chapter2/sft_mask_demo.py | 显示移位标签、assistant-only mask、有效位置与损失 |
| chapter2/real_sft_evidence.py | 用固定 seed 真正训练 10,935 / 40,111 参数字符级因果 MLP，记录预训练、assistant-only SFT、目标成功率和通用保留损失 |
| chapter2/results/real_sft_curves.csv 与 real_sft_summary.json | 保存逐步原始曲线与环境无关汇总字段；正文图可由脚本重生成 |
| chapter2/preference_demo.py | 显示 DPO 风格相对间隔、偏好概率、损失与梯度方向 |
| chapter2/sampling_demo.py | 用固定 logits 与 seed 显示 greedy、temperature、top-p 的频率与候选截断 |
| chapter2/reasoning_budget_demo.py | 显示预算、任务难度、饱和与不可解任务 |
| chapter2/structured_output_demo.py | 显示 JSON 语法、Schema、业务语义和路径策略四层校验 |
| chapter2/model_selection_demo.py | 显示关键任务、安全、成本、延迟与容量硬门槛，再在可行集计算 Pareto 前沿 |

## 尚待补充的证据

- 当前真实梯度证据仍是本书自带的字符级微型模型；下一证据等级需在固定版本开放权重模型上做多随机种子 SFT，报告目标集、保留集、吞吐和置信区间；
- 用同一公开评估集复跑至少两种偏好优化方法，记录长度偏差、KL、训练稳定性和人评一致性；
- 接入一个可固定版本的开放权重 reasoning model，实测不同采样数、验证器和预算路由；
- 在第 13、14 章建立真实商业模型的固定任务集，记录版本、费用、p50/p95 延迟和置信区间；
- 出版前统一复核 OpenAI 与 Anthropic 的型号、参数名、默认值、存储策略和功能成熟度。

## 引用原则

1. 论文支持机制与特定实验结论，官方文档支持当日产品事实，书籍支持阅读路线；三者不互相替代；
2. 用户提供 PDF 是选题索引，不是可直接复制的事实库；所有术语回到一手来源核对；
3. “推理”“思考”等词在 API 层按厂商定义描述，不把可见或隐藏 Token 断言为人类心智过程；
4. 结构化输出只保证声明范围内的形状，正文必须保留语义、权限与执行验证；
5. 所有真实产品能力均带 2026-08-09 核对日期，出版前再次验证。
