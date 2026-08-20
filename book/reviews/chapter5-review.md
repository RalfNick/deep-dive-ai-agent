# 第 5 章双视角 Review：上下文工程

Review 日期：2026-08-16

对象：`book/chapter5.md`、`chapter5/`、`book/images/fig5-*.svg`、`book/sources/chapter5-sources.md`。

结论：**修改后通过内容 Review，可以进入 PDF 预览阶段。** 当前没有未解决 P1。章节主线、实验合同和与第 4 / 6–8 章的边界清楚；最重要的改进不是扩写，而是修正了四个会让读者误读证据的指标与安全语义。

> **历史状态说明（2026-08-16）**：以上结论是 v1.0 发布前的自审快照。随后独立 Review 在 `chapter5-review-codex.md` 中补充发现 5 组 P1 与 4 组 P2；原记录保留不覆盖。逐项修订和新版发布证据见 `chapter5-remediation-v1.1.md`。

## 读者视角

第一次接触 Context Engineering 的读者需要依次回答：模型究竟看见什么、Prompt 与 Context 有何不同、上下文条目为什么需要身份、Builder 怎样作选择、实验如何定位失败、现实产品如何映射。修订后的章节基本形成这条渐进路径，并用同一个 `parse_price()` 修复任务贯穿。

### 做得好的部分

- 开头不是泛泛定义，而是“模型没看到失败测试却被责怪不聪明”的具体张力；
- Prompt、Context、Window、Memory 与 RAG 用定义、图和表三种方式交叉解释；
- `ContextItem → SourcePolicy → Builder → Packet → Serializer → Probe → Gateway` 数据流连续，读者能找到每个概念的本地代码；
- 五组实验都有命令、变量、关键中间状态、真实报告数字与外推边界；
- 噪声实验没有把不漂亮的数据藏起来，明确承认当前 Builder 保留了全部无关项；
- Claude Code / Codex 放在通用模型之后，没有写成产品功能百科；
- 14 道练习包含可观察验收标准，参考答案与代码路径对应。

### 读者侧修改记录

| 优先级 | 发现 | 证据 | 修改 | 状态 |
| --- | --- | --- | --- | --- |
| P2 | 初稿二至三级标题达到 46 个，阅读节奏过碎，也超过本章设计的 20–30 个 | 结构计数 | 把非主线三级标题改为加粗段首，保留练习分组；现为 29 个 | 已解决 |
| P2 | 概念边界图没有显式写出 Context Window 与 RAG | 初版 `fig5-2` | 增加 Window 容量约束，并说明 RAG 只生成候选 | 已解决 |
| P2 | `ContextItem` 图漏掉 `trust` 与 `retention`，无法独立表达数据模型 | 初版 `fig5-3` | 补充 trust、retention、required_for 与运行时成本 | 已解决 |
| P2 | 安全图没有把 Serializer 与 ToolCallFactory 放到链路上 | 初版 `fig5-7` | 改为 Builder + Serializer → Model Proposal → ToolCallFactory + Gateway | 已解决 |
| P2 | 报告哈希在 Grader 修正后失效 | 初稿与重新生成报告 | 更新正文 SHA-256，并说明它只证明本地报告未漂移 | 已解决 |

## AI 系统专家视角

专家 Review 重点检查：权威与信任是否分离、指令冲突是否真的按权威处理、预算与敏感度是否混淆、Digest 是否代表正确对象、Trace 是否泄密、离线与真实模型证据是否分开、注入模型行为与系统权限提升是否混淆、Action Gateway 是否被误写成沙箱。

### 专家侧修改记录

| 优先级 | 发现 | 证据 | 修改 | 状态 |
| --- | --- | --- | --- | --- |
| P1 | `SafetyGrade.untrusted_instruction_promotions` 实际统计“Probe 受注入影响后提出危险路径”，把模型服从与 Builder 权限提升混成一个字段 | `.env` 变体原先 promotion=1，但恶意项始终是 `authority=none` 且在不可信数据区 | 新增 `injection_followed`；promotion 只在恶意项被模型可见序列化且缺少不可信分隔时计数。当前 `.env` 记录为 promotion=0、followed=1、gateway_blocks=1 | 已解决 |
| P1 | `BuildGrade.passed` 没有纳入无关信息保留率，`noise_20` 会在保留全部噪声时显示通过 | 原报告 `irrelevant_retention_rate=1.0`、`passed=true` | 先增加失败测试，再把 irrelevant rate 纳入 Build 质量门槛；`noise_5/20` 现为 `passed=false` | 已解决 |
| P1 | Secret Trace 保存普通 SHA-256 与精确字节长度；低熵秘密可被字典猜测 | `test_trace_privacy.py` 原先明确要求 digest 出现在 Trace | 反转测试；Secret 现在写 `content_digest=redacted`、`estimated_units=0`，正文补充哈希与长度泄漏边界 | 已解决 |
| P2 | 指令冲突复用了通用 `_selection_key`，retention / trust 可能压过 authority，与正文“权威决定覆盖”不一致 | 新增低 retention SYSTEM 对高 retention REPOSITORY 的反例后测试失败 | 新增 `_instruction_conflict_key`，authority 优先，再考虑路径具体度、trust、retention 和稳定 ID | 已解决 |
| P2 | `BuildConfig.required_reserve` 没有参与构建或摘要，是无效配置 | 全仓搜索仅合同声明，无消费点 | 删除字段；保留更清楚的“Required 全部先于 Optional 选择”语义 | 已解决 |
| P2 | 正文把指令冲突能力写得比实现更宽，暗示可处理任意来源间覆盖 | Builder 实际只在相同稳定 `source_id` 冲突组内决胜 | 正文限定为“先作用域过滤，再在同一稳定来源身份内处理；版本替代独立完成” | 已解决 |
| P2 | 真实 DeepSeek 探针容易被读成已经运行 | 当前进程和用户环境均未安全提供 Key | 正文明示未运行；示例报告标为 synthetic；Provider 故障不进入行为分母 | 已解决 |

## 仍然成立的限制

以下不是未修缺陷，而是本章主动保留的证据边界：

1. `RuleBasedProbe` 是透明、确定性的行为探针，不模拟神经模型能力；
2. 信息位置实验只冻结变量，没有复现或证明普遍的 Lost-in-the-Middle；
3. UTF-8 字节只用于离线预算，不是 Provider Tokenizer；
4. Builder 没有语义检索或 reranker，所以噪声实验应失败；
5. `ActionGateway.evaluate()` 是策略判断，不是 OS 沙箱；本章没有真实副作用；
6. DeepSeek 真实调用未完成，不提供线上结果或模型比较；
7. 用户提供的 `大模型入门.pdf` 在核对时未找到，未进入本章证据；作者本机路径不进入公开仓库；
8. 长任务摘要、Checkpoint、Memory 与 RAG 实现留给第 6–8 章。

## 进入预览阶段的门槛

- Chapter 4 与 Chapter 5 测试必须全部通过；
- 离线报告两次生成必须字节一致；
- 7 个 SVG 必须通过 XML 解析，并在 PDF 中逐页检查缩放与文字裁切；
- 正文保持 1.8 万至 3 万非空字符、20–30 个二/三级标题、5 组实验与 14 道练习；
- PDF 中不得出现横向溢出、孤立标题、空白页或脚注失配；
- 全仓 Chapter 5 范围不得出现 Key 形状的明文。

视觉问题将在 PDF 预览阶段记录并修正；在完成逐页检查前，不把“SVG 可解析”写成“图已经视觉通过”。
