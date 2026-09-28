# 第 15 章来源台账

本文件记录《深入浅出 AI Agent》第 15 章使用的一手论文、官方文档与本地证据。基础来源核对日期：**2026-09-27**；RC2 新增资料与本地证据核对日期：**2026-09-28**，详见各条目。

正文中的 24 条轨迹、12 条隔离记录、SFT/DPO 手算值和三种奖励变体全部来自本仓库确定性实验。论文中的结果没有在本仓库复现；产品文档只用于解释核对日可见的概念与迁移边界，不证明本项目兼容对应平台。

## 本地证据

### local-post-training-report

- 标题：Chapter 15 deterministic post-training report
- URL：https://github.com/RalfNick/deep-dive-ai-agent
- 类型：本地实验
- 核对日期：2026-09-28
- 用于：`chapter15.post-training.v2` 报告、24 条固定轨迹、审计到 SFT 的链路、同上下文 DPO 来源、单状态奖励更新、静态投机与安全门禁数字；仓库内实际来源是 `chapter15/reports/post-training-report.json`。RC1/v1 报告另存于 `chapter15/report-history/v1.0-rc1/`。
- 不用于/过期边界：有限动作模拟不代表真实大模型训练，不提供 Provider、GPU、Token、费用或模型能力结论；候选章节尚未发布到远端默认分支。

## 指令微调、偏好与 AI 反馈

### instructgpt

- 标题：Training language models to follow instructions with human feedback
- URL：https://arxiv.org/abs/2203.02155
- 类型：论文原文
- 核对日期：2026-09-27
- 用于：说明经典 RLHF 流程中的人工示范 SFT、输出排序、奖励模型和策略优化之间的关系。
- 不用于/过期边界：论文实验来自特定模型、标注分布与 2022 年系统；不推导今天任何产品的训练配方、效果或可用性。

### dpo-paper

- 标题：Direct Preference Optimization: Your Language Model is Secretly a Reward Model
- URL：https://arxiv.org/abs/2305.18290
- 类型：论文原文
- 核对日期：2026-09-27
- 用于：DPO 的策略/参考策略相对间隔、`beta` 与二元偏好损失；支持正文的手算结构。
- 不用于/过期边界：本地实验只复算有限动作损失，不复现论文语言模型训练、数据集结果或与 PPO 的性能比较。

### constitutional-ai

- 标题：Constitutional AI: Harmlessness from AI Feedback
- URL：https://arxiv.org/abs/2212.08073
- 类型：论文原文
- 核对日期：2026-09-27
- 用于：说明原则驱动的自我修订和 AI Feedback 可以成为偏好信号来源，人工反馈并非唯一可能来源。
- 不用于/过期边界：不把论文方法等同于 Anthropic 当前产品行为，也不声称本仓库复现了 RLAIF 或 harmlessness 结果。

## OpenAI 官方资料

### openai-fine-tuning

- 标题：Supervised fine-tuning — OpenAI API
- URL：https://developers.openai.com/api/docs/guides/supervised-fine-tuning
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：SFT 以输入与期望输出示范更新模型、先建立评测再训练、保留 holdout 的官方概念说明。
- 不用于/过期边界：核对时页面明确提示 fine-tuning 平台正在收尾且不再向新用户开放；模型清单、端点、字段、示例与时间线高度易变，正文不承诺可用性。

### openai-graders

- 标题：Graders — OpenAI API
- URL：https://developers.openai.com/api/docs/guides/graders
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：Grader 可为输出提供数值反馈、需要用人类金标校准，并存在 grader/reward hacking 风险。
- 不用于/过期边界：核对时页面明确标注 Graders 随相关 Evals/fine-tuning 工作流进入弃用；不固化 grader 类型、端点、模型白名单或执行镜像。

### openai-rft

- 标题：Reinforcement fine-tuning — OpenAI API
- URL：https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：RFT 的 prompt—采样—grader—策略更新闭环，以及任务需明确、可评分、有非零成功率且不易猜中的前置条件。
- 不用于/过期边界：核对时同样处于 fine-tuning 平台收尾期；正文不复制当前模型名、价格、配额、端点或可访问范围。

## Hugging Face 官方资料

### hf-transformers-chat-templates

- 标题：Writing a chat template — Transformers
- URL：https://huggingface.co/docs/transformers/chat_templating_writing
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：Chat Template 将结构化 message/tool call 编码为模型实际训练过的控制 Token 序列；训练与推理必须保持格式一致。
- 不用于/过期边界：模板字段、已支持模型和工具调用格式随 Transformers 与具体 tokenizer 变化，迁移前必须固定 revision 并验证往返解析。

### hf-datasets

- 标题：Build and load — Datasets
- URL：https://huggingface.co/docs/datasets/about_dataset_load
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：说明数据需要显式加载、版本化和预处理，不能把 Hub 名称当成稳定训练快照。
- 不用于/过期边界：不规定某个数据集可商用、无隐私风险或适合训练；许可、来源和 revision 必须逐项核对。

### hf-dataset-cards

- 标题：Dataset Cards — Hugging Face Hub
- URL：https://huggingface.co/docs/hub/datasets-cards
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：数据卡应记录许可、语言、规模、偏差、创建方式和使用边界，为本章数据治理清单提供字段参考。
- 不用于/过期边界：数据卡是信息入口而非法律或隐私审查结论；缺失元数据必须按未知处理。

### hf-trl-sft

- 标题：SFT Trainer — TRL
- URL：https://huggingface.co/docs/trl/sft_trainer
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：当前 TRL SFTTrainer 接受文本、对话和 prompt-completion 等数据形态，并依赖 Chat Template 与 loss mask 语义。
- 不用于/过期边界：API、默认值、支持模型和显存需求随版本变化；本项目未安装或执行 TRL，示例只做字段迁移。

### hf-trl-dpo

- 标题：DPO Trainer — TRL
- URL：https://huggingface.co/docs/trl/dpo_trainer
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：当前 TRL 的 DPOTrainer 将 preference 数据、策略与参考策略组织成训练输入。
- 不用于/过期边界：不声称本地 `PreferencePair` 可原样提交；模板、tokenization、reference model、padding 与 loss 选项必须按锁定版本验证。

### hf-trl-grpo

- 标题：GRPO Trainer — TRL
- URL：https://huggingface.co/docs/trl/grpo_trainer
- 类型：官方文档
- 核对日期：2026-09-27
- 用于：当前文档中的 prompt-only 数据、reward function、工具调用与 environment rollout 概念；Agent 训练需要限制轮数并验证模板前缀保持性。
- 不用于/过期边界：文档功能处于快速演进，不保证任意模型/工具模板兼容；本仓库未执行 GRPO、环境训练或 GPU rollout。

## Agent 后训练、奖励与污染研究

### agent-lightning

- 标题：Agent Lightning: Train ANY AI Agents with Reinforcement Learning
- URL：https://arxiv.org/abs/2508.03680
- 类型：论文原文
- 核对日期：2026-09-27
- 用于：近期 Agent RL 研究中执行与训练解耦、轨迹转训练 transition、信用分配和多步工具任务的研究方向。
- 不用于/过期边界：这是近期研究；论文中的结果没有在本仓库复现，不据此承诺对任意 Harness 零改造、稳定收益或生产适用性。

### reward-tampering

- 标题：Reward Tampering Problems and Solutions in Reinforcement Learning: A Causal Influence Diagram Perspective
- URL：https://arxiv.org/abs/1908.04734
- 类型：论文原文
- 核对日期：2026-09-27
- 用于：区分对奖励函数本身和奖励输入的篡改，并支撑“安全约束不能只依赖可被策略影响的标量奖励”这一风险边界。
- 不用于/过期边界：论文是一般 RL 安全分析，不直接证明本章测试篡改夹具等价于所有现实 reward hacking，也不提供充分的通用解决方案。

### benchmark-contamination

- 标题：Investigating Data Contamination in Modern Benchmarks for Large Language Models
- URL：https://aclanthology.org/2024.naacl-long.482/
- 类型：论文原文
- 核对日期：2026-09-27
- 用于：说明训练/评测重叠会削弱评测解释，污染检测本身也需要方法假设；支持按任务家族隔离 split。
- 不用于/过期边界：论文对特定模型与 Benchmark 的发现不能外推为本项目使用的模型已经污染；本章只验证本地重复与家族泄漏规则。

## RC2 参数高效训练资料

### reinforce-paper

- 标题：Simple statistical gradient-following algorithms for connectionist reinforcement learning
- URL：https://doi.org/10.1007/BF00992696
- 类型：论文原文
- 核对日期：2026-09-28
- 用于：从采样回报更新随机策略的 REINFORCE 思路。本章的 softmax 手算由该思路简化为单状态、即时奖励。
- 不用于/过期边界：不据此保证单个种子收敛，不声称本章实现多步 Agent RL、优势估计、KL、PPO 或 GRPO。

### hf-peft-lora

- 标题：LoRA — PEFT conceptual guide
- URL：https://huggingface.co/docs/peft/main/en/conceptual_guides/lora
- 类型：官方文档（main 分支页面；只使用概念与字段，不据此固定可运行版本）
- 核对日期：2026-09-28
- 用于：冻结基础权重、低秩适配器与 `r`、`target_modules`、`lora_alpha`、`bias` 的含义。
- 不用于/过期边界：不保证任意模型都有相同模块名或 adapter 足以拟合任务；本项目未执行 PEFT。

### qlora-paper

- 标题：QLoRA: Efficient Finetuning of Quantized LLMs
- URL：https://arxiv.org/abs/2305.14314
- 类型：论文原文
- 核对日期：2026-09-28
- 用于：量化、冻结基础模型并训练低秩适配器的思路；不是把所有训练状态降成 4 bit。
- 不用于/过期边界：论文硬件与模型成绩不作为本项目预算或效果保证。

### hf-bitsandbytes

- 标题：Bitsandbytes — Transformers
- URL：https://huggingface.co/docs/transformers/main/en/quantization/bitsandbytes
- 类型：官方文档（main 分支概念参考）
- 核对日期：2026-09-28
- 用于：权重量化、计算 dtype 与额外参数训练的边界；显存算术是本指南明确假设下的自算草图。
- 不用于/过期边界：未安装或验证硬件后端，不提供“某张显卡肯定够”的承诺；实际实施应改用固定版本文档与实测峰值。

## 台账维护规则

1. 产品能力只在 2026-09-27 的官方页面状态下成立；发布前必须重新核对 deprecation、版本、许可和访问范围。
2. 不用二手博客证明 API 字段、价格、模型白名单、硬件需求或合规承诺。
3. 论文用于解释方法与风险，不把作者报告的成绩改写成本项目成绩。
4. 所有本地数字必须回溯到 `chapter15/reports/post-training-report.json` 和 manifest；报告变化时先改 Schema 与测试。
5. 任何真实训练都必须重新冻结数据 revision、Chat Template、base model、代码版本、评测集和回滚目标。
