# 第 13 章 v1.0-rc2 本地候选记录

记录日期：2026-09-26。分支：`codex/chapter13-agent-evaluation`。前版基线：`74e143d38cb21669b6bf2cce05626a14830de69e`。状态：**本地候选，未推送、未发布**。

本版本在 rc1 上完成证据链复审。rc1 的正文、审稿报告、Schema 和版本记录均保留；rc2 新增用途视图与回归门禁、真实 JSON Schema 校验、非退化 Bootstrap 教学样本、事件序列与任务路径合同，以及 Live Judge 响应解析。本轮不修改 Chapter 12，也不把 Chapter 13 加入公开站点清单。

## 候选内容

- 正文 23,430 个字符，23 个二级标题与 7 个三级标题；5 组实验、14 道练习和 7 幅原创图。
- 12 个 Coding Agent 教学任务，保留 basic、edge、safety、recovery 四个内容切片，并新增 capability、regression、adversarial 三个用途视图。
- Baseline 与 Candidate 两种确定性策略，各任务使用 5 个固定种子，共 120 条计分 Trial。
- Outcome、Trajectory、Safety、Efficiency 四类评分器；安全、环境、总体、内容切片、Regression 用途与成对置信区间共同进入发布门禁。
- 当前稳定报告升级为 `chapter13.eval.v2`；`evaluation-report-v1.schema.json` 保留，v2 使用 Draft 2020-12 并由 pytest 对真实 JSON 自动校验。
- 离线 Judge 继续使用固定样本；可选 Live Judge 只在显式调用时访问 Provider，并先解析为 `{label, evidence}` 本地合同。

## 环境与规范结果

- Python 3.11.15；pytest 9.0.2；Markdown 3.10.2；jsonschema 4.26.0。
- 规范运行不联网、不读取 API Key，也没有真实 Provider Usage。
- Baseline：`pass@1=55%`、`pass@3=95%`、`pass^3=12.5%`、安全违规 9。
- Candidate：`pass@1=75%`、`pass@3=100%`、`pass^3=40%`、安全违规 0。
- basic、edge、safety、recovery 四个内容切片差值均为 0.20；capability、regression、adversarial 三个用途差值也均为 0.20。
- 规范成对任务差值为 20 个百分点，固定种子、10,000 次任务级 Bootstrap 的 95% 区间为 `[20%, 20%]`。
- 非计分异质差值示例的均值为 1.67%，95% 区间为 `[-5.83%, 9.17%]`，结论为 `inconclusive`。
- Judge 教学夹具：agreement 66.67%、coverage 66.67%、answered-only accuracy 75%、Unknown 33.33%。
- 发布门禁结果：`pass`。该结论只适用于固定教学任务、策略与规则，不是任何真实模型或 Agent 产品的发布结论。

## 本轮验证

| 验证 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -B -m pytest chapter13/tests -q` | 38 项通过 |
| 双目录完整实验 | JSON、Markdown、5 组报告和 manifest 逐字节一致 |
| JSON Schema Draft 2020-12 | 规范报告通过；错误类型、非法状态、嵌套未知字段和越界差值均拒绝 |
| 桌面预览 | 1440px，7/7 图片加载，0 失效锚点，无整页横向溢出 |
| 移动预览 | 390px，7/7 图片加载，图与表局部横向滚动，无整页横向溢出 |
| `.venv\Scripts\python.exe -B -m unittest discover -s tests -q` | 43 项通过 |
| `.venv\Scripts\python.exe -B -m scripts.check_repository` | 通过 |
| `.venv\Scripts\python.exe -B -m scripts.build_site` | `site_sources=170` |
| `.venv\Scripts\python.exe -B -m mkdocs build --strict` | 通过 |
| 公开清单核对 | `site/book/chapter13/index.html` 与 `_web/book/chapter13.md` 均不存在 |

## 规范产物哈希

| 产物 | SHA-256 |
| --- | --- |
| `book/chapter13.md` | `0ab68e1d46508a0ded1d9e0f42a5359bb9fa198822b009ef07ab070423ab90e5` |
| `book/sources/chapter13-sources.md` | `6e4f2adddbb471531f0083ad707d1888b989a35a56f3dba5ce7bef8e5dc8088a` |
| `book/reviews/chapter13-review-codex-v1.0-rc2.md` | `0054b3f7e51eecba092899549086a3d2aba046e65f477ed39ac92c6c3b9cc0d2` |
| `chapter13/reports/evaluation-report.json` | `1bae70811e2b13a18e313d6bc539026c684f67507bacb52daa10d4b5430d42d1` |
| `chapter13/reports/evaluation-report.md` | `45ef27925c1fe606e0ec755500b495d02e4d3b34f8b455fad0f6014bce1a9af3` |
| `chapter13/reports/manifest.json` | `8468233ea3c7643ff5123e4dfa88108dfaee14c26e6e691cb7e0336bd144a2a4` |
| `chapter13/reports/exercise-results.json` | `efe5828601cf438b4b97e4dd34e91a197abc39c46e77dda200a8cdb5b445e18` |
| `chapter13/schemas/evaluation-report-v1.schema.json` | `12c857de4270c9e35d936fa020b87de651549ceaca67bff1144d7a663d4f2d3b` |
| `chapter13/schemas/evaluation-report-v2.schema.json` | `d927b46042ec820a9a78da0885350cd8d96253da05cdda5e1282d030b7cb4f99` |

集合哈希按相对路径排序，将每个文件的 `relative_path␠␠sha256` 以 LF 连接后再次计算 SHA-256。`chapter13` 集合排除本地 `preview-pages/`、`.runs/`、测试临时目录、缓存和 `.pyc`。

| 集合 | SHA-256 |
| --- | --- |
| `chapter13/` 稳定实验包 | `940d448463afdd560c19c1318d29f52f69647622d45d93df02e9b5df8b450e83` |
| `book/images/chapter13/` | `cee4920a6db2292d43d3e2fedcb1be7f1c6002b2932dd219e16d2addbf49072c` |
| `infographic/chapter13/` | `0c5034cecfdc68deb10c3a5d4ef34df01582cbe5ed10593405877c6ea55bdaf7` |

## 已证明与未证明

本候选证明：固定任务和固定策略下，Evaluation Harness 能把任务内容切片与开发用途分开统计；能发现结果、轨迹、安全和效率问题；能以显式 `seq` 验证事件顺序；能用标准 JSON Schema 固定报告合同；能把 Regression 退化、环境故障、安全违规和统计不确定性转化为三态发布决策。

本候选没有证明：任何真实模型、Claude Code、Codex、OpenAI Evals、LangSmith 或 Inspect AI 的能力高低；教学任务对生产流量的代表性；目录级隔离可以替代生产沙箱；未经独立人工复核的 Judge 标签达到上线质量；Live Judge 的真实 Provider 兼容性；Bootstrap 可以消除任务选择偏差或任务内随机不确定性。

## 历史与发布边界

- rc1 完整基线保存在提交 `74e143d38cb21669b6bf2cce05626a14830de69e`，其审稿和版本记录未被改写。
- rc2 复审过程记录在 `book/reviews/chapter13-review-codex-v1.0-rc2.md`。
- 本轮不修改 `mkdocs.yml`、`book/SUMMARY.md`、公开 manifest、站点 allowlist 或部署配置。
- 本轮不推送 GitHub，不部署网站，不创建发布 tag，也不生成 PDF/EPUB。
