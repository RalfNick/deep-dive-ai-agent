# 第 14 章平台映射说明

核对日期：**2026-09-26**。

本文件说明如何把 `chapter14/` 的教学合同映射到 OpenTelemetry、Langfuse 与 OpenAI Agents SDK tracing。映射用于迁移概念，不构成兼容性认证，也不保证字段一一对应。

## 共同数据流

```text
Agent/Harness
  → 应用侧数据分类与脱敏
  → Trace/Span instrumentation
  → Processor / Collector / Exporter
  → Trace store 与总体 Metrics
  → Eval / Feedback 关联
  → 诊断、消融、回归任务
```

不论选择哪个后端，都建议在应用领域中保留稳定的 `release_id`、`environment`、`session_id`、`trace_id`、`scenario_slice`、`status`、错误码和 instrumentation/schema 版本。

## OpenTelemetry

概念映射：

- `TraceRecord.trace_id` → Trace ID；
- `SpanRecord.span_id` / `parent_span_id` → Span ID / Parent Span ID；
- `SpanRecord.depends_on` → 不能简单等同 Parent；可按场景使用 Span Link 或领域属性表达非树状依赖；
- `kind`、`status`、`duration_ms` → Span kind/status/timing 与稳定属性；
- Head/Tail Sampling → SDK/Collector 采样层；
- release 与环境 → Resource 或稳定 Attributes。

注意事项：

1. 本章显式保存工作依赖 DAG，用于教学关键路径；OpenTelemetry 的 Parent/Link 语义不保证与该 DAG 一一对应。
2. GenAI Agent Span 语义在核对时仍为 Development，接入前应重新确认属性名与稳定性。
3. Tail Sampling 通常需要在能看到足够完整 Trace 的位置决策，并承担缓冲、内存和延迟成本。
4. 敏感数据治理不能只依赖后端 UI；应用、SDK/Collector 与其他 Exporter 都要检查。

官方资料：

- https://opentelemetry.io/docs/concepts/signals/traces/
- https://opentelemetry.io/docs/concepts/sampling/
- https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md

## Langfuse

概念映射：

- `Session` → Langfuse Session；
- `TraceRecord` → Trace；
- `SpanRecord` → 嵌套 Observation；模型、工具等可选择更具体的 Observation 类型；
- Eval 结果/用户反馈 → Score，并关联 Trace、Observation、Session 或 Dataset Run；
- release、slice、environment → 适合筛选的稳定 metadata/tags（具体字段以当前 SDK 为准）；
- Incident slicing → Trace 查询、看板和 Dataset/Experiment 联动。

注意事项：

1. 保持 Trace 结构与命名稳定，否则跨版本 Dashboard 和 Evaluator 会失去共同口径。
2. 短生命周期进程应按当前 SDK 文档正确 flush；“应用退出”不等于遥测已送达。
3. 核对时 Python 集成推荐用 `mask_otel_spans` 处理导出副本；若同时存在其他 Exporter，要独立脱敏。
4. 若数据禁止离开信任边界，应在应用侧删除或转换，而不是先上传再依赖平台显示遮罩。

官方资料：

- https://langfuse.com/docs/observability/data-model
- https://langfuse.com/docs/observability/best-practices
- https://langfuse.com/docs/observability/features/masking
- https://langfuse.com/docs/evaluation/overview
- https://langfuse.com/docs/evaluation/scores/data-model

## OpenAI Agents SDK tracing

概念映射：

- Agent run → Trace；
- generation、function/tool、handoff、guardrail → SDK 内置 Span 类别；
- 本章自定义 approval、verifier、retry 或 incident marker → custom Span/Processor；
- Trace Processor → 自定义导出、过滤和路由边界；
- 敏感输入输出 → SDK 当前敏感数据配置加应用侧策略。

注意事项：

1. 自动插桩减少接入成本，不代表自动满足本书的字段、留存、采样和合规合同。
2. 若要实现自定义失败关闭导出，必须检查当前 Trace Provider/Processor 组合，避免默认 Processor 同时发送未脱敏数据。
3. 禁用新 Trace 不应被理解为清理已经缓冲或已导出的数据。
4. Agents SDK Trace 不能替代基础设施 Metrics、数据库/队列可观测性和业务 Outcome Eval。

官方资料：

- https://openai.github.io/openai-agents-python/tracing/
- https://openai.github.io/openai-agents-python/config/

## 推荐选择

- 需要跨服务、跨语言传播和厂商中立骨架：优先从 OpenTelemetry 开始。
- 需要快速把 LLM Trace、Prompt、Dataset、Score 和人工审阅组织起来：评估 Langfuse 等 LLM Observability 平台。
- 已使用 OpenAI Agents SDK，想先获得 Agent/工具/Handoff 的自动 Trace：使用 SDK 内置 tracing，再补齐应用侧脱敏、基础设施信号与 Eval。
- 大多数生产系统会组合使用：SDK instrumentation → OpenTelemetry/Processor → 一个或多个受控后端。

选择的关键不是功能清单最长，而是能否回答本团队的事故问题，并满足数据驻留、隐私、成本、留存、访问控制和可迁移性要求。

