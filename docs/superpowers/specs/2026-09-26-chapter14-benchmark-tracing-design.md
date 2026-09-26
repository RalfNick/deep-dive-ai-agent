# 第 14 章《Benchmark、Tracing 与生产诊断》设计说明

日期：2026-09-26  
目标分支：`codex/chapter14-benchmark-tracing`  
状态：待作者书面确认后进入实施计划  

## 1. 目标与读者

第 14 章面向已经理解 Agent Loop、Harness、工具调用、Coding Agent 和离线评估，但尚未系统学习生产观测与事故诊断的开发者。章节不以平台功能清单为中心，而回答一个具体问题：

> 离线评估已经通过，线上任务成功率也没有明显下降，为什么用户仍然觉得 Agent 变慢、变贵、偶尔卡住？

读完后，读者应能：

1. 区分公共 Benchmark、内部离线 Evaluation、生产 Observability 与 Incident Diagnosis；
2. 判断两份 Benchmark 结果是否具有可比性，而不是只比较一个总分；
3. 用 Session、Trace、Span、Event、Metric、Log、Score 描述一次 Agent 运行；
4. 从 Trace 计算端到端延迟、关键路径、重试放大和成本归因；
5. 设计兼顾稀有故障、成本与隐私的采样策略；
6. 通过切片、回放和消融实验，把线上症状收束为可验证的根因；
7. 将生产失败转成第 13 章式回归任务，并理解它与第 15 章后训练数据的边界。

## 2. 核心叙事

全章采用“生产事故诊断”主线。一个候选 Agent 在固定离线任务上通过发布门禁，部署后总体成功率仍接近基线，但 p95 延迟、每次运行成本单位和工具重试率明显恶化。普通日志只能看到若干超时和多次模型调用，无法证明它们属于同一条因果链。结构化 Trace 显示：Harness 的重试策略在工具超时后重复执行上下文装配与模型调用，导致尾延迟和成本被共同放大。

章节按四幕推进：

1. **分数不能替代现场**：建立 Benchmark、Evaluation、Observability、Diagnosis 的边界，并用 Benchmark Card 判断公开结果是否可比。
2. **把运行变成证据**：从日志堆进入 Session、Trace、Span 和显式依赖关系，建立可验证的遥测合同。
3. **从现象定位根因**：解释分位数、关键路径、Token/成本、采样、隐私和观测盲区。
4. **形成改进闭环**：通过切片、回放和消融定位重试策略，修复后重放旧 Trace，并把代表性失败沉淀为离线回归任务。

Benchmark 不是独立支线。它提供“外部比较为什么也需要完整运行合同”的第一层反例；生产 Trace 则把同一原则带入真实运行：任何数字都必须附带任务、环境、Harness、预算和数据完整性。

## 3. 章节边界

### 3.1 本章包含

- Benchmark Card 与可比性判定；
- SWE-bench 家族作为公开 Benchmark 阅读案例，但不复制实时排行榜；
- Metrics、Logs、Traces、Evals、Feedback 的责任边界；
- Session、Trace、Span、Event、Score 与关联 ID；
- 端到端延迟、nearest-rank 分位数、显式依赖图和关键路径；
- Token/成本单位、工具重试和上下文装配的归因；
- Head Sampling、Tail Sampling、遥测完整率和隐私脱敏；
- 版本/场景/工具/错误类型切片；
- 回放、消融、事故报告和生产样本回流；
- Langfuse、OpenTelemetry 与 OpenAI Agents SDK Tracing 的责任映射。

### 3.2 本章不包含

- 不比较真实模型、Claude Code、Codex 或观测平台谁更强；
- 不复制或冻结某天的排行榜名次；
- 不部署 Langfuse、ClickHouse、OpenTelemetry Collector 或云服务；
- 不把日志、指标或 Trace 后端实现写成运维手册；
- 不采集或展示隐藏思维链；只记录工具行动、公开输入输出的受控表示和结构化摘要；
- 不按供应商当前价格计算真实费用；实验使用版本化成本单位；
- 不展开第 15 章的 SFT、偏好优化、强化学习和数据训练流程；
- 不展开第 16 章的长期持续改进组织机制。

## 4. 贯穿数据集

实验使用完全虚构、确定性生成的生产风格数据，不连接真实模型或线上系统。数据包含三个发布版本，每个版本 24 条 Trace，共 72 条计分 Trace：

| 发布版本 | 用途 |
| --- | --- |
| `stable` | 事故前基线 |
| `incident` | 质量近似稳定，但延迟、成本和重试恶化 |
| `fixed` | 只修正已定位的 Harness 重试策略 |

每个版本覆盖四种流量切片：简单问答、知识检索、写操作和故障恢复，每个切片 6 条。任务成功日程、Span 时序、Token 使用、错误和重试均由固定夹具与固定种子产生。最终报告只陈述代码实际计算出的数值，不在设计阶段预填结论数字。

另有两份虚构 Benchmark Submission，用于展示相同 `Resolved %` 在任务版本、Harness、预算、重试或运行次数不同的情况下不能直接比较。公开 Benchmark 仅用于解释阅读方法，不作为本地策略的成绩来源。

## 5. 数据合同

### 5.1 `BenchmarkCard`

字段包括：`benchmark_id`、`benchmark_version`、`task_subset`、`task_period`、`subject`、`harness`、`model`、`tools`、`environment`、`step_budget`、`token_budget`、`timeout_ms`、`retry_policy`、`attempts_per_task`、`metric`、`exclusions`、`contamination_risk` 和 `source`。

可比性判定输出 `comparable`、`partially_comparable` 或 `not_comparable`，同时返回不一致字段和原因码。任务集合或指标口径不同、关键字段缺失时不得输出 `comparable`。该判定只检查报告合同，不证明任务代表性。

### 5.2 `SpanRecord`

字段包括：`trace_id`、`span_id`、`parent_span_id`、`depends_on_span_ids`、`kind`、`name`、`start_ms`、`end_ms`、`status`、`attributes`、`input_digest`、`output_digest`、`input_tokens`、`output_tokens`、`cost_units` 和 `error_type`。

`parent_span_id` 表示结构归属，`depends_on_span_ids` 表示执行依赖。二者不能混用：父子树适合阅读与聚合，依赖 DAG 用于计算关键路径。字段缺失时保留 `null`，不得从文本长度伪造 Token 或成本。

### 5.3 `TraceRecord`

字段包括：`trace_id`、`session_id`、`release_id`、`scenario_id`、`slice`、`started_at_ms`、`ended_at_ms`、`status`、`outcome_score`、`spans`、`tags`、`sampling` 和 `telemetry_complete`。

Trace 验证必须检查：ID 唯一、父节点存在、父子无环、依赖无环、子 Span 时间位于父 Span 内、根时间与端到端时间一致、状态枚举合法、Usage 非负，以及稳定属性中不存在禁止字段。

### 5.4 `SamplingDecision`

字段包括：`trace_id`、`stage`、`decision`、`reason_codes`、`probability` 和 `policy_version`。Head Sampling 根据 Trace ID 做固定概率决策；Tail Sampling 可依据完整 Trace 中的错误、长尾延迟、审批、安全事件和新发布版本做决定。

### 5.5 `IncidentReport`

字段包括：`symptom`、`affected_slices`、`data_completeness`、`candidate_causes`、`supporting_trace_ids`、`counterevidence_trace_ids`、`ablation_results`、`root_cause`、`confidence`、`unknowns`、`recommended_actions` 和 `regression_task_ids`。

事故报告必须同时保留支持证据与反证。没有足够 Trace 或遥测完整率不足时，结论应为 `inconclusive`，不能把“没有观察到”写成“没有发生”。

## 6. 指标与算法口径

- 端到端延迟：`ended_at_ms - started_at_ms`；
- Span 时长：`end_ms - start_ms`；
- 分位数：使用 nearest-rank，报告中记录算法版本；
- Span 时长总和：只用于展示嵌套和并行导致的重复计数，不作为端到端延迟；
- 关键路径：排除只承担分组作用的 root/container Span，在 `depends_on_span_ids` 构成的工作 Span DAG 上按时长求最长路径；缺失依赖、引用分组 Span 或存在环时不输出结果；
- 重试放大率：实际尝试数与逻辑操作数之比；
- Token 与成本：只聚合显式 Usage；缺失部分单独报告 Coverage；
- 成本单位：使用仓库内版本化 Rate Card，不声称等同于任何供应商价格；
- 质量：使用夹具中的确定性 Outcome，不以在线点赞代替客观正确性；
- 遥测完整率：完整 Trace 数除以应记录 Trace 数，独立于任务成功率；
- Tail Sample 只用于诊断，不直接用于估计总体错误率；总体分母来自未采样的低基数 Metrics 或带采样权重的概率样本。

## 7. 五组实验

### 实验 14-1：同一个分数，为什么不能直接比较

输入两份总分相同的 Benchmark Card。逐字段比较任务、Harness、预算、环境、重试、尝试次数和指标，输出可比性等级、差异字段和判断边界。

### 实验 14-2：日志堆与 Trace 树

把一次运行拆成乱序普通日志，先尝试按时间排序，再用 Trace/Span/Parent/Dependency 重建结构。观察相同时间戳、并行工具和后台恢复如何使普通日志无法表达完整因果关系。

### 实验 14-3：端到端延迟到底花在哪里

在一个含并行检索、模型调用、工具超时和验证的 Trace 中，分别计算端到端延迟、Span 总和、依赖 DAG 关键路径、重试放大、Token Coverage 和成本单位。至少包含一个“Span 总和大于端到端时间”的反例。

### 实验 14-4：采样、脱敏与观测盲区

比较固定概率 Head Sampling、错误/慢请求优先 Tail Sampling 和组合策略。使用稀有错误验证 Head Sampling 可能漏报；使用字段级红线验证脱敏在缓冲、采样和导出之前完成。Trace 被采样掉时，低基数请求/错误 Metrics 仍保留。

### 实验 14-5：从告警到根因

比较 `stable`、`incident`、`fixed` 三个版本，按场景、工具和错误类型切片。对模型、Prompt、上下文装配、工具延迟和 Harness 重试策略执行确定性消融。只有当某项消融能消除症状且反证不冲突时，才把它写入 `root_cause`；否则输出 `inconclusive`。最后生成回归任务和事故报告。

## 8. 代码结构与职责

```text
chapter14/
├── __init__.py
├── contracts.py            # 稳定数据合同与枚举
├── benchmark.py            # Benchmark Card 与可比性判定
├── trace_builder.py        # 固定夹具生成 72 条 Trace
├── trace_validation.py     # 树、DAG、时间和隐私字段验证
├── metrics.py              # 分位数、关键路径、成本与 Coverage
├── sampling.py             # Head/Tail/组合采样
├── privacy.py              # 导出前脱敏和敏感字段门禁
├── diagnosis.py            # 切片、消融和 Incident Report
├── experiments.py          # 五组实验 CLI 与规范报告
├── exercise_solutions.py   # 练习独立运行入口
├── preview.py              # 本地预览入口
├── fixtures/
├── schemas/
├── reports/
├── tests/
├── integrations.md         # 当前平台映射与可选接入示例
├── README.md
└── reference-answers.md
```

核心运行依赖以 Python 标准库为主，测试锁定 pytest。平台 SDK 不是规范实验依赖；`integrations.md` 中的示例必须标注核对日期和版本边界。

## 9. 正文结构

正文按以下主题推进，最终控制为 25–35 个二三级标题：

1. 通过离线评估却发生线上事故；
2. 本章短答案与阅读路线；
3. Benchmark、Evaluation、Observability、Diagnosis 的边界；
4. Benchmark 测量系统而不只是模型；
5. Benchmark Card 与实验 14-1；
6. SWE-bench 家族及公共结果阅读方法；
7. Metrics、Logs、Traces、Evals、Feedback；
8. Session、Trace、Span、Event 与关联 ID；
9. 模型、工具、检索、审批、重试和验证 Span；
10. 实验 14-2；
11. 平均值、分位数、并行和关键路径；
12. Token、成本、重试与高基数；
13. 实验 14-3；
14. Head/Tail Sampling、遥测完整率与隐私；
15. 实验 14-4；
16. 症状确认、切片、假设、反证和消融；
17. 实验 14-5；
18. 生产 Trace 回流离线评估；
19. Langfuse、OpenTelemetry、OpenAI Tracing 责任映射；
20. 常见失败模式与 Incident Report；
21. 本章代码阅读顺序；
22. 已证明、未证明、小结、练习与下一章衔接。

## 10. 插图设计

共 7 幅原创图，继续使用浅色纸张、手绘描边、蓝绿紫橙分区的既有风格；文字和箭头由可控矢量布局生成，最终图片放在 `book/images/chapter14/`，源文件与生成记录放在 `infographic/chapter14/`。

1. 离线绿色、线上红色：Eval、Benchmark 与生产现场之间的证据断层；
2. Benchmark 可比性检查：Dataset、Harness、预算、环境、统计口径；
3. 五类观测信号地图：Metrics、Logs、Traces、Evals、Feedback；
4. Session → Trace → Span：一次 Agent 请求的结构树与依赖边；
5. 关键路径时间线：串行、并行、等待、重试和端到端时间；
6. 采样与隐私漏斗：记录、脱敏、采样、导出、存储；
7. 生产诊断闭环：Detect → Locate → Replay → Ablate → Verify → Release。

## 11. 练习设计

共 14 道：4 道基础、6 道进阶、4 道综合。

- 基础：概念边界、Benchmark 可比性、读 Trace、nearest-rank 分位数；
- 进阶：重建 Span 树、验证依赖 DAG、计算关键路径、分析重试放大、设计采样规则、分类隐私字段；
- 综合：设计 Benchmark Card、诊断版本退化、把 Trace 转成回归任务、审查一份证据不足的事故报告。

计算题提供固定输入和可复算答案；代码题有独立 CLI 入口；设计题给出评分判据。参考答案不能只重复题目要求。

## 12. 平台与资料策略

来源台账至少覆盖：

- SWE-bench 官方站点、论文和 Verified 说明；
- OpenTelemetry Traces、Sampling 与 GenAI Agent Semantic Conventions；
- Langfuse Observability 数据模型、Tracing 最佳实践、Masking、Evaluation Loop；
- OpenAI Agents SDK Tracing、敏感数据开关和自定义 Trace Processor；
- 分布式追踪、尾采样、分位数和可观测性的经典资料；
- Benchmark 污染、可复现性和 Agent 评估基础研究。

所有快速变化的产品资料记录核对日期、页面版本或固定提交。OpenTelemetry GenAI Agent 约定在核对时处于 Development，本章只做概念映射，不声称本地 Schema 符合未来稳定标准。平台当前价格、排行榜名次和易变化的 UI 步骤不进入正文稳定结论。

## 13. 隐私与故障策略

- 默认不记录原始用户标识、凭据、Authorization、Cookie、隐藏答案、完整文件内容或隐藏思维链；
- 能用摘要、枚举和稳定哈希回答诊断问题时，不保存原文；
- 脱敏在本地缓冲和导出之前执行；Collector 侧脱敏只能作为第二道防线；
- 线上遥测导出失败不得阻断用户任务，但必须增加丢失计数并降低事故结论置信度；
- 规范实验中的非法 Trace fail-fast，避免用错误数据生成貌似合理的报告；
- 短进程需要显式 flush，但正文同时说明 flush 的阻塞与失败语义；
- 高基数内容只进入受控 Trace 属性，不能直接成为 Metrics 标签。

## 14. 验收标准

- 正文约 2.3–2.8 万中文字符，25–35 个二三级标题；
- 5 组确定性实验、至少 4 个失败样本、4–6 张比较表；
- 72 条生产风格计分 Trace，三个版本和四个平衡切片；
- 7 幅图、14 道练习、完整参考答案；
- 版本化 JSON Schema、JSON/Markdown 规范报告和可重复哈希；
- 测试覆盖合同验证、树/DAG、时间边界、分位数、关键路径、成本 Coverage、采样、脱敏、可比性判定、消融和报告；
- 两次完整实验产生相同稳定报告；
- 正文命令、路径、数值、表格和报告一致；
- 读者视角与 AI/可观测性专家视角两轮审稿，修复 P0/P1；
- 桌面与 390px 移动预览通过，7 幅图加载、表格可滚动、无失效锚点和整页横向溢出；
- 全书现有回归、仓库检查和 MkDocs strict 构建通过；
- 新增 `book/versions/chapter14-v1.0-rc1.md`，保留前 13 章历史；
- 创建本地候选提交，不推送、不发布、不修改公开章节 allowlist。

## 15. 版本与交付边界

实施从第 13 章 rc2 提交 `be655ca04f6449808bdbab64e5b3ee00c10a4c08` 开始。第 13 章正文、代码、报告、Schema、审稿和版本记录不改写。第 14 章使用新目录、新图目录、新来源台账、新审稿文件和新版本记录。

本轮交付是本地 `v1.0-rc1` 候选，不创建发布 tag，不推送 GitHub，不更新 `book/manifest.json`、`book/SUMMARY.md`、`mkdocs.yml` 或公开站点构建清单，不部署网站，也不生成 PDF/EPUB。
