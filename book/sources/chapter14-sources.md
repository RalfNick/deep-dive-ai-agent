# 第 14 章来源台账

本文件记录《深入浅出 AI Agent》第 14 章外部资料、核对日期与使用边界。正文中的实验数字均来自仓库内 `chapter14/reports/diagnostic-report.json`，不由外部网页提供。

统一核对日期：**2026-09-26**。

## 本地实验与图表

### local-diagnostics

- 来源：`chapter14/reports/diagnostic-report.json`
- Schema：`chapter14.diagnostics.v1`
- 固定夹具：`chapter14.trace-fixture.v1`
- 覆盖内容：3 个发布、每个 24 条 Trace、4 个切片，共 72 条 Trace；Benchmark 审计、延迟与关键路径、成本单位、重试放大、采样、消融、Incident Report 与回归任务。
- 可复现命令：`python -B -m chapter14.experiments --group all --output <new-directory>`
- 证据限制：确定性教学夹具，不代表真实模型能力；成本单位不是供应商价格；Tail 样本不是总体分母；不构成平台兼容性认证。
- 稳定产物哈希：见 `chapter14/reports/manifest.json`。规范 `diagnostic-report.json` 的 SHA-256 为 `49f651364419533460abf924509567c0ed04a127a91743fa968acb51c5d9fc75`。

### local-diagrams

- 来源：`infographic/chapter14/generate_diagrams.py`
- 设计源文件：`infographic/chapter14/*.tldr`
- 发布图：`book/images/chapter14/*.svg`
- 使用方式：正文 7 幅图均由同一场景模型导出；SVG 自包含，技术文字由代码排版，不依赖生成式图片中的文字。

## SWE-bench

### swe-bench

- 标题：SWE-bench 官方站点
- URL：https://www.swebench.com/
- 核对日期：2026-09-26
- 正文使用：Original 2,294 个问题、12 个 Python 仓库；Verified 500；Lite 300；Multilingual 300、42 个仓库、9 种语言；Multimodal 480。
- 稳定性：数据集规模相对稳定；实时排行榜分数高度易变，因此正文不抄录当前名次与分数。

- 标题：SWE-bench: Can Language Models Resolve Real-World GitHub Issues?
- URL：https://arxiv.org/abs/2310.06770
- 核对日期：2026-09-26
- 正文使用：SWE-bench 把真实 GitHub issue 与仓库快照组织成软件工程任务；论文报告原始集合规模。

### swe-bench-verified

- 标题：SWE-bench Verified
- URL：https://www.swebench.com/verified.html
- 核对日期：2026-09-26
- 正文使用：Verified 包含 500 个经人工核验样本；官方对不同 Harness/发布版本的比较限制说明，特别是工具调用与解析式动作、默认运行环境等差异。
- 边界：页面会随 Benchmark 演进；正文只引用核对时明确的比较原则，不引用实时排名。

- 标题：Introducing SWE-bench Verified
- URL：https://openai.com/index/introducing-swe-bench-verified/
- 页面更新时间：2025-02-24（页面标注）
- 核对日期：2026-09-26
- 正文使用：人工核验任务、测试合同以及公开 Benchmark 可能存在污染的限制。
- 边界：文章中历史模型成绩不用于正文，以避免把过期成绩写成当前比较。

### benchmark-contamination

- 标题：Time Travel in LLMs: Tracing Data Contamination in Large Language Models
- URL：https://arxiv.org/abs/2310.18018
- 核对日期：2026-09-26
- 正文使用：公共评测存在训练数据污染风险，时间与来源应进入评测解释。

- 标题：Investigating Data Contamination in Modern Benchmarks for Large Language Models
- URL：https://aclanthology.org/2024.naacl-long.482/
- 核对日期：2026-09-26
- 正文使用：污染检测本身存在方法限制，因此正文将 `contamination_risk` 设计为可为 `unknown` 的审计字段，而非二元断言。

## OpenTelemetry

### opentelemetry

- 标题：OpenTelemetry — Traces
- URL：https://opentelemetry.io/docs/concepts/signals/traces/
- 核对日期：2026-09-26
- 正文使用：Trace、Span、Event、Attribute、Status、Span Link 的概念；Link 可表达跨 Trace 或非严格父子关系的因果关联。
- 边界：本章 `TraceRecord`/`SpanRecord` 是教学领域模型，不宣称符合 OpenTelemetry wire format 或全部语义约定。

- 标题：OpenTelemetry — Sampling
- URL：https://opentelemetry.io/docs/concepts/sampling/
- 页面最后修改日期：2025-10-16（核对时页面标注）
- 核对日期：2026-09-26
- 正文使用：Head Sampling 在 Trace 早期决策，不能看到完整 Trace；Tail Sampling 能依据完成后的 Span/错误/延迟决策，但需要暂存状态并消耗更多资源。
- 边界：具体 Collector 组件、配置字段和性能随版本变化，正文不复制配置清单。

### otel-genai

- 标题：OpenTelemetry Semantic Conventions for Generative AI — Agent Spans
- URL：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md
- 核对日期：2026-09-26
- 核对状态：页面标注 `Development`。
- 正文使用：说明 GenAI/Agent Span 语义仍在演进；本章因此只做概念映射，不做兼容性认证。

## Langfuse

### langfuse

- 标题：Langfuse Observability Data Model
- URL：https://langfuse.com/docs/observability/data-model
- 核对日期：2026-09-26
- 正文使用：Observation 可嵌套构成 Trace；Session 可聚合多条 Trace；短生命周期进程需要正确 flush。

- 标题：Langfuse Observability Best Practices
- URL：https://langfuse.com/docs/observability/best-practices
- 核对日期：2026-09-26
- 正文使用：稳定的 Trace 结构与命名影响过滤、看板、Evaluator 和 Experiment 的长期可用性。

- 标题：Langfuse Masking
- URL：https://langfuse.com/docs/observability/features/masking
- 核对日期：2026-09-26
- 正文使用：掩码处理导出副本；存在多个 Exporter 时需分别处理；数据不得离开信任边界时应优先在应用侧脱敏。
- 易变说明：核对时 Python 方案推荐 `mask_otel_spans`；这是产品 API 细节，正文只保留“不应假设一个 Exporter 的掩码覆盖其他 Exporter”这一稳定原则。

### langfuse-evaluation

- 标题：Langfuse Evaluation Overview
- URL：https://langfuse.com/docs/evaluation/overview
- 核对日期：2026-09-26
- 正文使用：在线评估面向实时 Trace，离线评估面向预定义数据集与 Experiment。

- 标题：Langfuse Scores Data Model
- URL：https://langfuse.com/docs/evaluation/scores/data-model
- 核对日期：2026-09-26
- 正文使用：Score 可关联 Trace、Observation、Session 或 Dataset Run。
- 边界：字段与产品界面可能变化，正文不写请求参数或套餐能力。

## OpenAI Agents SDK

### openai-agents-sdk

- 标题：OpenAI Agents SDK — Tracing
- URL：https://openai.github.io/openai-agents-python/tracing/
- 核对日期：2026-09-26
- 正文使用：SDK 可跟踪 Agent 运行、生成、函数/工具调用、Handoff、Guardrail 和自定义 Span；支持自定义 Processor 与导出路径。
- 安全边界：敏感数据配置与自定义 Processor 不替代应用自己的数据分类、脱敏和失败关闭策略；关闭 tracing 也不能被当成清理既有缓冲数据的证明。

- 标题：OpenAI Agents SDK — Configuration
- URL：https://openai.github.io/openai-agents-python/config/
- 核对日期：2026-09-26
- 正文使用：日志与 Trace 的敏感数据选项需要显式治理。
- 易变说明：SDK 配置名与默认行为可能变化，集成前必须重新核对当前版本。

## 分布式追踪与 SRE

### dapper

- 标题：Dapper, a Large-Scale Distributed Systems Tracing Infrastructure
- URL：https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/
- 核对日期：2026-09-26
- 正文使用：大规模追踪需要低开销、对应用尽量透明、广泛部署与采样机制。
- 边界：Dapper 是经典基础设施论文，不代表今天某个观测产品的实现。

### google-sre

- 标题：Google SRE Book — Service Level Objectives
- URL：https://sre.google/sre-book/service-level-objectives/
- 核对日期：2026-09-26
- 正文使用：平均值会隐藏长尾；分位数更适合表达典型与尾部请求体验。

- 标题：Google SRE Book — Effective Troubleshooting
- URL：https://sre.google/sre-book/effective-troubleshooting/
- 核对日期：2026-09-26
- 正文使用：系统化排障需要问题报告、诊断、测试与负面结果记录，而不是凭直觉连续修改多个变量。

## 使用与更新规则

1. 正文中的产品能力只在上述核对日期成立；发布前若更改产品映射，应重新访问官方文档并更新日期。
2. 不从二手博客推导产品 API、价格、默认值或合规承诺。
3. 不把公共 Benchmark 的实时榜单分数固化进稳定书稿；需要示例时使用带日期截图或本地教学夹具。
4. 不把论文中的污染风险研究转写为对某个具体模型已经污染的断言。
5. 所有本地数值都必须能从 `chapter14/reports/diagnostic-report.json` 的稳定字段回溯；若报告变更，先更新 Schema 和测试，再更新正文。

