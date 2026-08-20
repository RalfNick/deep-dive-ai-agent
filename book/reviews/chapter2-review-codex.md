# 第 2 章 Review：大模型的训练、对齐与推理

Review 日期：2026-08-13。

Review 对象：

- `book/chapter2.md`
- `chapter2/sft_mask_demo.py`
- `chapter2/real_sft_evidence.py`
- `chapter2/preference_demo.py`
- `chapter2/sampling_demo.py`
- `chapter2/reasoning_budget_demo.py`
- `chapter2/structured_output_demo.py`
- `chapter2/model_selection_demo.py`
- `chapter2/README.md`
- `chapter2/reference-answers.md`
- `chapter2/results/real_sft_curves.csv`
- `chapter2/results/real_sft_summary.json`
- `book/sources/chapter2-sources.md`
- `output/pdf/chapter2-preview.pdf`

## 总体结论

第二章的选题、主问题和章节顺序是合理的，已经完成从“语言模型原理”到“可用模型与 Agent 运行时”的关键过渡，建议判定为**条件通过**。

正文依次区分预训练、SFT、偏好优化与强化学习，再进入推理时计算、采样、API 协议、模型选择和 Coding Agent 产品映射。这个顺序回答了一个清楚的问题：**同样以逐 Token 生成为基础的模型，为什么会从续写器逐步变成可供 Agent 系统调用的行为组件。** 它既承接第一章，也给第三章的最小 Agent Loop 和第四章的 Harness Engineering 提供了概念接口，不建议拆章或大幅重排。

本章最突出的优点是边界意识强：参数改变、上下文改变和环境改变没有混为一谈；SFT、DPO、RLVR、推理预算和采样控制也没有写成一组营销名词；七个实验都明确说明了“能证明什么、不能证明什么”。

当前影响进入终稿的不是整体大纲，而是三处证据或契约问题：

1. 路径策略实验在 Windows 下接受盘符绝对路径和盘符相对路径，却把自己描述成工作区边界；
2. 真实 SFT 实验先重复语料再按字符切分，所谓“预训练验证集”与训练集高度重合；
3. 贯穿案例在第一章约定返回 `float`，本章却把 `Decimal` 版本写成可验证奖励，跨章节合同不一致。

综合评价约为 **8.3/10**。修复三项 P1、补齐实验元数据和最小回归测试后，可以进入复审稿。

## 规模与写作标准核对

当前正文约包含：

- 17,465 个中日韩统一表意文字字符；
- 14 个二级标题、29 个三级标题；
- 7 张原创 SVG；
- 7 个无 API Key 实验，其中 1 个执行真实 NumPy 梯度训练；
- 17 道分级练习；
- 38 页 PDF 预览。

概念边界、公式、可运行代码、中间状态、失败模式、工程限制、延伸阅读和下一章衔接均已出现。实验数和练习数略高于 `book/WRITING_GUIDE.md` 的建议范围，但没有明显为了凑数量而重复；正文汉字数则略低于“约 1.8 万”的建议下限，差距很小，无需为了达标扩写。

`book/README.md` 把本章写成“约 3.4 万中文字符”，与上述汉字统计不一致。本章约有 31,165 个非空白字符，因此该数字可能混用了“全部字符”和“中文字符”两种口径。建议全书统一采用“汉字数”或“非空字符数”之一，并在写作规范中说明统计方法。

## 实际验证结果

本次实际运行：

```powershell
python chapter2/sft_mask_demo.py
python chapter2/real_sft_evidence.py
python chapter2/preference_demo.py
python chapter2/sampling_demo.py
python chapter2/reasoning_budget_demo.py
python chapter2/structured_output_demo.py
python chapter2/model_selection_demo.py
python -m compileall -q chapter2
python -m unittest discover -s chapter2 -p "test*.py" -v
```

验证环境：

```text
Python 3.11.15
NumPy 2.2.6
```

结果：

- 七个实验脚本均正常退出；
- Python 编译检查通过；
- SFT mask 的有效位置数与平均损失和正文一致；
- DPO 标量示例的偏好间隔、概率与损失变化和正文一致；
- greedy、temperature 和 top-p 的候选分布与正文一致；
- 推理预算实验在预算 4、8、16、32、64 下分别解出 0、1、2、3、3 个迷宫，与正文一致；
- 结构化输出的六个教学样本依次产生语法、结构、枚举、语义、策略和成功结果；
- 模型选择实验的硬门槛过滤与 Pareto 结果和正文一致；
- 真实 SFT 实验在隔离目录中重新生成 CSV、JSON 和 SVG，三个文件的 SHA-256 均与仓库制品完全一致；
- 7 个 SVG 均可通过 XML 解析；
- 正文引用的 7 个本地文件或图片目标全部存在；
- 16 个脚注引用均有定义，没有未使用定义；
- `unittest discover` 发现 **0 项独立测试**。

真实 SFT 的关键结果也可复现：micro-11k 的六题成功率由 0 提升到 0.667，micro-40k 由 0 提升到 0.833；两者的目标损失均下降，但保留集变化方向不同。这支持正文“目标能力与保留能力必须联合评估”的有限结论，但不能消除下文所述的数据切分问题。

## P1：必须修改

### 1. 路径策略校验在 Windows 下可以绕过

`chapter2/structured_output_demo.py:42` 当前只拒绝两类字符串：

```python
if ".." in plan.file or plan.file.startswith(("/", "\\")):
    return "policy_error: file must stay inside the workspace", None
```

在本仓库实际使用的 Windows 环境中，以下结果可以直接复现：

```text
'C:\\secrets.py' -> ok
'C:secrets.py'    -> ok
'/etc/x.py'       -> policy_error
'../x.py'         -> policy_error
'src/app.py'      -> ok
```

`C:\secrets.py` 是盘符绝对路径，`C:secrets.py` 是带盘符的相对路径，两者都不应被“文件必须位于工作区内”的策略接受。字符串包含检查也没有处理路径规范化、符号链接或目录联接，以及校验与实际写入之间的竞态。

问题不只在示例代码。正文 `book/chapter2.md:552-580` 把该实验描述为语法、Schema、业务语义和权限策略四层检查，并说只有合法计划能通过。初学者可能因此把字符串过滤当成可用于 Agent 的路径安全边界，这与本章强调的“Schema 不能代替权限控制”相冲突。

#### 建议修改

- 让校验器接收明确的 `workspace_root`；
- 拒绝 POSIX 绝对路径、Windows 盘符绝对路径、UNC 路径和带盘符相对路径；
- 对 `workspace_root / user_path` 做规范化或解析，再验证目标能够 `relative_to(workspace_root)`；
- 在生产边界说明符号链接、Windows junction 和 TOCTOU 仍需由沙箱或受控文件 API 处理；
- 增加 Windows、POSIX、混合分隔符和链接逃逸测试；
- 如果不想把教学脚本扩大成完整路径安全示例，就把它明确改名为“字符串级策略示意”，并写明它**不能**形成真实工作区边界。

同时把文件首行的“三层校验”改成“四层校验”，与实现和正文一致。

### 2. “预训练验证损失”受到重复语料泄漏影响

`chapter2/real_sft_evidence.py:329-333` 先把通用语料重复 32 次，再按字符位置做 82%/18% 切分：

```python
general_lines = PRETRAIN_LINES + tuple(RETAIN_TEXT.splitlines())
pretrain_text = "\n".join(general_lines * 32)
split = int(len(pretrain_text) * 0.82)
pretrain_train = contexts_for_text(pretrain_text[:split], char_to_id)
pretrain_valid = contexts_for_text(pretrain_text[split:], char_to_id)
```

因为同一组文本已经重复多轮，后 18% 并不是独立的未见验证语料。本次对“上下文—下一字符”样本做集合检查得到：

```text
train examples:                 5876
validation examples:            1291
validation pairs seen in train: 1279
overlap rate:                   99.070%
```

因此 `pretrain_valid_end` 降到约 0.02 主要显示模型能够拟合重复语料，不能按通常含义解释为对未见通用文本的验证性能。正文 `book/chapter2.md:222-243`、图 2-7 和结果 JSON 都使用了“预训练验证损失”这一名称，会放大证据含义。

SFT 的 `SFT_TRAIN` 与 `SFT_VALID` 是分开的，所以这项问题不否定六题目标成功率；它影响的是预训练曲线的命名、切分完整性和实验可审计性。

#### 建议修改

- 先在独立文本或模板层划分 train/validation，再分别进行训练所需的重复或采样；
- 确保验证集的完整行、提示模板或上下文—目标对没有进入训练集；
- 在制品中记录样本数、唯一样本数、重复率、数据哈希和交集检查结果；
- 修复前将该指标改称“重复语料后段损失”或“拟合监控损失”，不要称为验证损失；
- 重新生成 CSV、JSON、图 2-7 和正文中的表格数值，并解释新旧结果不可直接比较。

### 3. `parse_price()` 的跨章节返回类型合同不一致

第一章明确约定：

```python
parse_price("￥19.90") == 19.9
```

位置：`book/chapter1.md:1048`、`chapter1/coding_agent_demo.py:26`。实际实现返回 `float`。

第二章在 RLVR 示例中却写成：

```python
parse_price("￥19.90") == Decimal("19.90")
```

位置：`book/chapter2.md:355`。在 Python 中，`Decimal("19.90") == 19.9` 为 `False`。本章 `book/chapter2.md:459` 又把“必须返回 Decimal”称为上下文未给出的隐藏需求，进一步说明它不是读者已知的稳定合同。

贯穿案例的价值在于让训练、推理、工具和 Harness 围绕同一个验收标准演进。这里静默改变返回类型，会让后续章节的成功/失败证据无法直接比较，也削弱本章关于“验证器定义游戏规则”的论证。

#### 建议修改

优先保持第一章现有合同，把 `book/chapter2.md:355` 改回：

```python
parse_price("￥19.90") == 19.9
```

如果全书确实要升级为货币场景更合理的 `Decimal`，则需要在首次变更处显式说明需求升级，并同步修改第一章实现、测试、后续章节验收和所有 Trace。不要只改第二章的一条奖励条件。

## P2：应当修改

### 4. 真实 SFT 制品缺少足够的复现实验元数据

`real_sft_summary.json` 当前记录了 seed、上下文长度、词表大小、参数量和最终指标，但关键训练设置仍只存在于代码中，例如预训练/SFT 步数、batch size、学习率、数据版本和两种模型配置。它也没有记录 Python、NumPy、平台、执行命令、数据哈希、代码提交和生成时间。

对于正文所称的“可审计制品”，只保存最终指标还不够。建议给 JSON 增加：

- `schema_version` 与 `generated_at`；
- Python、NumPy 和平台信息；
- 完整模型和优化配置；
- train/validation/retain 样本数、唯一数、交集率和哈希；
- 生成命令与代码版本；
- 每个制品的 SHA-256。

脚本已经支持 `--no-artifacts`，但 README 没有说明。建议补上该命令，让读者可以先做不改写仓库制品的验证运行。

### 5. 七个实验没有独立回归测试

当前脚本固定数据、显式 seed，复现性不错，但 `unittest discover` 找不到测试。脚本能打印预期输出，不等于关键教学不变量受到保护，尤其路径校验已经证明示例输出覆盖不足。

建议增加 `chapter2/tests/`，至少覆盖：

1. mask 有效位置与损失只受目标位置影响；
2. DPO 损失和解析梯度通过有限差分检查；
3. temperature 边界、top-p 截断和固定 seed 可复现；
4. 推理预算增加时可达状态不应反向减少，并记录展开节点口径；
5. 路径校验覆盖 Windows 盘符、UNC、POSIX、`..`、混合分隔符和工作区内路径；
6. 模型硬门槛失败不能被加权分数覆盖；
7. 真实 SFT 的数据切分无交集，固定环境下指标落在容差范围内。

### 6. 结构化输出实验不是实际 JSON Schema 校验，措辞应更精确

`structured_output_demo.py` 使用 `json.loads` 和手写 Python 条件模拟字段集合、类型和枚举约束，并未调用 JSON Schema validator。作为教学最小实现完全可接受，但正文和 README 中的“Schema”容易让读者误以为这里验证了某个正式 schema 文件或复现了供应商 Structured Outputs。

建议在实验标题或说明中写明“手写的 Schema-like 形状检查”，同时保留概念层面对 JSON Schema 的解释。如果要称为真实 Schema 实验，则增加 schema 文件和标准校验器，并保留语义、策略、执行层作为其后的独立步骤。

### 7. 四道设计题的参考答案没有完全覆盖题面验收条件

`chapter2/reference-answers.md` 整体简洁、方向正确，但以下题目尚不足以让读者自检：

- 第 2 题要求构造“指令对齐、事实性、任务成功中两项提升、另一项下降”的同一个例子；答案给了指标和多个反例，却没有明确完成一个“两升一降”三元组。
- 第 13 题要求设计 100 条最小评估集、上线门槛和严重错误成本；答案列了类别与指标，没有给出 100 条的配额、阈值或成本矩阵。
- 第 14 题要求 rubric 处理回答长度、候选顺序、测试真实性、最小修改和权限违规；答案只具体覆盖长度、顺序和一般数据质量，没有给出后三项的判定规则。
- 第 16 题要求列出语法、结构、语义、策略和执行五层；答案漏写语法层，给出的 `{"file":"../secret","operation":"patch"}` 也没有配套完整 schema，无法证明它在该 schema 下“JSON 完全合法”。

建议给每道设计题补一份“最低合格答案”，先逐项对应题面，再保留开放讨论。参考答案不必唯一，但必须能验证学生是否完成了题目中的全部硬要求。

### 8. 章节状态中的字符统计口径需要统一

如前所述，`book/README.md:43` 写“约 3.4 万中文字符”，当前正文约为 17,465 个 CJK 字符、31,165 个非空白字符。建议统一书稿元数据，避免后续把章节长度、编辑工作量和版面估算建立在不同统计口径上。

更稳妥的写法是：

> 约 1.75 万汉字、3.1 万非空字符，7 张图，7 个无 API Key 实验，17 道练习。

### 9. PDF 的两处分页可以继续抛光

38 页预览版整体可读：中文字体正常，代码、表格、公式和 7 张图没有发现裁切、重叠、破图或不可辨识内容，页眉页脚也保持一致。

需要优化的是：

- 第 5 页只有“预训练”标题和一小段引入，页面下半部留白很大；
- 第 32 页在“生产中的失败、成本与安全”开头列出一句话后，成本公式被推到下一页，留下大块空白；
- 第 38 页参考资料结束后留白较多，影响较小。

建议调整标题后的最小保留行数、公式/引用块的 `break-inside`、孤行寡行和章节前分页规则。前两处属于排版质量问题，不是内容发布阻断项。

### 10. 产品现状段落技术上通过，但必须保留出版前复核门

`book/chapter2.md:699-725` 主动标注“截至 2026-08-09”，这是正确做法。本次在 2026-08-13 重新核对官方文档，正文涉及的主要事实仍成立：

- OpenAI 当前模型指引仍描述 GPT-5.6 及其 reasoning effort、持久化推理、程序化工具调用和 multi-agent beta；
- Responses 仍推荐用于新项目，并有 typed output items、默认存储和 `store: false` 等状态语义；
- OpenAI RFT 页面仍说明托管平台正在逐步下线、不再接受新用户；
- Anthropic 仍把 effort 描述为软控制，把 `max_tokens` 描述为单次请求硬上限，把 task budget 描述为跨工具循环的建议性预算。

核对来源：[OpenAI Model guidance](https://developers.openai.com/api/docs/guides/latest-model)、[Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)、[Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)、[Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)、[Reinforcement fine-tuning](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning)、[Anthropic Effort](https://platform.claude.com/docs/en/build-with-claude/effort)、[Anthropic Task budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets)。

这里当前没有发现事实错误，但产品名、型号、支持档位和服务状态变化很快。建议把“更新来源台账日期并重新生成事实快照”列为每次出版构建的硬门槛，而不是依赖编辑记忆。

## 对大纲与章节结构的判断

### 当前主线成立

章节的实际主线可以压缩为：

```text
训练改变参数
  → SFT 塑造可模仿行为
  → 偏好/RL 改变选择倾向
  → 推理时系统分配上下文与计算
  → API 把生成结果变成可处理协议
  → 评估与硬门槛决定能否进入 Agent 产品
```

这条因果链清楚，也避免了两个常见跳跃：一是从 Transformer 直接跳到 Agent，二是把“更强模型”直接等同于“更可靠产品”。因此不建议把训练、推理和 API 三部分拆成彼此独立的章节。

### 建议保留的章节顺序

1. 生命周期与“对齐”边界；
2. 预训练；
3. SFT 与真实梯度实验；
4. 偏好优化、RLHF/DPO/RLVR 与奖励投机；
5. 推理时计算、采样和预算；
6. API、结构化输出和状态边界；
7. 模型选择；
8. 前沿事实与 Claude Code/Codex 映射；
9. 生产失败、成本、安全与小结。

当前正文已经基本遵循该顺序。模型选择放在 API 之后是合适的，因为读者到那里已经知道需要比较的不只是静态模型分数，还包括协议能力、预算、容量和治理约束。

### 建议收紧而不是扩写的部分

- 第一章已经介绍 temperature 与 top-p，完整机制、seed 限制和推理预算应以第二章为主；第一章可压缩，第二章无需再删核心内容。
- “Claude Code、Codex 与本章的关系”应继续保持映射性质，不再扩写成产品使用教程；真正的 Loop 与 Harness 留给第三、四章。
- 前沿观察应保留日期和官方来源，不宜继续堆更多厂商型号，否则会迅速增加维护成本。
- 延伸阅读按学习目标分路线是有效的，不需要再扩成书单综述。

## 写得好的部分

### 1. 开头问题具体，且与全书主线一致

用同一个 `parse_price()` 请求对比基础模型、对话模型和 Coding Agent，能自然引出训练、推理系统和外部工具三个层次。开头不是泛泛介绍“大模型训练是什么”，而是在解释产品行为差异。

### 2. 生命周期边界是本章最有价值的心智模型

“参数改变、上下文改变、环境改变”这一组区分准确、易复用，也为第三章的模型提议与工具执行、第四章的权限和沙箱打下了基础。建议将其视为本章核心结论之一，不要在修订中弱化。

### 3. SFT mask 讲到了真正影响训练目标的细节

正文不仅说“用户 Token 不算 loss”，还解释了移位标签、`-100`、角色起始标记和部署生成起点。这比只展示一段 Trainer 配置更有教学价值。

### 4. 偏好与强化学习没有被写成单一路线

RLHF、DPO、RLAIF、Constitutional AI、RLVR 和 GRPO 的责任边界基本准确，而且持续提醒读者 chosen 不等于真相、可验证奖励不等于完整意图、奖励模型不等于最终裁判。奖励投机紧跟训练方法出现，结构合理。

### 5. 推理控制的几个旋钮区分得清楚

temperature、top-p、seed、reasoning effort、最大输出 Token 和任务预算没有被混为一谈。正文对测试时计算论文数字的适用范围也有明确限制，没有把研究条件下的倍率写成通用产品结论。

### 6. API 段落成功把模型输出重新放回系统责任中

结构化输出、工具调用、业务语义、权限和实际执行分层，是从第二章进入 Agent 工程的必要桥梁。即使路径示例需要修复，这一段的教学方向本身是正确的。

### 7. 模型选择采用硬门槛和 Pareto 前沿，而不是排行榜叙事

先过滤安全、容量和能力不合格项，再比较成本、延迟和成功率，符合生产决策。该实验也明确说明教学夹具不能用于真实厂商排名，证据边界清楚。

### 8. 小结诚实说明了没有证明什么

`book/chapter2.md:946` 明确说字符级微型模型没有证明任何大模型在业务上达到生产要求。这一结论与章节实验规模匹配，应保留。

## 推荐修改顺序

### 第一轮：修证据与合同

1. 修复路径策略或降低其安全声明，并增加跨平台路径测试；
2. 重做真实 SFT 的训练/验证切分，重新生成三个制品；
3. 统一 `parse_price()` 的返回类型合同；
4. 核对正文表格、图 2-7、README 和结果 JSON 是否全部同步。

### 第二轮：补可复现性

1. 为真实 SFT 增加完整元数据、数据哈希和交集审计；
2. 增加 `chapter2/tests/`；
3. 在 README 记录 `--no-artifacts` 和一条完整复现命令；
4. 统一字符统计和章节状态。

### 第三轮：编辑与版式

1. 补齐第 2、13、14、16 题的参考答案；
2. 统一“三层/四层”和“Schema/Schema-like”的措辞；
3. 调整 PDF 第 5、32 页分页；
4. 出版前再次核对官方产品事实和链接。

## 复审验收清单

- [ ] Windows 盘符绝对路径、盘符相对路径、UNC、POSIX 绝对路径和 `..` 逃逸均被拒绝；
- [ ] 工作区内正常相对路径仍能通过；
- [ ] 路径策略文字明确承认沙箱、链接与 TOCTOU 边界；
- [ ] 预训练 train/validation 的上下文—目标对交集为 0，或对任何不可避免的交集给出定义和理由；
- [ ] CSV、JSON、SVG 和正文数值由修复后的同一次运行生成；
- [ ] 实验 JSON 包含环境、超参数、数据哈希和代码版本；
- [ ] 全书 `parse_price()` 采用同一个返回类型和验收表达；
- [ ] `python -m unittest discover -s chapter2 -p "test*.py" -v` 能发现并通过测试；
- [ ] 四道参考答案覆盖题面的全部硬要求；
- [ ] README 的字符数采用全书统一口径；
- [ ] PDF 不再出现第 5、32 页的大块非必要留白；
- [ ] 发布前重新核对 OpenAI、Anthropic 官方文档并更新核对日期。

## 最终判断

第二章的大纲合适，内容层次也基本成熟。它已经回答了“模型怎样从会续写变成可被 Agent 系统使用的组件”，同时成功把模型能力与运行时责任分开。当前不需要增加更多概念，也不需要重写章节结构；最有效的修订是把实验安全边界、数据切分和贯穿案例合同做到与正文主张同样严谨。

完成 P1 后，本章可以继续保持“二审稿”定位；完成测试、元数据、参考答案和分页修订后，建议升级为“复审稿”。
