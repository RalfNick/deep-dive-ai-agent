# 第 13 章 v1.0-rc1 本地候选记录

记录日期：2026-09-24。分支：`codex/chapter13-agent-evaluation`。状态：**本地候选，未推送、未发布**。

本版本新增第 13 章《Agent 评估：答案正确还不够》、自包含实验包、7 幅原创图、来源台账、参考答案、双视角审稿报告和本地预览。Chapter 12 正文、实验与历史版本未修改。

## 候选内容

- 正文 22,987 个字符，23 个二级标题与 7 个三级标题；5 组实验、14 道练习、7 幅图、6 张表。
- 12 个 Coding Agent 教学任务，覆盖 basic、edge、safety、recovery 四个切片。
- Baseline 与 Candidate 两种确定性策略，各任务使用 5 个固定种子，共 120 条计分 Trial。
- Outcome、Trajectory、Safety、Efficiency 四类评分器，以及安全硬否决、切片退化和成对置信区间发布门禁。
- 版本化 `chapter13.eval.v1` 报告 Schema、稳定 JSON/Markdown 报告、五组实验报告和练习结果。
- 离线 Judge 教学校准；可选 Live Judge 只在应用代码显式调用时读取指定环境变量。

## 环境与规范结果

- Python 3.11.15；pytest 9.0.2；Markdown 3.10.2。
- 规范运行不联网、不读取 API Key，也没有真实 Provider Usage。
- Baseline：`pass@1=55%`、`pass@3=95%`、`pass^3=12.5%`、安全违规 9。
- Candidate：`pass@1=75%`、`pass@3=100%`、`pass^3=40%`、安全违规 0。
- 成对任务差值 20 个百分点；固定种子、10,000 次任务级 Bootstrap 的 95% 区间为 `[20%, 20%]`。
- Judge 教学夹具：agreement 66.67%、coverage 66.67%、answered-only accuracy 75%、Unknown 33.33%。
- 发布门禁结果：`pass`。该结果只适用于固定教学任务、策略与规则，不是任何真实模型或 Agent 产品的发布结论。

## 本轮验证

| 验证 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -B -m pytest chapter13/tests -q` | 33 项通过 |
| 双目录完整实验 | JSON、Markdown、5 组报告和 manifest 逐字节一致 |
| JSON Schema 正向校验 | 规范报告通过，合法的 `slice_delta=-0.12` 通过 |
| JSON Schema 负向校验 | 错误类型、非法状态、嵌套未知字段、`slice_delta < -1` 均拒绝 |
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
| `book/chapter13.md` | `8d10d4c28455188a0f3d315f69f2a9da5aff1e89269b9ab2846c1c856fc3a7ed` |
| `book/sources/chapter13-sources.md` | `5f1aca03352b884c3e76ac1aa06e1ca60efff91924fa6430815b0b5bda12b989` |
| `book/reviews/chapter13-review-codex-v1.0-rc1.md` | `6767f95c8bbdd02ddc3d7612c2467dd12a169f312c83d5898fd0f9d9e8e3b609` |
| `chapter13/reports/evaluation-report.json` | `fcea34ceb266a557a8087ede1a007256fe657c557f76d6a2f9ed06a5abe8860e` |
| `chapter13/reports/evaluation-report.md` | `0463f7f846e3aa6c89e7c29a72b7488c51e24762ba066433359a2b9dd0cf25ce` |
| `chapter13/reports/manifest.json` | `ca5530dc822f5c6d38663c2baaaac4b58e41f5106f007e01fa0ec0821eaa4710` |
| `chapter13/reports/exercise-results.json` | `efe5828601cf438b4b97e4dd34e91a197abc39c46e77dda200a8cdb5b445e18` |
| `chapter13/schemas/evaluation-report-v1.schema.json` | `12c857de4270c9e35d936fa020b87de651549ceaca67bff1144d7a663d4f2d3b` |

集合哈希按相对路径排序，将每个文件的 `relative_path␠␠sha256` 以 LF 连接后再次计算 SHA-256。`chapter13` 集合排除本地 `preview-pages/`、`.runs/`、测试临时目录和缓存。

| 集合 | SHA-256 |
| --- | --- |
| `chapter13/` 稳定实验包 | `f674426a8b4d4f8f5ccab6be459e3000c77e01434a0faf6e8495a1566c0b4c57` |
| `book/images/chapter13/` | `cee4920a6db2292d43d3e2fedcb1be7f1c6002b2932dd219e16d2addbf49072c` |
| `infographic/chapter13/` | `9a8a799b7cf556271927f38906fdfb83dcbba7e65180e19d18c5304daed0fab1` |

## 已证明与未证明

本候选证明：固定任务和固定策略下，Evaluation Harness 能区分声明、结果与轨迹；能发现受保护文件修改、隐藏答案读取、越界写入、预算失败和环境错误；能稳定计算多次试验指标、任务切片、成对区间与三态发布门禁。

本候选没有证明：任何真实模型、Claude Code、Codex、OpenAI Evals、LangSmith 或 Inspect AI 的能力高低；教学任务对生产流量的代表性；目录级隔离可以替代生产沙箱；未经独立人工复核的 Judge 标签达到上线质量；当前 Bootstrap 区间能够覆盖任务内随机不确定性。

## 历史与发布边界

- 审稿过程和已修问题记录在 `book/reviews/chapter13-review-codex-v1.0-rc1.md`。
- 图 13-4/13-5 的内部资产前缀沿用生成顺序，与读者可见图号不同，但正文图号、链接和渲染均正确。
- 本轮不修改公开站点导航、章节 allowlist 或部署配置，不推送 GitHub，不部署 `wlxralf.com`。
- 后续若发布 rc2 或正式版，应新增版本记录，不覆盖本文件及本次提交历史。
