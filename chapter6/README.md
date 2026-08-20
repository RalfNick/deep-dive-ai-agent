# Chapter 6 deterministic context-continuity lab

本目录是《深入浅出 AI Agent》第 6 章的离线证据包。它用一条固定的 30 事件价格修复轨迹，分别检查执行连续性与语义连续性。默认实验不联网、不读取 API Key、不使用随机模型输出；所有 case 都是 `sample_count=1` 的合同验证，不是模型或产品 Benchmark。

## 环境与入口

- Python 3.11 或更高版本；
- 离线实验只使用标准库，并复用仓库内 Chapter 5 `ContextPacket` 合同；
- 命令必须从仓库根目录运行；
- `serialized_bytes` 是 canonical JSON 的 UTF-8 字节数，不是 Provider Token。

先运行回归测试：

```powershell
python -m unittest discover -s chapter4/tests -v
python -m unittest discover -s chapter5/tests -v
python -m unittest discover -s chapter6/tests -v
```

生成固定报告：

```powershell
python -m chapter6.experiments.run_all --output chapter6/reports
```

按组观察生成后的机器报告：

```powershell
$report = Get-Content -Raw chapter6/reports/context-continuity.json | ConvertFrom-Json
$report.cases | Group-Object experiment | Select-Object Name,Count
$report.cases | Where-Object experiment -eq 'checkpoint_vs_rehydration' | Format-Table variant,decision_kind,serialized_bytes_after
```

## 报告合同

`reports/context-continuity.json` 是机器可读主报告，包含每个变体的独立指标、支持结论与不支持结论。`reports/context-continuity.md` 是同一数据的人读表格。`reports/context-continuity-trace.jsonl` 保存选择、丢弃、重建和拒绝事件；每行是一个 canonical JSON 对象。JSON 的未测字段为 `null`，Markdown 中显示为 `—`，不得改写成 0。

固定生成应当字节稳定。可用测试验证：

```powershell
python -m unittest chapter6.tests.test_report_reproducibility -v
```

报告中的保留率只对 Fixture 声明的字段集合计算。布尔观察、计数、字节数和比率保持分列，不提供聚合总分。

## 代码地图

| 路径 | 责任 |
| --- | --- |
| `fixtures/price_repair.py` | 30 事件轨迹、Seed 与预期不变量 |
| `context_continuity/contracts.py` | Event、CarryItem、Artifact、Checkpoint 与 Working Set |
| `context_continuity/event_log.py` | 追加式 JSONL 事件与 Digest 验证 |
| `context_continuity/stores.py` | Artifact/Checkpoint Store 与有序提交边界 |
| `context_continuity/compaction.py` | append-all、窗口、自由文本规则与结构化压缩 |
| `context_continuity/rehydrator.py` | 验证后复用 Chapter 5 Builder 构造 Packet |
| `context_continuity/policy.py` | 只用于探测可见语义状态的确定性决策规则 |
| `context_continuity/graders.py` | 字段保留、恢复、重复工作、误报和 Trace 指标 |
| `experiments/` | 五组实验、失败矩阵、固定报告与可选 live probe |
| `publication_checks.py` | 标题、图、练习、来源、Secret、单位与排名静态门禁 |
| `reference-answers.md` | 14 道练习的推理、错误与验收规则 |

## 五组实验与失败注入

五组实验依次检查：完整追加的增长、滑动窗口的静默失忆、自由文本规则与结构化 Artifact、Checkpoint-only 与 Rehydration、summary-of-summary 与从 Event Log 再生。所有组共享 Fixture、事件顺序、固定策略和工具结果。

失败矩阵包括：

1. 删除事件 2 的公共签名约束；
2. 摘要遗漏仍未解决的失败并注入完成声明；
3. live Workspace Digest 与 Artifact/Checkpoint 不一致；
4. Artifact Schema 不受支持；
5. Artifact 来源 Digest 被破坏。

前两项允许构造受控的语义失败，用于观察危险决策或误报完成；后三项必须在 Chapter 5 Builder 之前拒绝，不能返回半份 Packet。

## 证据支持范围

本实验支持：固定规则下声明字段是否保留；是否产生真实 Chapter 5 Packet/Trace；声明恢复点是否正确；是否重复已否定尝试；边界损坏是否安全失败；规范化 UTF-8 字节数；固定报告能否重复生成。

本实验不支持：真实模型平均成功率或摘要准确率；Claude Code、Codex、LangGraph 排名；生产最优压缩阈值；厂商内部摘要格式；业务副作用 exactly-once；分布式事务、完整沙箱或合规认证；任意工作负载的普遍结论。

## 可选 DeepSeek live probe

Live probe 与离线基线完全分离。它只在显式提供环境变量时运行，结果必须写入 `chapter6/live-reports/` 或其他未被固定报告消费的位置：

```powershell
$env:DEEPSEEK_API_KEY = '<your-key>'
python -m chapter6.experiments.live_probe --repeats 5 --output chapter6/live-reports/deepseek-compaction.json
```

未提供凭据时命令返回状态码 2，不生成伪造成功结果。Live 报告分别记录 requested model、returned model、有效尝试与 Provider failure；不得把 429、超时或非法响应计入行为分母。适配器不会把凭据、认证头或原始 Secret 写入报告。Live 观察不更新 `reports/context-continuity.*`，也不改变本章确定性结论。

## 已知限制

- Fixture 只有一个仓库任务，所有变体 `sample_count=1`；
- 自由文本摘要由确定性规则模拟，不代表真实摘要模型分布；
- `commit_boundary()` 演示 Artifact 先于 Checkpoint 的本地顺序，不是分布式事务协调器；
- Rehydrator 校验来源、Schema、游标和 Workspace；真实 Locator 内容解析仍需要产品 Resolver；
- `serialized_bytes` 只能支持本地体积比较，不能替代目标模型 Tokenizer 或账单；
- Secret 扫描是出版门禁，不是完整的数据防泄漏系统；
- 官方产品事实会变化，出版前须按 `book/sources/chapter6-sources.md` 重新核对。

## 出版门禁

```powershell
python -m unittest chapter6.tests.test_publication_checks -v
python -m unittest discover -s chapter6/tests -v
```

完整出版检查还会把 `book/chapter6.md`、本答案、来源台账和七张 SVG 一并传给 `validate_chapter_contract()`；远程链接可达性、真实产品内部实现和 PDF 视觉质量不属于该静态函数的判断范围。

真实成稿门禁显式传入 `enforce_manuscript_length=True`，使用 `publication_cjk_characters()` 统计反引号和波浪号代码围栏之外的 CJK 统一表意字符；Markdown 标记、空白、URL、拉丁标识和代码都不能增加计数。目标范围为 25,000—30,000。

## 返回正文

- [第 6 章正文](../book/chapter6.md)
- [第 6 章参考答案](./reference-answers.md)
