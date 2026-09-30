# 第 17 章 v1.0-rc2 本地修订记录

日期：2026-09-30。分支：`codex/chapter17-multimodal-realtime`。RC1 固定提交 `549de8498ad2cf38d6185058b53017f6e9d60489`、[RC1 九文件报告](../../chapter17/reports/reference-rc1/manifest.json)、[RC1 审稿](../reviews/chapter17-review-codex-v1.0-rc1.md)与[RC1 版本记录](chapter17-v1.0-rc1.md)不改写。当前书稿、代码和[RC2 九文件报告](../../chapter17/reports/reference-rc2/manifest.json)是复审修订后的本地候选，未推送、合并、创建 PR/tag 或部署；公开 manifest 仍为 `0.14.0`，第 17 章不在站点 allowlist。

## 内容与修订

正文 20,317 个叙述汉字（沿用 RC1 的排除代码、表格、标题、图片行、脚注定义和列表行的口径）、36 个二/三级标题、七图、五张比较表、五组实验、13 道练习与答案。七图文件不改；图 2–7 可编辑源与图 1 受控生成逻辑保持原样。组 2/5 增加缺刻度、双图例、缺单位、真正零分母与过期图表五例，总数由 20 到 25。正文同步解释像素下取整、行动后验时间、固定安全门禁的计算口径与练习缺号语义。产品引用未新增，来源台账仅把本地报告证据从 RC1 指向 RC2。

代码修复严格 UTF-8/扁平 SVG、CSV 原始表头、缩小时合法显示像素与行动后取得的画面。`security_violations` 不再是常量，而是固定套件里未授权执行、旧帧执行、危险 SVG 被当作答案及缺后验误报完成等硬门禁的逐案例派生指标；报告校验器可发现伪造的违规布尔值。这只是教学用固定政策，不替代生产安全评估。全部具体发现、RED→GREEN 测试和三项范围裁决见[复审处理](../reviews/chapter17-review-codex-v1.0-rc2.md)。

## 环境与验证

Windows；Python 3.11.15、pytest 9.0.2、jsonschema 4.26.0、Markdown 3.10.2、Node 24.15.0、Playwright 1.62.1、MkDocs 1.6.1、现有 Edge。复用现存 Python/Node 环境，未安装模型、依赖、容器或音频服务，未读取 API Key，未调用真实 Provider、桌面、麦克风或网络。新环境依赖已声明但未做新环境安装验收。

| 检查 | 实际命令与结果 |
| --- | --- |
| 本章 | `.venv-chapter15/Scripts/python.exe -B -m pytest chapter17/tests -q -p no:cacheprovider`：73 通过 |
| 全书相关回归 | 同解释器运行 `pytest chapter17/tests chapter15/tests chapter16/tests tests -q -p no:cacheprovider`：336 通过、93 子测试通过 |
| 规范报告 | `python -B -m chapter17.experiments --group all --output chapter17/.runs/rc2-final-a` 与新目录 `rc2-final-b`：九文件分别与 `reports/reference-rc2/` 同名文件 SHA-256 完全一致；`reference-rc1/` 原九文件保留 |
| 独立练习 | `python -B -m chapter17.exercise_solutions --all --output chapter17/.runs/rc2-answers-final.json`：与 RC2 `exercise-results.json` 字节一致 |
| 本地页面 | `python -B -m chapter17.preview`、`node book/check_chapter17_preview.mjs`：1440×1000 与 390×844 均七图加载、五表局部滚动、零失效锚点和整页溢出；截图仅在忽略的 `chapter17/preview-pages/screenshots/` |
| Node / 公开站点 | `npm --prefix book test`：4 通过；`.venv/Scripts/python.exe -B scripts/build_site.py --root . --output _web`：218 份公开源；`.venv/Scripts/python.exe -B -m mkdocs build --strict`：exit 0，第 17 章未进入 `_web` |
| 仓库安全 | `.venv/Scripts/python.exe -B scripts/check_repository.py --root . --git-history`：exit 0；历史教学夹具仍仅按 RC1 已记录的精确对象/行号豁免路径扫描，密钥扫描不豁免 |

规范报告摘要：`schema_version=chapter17.multimodal.v1`；`answer=10`、`unknown=11`、`blocked=2`、`refresh=2`，总计 25；声明硬门禁违规 0；证据引用覆盖 25/25。报告未测 Token、费用、模型正确率、真实延迟或用户体验。

| 文件 | SHA-256 |
| --- | --- |
| `book/chapter17.md` | `5175D249ED23EF4B0FF22C5745C6F805236DCEAAB1CF0806460D0B0BDFA36A2F` |
| `book/sources/chapter17-sources.md` | `7C17B1E93EE5A10E847045C2EAB53E68D0C63EB72C8760102D569AEFC5D10A2A` |
| `chapter17/reports/reference-rc2/report.json` | `0E15B88785123F90F332EF8AE89A8B4E0C42D98540A1629B40C5B18966B24A9D` |
| `chapter17/reports/reference-rc2/manifest.json` | `230A0E4707A62EFC3E70CA2D96067D8914D84B6E654EA45612D8F909BFC999BA` |
| `chapter17/reports/reference-rc2/exercise-results.json` | `519417409ADF4A878827014292C5D1D1A0FB24CDF829E117DFE29C4B8556B6CD` |

以上 SHA-256 是文件字节摘要；九文件各自摘要见规范 manifest。RC1 字节摘要见其原版本记录，不能把 RC2 的 25 例结果回填到 RC1。

## 已证明与未证明

已证明：在作者固定夹具及明确的有限合同内，新增恶意编码/嵌套/歧义 CSV、坐标边缘及前后时序会被正确拒绝或归为未知；注入未授权执行会让固定安全门禁计数上升；报告与练习可重建。未证明：真实视觉/语音模型能力、任意 SVG/OCR、真实 GUI 竞态和原子隔离、现实音频协议互操作、生产安全、延迟与成本。本地 RC2 是教学稿修订，不是正式发布。
