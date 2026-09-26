# 第 14 章实验包：Benchmark、Tracing 与生产诊断

这是《深入浅出 AI Agent》第 14 章的自包含配套工程。它用两组 Benchmark Card 和 72 条确定性 Trace，展示怎样审计分数可比性，计算延迟、关键路径、用量与重试指标，在脱敏后执行 Head/Tail 采样，并通过切片、反证与消融把一次生产退化固化成回归任务。

本实验包验证的是 **Production Diagnostics Harness 的机制**，不是模型或观测平台能力。所有 Trace 都是固定教学夹具；`cost_units` 来自本地费率卡，不是美元或任何供应商价格。

## 环境与依赖

运行时代码只使用 Python 标准库。测试固定使用 Python 3.11、pytest 与 `jsonschema`。

```powershell
# 在仓库根目录执行
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes `
  -r chapter14/requirements-dev.txt
.\.venv\Scripts\Activate.ps1
```

规范实验不会读取 API Key，也不会联网。不要把生产 Trace、密钥、真实 Prompt 或未脱敏工具参数复制到本目录。

## 最短运行路径

```powershell
python -B -m pytest chapter14/tests -q
python -B -m chapter14.experiments --group all --output chapter14/.runs/reader-first
python -B -m chapter14.exercise_solutions --all
python -B -m chapter14.preview
```

输出目录已存在时，命令默认拒绝覆盖。确实需要替换时显式添加 `--replace`；旧目录会重命名为相邻的 `.previous-N`，不会被删除。

## 五组实验

| 组 | 核心问题 | 主要证据 |
| --- | --- | --- |
| 14-1 | 两个 Benchmark 分数能否直接比较 | Benchmark Card、合同差异与三态结论 |
| 14-2 | 乱序日志能否还原因果结构 | Trace/Span ID、父子树、依赖图与结构校验 |
| 14-3 | 成功率不变时怎样发现资源退化 | p50/p95、关键路径、用量覆盖、成本单位与重试放大 |
| 14-4 | 怎样在容量、事故证据和隐私之间取舍 | 应用侧脱敏、Head/Tail/Combined Sampling、分母分离 |
| 14-5 | 怎样从症状走到可回归根因 | 切片、支持证据、反证、五组消融与三条回归任务 |

可以单独运行一组：

```powershell
python -B -m chapter14.experiments --group 3 --output chapter14/.runs/group-3
```

## 固定数据集

- `fixtures/benchmark-cards.json`：一组真正对齐的控制比较，以及一组“同分但 Harness/预算/重试不同”的误导比较。
- `fixtures/scenarios.json`：24 个场景，平均分成 `simple`、`retrieval`、`write`、`recovery` 四个切片。
- `fixtures/rate-card.json`：版本化教学成本单位。
- `trace_builder.py`：为 `stable`、`incident`、`fixed` 三次发布各生成 24 条 Trace。

每次发布都是 23/24 成功。`incident` 只在 recovery 路径引入额外重试工作；`fixed` 恢复稳定合同。这个安排用于验证诊断管线能否在 Outcome 不变时发现延迟、成本与重试退化。

## 报告合同

规范报告位于 `reports/`：

- `diagnostic-report.json`：完整机器合同，Schema 为 `chapter14.diagnostics.v1`；
- `diagnostic-report.md`：人类可读摘要；
- `group-1.json` 至 `group-5.json`：五组实验的局部证据；
- `manifest.json`：产物字节数与 SHA-256。

完整 JSON 由 `schemas/production-diagnostics-v1.schema.json` 使用 Draft 2020-12 验证。字段含义变化时必须发布新 Schema 版本，不能在 v1 下静默改义。

## 关键口径

- 分位数：`nearest-rank.v1`。
- 关键路径：`work-dag-longest-path.v1`；它是已观测工作 DAG 的最长路径，不包含排队、调度和未插桩空档，也不等同于完整端到端延迟。
- 未归因时间：`endpoint_duration_ms - critical_path_duration_ms`；它提示观测缺口，不自动等于队列时间。
- 重试放大：`billable-attempts-per-declared-operation.v1`。
- 成本：`chapter14.cost-units.v1`，不是 Provider Price。
- Trace Coverage：被保留明细的请求比例。
- Telemetry Completeness：关键遥测完整的请求比例。
- 总体失败率：来自采样前 Population Counter，不从 Tail 样本估计。

## 代码阅读顺序

1. `contracts.py`：稳定数据合同。
2. `benchmark.py`：Benchmark Card 加载与可比性审计。
3. `trace_builder.py`、`trace_validation.py`：确定性 Trace 与两类图验证。
4. `metrics.py`：分位数、关键路径、用量与发布比较。
5. `privacy.py`、`sampling.py`：Head 只取 Trace ID，完整载荷先脱敏，再做 Tail 判定、缓冲或导出。
6. `diagnosis.py`：切片、消融、事故结论与回归任务。
7. `experiments.py`：五组实验、Schema 校验、报告与防覆盖。

## 平台映射

[integrations.md](integrations.md) 把本章领域模型映射到 OpenTelemetry、Langfuse 与 OpenAI Agents SDK。它只用于理解责任边界，不是兼容性声明；产品 API 与语义状态以核对日期后的官方文档为准。

## 练习与本地预览

[reference-answers.md](reference-answers.md) 给出 14 道题的参考解释。机器可检查答案由 `exercise_solutions.py` 生成：

```powershell
python -B -m chapter14.exercise_solutions `
  --all `
  --output chapter14/.runs/exercise-results.json
```

生成本地候选预览后，可用可选的 Playwright 依赖执行桌面端与移动端检查：

```powershell
python -B -m chapter14.preview
node book/check_chapter14_preview.mjs
```

`preview-pages/`、截图和 `.runs/` 都是本地临时产物，不进入规范报告或公开站点。

## 证据边界

- 72 条 Trace 是教学夹具，不代表生产流量和真实随机性。
- 固定消融展示诊断方法，不证明真实世界因果。
- `cost_units` 不能换算成美元或厂商账单。
- Tail 保留计数不能作为总体错误率、延迟或场景占比。
- 本地脱敏器是教学实现，不能替代组织的数据分类、密钥扫描、访问控制和合规评审。
- 本地合同不声明符合任何观测平台的全部 Schema 或传输协议。
