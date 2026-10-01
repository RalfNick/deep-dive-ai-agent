# 第 17 章 v1.0-rc3 本地修订记录

日期：2026-10-01（Asia/Shanghai）。分支：`codex/chapter17-multimodal-realtime`。本轮处理 RC2 的三项技术一致性问题与两项读者体验问题，不新增章节、不接入模型或真实设备、不推送、不合并、不建 PR/tag、不部署。公开 manifest 保持 `0.14.0`。

## 历史保护

RC2 冻结提交为 `4d96603c72b87b1b9c6aa33b7ef853f5c0be3344`。[RC2 稿图快照](chapter17-v1.0-rc2/README.md)保留原正文、七图、台账、答案及台账直接引用的四份证据，共 14 份冻结文件，全部与该提交逐字节一致。快照不是独立运行包，完整代码仍以冻结提交为准。[RC1](../../chapter17/reports/reference-rc1/manifest.json)与[RC2](../../chapter17/reports/reference-rc2/manifest.json)的 18 份原报告、原版本记录、原审稿均未改写；第 1–16 章源文件不变。

## 本轮修改

1. **限定图表输入，而不伪称通用视觉能力。** SVG 只接受固定 520×380 viewport、两种明确的柱体着色和固定元素结构；拒绝被测透明/白色柱、裁切 viewport、画布外坐标和额外遮挡层。正文明确这是受控绘图语法检查，不是任意 SVG 的完整渲染或可见性证明。
2. **把语音生成与播放分开。** `response_cancel_requested` 只表示请求，`response_cancelled` 表示生成取消已确认，二者不更新播放器。只有 `playback_stopped` 标记停播；截断和后台状态另行归约。缺号或身份冲突时生成、后台状态保守为 `unknown`。事件名称是本章中性教学语义，不是厂商协议映射。
3. **修复输入证据归属。** 三个组 4 案例分别读取 `voice-interruption.json`、`voice-task-cancel.json`、`voice-conflict.json`，报告各自保存输入名、实际字节摘要及归约结果；不再让派生事件共同冒用原始流摘要。
4. **补上看得见的实验结果。** 图表/语音有精简 JSON 摘录，屏幕实验有四行真实摘要；图表与屏幕的完整短片段可运行，状态判断摘录明确不是独立程序。逐步解释观察值、计算结果、外层状态与执行回执的区别。
5. **调整阅读节奏。** 开篇只聚焦两根柱子，三个场景分别推进；解释首次出现的观察合同、血缘与归约，合并重复局限说明。图 17-6 仅把标签改为“生成取消已确认”，布局和配色保持；练习 17-10 与答案同步生成状态。

正文按既有口径为 20,634 个叙述汉字，36 个二/三级标题、七图、五表、五组实验、13 题。来源中 O2 的官方中断/截断说明于 2026-10-01 复核；其余外部来源保留 2026-09-30 核对日期，不声称全部重新查证。

## 环境与实际验证

复用现存 Windows 环境：Python 3.11.15、pytest 9.0.2、jsonschema 4.26.0、Markdown 3.10.2、Node 24.15.0、Playwright 1.62.1、MkDocs 1.6.1、现有 Edge；图 17-6 另用现有 tldraw 6.0.2 导出一次本地 PNG 检查文字与连线。没有安装依赖、模型、容器或音频服务，没有读取 API Key 或调用 Provider/麦克风/真实桌面。只查阅官方文档，实验仍完全离线。

| 检查 | 命令或方法与实际结果 |
| --- | --- |
| 失败先行 | 新增的图表、取消语义与输入血缘共 12 个测试，修复前 12 失败、30 通过；修复后这三个测试文件共 42 通过 |
| 本章 | `.venv-chapter15/Scripts/python.exe -B -m pytest chapter17/tests -q -p no:cacheprovider`：85 通过 |
| 相关回归矩阵 | 同解释器运行 `pytest chapter17/tests chapter15/tests chapter16/tests tests -q -p no:cacheprovider`：348 通过、93 子测试通过；这不是整库所有章测试 |
| 报告与练习复现 | `python -B -m chapter17.experiments --group all --output chapter17/.runs/rc3-final-a` 与新目录 `rc3-final-b`，九文件均与 `reports/reference-rc3/` 同名文件字节一致；`python -B -m chapter17.exercise_solutions --all --output chapter17/.runs/rc3-answers-final.json` 与规范答案字节一致 |
| 正文一致性 | 实际运行两个完整 Python 短片段，分别得到 Jan 80/Feb 100、`answer 25` 与四种屏幕状态；两个 JSON 摘录逐字段比对规范报告；练习 17-10 的保留序号、重新编号及替换请求三种结果实际归约核对 |
| 本地预览 | `python -B -m chapter17.preview`、`node book/check_chapter17_preview.mjs`：1440×1000 和 390×844 均七图加载、五表局部滚动、零失效锚点、零整页横向溢出、零远程运行依赖；截图在忽略的 `chapter17/preview-pages/screenshots/` |
| Node / 本地站点 | `npm --prefix book test`：4 通过；`.venv/Scripts/python.exe -B scripts/build_site.py --root . --output _web`：218 份公开源；`.venv/Scripts/python.exe -B -m mkdocs build --strict`：exit 0；`_web/book/chapter17.md` 不存在 |
| 仓库安全 | `.venv/Scripts/python.exe -B scripts/check_repository.py --root . --git-history`：exit 0；未放宽已有历史夹具精确豁免，未豁免密钥检查 |

路径测试起初错误指定仓库内临时目录，与旧测试“输出在仓库外应被拒绝”的前提冲突，留下了一页测试 HTML；已核实并仅清理该临时页，改用默认测试临时目录后相关矩阵通过。快照补齐冻结链接证据后，仓库链接检查通过；没有修改旧测试来绕过断言。

### 整库根目录测试的限制

实际尝试 `.venv-chapter15/Scripts/python.exe -B -m pytest -q -p no:cacheprovider`，得到 **15 项收集错误，exit 2**，不能报告成“全书通过”：第 1 章缺 NumPy（3 项），第 9 章缺 MCP（3 项），第 12 章的两个框架测试缺 Agents SDK（2 项），其演示夹具因缺 `src` 被根目录收集（1 项），第 11/12/13/4 章出现同名测试模块导入冲突（6 项）。这些收集问题未在本轮修复，未额外安装依赖。相关矩阵的通过只适用于上表明确列出的目录。

## 稳定报告与字节摘要

规范报告 Schema 仍为 `chapter17.multimodal.v1`，顶层合同不变；可扩展的案例 `details` 增加 `generation` 与实际事件来源。25 例：`answer=10`、`unknown=11`、`blocked=2`、`refresh=2`；固定政策硬门禁违规 0，证据覆盖 25/25。没有 Token、费用、模型正确率或实测实时延迟。

| 文件 | SHA-256 |
| --- | --- |
| `book/chapter17.md` | `74BF1981CDC929197FE299D00BB449D77EE33CA79A2EB1BFF1A44A9463E65AF8` |
| `book/sources/chapter17-sources.md` | `9F928358F0917C5C2D9D81A4C41F6741B45F7BC4ED607428CB713FE1D4DE72DC` |
| `chapter17/reports/reference-rc3/report.json` | `68C76EC0808306B5E21CFF7ECF11AC9DBC458293BF1428A99F068860B4903AA7` |
| `chapter17/reports/reference-rc3/manifest.json` | `DA40BDF9B8B4284656A0CF080CE5FD6D57C0BF5E7412C20041FFE79EDE155B27` |
| `chapter17/reports/reference-rc3/exercise-results.json` | `69C071370717C644BD74FE54B94F2C3C6B111AC721FCCC94CA1935069D362516` |

以上是文件字节摘要；其他文件摘要见规范 manifest。旧记录中的 RC1/RC2 数值与摘要只属于旧版，不回填。

## 已证明与未证明

已证明：所列固定恶意/裁切图表会被拒绝；生成取消请求、确认与停播在教学归约器中分离；三个语音案例可从各自实际输入重算；报告、答案和正文短示例可复现。未证明：通用 SVG 可见性、真实视觉/语音模型质量、任意 GUI 竞态及生产隔离、音频设备播放位置、厂商协议互操作、线上延迟与成本。当前可作为本地 RC3 教学候选保留；读者与专家复核见[RC3 审稿](../reviews/chapter17-review-codex-v1.0-rc3.md)。
