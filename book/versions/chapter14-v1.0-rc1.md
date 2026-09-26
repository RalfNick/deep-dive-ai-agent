# 第 14 章 v1.0-rc1 本地候选记录

记录日期：2026-09-26。分支：`codex/chapter14-benchmark-tracing`。基线：Chapter 13 rc2 提交 `be655ca04f6449808bdbab64e5b3ee00c10a4c08`。状态：**本地候选，未推送、未发布**。

本版本首次形成第 14 章完整候选：正文、72-Trace 生产诊断实验、Benchmark Card、版本化 JSON Schema、五组报告、14 道练习与答案、7 幅原创矢量图、来源台账、平台映射、双视角审稿和两宽度本地预览。本轮保留 Chapter 13 rc2，不把 Chapter 14 加入公开站点、导航或 manifest。

## 候选内容

- 正文 23,877 个字符，16 个二级标题与 19 个三级标题；5 组实验、6 张比较表、14 道练习和 7 幅原创图。
- 24 个教学场景，分为 `simple`、`retrieval`、`write`、`recovery` 四个切片；`stable`、`incident`、`fixed` 各运行一次同场景集合，共 72 条确定性 Trace。
- Benchmark Card 显式记录任务、被测系统、资源、指标与来源合同，输出 `comparable / partially_comparable / not_comparable`。
- Trace 同时保存 Parent Tree 与工作依赖 DAG；分位数为 `nearest-rank.v1`，关键路径为 `work-dag-longest-path.v1`。
- 隐私路径先转换与验证，再进入 Combined/Tail Sampling；总体 Metrics 与诊断保留集合使用不同分母。
- Incident Report 包含支持证据、反证、完整率、Unknown、五组消融、结论和三条回归任务。
- 稳定报告 Schema 为 `chapter14.diagnostics.v1`；练习结果 Schema 为 `chapter14.exercises.v1`。

## 环境与规范结果

- Python 3.11.15；pytest 9.0.2；jsonschema 4.26.0；预览 Markdown 3.10.2；Node.js 24.15.0；Playwright 1.62.1。
- 规范运行离线、不读取 API Key、不调用真实模型或观测平台。
- 三次发布各 24 条 Trace、23 次成功；Outcome 均值均为 `0.958333`，Telemetry Completeness 均为 `0.958333`。
- `stable`：p95 432 ms、关键路径 p95 392 ms、成本单位 16.03、重试放大 1.3125。
- `incident`：p95 612 ms、关键路径 p95 562 ms、成本单位 17.74、重试放大 1.4375。
- `fixed` 恢复到 `stable` 对应值；退化仅出现在 recovery 切片，其 p95 从 440 ms 升到 620 ms。
- 72 条 Trace 中保留 49 条诊断明细，Trace Coverage 为 `0.680556`；69 条遥测完整，Completeness 为 `0.958333`；总体最终失败请求为 3。
- 唯一同时移除延迟、成本和重试放大症状的教学消融是 `retry_policy`；报告结论为 `confirmed`，同时保留现实因果未证明等 Unknown。

## 本轮验证

| 验证 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -B -m pytest chapter14/tests -q` | 66 项通过 |
| 两次完整诊断实验 | 8 个稳定产物逐字节一致，并与 canonical reports 一致 |
| 两次练习输出 | 14 道答案逐字节一致 |
| JSON Schema Draft 2020-12 | 规范报告通过；非法 release/conclusion、嵌套未知字段、负时长和缺失完整率被拒绝 |
| 隐私与因果回归 | 未脱敏 Combined/Tail Trace 被拒绝；依赖时间倒置在指标前失败关闭 |
| 桌面预览 | 1440×1000，7/7 图片、6/6 表格、0 失效锚点，无整页横向溢出 |
| 移动预览 | 390×844，7/7 图片可横向滚动，6/6 表格受容器约束，无整页横向溢出 |
| `.venv\Scripts\python.exe -B -m unittest discover -s tests -q` | 43 项通过 |
| 仓库与站点 | `scripts.check_repository`、`scripts.build_site`、`mkdocs build --strict` 通过 |
| 公开清单 | `_web/book/chapter14.md` 与 `site/book/chapter14/index.html` 不存在；`mkdocs.yml` 与 `book/manifest.json` 不含 Chapter 14 |
| 历史保护 | Chapter 13 rc2 相关路径相对基线提交无差异 |

## 规范产物哈希

| 产物 | SHA-256 |
| --- | --- |
| `book/chapter14.md` | `2d7f4a21aa01853d6285879911dd113724a27b09ea598c16be258ef86b4b35f7` |
| `book/sources/chapter14-sources.md` | `2d1a4a94addafe0bbaec31913349c8de95f935c7a7c79e94afc0796c5e448872` |
| `book/reviews/chapter14-review-codex-v1.0-rc1.md` | `2cbb8776f230f8b5cbc8858d883cb14990f75e1671ec0bb0597666fd16b1adb4` |
| `chapter14/reports/diagnostic-report.json` | `49f651364419533460abf924509567c0ed04a127a91743fa968acb51c5d9fc75` |
| `chapter14/reports/diagnostic-report.md` | `2c382ee6b0323c36c679039d9a9357b86ad9eefb33b62802ce48922c04576411` |
| `chapter14/reports/manifest.json` | `153ed69b711a2c469d79a41ab24a7d92b320138b9c8a714e58baa782d8f79b01` |
| `chapter14/reports/exercise-results.json` | `2591f05303e73f18297ad3f66ba5cd333d4c850acc0a258e2841967a5f9847ed` |
| `chapter14/schemas/production-diagnostics-v1.schema.json` | `827c0bff85d0057d0f95df089712267140f6d452b738f29b28fec0d49157dafd` |

集合哈希按相对路径排序，将每个文件的 `relative_path␠␠sha256` 以 LF 连接后再次计算 SHA-256。`chapter14/` 集合排除本地 `.verification/`、`.runs/`、`preview-pages/`、缓存和 `.pyc`。

| 集合 | 文件数 | SHA-256 |
| --- | ---: | --- |
| `chapter14/` 稳定实验包 | 43 | `d75161dfd5a5abc82b50b5829958f40e8b68186341b04a858ddd4d15d54c7a40` |
| `book/images/chapter14/` | 7 | `d06b54cd81f71b7a6a4cdc45149ab3c34c5b90d0bcf3990e981e6925ec05862d` |
| `infographic/chapter14/` | 10 | `3b5737ae4a43a7dc6ff4a0211b1b0a0e62659644ee4478d42cebda952463202b` |

## 已证明与未证明

本候选证明：给定固定测量合同，系统可以拒绝不可比 Benchmark；能在 Outcome 不变时发现 p95、成本与重试退化；能验证 Parent Tree 与依赖 DAG，计算不重复并行工作的关键路径；能把总体计数与 Tail 诊断样本分离；能在隐私转换后采样；能用切片、支持/反证与消融生成可回归事故结论。

本候选没有证明：任何真实模型、Claude Code、Codex 或观测平台的能力高低；72 条 Trace 对生产流量的代表性；教学 `cost_units` 等同于真实价格；固定反事实夹具能够证明现实因果；本地 Schema 符合 OpenTelemetry、Langfuse 或 OpenAI Agents SDK 的完整协议；教学脱敏器满足组织的全部安全与合规要求。

## 历史与发布边界

- Chapter 13 rc2 基线保存在 `be655ca04f6449808bdbab64e5b3ee00c10a4c08`，本轮没有修改其正文、代码、图、报告、审稿或版本记录。
- 本章审稿过程记录在 `book/reviews/chapter14-review-codex-v1.0-rc1.md`。
- 本轮不修改 `mkdocs.yml`、`book/SUMMARY.md`、`book/manifest.json`、站点 allowlist 或部署配置。
- 本轮不推送 GitHub，不创建 PR，不部署网站，不创建发布 tag，也不生成 PDF/EPUB。

