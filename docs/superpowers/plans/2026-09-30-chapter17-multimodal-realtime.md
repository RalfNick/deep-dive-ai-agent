# 第 17 章《多模态与实时 Agent》Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with native execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一章可读、可复算的本地候选书稿，连同受限 SVG 图表验证、模拟 Computer Use、实时事件实验、七图、练习、来源、审稿和版本记录。

**Architecture:** `chapter17/` 独立于旧章运行：统一媒体/事件合同连接图表、屏幕、语音三条受控支路；每条支路显式产出来源、未知和执行证据，最后由报告入口汇总。正文先用图表手算建立直觉，再依次引出视觉误读、屏幕时效和语音事件，产品 API 只作带日期的责任映射。

**Tech Stack:** Python 3.11+ 标准库（`decimal`、`csv`、`xml.etree.ElementTree`、`json`、`hashlib`）；pytest==9.0.2、jsonschema==4.26.0 用于锁定开发测试；现有 Markdown==3.10.2 用于本地预览；复用仓库已有受控 SVG/Tldraw 绘图器。无需模型、网络、Docker、GPU、麦克风或真实桌面控制。

**Spec:** `docs/superpowers/specs/2026-09-30-chapter17-multimodal-realtime-design.md`；执行者必须先读规格与本计划。设计分支 `codex/chapter17-multimodal-realtime`，基线 `84fd308`。

## Global Constraints

- 正文为 `book/chapter17.md`，约 2.0–2.5 万叙述汉字、28–36 个二三级标题、7 幅原创技术图、4–5 张比较表、5 组实验、至少 4 个失败样本、13 道分层练习；先讲现象和手算，再讲代码与接口。
- 运行时优先 Python 标准库；默认不读 API Key、不联网、不控制真实桌面、不录音，不安装额外框架；测试/预览依赖沿用本书已锁定版本，不猜测哈希。
- SVG 解析仅支持作者控制的柱状图约定；静态 PNG、文档页和语音离线观察必须标明为固定样本，不得宣称测出通用视觉/语音模型能力。
- 图/CSV 冲突、缺刻度/图例/单位、零分母、过期帧、缺授权、缺执行回执均显式为 `unknown`、`blocked` 或 `refresh`，不能隐式转成成功。
- 屏幕只用合成夹具与模拟回执；语音事件只用本书中性字段。响应停播、对话截断、后台任务取消和已发生副作用分开记录。
- 固定时钟、输入和序号；规范 JSON 不含当前时间、随机 UUID、主机绝对路径或真实密钥。已有输出路径一律拒绝覆盖；`.runs/` 与预览 HTML 不提交。
- 正文中的官方产品事实在实施日复核并入 `book/sources/chapter17-sources.md`；不报未测量的 Token、费用、真实延迟、模型正确率或厂商排名。
- 1–14 章已发布、第 15/16 章 RC 历史、公开 `book/manifest.json` 和站点 allowlist 不改写；第 17 章只形成 `v1.0-rc1` 本地候选，不推送、合并、建 PR/tag、部署、译文或 PDF。
- 用户已选择 native：主执行者逐任务完成并保留可复核提交；结尾按读者与工程专家双视角审稿，再做一次新上下文只读整分支复审，不将其说成独立实测模型认证。

## Review Focus

以下五类输入最容易被“正常样例通过”掩盖；对应任务必须先写失败测试再修复：

1. 带 DTD、外部引用或变换的 SVG：任务 2 应拒绝或返回 `unknown`，绝不能读取外部资源或按错误坐标取值。
2. 重复月份、混合单位或 UTF-8 BOM 的 CSV：任务 2 应明确拒绝歧义；BOM 可规范化但不得改变月份或数值。
3. 截图缩放不是等比或显示尺寸为零：任务 3 必须分别换算 x/y 并拒绝零尺寸、越界或错误帧。
4. 相同序号不同内容、事件缺号或任务完成后的取消：任务 4 必须给出冲突/未知或不可撤销状态，不重复改写已完成结果。
5. 输出目录虽在 `chapter17/.runs/` 下却经过链接或 Windows reparse 父目录：任务 5 必须拒绝且不覆盖旧证据。

## File Map

| 文件 | 单一责任 |
| --- | --- |
| `chapter17/contracts.py`, `chapter17/fixtures.py` | 不可变媒体/观察/决策/事件合同；固定夹具入口 |
| `chapter17/chart.py`, `chapter17/fixtures/chart-*.svg`, `chapter17/fixtures/chart-values.csv` | 受限图表取数及独立 CSV 核验 |
| `chapter17/screen.py`, `chapter17/fixtures/screens.json` | 合成帧、坐标、新鲜度、权限及模拟回执 |
| `chapter17/voice.py`, `chapter17/fixtures/voice-events.json` | 固定事件状态归约与打断/后台任务区分 |
| `chapter17/evidence.py`, `chapter17/experiments.py`, `chapter17/output.py`, `chapter17/schemas/report-v1.schema.json` | 五组实验、规范报告、确定性输出与拒绝覆盖 |
| `infographic/chapter17/generate_diagrams.py`, `infographic/chapter17/*.tldr`, `book/images/chapter17/*.svg` | 七幅图的可编辑源和受控 SVG 输出 |
| `book/chapter17.md`, `book/sources/chapter17-sources.md`, `chapter17/README.md` | 正文、来源台账和读者入口 |
| `chapter17/reference-answers.md`, `chapter17/exercise_solutions.py`, `chapter17/preview.py` | 分层答案、可执行答案、仅本地预览 |
| `book/reviews/chapter17-review-codex-v1.0-rc1.md`, `book/versions/chapter17-v1.0-rc1.md` | 审稿发现和本地候选的证据边界 |

## Tasks

### Task 1: 固定合同与夹具入口

**Files:** Create `chapter17/__init__.py`, `chapter17/contracts.py`, `chapter17/fixtures.py`, `chapter17/tests/__init__.py`, `chapter17/tests/test_contracts.py`, `chapter17/tests/test_fixtures.py`, `chapter17/requirements-dev.in`, `chapter17/requirements-dev.txt`.

**Interfaces:** `MediaRef(kind: str, source_id: str, sha256: str, locator: str, captured_at_ms: int, scope: str)`、`Observation(media_ref: MediaRef, method: str, region: str, values: tuple[tuple[str, Decimal], ...], unit: str | None, issues: tuple[str, ...])`、`Decision(status: Literal["answer", "unknown", "blocked", "refresh"], value: Decimal | None, unit: str | None, reasons: tuple[str, ...], evidence_ids: tuple[str, ...])`、`EventRecord(seq: int, event_ms: int, session_id: str, turn_id: str, task_id: str, kind: str, payload: tuple[tuple[str, str], ...])` 为不可变 dataclass；`make_media_ref(kind: str, source_id: str, content: bytes, locator: str, captured_at_ms: int, scope: str) -> MediaRef` 计算内容摘要；`load_fixture(name: str) -> bytes` 只读 `chapter17/fixtures/` 中精确文件名。数值统一 `Decimal`，时间统一非负整数毫秒。

- [ ] 先写 `test_media_ref_digest_and_immutability`、`test_fixture_rejects_parent_or_absolute_name`、`test_decision_status_is_explicit`，分别断言摘要可重算、`../`/绝对路径不读取、状态只接受 `answer/unknown/blocked/refresh`。
- [ ] 运行 `python -B -m pytest chapter17/tests/test_contracts.py chapter17/tests/test_fixtures.py -q`，确认缺失实现导致 RED。
- [ ] 实现以上 dataclass 与夹具白名单入口；开发锁文件从现有已核实锁定依赖机械沿用，不推断新包哈希。
- [ ] 运行同一命令确认 GREEN。
- [ ] 用精确路径暂存并提交 `feat(chapter17): define media evidence contracts`。

### Task 2: 可复算图表观察与独立数值核对

**Files:** Create `chapter17/chart.py`, `chapter17/fixtures/chart-base.svg`, `chapter17/fixtures/chart-truncated-axis.svg`, `chapter17/fixtures/chart-values.csv`, `chapter17/tests/test_chart.py`；其他故障 SVG 可由测试在内存中变异，不复制许多夹具。

**Interfaces:** `observe_svg_chart(svg: bytes, media: MediaRef) -> Observation` 只接受无脚本、无 DTD/外链/变换的受控线性柱状图；依据可见刻度文本及其 y 坐标、柱形几何和 x 轴可见月份文本取候选值，不读取隐藏 `data-value`。`decide_chart(observation: Observation, csv_bytes: bytes) -> Decision` 核对 `month,unit,count` 三列后用 `Decimal` 计算相对增长率（单位 `percent`），冲突/缺项返回 `unknown`。

- [ ] 写 `test_80_to_100_yields_25_percent_with_two_sources`、`test_truncated_axis_70_still_yields_25` 和缺刻度/混淆图例/零分母/图表与 CSV 不一致的负例；断言来源 ID 与计算步骤可追溯。
- [ ] 加 Review Focus 测试：DTD、`<image href>`、`transform` 拒绝；重复月份/混合单位拒绝；UTF-8 BOM 合法文件仍解析到同一值。
- [ ] 运行 `python -B -m pytest chapter17/tests/test_chart.py -q` 确认 RED。
- [ ] 实现最小 SVG 几何解析与 CSV 验算，不引入通用 OCR。
- [ ] 再运行该测试及 Task 1 测试确认 GREEN。
- [ ] 精确路径暂存并提交 `feat(chapter17): verify authored charts against data`。

### Task 3: 有画面版本的模拟 Computer Use

**Files:** Create `chapter17/screen.py`, `chapter17/fixtures/screens.json`, `chapter17/tests/test_screen.py`；模拟帧的可见示意图由任务 6 绘制，真值框仅在测试夹具中。

**Interfaces:** `Frame(frame_id: str, captured_at_ms: int, image_width: int, image_height: int, display_width: int, display_height: int, targets: dict[str, tuple[int, int, int, int]], state: dict[str, bool])` 和 `ActionProposal(frame_id: str, action: str, target_id: str, image_x: int, image_y: int, expected_state: tuple[str, bool])`；`ActionReceipt(frame_id: str, status: Literal["verified", "blocked", "refresh", "unknown"], executed: bool, display_xy: tuple[int, int] | None, post_frame_id: str | None, reasons: tuple[str, ...])`；`simulate_action(proposal: ActionProposal, current: Frame, after: Frame | None, *, now_ms: int, allowed_actions: frozenset[str], approved: bool) -> ActionReceipt`。新鲜度上限固定 2000 ms；x/y 分别按显示尺寸换算，结果只写模拟回执。屏幕里的任何文字均不得扩张 `allowed_actions`。

- [ ] 写 `test_400_225_on_800_450_maps_to_800_450_on_1600_900`、`test_stale_frame_does_not_click`、`test_missing_approval_is_blocked`、`test_post_frame_required_for_verified_success`。
- [ ] 加 Review Focus 测试：非等比缩放分别计算、零尺寸和越界拒绝；同坐标在新帧变成另一控件时拒绝；画面内“忽略审批”文字不能授权。
- [ ] 运行 `python -B -m pytest chapter17/tests/test_screen.py -q` 确认 RED。
- [ ] 实现帧身份、新鲜度、策略、转换、目标命中和后验状态核对。
- [ ] 再运行本任务及前两任务测试确认 GREEN。
- [ ] 精确暂存提交 `feat(chapter17): simulate fresh authorized screen actions`。

### Task 4: 语音打断与后台任务状态

**Files:** Create `chapter17/voice.py`, `chapter17/fixtures/voice-events.json`, `chapter17/tests/test_voice.py`.

**Interfaces:** `VoiceState(playback: str, conversation_tail: str, backend_task: str, committed_actions: tuple[str, ...], issues: tuple[str, ...])`；`reduce_events(events: tuple[EventRecord, ...]) -> VoiceState`。事件种类限 `speech_started/response_cancelled/playback_stopped/conversation_truncated/task_started/task_completed/task_cancelled/action_committed`；同序号同内容重放幂等，不同内容冲突；缺号不补造事件。`speech_started` 不自行假定后台任务已取消。

- [ ] 写 `test_interrupt_stops_playback_not_running_task`、`test_truncate_removes_unplayed_tail`、`test_explicit_task_cancel_is_separate`、`test_committed_action_survives_late_cancel`。
- [ ] 加 Review Focus 测试：重复且相同的事件不重复副作用；同序号异内容、缺号和逆序事件进入显式 `unknown`/冲突而非“任务完成”。
- [ ] 运行 `python -B -m pytest chapter17/tests/test_voice.py -q` 确认 RED。
- [ ] 实现有限状态归约，固定事件的具体顺序在夹具中一眼可读。
- [ ] 再运行已有章节 17 测试确认 GREEN。
- [ ] 精确暂存提交 `feat(chapter17): reduce realtime interruption events`。

### Task 5: 五组实验、规范报告与安全输出

**Files:** Create `chapter17/evidence.py`, `chapter17/experiments.py`, `chapter17/output.py`, `chapter17/schemas/report-v1.schema.json`, `chapter17/tests/test_experiments.py`, `chapter17/tests/test_output.py`, `chapter17/tests/test_schema.py`；生成 `chapter17/reports/` 下规范样本。

**Interfaces:** `run_group(group: int) -> dict` 对应规格五组，`run_all() -> dict` 返回 `schema_version="chapter17.multimodal.v1"`、五组、summary、source_proof、limits；summary 至少有 `cases_total`、`answers`、`unknown`、`blocked`、`refresh`、`security_violations` 和证据覆盖分子/分母，所有计数从逐案例状态计算；`validate_report(report: dict) -> None` 做跨组证据一致性检查；`write_bundle(root: Path, destination: Path, report: dict, exercises: dict | None = None) -> tuple[Path, ...]` 只准 `chapter17/.runs/` 或 `chapter17/reports/`，创建新目录后写 5 个 group JSON、总 JSON、摘要 Markdown、manifest，附练习时再加练习 JSON；`main(argv: list[str] | None = None) -> int` 提供 `--group all|1..5 --output ...`。Decimal 在稳定报告中用十进制字符串，不用浮点近似。

- [ ] 写 `test_five_groups_show_claim_and_counterexample`、`test_report_requires_evidence_and_unknown_reasons`、`test_schema_rejects_missing_group`；断言 25% 的候选结论、旧帧阻断、播报与后台任务分离均在报告里有可定位证据。
- [ ] 写 `test_two_runs_have_identical_canonical_bytes`、`test_existing_empty_output_is_refused`、`test_output_outside_root_or_reparse_parent_is_refused` 和默认路径下不访问网络/密钥的测试。
- [ ] 运行 `python -B -m pytest chapter17/tests/test_experiments.py chapter17/tests/test_output.py chapter17/tests/test_schema.py -q` 确认 RED。
- [ ] 实现规范 JSON、摘要、manifest 与 CLI，不直接导入第 16 章内部模块。
- [ ] 运行完整 `chapter17/tests` 确认 GREEN。
- [ ] 将两份新输出目录与规范 `reports/` 的稳定文件逐字节比较。
- [ ] 精确暂存提交 `feat(chapter17): generate deterministic multimodal evidence`。

### Task 6: 七幅可读且可编辑的原创图

**Files:** Create `infographic/chapter17/__init__.py`, `infographic/chapter17/generate_diagrams.py`, `infographic/chapter17/README.md`, `infographic/chapter17/02-*.tldr` 至 `07-*.tldr`, `book/images/chapter17/01-*.svg` 至 `07-*.svg`, `chapter17/tests/test_diagrams.py`。第一图的可编辑真源是图表夹具与受控图形生成逻辑，02–07 沿用仓库现有 Scene→SVG/Tldraw 双输出模式。

**Interfaces:** `build_scenes() -> tuple[Scene, ...]`、`generate(root: Path) -> tuple[Path, ...]`；单次调用生成七幅 SVG，重复调用字节相同。第一图保留一月80、二月100、千件、零/截断轴读图提示；不能在图中埋隐藏答案属性。

- [ ] 先写图形合同测试：恰好七幅、ID 唯一、首图数值/单位可见、无外部链接/脚本、重复生成相同字节、标签坐标在画布安全区内；截断与箭头层级仍需人工看渲染图。
- [ ] 运行 `python -B -m pytest chapter17/tests/test_diagrams.py -q` 确认 RED。
- [ ] 用浅色纸张与蓝绿紫橙分区生成七图和可编辑源。
- [ ] 查看七图实际渲染，核对箭头、轴、中文和讲解顺序。
- [ ] 运行图形合同测试确认 GREEN。
- [ ] 精确暂存提交 `docs(chapter17): add seven original diagrams`。

### Task 7: 完整书稿与来源台账

**Files:** Create `book/chapter17.md`, `book/sources/chapter17-sources.md`, `chapter17/README.md`, `chapter17/tests/test_manuscript.py`, `chapter17/tests/test_sources.py`.

**Interfaces:** 正文图号对应任务 6，五个实验框对应 `run_group(1..5)`，读者命令对应任务 5；来源台账每条记录链接、用途、版本或论文版本、核对日期、不能支持的外推。第 18 章只预告 Multi-Agent 与最终系统，不提前写其实现。

- [ ] 写内容合同测试：章节标题、7 图链接、5 组标准实验框、13 道完整题目、出处文件、所有相对路径存在。
- [ ] 运行内容合同测试确认 RED。
- [ ] 查核设计规格列出的论文与官方页面，写入核对日期和用途边界。
- [ ] 写四幕完整正文，先用 `80→100 = 25%` 和两处实际实验失败讲清问题，再展开边界、流程、实验和产品映射；正文叙述汉字单独计数。
- [ ] 跑五组实验并逐项核对书稿中的数值、状态、命令和限制。
- [ ] 运行本任务测试确认 GREEN。
- [ ] 从读者视角自审：不翻代码仍能复述四幕结论。
- [ ] 精确暂存提交 `docs(chapter17): write multimodal and realtime chapter`。

### Task 8: 十三题答案与本地预览

**Files:** Create `chapter17/reference-answers.md`, `chapter17/exercise_solutions.py`, `chapter17/preview.py`, `chapter17/tests/test_exercises.py`, `chapter17/tests/test_preview.py`; Modify `chapter17/experiments.py` 以在全组输出时纳入答案，更新 `chapter17/reports/` 规范 bundle；Modify `book/chapter17.md` 的练习与答案链接（若任务 7 已写好，不重复增题）。

**Interfaces:** `payload() -> dict` 返回十三题的固定答案/判据，其中图表变化率、截断轴、坐标缩放和事件排序四题可复算；`main(argv: list[str] | None = None) -> int` 支持 `--all --output ...` 且不覆盖；`build_preview(root: Path, *, output: Path | None = None) -> Path` 仅写 `chapter17/preview-pages/` 忽略目录。

- [ ] 写 `test_13_answers_have_computed_examples`、`test_answer_output_is_stable_and_refuses_overwrite`、`test_preview_does_not_touch_public_manifest`、`test_all_bundle_includes_exercise_results`。
- [ ] 运行本任务测试确认 RED。
- [ ] 写出十三题的计算过程、可运行命令或否决判据，实现稳定的 `exercise_solutions.py`。
- [ ] 将 `chapter17.experiments --group all` 接入答案输出，附带 `exercise-results.json`。
- [ ] 实现只写入 `chapter17/preview-pages/` 的本地预览入口。
- [ ] 重新生成 `chapter17/reports/`，确认新增练习文件和 manifest 摘要相符。
- [ ] 跑题目/预览测试与完整 `chapter17/tests` 确认 GREEN。
- [ ] 在 1440×1000、390×844 检查七图加载、表格局部滚动、页内锚点和整页溢出。
- [ ] 精确暂存提交 `docs(chapter17): add exercises and local preview`。

### Task 9: 双视角审稿、版本冻结与整分支验证

**Files:** Create `book/reviews/chapter17-review-codex-v1.0-rc1.md`, `book/versions/chapter17-v1.0-rc1.md`; Modify `AGENTS.md`, `book/versions/CHAPTER_VERSIONS.md`, `docs/MIGRATION_MANIFEST.md` 中受影响的状态/校验字段。不得改 `book/manifest.json`、公开导航或旧章正文。

**Interfaces:** Review 逐项记读者是否能复述、专家是否发现概念/数值/来源越界、已修与未修；版本记录包括环境、命令、规范报告摘要哈希、预览结果、已证明与未证明结论。迁移台账只刷新 `CHAPTER_VERSIONS.md` 的字节数和 SHA-256，保留旧来源标签和来源提交。

- [ ] 做读者与 AI 工程双视角审稿并写入审稿记录。
- [ ] 对审稿发现的高优先级问题补失败测试，再按 RED→GREEN 修复；实质修订仍处于 RC1 首次冻结前。
- [ ] 两次运行 `python -B -m chapter17.experiments --group all --output chapter17/.runs/final-a` 与 `...final-b`，比较每个规范文件字节/哈希。
- [ ] 运行 `python -B -m chapter17.exercise_solutions --all --output chapter17/.runs/answers-final.json` 和 `python -B -m pytest chapter17/tests -q`。
- [ ] 运行 `python -B -m pytest chapter15/tests chapter16/tests tests -q`，记录实际结果。
- [ ] 运行 `npm --prefix book test`，记录实际结果。
- [ ] 运行 `python -B scripts/check_repository.py --root . --git-history`，记录实际结果。
- [ ] 在现有 MkDocs 环境运行 `python -B -m mkdocs build --strict`，记录实际结果。
- [ ] 检查 `book/manifest.json` 与公开 allowlist 保持原样，第 1–16 章历史无意外修改。
- [ ] 记录报告哈希、书稿叙述汉字数、七图与桌面/移动预览结果，更新本地候选台账和迁移哈希。
- [ ] 精确暂存提交 `docs(chapter17): freeze local rc1 candidate`。
- [ ] native 全分支完成后由新上下文只读复审一次；若发现必须修复的问题，保留原 RC1 冻结点/报告，再以新提交及版本记录修复；最终 `git status --short` 应为空，不推送或发布。

## Execution Handoff

本计划仅供审阅，尚未执行 Task 1–9。用户已选 native；用户确认本计划后调用 `superpowers:executing-plans`，按任务顺序做 TDD、局部测试和本地提交，不为每个任务派实现代理。计划形成或设计稿确认都不授权发布、真实 API 调用或公共站点修改。
