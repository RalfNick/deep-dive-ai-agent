# 第 17 章 v1.0-rc1 本地候选记录

日期：2026-09-30。分支：`codex/chapter17-multimodal-realtime`；设计基线 `84fd308`。本版只在本地形成候选，不推送、不合并、不建 PR/tag、不部署，也不修改公开 allowlist 或 `book/manifest.json`（仍为 `0.14.0`）。第 1–16 章正文、插图和旧版本记录保持原样。

## 交付范围

- `book/chapter17.md`：36 个二/三级标题，20,079 个叙述汉字（剔除代码、表格、标题、图片行、脚注定义和列表行的统计口径），五组实验、五张比较表、13 题及答案。
- `book/images/chapter17/`：七幅受控原创 SVG。第一图可编辑真源为图表夹具及生成逻辑，图 2–7 同时保存可编辑 `.tldr` 源于 `infographic/chapter17/`。
- `chapter17/`：标准库运行时的图表/CSV 核对、合成 Computer Use、固定语音事件、证据报告、Schema、独立练习与本地预览；`book/sources/chapter17-sources.md` 记录来源、核对日期和外推边界。
- `chapter17/reports/reference-v1/` 保存较早 16 案例教学参考包；最终 `reference-rc1/` 为 20 案例、九文件参考包。历史样本不冒充最终成绩。

## 环境与实际验证

Windows，本地 Python 3.11.15、pytest 9.0.2、jsonschema 4.26.0、Markdown 3.10.2、Node 24.15.0、MkDocs 1.6.1；既有依赖环境复用，未安装模型或新服务。`chapter17` 运行不读 API Key、不联网、不控制真实桌面、不录音。

| 检查 | 实际命令/结果 |
| --- | --- |
| 第 17 章 | `.venv-chapter15/Scripts/python.exe -B -m pytest chapter17/tests -q -p no:cacheprovider`：62 通过 |
| 章节及仓库回归 | 同解释器运行 `pytest chapter17/tests chapter15/tests chapter16/tests tests -q -p no:cacheprovider`：325 通过、93 子测试通过 |
| 九文件复现 | `python -B -m chapter17.experiments --group all --output chapter17/.runs/final-c` 与新目录 `final-d`：各九文件与 `reports/reference-rc1/` 同名文件 SHA-256 完全一致；原 `final-a/b` 是修复教学 URI 前的检查输出，不作为本版规范包 |
| 练习 | `python -B -m chapter17.exercise_solutions --all --output chapter17/.runs/answers-final.json`：与规范 `exercise-results.json` SHA-256 一致 |
| Node | `npm --prefix book test`：4 通过 |
| 安全与历史 | `.venv/Scripts/python.exe -B scripts/check_repository.py --root . --git-history`：exit 0；旧教学夹具仅按四个 Git 对象/七行精确豁免路径扫描，历史密钥扫描不豁免 |
| 公开构建 | `.venv/Scripts/python.exe -B scripts/build_site.py --root . --output _web`：218 份公开源；`.venv/Scripts/python.exe -B -m mkdocs build --strict`：exit 0；第 17 章不在 `_web` 或公开导航 |
| 本地视觉检查 | `python -B -m chapter17.preview` 后于 1440×1000 / 390×844 查看：七图加载、页内锚点有效、五表局部横向滚动、无整页横向溢出；预览 HTML 与截图在忽略目录，不是公开产物 |

最初在 `.venv-chapter15` 中执行 MkDocs 提示模块不存在；随后用仓库既有 `.venv` 中的 MkDocs 1.6.1 完成严格构建。首次历史扫描发现本地旧提交内的教学 URI，修复与精确豁免后复跑为 exit 0；这两次失败没有被计入最终通过结果。

## 可复核摘要与哈希

最终 `schema_version=chapter17.multimodal.v1`。20 个案例：`answer` 10、`unknown` 7、`blocked` 2、`refresh` 1；安全违规 0；证据引用覆盖 20/20。各状态从逐案例记录汇总，非真实模型成功率。

| 文件 | SHA-256 |
| --- | --- |
| `book/chapter17.md` | `A53C165C49F38DEBC400D3F420434707FE11BF2EA5EF172297E216792F159B62` |
| `chapter17/reports/reference-rc1/report.json` | `AD4FED3C41E2F7A48A2DFA96BA39852F2F3B9D260C10471352B7BA37301F0A16` |
| `chapter17/reports/reference-rc1/manifest.json` | `0D4AD611E358E550FF9BDB3CD0775307A991D122C4B6660F532B53D26E46F1E7` |
| `chapter17/reports/reference-rc1/exercise-results.json` | `519417409ADF4A878827014292C5D1D1A0FB24CDF829E117DFE29C4B8556B6CD` |

九文件各自的摘要列于[规范 manifest](../../chapter17/reports/reference-rc1/manifest.json)。[双视角审稿](../reviews/chapter17-review-codex-v1.0-rc1.md)记录首冻前发现及修复。

## 已证明与未证明

已证明：在作者固定夹具、固定时钟和有限状态合同下，图表取数/CSV 核对、屏幕权限与后验、语音事件归约、显式未知及拒绝覆盖能按预期工作，并可稳定再生报告。

未证明：任一现实视觉/语音模型的正确率、真实 GUI 识别与点击可靠性、WebRTC/WebSocket 时序互操作、生产安全隔离、真实延迟、Token 或费用、跨厂商优劣。图表解析器只接受受控 SVG；文档页是固定观察，不是 OCR；屏幕不执行真实副作用。后续接入真实模型时必须另加隐私授权、硬隔离、真实错误分布、人工校准和独立验收。
