# 第 15 章真实训练迁移指南

这是一份“从教学模拟迁移到真实训练”的检查清单，不是可直接复制运行的配方。本章运行时不依赖 Transformers、Datasets 或 TRL；本章测试不会联网，不会读取 API Key，也没有下载权重、启动 GPU 训练或调用任何 Provider。

截至 2026-09-27，OpenAI 官方 SFT/RFT 页面标注 fine-tuning 平台正在收尾且不再向新用户开放，Graders 页面也标注进入弃用流程。所以下文只做概念映射。准备使用托管服务时，必须重新查看 Provider 文档、deprecation 页面、数据处理条款、区域可用性与模型支持范围。

## 1. 先确认训练真的是最小干预

把 `FailureObservation` 的反事实检查完整跑一遍：

1. 缺事实时先修 RAG/Context；
2. 能用确定性规则阻断时先修 Harness；
3. 指令和验收含糊时先修 Prompt/Skill；
4. 更强现有模型在相同条件下通过时先考虑模型路由；
5. 只有错误跨任务重复、上游解释已排除且存在可复用监督时，才进入后训练候选。

如果结论仍是 `inconclusive`，应补证据，而不是扩大训练预算。

## 2. 本地合同如何映射到真实数据

| 本地字段 | SFT | DPO | GRPO / Agent RL | 迁移注意 |
| --- | --- | --- | --- | --- |
| `TaskCase.prompt` | user message / prompt | 共同 prompt | rollout 初始任务 | 不把 eval 任务复制进 train |
| `TrajectoryStep.observation` | message/tool result | chosen/rejected 的共同状态 | environment observation | 先脱敏，保留结构，不保留凭据 |
| `TrajectoryStep.action` | assistant target 或 tool call | chosen/rejected action | policy action | 工具名与参数 Schema 必须版本化 |
| `TrajectoryStep.tool_result` | tool message | 偏好证据 | environment transition | 缺回执的样本隔离，不猜测结果 |
| `SupervisedExample` | prompt-completion / messages | 不直接使用 | 可作 warm start | 只允许 train split |
| `PreferencePair` | 不直接使用 | 同状态 chosen/rejected | 可用于 reward 校准 | 跨状态配对无效 |
| `RewardSpec` | 不适用 | 不适用 | reward / grader 设计 | safety veto 不与任务分相加 |
| `AuditFinding` | 数据阻断 | 数据阻断 | rollout 阻断 | blocker 修复前不得训练 |

## 3. Chat Template 与 tool call 不是“格式小事”

模型真正接收的是 Chat Template 编码后的 Token 序列，而不是抽象的 `messages` 字典。对工具型 Agent，至少冻结：

- tokenizer 与 base model revision；
- system/user/assistant/tool 角色的序列化方式；
- tool definition、tool call、tool result 的字段与顺序；
- EOS、generation prompt 与 loss mask；
- 训练格式和推理 Harness 的往返解析测试。

下面只展示形状，不对应某个当前 Provider 的上传接口。

> **示例，未在本项目执行。**

```jsonl
{"messages":[{"role":"user","content":"先检查再修复链接"},{"role":"assistant","tool_calls":[{"name":"read_file","arguments":{"path":"README.md"}}]},{"role":"tool","name":"read_file","content":"..."},{"role":"assistant","content":"已根据验证结果完成修复"}],"metadata":{"task_id":"task-010","split":"train","source_run_id":"run-001"}}
```

不要在序列化后丢掉 `task_id`、数据版本和来源；它们可以不进入模型上下文，但必须留在训练审计侧。

## 4. SFT：把通过审计的目标动作变成示范

SFT 数据只来自 `eligible_ids ∩ train split`。`validation` 用于选择 checkpoint，`eval` 只用于最终冻结评测。为每个样本保留：原始轨迹引用、转换历史、Chat Template revision、是否只对 assistant completion 计算 loss。

> **示例，未在本项目执行。**

```python
# 概念伪代码：实际 API、参数和版本请以锁定 revision 的官方文档为准。
dataset = load_versioned_train_split()
assert no_eval_family_leakage(dataset)
trainer = SFTTrainer(model=BASE_REVISION, train_dataset=dataset, args=PINNED_CONFIG)
trainer.train()
```

真实显存取决于参数量、精度、序列长度、batch、优化器状态、激活、并行方式和是否使用 adapter。不能用“某型号显卡肯定够”代替一次带峰值显存记录的 dry run。

### 4.1 全量、LoRA 与 QLoRA，先选改变的参数

LoRA 冻结基础权重，用低秩矩阵表示增量；QLoRA 在量化、冻结的基础模型上训练适配器。两者是参数/存储选择，不是新监督目标：它们都可承接 SFT，适用性取决于任务与模型。[PEFT LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)、[QLoRA 原论文](https://arxiv.org/abs/2305.14314)

| 方式 | 更新对象 | 开始前优先检查 | 不应据此保证什么 |
| --- | --- | --- | --- |
| 全量微调 | 全部目标权重 | 梯度、优化器和 checkpoint 成本 | 参数更多就一定更好 |
| LoRA | 指定模块的适配器 | 模块名、rank、是否另训输出头 | 任意行为都能由小适配器表达 |
| QLoRA | 量化基础模型上的适配器 | 量化后端、计算 dtype、硬件兼容 | 模型体积小就一定训练得下 |

选择顺序是：先核对模型与数据许可；冻结基础模型 revision；检查模块名和工具模板；再由显存约束选小范围 LoRA 或量化方案。以下只是讨论用的配置卡，**未执行，不是所有架构通用的推荐参数**：`r=8, lora_alpha=16, bias=none`；`target_modules` 必须由实际模型结构决定，不能默认每个模型都有 `q_proj/v_proj`。[LoRA 配置字段](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)

### 4.2 显存先列账，不先报显卡型号

可用下面的算术草图建立预算，随后用实际 dry run 测峰值。设冻结基础参数为 N，适配器可训练参数为 P；**这不是峰值显存预测模型**：

```text
基础权重：N × 存储字节/参数
可训练权重：P × 权重字节 + P × 梯度字节
优化器：P × 状态字节 + 可能的 FP32 主副本
另加：激活、临时张量、量化元数据、参考模型、KV/rollout、缓存与碎片
```

例如只算 70 亿参数的基础权重：BF16 两字节约 14 GB（13.04 GiB），理想 4 bit 载荷约 3.5 GB（3.26 GiB），后者还没计量化尺度与未量化模块。若假设适配器权重/梯度各 2 字节、Adam 两份 FP32 状态共 8 字节、另有 4 字节主副本，可训练部分约为 `16P` 字节；实现没有主副本或使用不同优化器时，此项就会变化。单个 4096×4096 矩阵加 rank=8 的两个低秩矩阵，P 为 `8×(4096+4096)=65,536`，但整个模型的 P 必须按全部目标模块求和。

序列变长或 batch 变大仍会增加激活压力；DPO 的参考策略与 RL 的多条 rollout 也可能成为主项。量化主要改变权重存储，不抹去这些成本。支持后端、精度和训练限制需按冻结版本重新核对。[Transformers bitsandbytes](https://huggingface.co/docs/transformers/main/en/quantization/bitsandbytes)

### 4.3 最小 smoke test 的验收卡（未在本项目执行）

在准备好独立训练环境后，先选 8–16 条**已审计的 train** 样本，用保守序列长度、micro-batch=1 跑 2–5 个更新步骤；这只是排错规模，不是有效训练规模。开始前预先登记：基础模型/模板 revision、mask 规则、可训练模块、dtype、随机种子、设备与预算。依次核验：

1. 模板编码后能区分 user、assistant 和 tool；目标 Token 没被全部 mask；
2. 工具调用与参数能往返解析，截断不会切坏目标 JSON；
3. loss 与梯度有限，只有预定参数在更新；
4. 记录真实峰值显存，不能把上面的权重算术当峰值；
5. 保存并重新加载 adapter，确认基础模型、模板和 adapter 版本匹配；
6. 在隔离小回归集上检查安全和解析，再决定是否扩大实验。

smoke test 通过只证明训练链路可运行，不证明任务质量提高。配置选择只用 validation；冻结后才跑最终 eval。完整回滚必须保留 baseline 模型、adapter、tokenizer、模板和 Harness 的组合。

## 5. DPO：先证明偏好对可比较

DPO 的 chosen 与 rejected 必须对应同一个任务状态和相同可用信息。数据管道应拒绝：

- 不同 prompt/状态硬拼出的偏好对；
- 因答案更长、更自信或格式更华丽产生的伪偏好；
- 来自 hidden answer、敏感载荷、未知来源、缺失回执或 eval split 的任一侧；
- chosen 侧含安全违规、受保护写入或未验证结果；
- 无法追溯到人工规则、专家标注或已校准 Judge 的标签。

> **示例，未在本项目执行。**

```json
{"prompt":[{"role":"user","content":"修复前先做什么？"}],"chosen":[{"role":"assistant","content":"先读取并验证现状"}],"rejected":[{"role":"assistant","content":"直接修改受保护测试"}],"metadata":{"chosen_state_id":"write_requested","rejected_state_id":"write_requested","source_ids":["traj-010","rejected-traj-010"],"rejected_kind":"authored_counterexample_not_executed"}}
```

完整、可追溯的失败或违规**反例**可以进入 rejected，用于表达不应采取的行为；它不是允许执行该行为的授权，也不能再导入 SFT 好示范。对真实内容仍需做许可、隐私和用途审查。仅比较相同 state_id 字符串不够，应核对共同 prompt、可用工具、权限、前缀历史及仓库快照；本地单步夹具只验证其显式字段，不是完整生产状态等价证明。

本地 `dpo_margin=0.15` 与 `loss≈0.620957` 使用人工固定 log probability，未由模型计算，不意味着任何真实 checkpoint 已改善。

## 6. GRPO / Agent RL：环境与奖励共同成为产品

GRPO 或其他 Agent RL 不只是换一个 Trainer。还需要可重置环境、工具生命周期、超时/预算、rollout 隔离、状态回执、信用分配和 reward 版本。tool call 模板必须能在追加 tool message 后保持既有前缀稳定，否则训练看到的概率与执行时语义可能错位。

> **示例，未在本项目执行。**

```python
# 概念伪代码：没有在本仓库安装或运行 TRL/Transformers。
trainer = GRPOTrainer(
    model=BASE_REVISION,
    train_dataset=prompt_only_train_split,
    environment_factory=VersionedSandboxEnv,
    reward_funcs=[outcome_reward, process_reward],
)
trainer.train()
```

即使框架把多个 reward 相加，发布门禁也不应照搬同一个标量。受保护文件写入、越权访问、隐藏答案和环境无效应独立统计并硬否决。

## 7. 许可、隐私和数据治理

每一批数据都应有 data card 或等价台账，至少记录：

- 来源、采集目的、所有者、许可与再分发条件；
- 用户内容是否允许用于训练，是否包含个人信息、商业秘密或源代码；
- 脱敏规则、盐管理、删除请求与保留期限；
- 派生/合成数据使用了什么模型与条款；
- train/validation/eval 的家族级去重结果；
- 标注者指南、分歧率、Unknown 与升级流程。

“公开可见”不等于“允许训练”。许可证、隐私、劳动与地域要求需要由相应负责人审查；缺失字段按未知处理，不默认放行。

## 8. 冻结评测集与安全硬门禁

训练前先冻结评测集、任务家族、Harness、Verifier、预算和环境镜像。训练后至少比较：

- 总体与各任务切片 outcome；
- 多次 trial 的稳定性；
- 工具选择、恢复、停止与预算行为；
- 受保护文件、越界、隐藏答案和数据外泄；
- 步骤、Token、时延和费用（只有 Provider 返回真实 usage 时才填写）。

安全硬门禁不能被 outcome、速度或成本抵消。缺覆盖或环境错误返回 `inconclusive`，不伪装成 pass。

## 9. 版本、灰度与回滚

一个可发布候选至少绑定：

`base model revision + tokenizer + Chat Template + dataset digest + transform code + objective/config + seed + Harness + frozen eval + safety gate`。

先在隔离环境回放，再小流量灰度。回滚不仅要恢复模型，也要恢复与其匹配的 tokenizer、模板、工具 Schema 和 Harness；否则“模型回滚”仍可能运行在不兼容外围系统中。训练数据、checkpoint 和评测报告应有独立 retention 策略。

## 10. 真实实施前的停止清单

出现任一情况就暂停：

- 任务边界或成功条件仍有专家分歧；
- 数据许可、隐私或来源无法确认；
- eval 与 train 存在任务家族重叠；
- Grader 未与人工金标校准，或可被猜测/投机；
- 没有安全硬门禁、灰度观测或完整回滚目标；
- 只记录最好 checkpoint，没有预注册比较规则；
- 当前 Provider 文档与本指南核对日期不一致且尚未重新验证。

这份指南的作用，是把“我想微调一个模型”改写为一个可审计的工程变更：为什么训练、用什么数据、优化什么、如何证明没有退化、出问题怎样撤回。
