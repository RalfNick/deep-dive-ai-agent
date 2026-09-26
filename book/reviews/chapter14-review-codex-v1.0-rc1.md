# 第 14 章 v1.0-rc1 双视角审稿报告

审稿日期：2026-09-26。对象：`book/chapter14.md`、`chapter14/` 实验包、稳定报告 Schema、来源台账、7 幅插图、14 道练习与本地预览。实现基线：Chapter 13 rc2 提交 `be655ca04f6449808bdbab64e5b3ee00c10a4c08`。结论：**GO，可冻结为本地 v1.0-rc1 候选；本轮不推送、不发布。**

本轮没有调用第二个审稿 Agent：当前任务要求在同一执行上下文连续实施，也没有授权子代理。因此本文是按独立审稿模板完成的分轮自审，覆盖计划、代码、正文、图、实验与发布边界，但它比“由一个未参与实现、拥有全新上下文的审稿人复核”少一层独立性。这一限制不影响自动验证结果，却应保留在候选记录中。

## 总体结论

本章主线成立：它没有把 Benchmark、Tracing 和平台功能写成并列知识点，而是从“离线成功率不变、线上 p95/成本/重试退化”的事故出发，逐层建立 Benchmark Card、五类观测信号、Session/Trace/Span、依赖感知关键路径、采样与隐私、切片/反证/消融和回归任务。所有本地数字来自同一份 72-Trace 规范报告；容易变化的平台信息进入带核对日期的来源台账。

首次读者能够先获得一句短答案，再运行五组实验；专家能够沿 JSON、Schema、测试和 Trace ID 回查结论。审稿发现两项 P1 实现偏差，均已通过失败先行测试修复。当前没有剩余 P0/P1。

## 审稿中修复的问题

| 优先级 | 发现 | 为什么重要 | 修复与证据 |
| --- | --- | --- | --- |
| P1 | 正文规定“先脱敏，再采样”，旧 `sampling_report` 却先根据原始 Trace 选择保留集合，只对已保留明细脱敏 | Tail 采样需要暂存完整 Trace；若原始敏感内容先进入采样缓冲，UI 侧遮罩和事后脱敏不能恢复信任边界 | `privacy.py:57` 新增 `redact_trace`；`sampling.py:63` 在 Combined/Tail 决策前拒绝不安全 Trace，并在报告选择保留集合前转换全部 Trace；`test_sampling_privacy.py:98` 固定 raw-reject/safe-accept |
| P1 | 依赖 DAG 只检查未知节点和环，没有拒绝“依赖项还未结束，后续 Span 已开始”的时间矛盾 | 无效依赖时间仍可进入最长路径计算，制造不可能的因果链和误导性关键路径 | `trace_validation.py:97` 新增 `dependency_time_order`；`test_trace_validation.py:74` 证明无效 DAG 在指标前失败关闭 |

两个修复不改变规范报告数值与哈希。重新生成的 8 个诊断产物与仓库中的 canonical artifacts 逐字节一致。

## 首次读者视角

### 优点

1. 开场不是抽象定义，而是“24 个任务仍然 23 个成功，为什么用户觉得变慢”的具体冲突。读者很快理解本章不是重复第 13 章。
2. 概念顺序合理：先解释“通过有条件”，再审 Benchmark，随后建立信号与 Trace 结构，最后进入采样和因果诊断。
3. 分位数与关键路径都有可手算例子。`80 + max(120, 200) + 40 = 320 ms` 能直观解释为什么 Span 时长不能相加。
4. 图的阅读顺序与正文一致。7 幅图分别承担证据断层、可比性、信号边界、结构/依赖、关键路径、采样/隐私和诊断闭环，没有用图替代必要解释。
5. 五个实验都先提出读者要观察的问题，再给命令与证据边界；不会把固定夹具误写成真实模型成绩。
6. 14 道练习从概念、手算、读报告逐步进入采样、隐私、反证与消融。第 2、3、5、6、14 题直接执行本章代码，其余题有结构化 Rubric。

### 可读性判断

正文为 23,877 个字符，16 个二级标题、19 个三级标题，共 35 个二三级标题；包含 5 组实验、7 幅图和 6 张比较表。篇幅处于计划的 2.3–2.8 万字符范围，标题数量位于 25–35 的上边界。部分“生产误判”使用粗体段首而非继续增加目录层级，避免长文章被切得过碎。

桌面预览在 1440×1000 下保持单栏阅读；390×844 下正文无整页横向溢出，宽表与技术图只在自己的容器中横向滚动。7 幅图的左、右视区均已检查，标题、箭头和结论框没有被图片本身裁掉。

## 可观测性与评估专家视角

### Benchmark 可比性

`BenchmarkCard` 将任务、被测系统、资源、指标和来源分开。比较器有 `comparable / partially_comparable / not_comparable` 三态，并刻意不让相同分数覆盖合同差异。公开 SWE-bench 只用于讲解版本、子集和 Harness 变化；正文不固化实时榜单成绩。

仍需保留的边界是：Card 只能审计已声明合同，不能证明任务代表性、运行者没有漏报配置，或数据未被污染。因此结果中保留 `contract_comparison_only` 与 `task_representativeness_not_proven`。

### Trace 结构与关键路径

父子树和工作依赖 DAG 在合同中独立表达并独立检查。根/容器 Span 不进入工作 DAG，避免容器耗时与子工作重复相加；未知父节点、越出父区间、父图/依赖图成环、依赖容器以及依赖时间倒置都会在指标计算前失败关闭。

分位数固定为 `nearest-rank.v1`。关键路径固定为 `work-dag-longest-path.v1`。这两个名字进入报告，避免其他平台改用插值分位数或不同 Span 口径后仍把数字当作同一指标。

### 用量、成本与重试

缺失 Token 保持 `null`，已知总量与 Coverage 同时报告；教学成本使用 `chapter14.cost-units.v1`，没有供应商币种或价格。重试放大率按“可计费尝试 / 声明的逻辑操作”计算，而不是简单数 Retry Span。Outcome 稳定与资源退化能在同一 release comparison 中并列呈现。

### 采样、隐私与遥测缺失

总体计数与诊断保留集合分开。72 个请求、3 个最终失败来自 Population Counter；49 条保留 Trace、12 条带错误 Span 只描述诊断样本。报告没有生成 Tail Sample Error Rate。

Combined/Tail 路径现在要求 Trace 已经过 Export Safety Gate；`sampling_report` 在决定输出哪些明细前对全部输入执行字段转换和验证。Telemetry Completeness 与 Trace Coverage 分开，低完整率会让 Incident Report 降级为 `inconclusive`，不会把“没有看到”解释成“没有发生”。

### 因果结论

切片只用于定位，不被写成因果证明。报告同时保存三条支持 Trace 与四条反证 Trace；五组显式消融中，只有固定 `retry_policy` 同时消除延迟、成本和重试放大症状。结论仍标明 `deterministic_counterfactual_fixture`，并保留 Provider Usage 部分缺失和教学夹具不证明现实因果两个 Unknown。

### 标准与平台状态

OpenTelemetry、Langfuse 与 OpenAI Agents SDK 只做责任映射，不复制易变 API 清单。来源台账统一记录 2026-09-26；OpenTelemetry GenAI Agent 语义按核对时的 Development 状态记录，本章没有声称 Schema conformance 或平台优劣。

## 代码审查结论

### Strengths

- 合同、Trace 生成、结构验证、指标、隐私、采样、诊断与报告分层清晰，标准库运行时不依赖平台 SDK。
- 规范报告使用 Draft 2020-12 Schema；非法 release/conclusion、嵌套未知字段、负时长和缺失完整率都有反例。
- 报告生成使用 staging 与防覆盖策略，`--replace` 先保留 `.previous`，避免直接破坏旧证据。
- 64 项原有检查之外，审稿新增 2 项边界测试，当前 Chapter 14 共 66 项测试。

### Issues

#### Critical

无。

#### Important

审稿发现的两项 P1 已在上表修复；无剩余项。

#### Minor

- 本地 `assess_incident_submission` 是读者练习门禁，不是完整 Incident Management Schema。真实系统还应验证时间窗口、责任人、查询快照和审批状态。
- 当前 Tail 采样为进程内教学实现，不评估 Collector 在高并发下的缓冲内存、背压和丢失行为。

### Declined to judge

- 真实 OpenAI、Anthropic 或其他模型的能力与延迟：规范运行没有调用 Provider。
- OpenTelemetry、Langfuse、OpenAI Agents SDK 的吞吐、价格和兼容性：本章只做概念映射。
- 组织级隐私、数据驻留和监管合规：需要具体法域、数据分类与部署信息。
- 千万级生产流量下的采样容量：本章只有 72 条确定性 Trace。

### Assessment

**Ready to merge? Yes, as a local rc1 candidate.**

实现与书稿已经对齐批准计划，P1 偏差有回归测试，证据边界明确。这里的“Ready”只表示适合冻结在当前本地候选分支，不授权合并、推送、建 PR、加入公开导航或部署。

## 验证证据

| 验证 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -B -m pytest chapter14/tests -q` | 66 项通过 |
| 双目录完整实验 | 8 个稳定产物逐字节一致，且与 canonical reports 哈希一致 |
| 双目录练习结果 | 14 道答案逐字节一致 |
| JSON Schema Draft 2020-12 | 规范报告通过；语义反例被拒绝 |
| 桌面预览 | 1440×1000，7/7 图片、6/6 表格、0 失效锚点，无整页横向溢出 |
| 移动预览 | 390×844，7/7 图片可局部横向滚动，6/6 表格受容器约束，无整页横向溢出 |
| `.venv\Scripts\python.exe -B -m unittest discover -s tests -q` | 43 项通过 |
| 仓库检查 | `scripts.check_repository` 通过 |
| 站点构建 | `scripts.build_site` 输出 177 个 source；`mkdocs build --strict` 通过 |
| 公开边界 | `_web/book/chapter14.md`、`site/book/chapter14/index.html` 均不存在；导航与公开 manifest 不含 Chapter 14 |
| 历史保护 | Chapter 13 rc2 相关路径相对 `be655ca` 无差异 |

## 已知限制

- 72 条 Trace、24 个场景与三次发布都是确定性教学夹具，不代表生产流量、模型随机性或供应商能力。
- 费率卡只产生教学 `cost_units`，不能折算成美元或真实账单。
- 反事实消融由固定夹具构造，证明的是诊断流程能区分预置候选，不是真实世界因果发现能力。
- 本地脱敏器和 Export Gate 不替代密钥扫描、访问控制、数据删除、加密、审计与法律合规。
- Playwright 验证的是当前本地浏览器与两个视口，不覆盖所有字体、浏览器、辅助技术和印刷输出。
- 双视角审稿由同一执行主体分轮完成，缺少独立审稿人的上下文隔离。

## 最终判断

本章达到了“通俗解释 + 可手算例子 + 可运行证据 + 明确限制”的候选标准。Benchmark 不再被写成孤立排行，Tracing 不再被简化为日志 UI，生产诊断也没有从相关性直接跳到根因。修复后的隐私顺序与依赖时间合同使代码真正执行正文承诺。可以冻结为本地 `v1.0-rc1`，但仍未发布。

