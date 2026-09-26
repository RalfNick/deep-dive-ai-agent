# 第 14 章 v1.0-rc2 本地候选记录

记录日期：2026-09-26。分支：`codex/chapter14-benchmark-tracing`。精修基线：Chapter 14 rc1 提交 `023b714f26a6237e027d789052b022bdf0f56041`。状态：**本地候选，未推送、未发布**。

本版本保留 rc1 的完整章节结构和确定性实验，只修复审稿发现的三个边界：已观测工作关键路径与端到端等待的区别、`confirmed` 事故报告的反证硬门禁，以及 Head/Tail Sampling 的准确时序。rc1 的正文、审稿和版本记录继续保留，不被覆盖。

## 本轮变化

- 正文由 23,877 增至 24,688 个字符，仍为 16 个二级标题、19 个三级标题、5 组实验、6 张比较表、14 道练习和 7 幅原创图。
- `critical_path` 新增 `critical_path_unattributed_elapsed_ms`；教学样本同时展示端到端 331 ms、已观测工作关键路径 296 ms 和 35 ms 未归因时间。
- `IncidentReport` 构造器与 JSON Schema 同时拒绝缺少支持证据或反证的 `confirmed`，同时允许 `inconclusive` 显式保留证据缺口。
- `head_sample` 只接收 `trace_id`；Tail、缓冲和导出只接收已脱敏并通过安全门禁的完整 Trace。
- 图 14-6 重画为 Head 标识路径与完整载荷路径；其 SVG 与可编辑 TLDraw 源文件同步更新。
- group-3、group-4 和 manifest 重新生成；核心发布指标、事故根因、练习答案与主报告保持不变。

## 规范结果

- 三次发布各 24 条 Trace、23 次成功；Outcome 均值仍为 `0.958333`，Telemetry Completeness 仍为 `0.958333`。
- `stable` p95 仍为 432 ms，`incident` 为 612 ms，`fixed` 恢复到 432 ms；退化仍只出现在 recovery 切片。
- 72 条 Trace 中仍保留 49 条诊断明细；总体请求数和最终失败数仍来自采样前计数器。
- 事故报告仍以 `retry_policy` 为规范夹具中唯一同时移除三类症状的消融，并保留三条支持 Trace、四条反证 Trace 与现实因果未证明等 Unknown。
- 新增字段只解释观测缺口；它没有改变关键路径 p50/p95，也不把未归因时间命名为队列时间。

## 本轮验证

| 验证 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -B -m pytest chapter14/tests -q` | 69 项通过 |
| 两次完整诊断实验 | 8 个稳定产物逐字节一致 |
| 两次练习输出 | 14 道答案逐字节一致 |
| JSON Schema Draft 2020-12 | 规范报告通过；无支持证据/无反证的 `confirmed` 均被拒绝 |
| 图形生成 | 7 组 SVG/TLDraw 通过自包含、标题、标签和箭头绑定测试 |
| `.venv\Scripts\python.exe -B -m unittest discover -s tests -q` | 43 项通过 |
| 仓库与站点 | `scripts.check_repository`、`scripts.build_site`、`mkdocs build --strict` 通过 |
| 公开清单 | `_web/book/chapter14.md` 与 `site/book/chapter14/index.html` 不存在；`mkdocs.yml` 与 `book/manifest.json` 不含 Chapter 14 |
| 历史保护 | Chapter 13 rc2 路径相对基线 `be655ca` 无差异；Chapter 14 rc1 记录保留 |

## 规范产物哈希

| 产物 | SHA-256 |
| --- | --- |
| `book/chapter14.md` | `70f4ecddc5ad9339704d335ca74c02f42e0a4638b796b1db54dae5d4e53c14ab` |
| `book/sources/chapter14-sources.md` | `2d1a4a94addafe0bbaec31913349c8de95f935c7a7c79e94afc0796c5e448872` |
| `book/reviews/chapter14-review-codex-v1.0-rc2.md` | `49f0e9675d08803b7ea2343f9d2f3994fe79b78ab1da2c841603074ee866d99f` |
| `chapter14/reports/diagnostic-report.json` | `49f651364419533460abf924509567c0ed04a127a91743fa968acb51c5d9fc75` |
| `chapter14/reports/diagnostic-report.md` | `2c382ee6b0323c36c679039d9a9357b86ad9eefb33b62802ce48922c04576411` |
| `chapter14/reports/manifest.json` | `4e9bb8fccdad9af13cbf6d83755a834b814da9274625ab435536d032fbc41986` |
| `chapter14/reports/exercise-results.json` | `2591f05303e73f18297ad3f66ba5cd333d4c850acc0a258e2841967a5f9847ed` |
| `chapter14/schemas/production-diagnostics-v1.schema.json` | `0ea6d94410181df249df04c43cc6000955ec854f265575af709916092b7808da` |

集合哈希按相对路径排序，将每个文件的 `relative_path␠␠sha256` 以 LF 连接后再次计算 SHA-256。`chapter14/` 集合排除本地 `.verification/`、`.runs/`、`preview-pages/`、缓存和 `.pyc`。

| 集合 | 文件数 | SHA-256 |
| --- | ---: | --- |
| `chapter14/` 稳定实验包 | 43 | `a7700cb2a3b363a4a471309d13f7f6d93563c48d9638d962b38ab2c7c43af814` |
| `book/images/chapter14/` | 7 | `bc68b9ae3727c9f396d9cbb07c2944faa084f1d7784b974953c60efae07ef698` |
| `infographic/chapter14/` | 10 | `f065e5cbb12d3935990a9fc0b13c098cea6dfeb7e1b7a2d8a1cd7aa60f5ca7b1` |

## 已证明与未证明

本候选证明：本地实现能够区分端点耗时、工作总量、已观测工作关键路径和未归因时间；能够在领域对象与 JSON Schema 两层拒绝证据不足的 `confirmed`；能够仅用 Trace ID 执行 Head 决策，并让完整载荷在 Tail、缓冲与导出前经过脱敏和安全验证。

本候选没有证明：未归因时间具体属于排队、调度、网络还是缺失插桩；要求至少一条反证适合所有组织的事故管理流程；本地采样器具有生产 Collector 的容量与背压能力；任何真实模型或观测平台的能力高低；72 条教学 Trace 可以代表生产分布。

## 历史与发布边界

- rc1 保存在提交 `023b714f26a6237e027d789052b022bdf0f56041`，原审稿与版本记录保持不变。
- rc2 审稿记录位于 `book/reviews/chapter14-review-codex-v1.0-rc2.md`。
- 本轮不修改 `mkdocs.yml`、`book/SUMMARY.md`、`book/manifest.json`、站点 allowlist 或部署配置。
- 本轮不推送 GitHub，不创建 PR，不部署网站，不创建发布 tag，也不生成 PDF/EPUB。
