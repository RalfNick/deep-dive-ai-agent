# 第 6 章四视角 Review：长任务中的上下文架构

日期：2026-08-17

评审基线：`3d8da24`（`codex/chapter6-context-continuity`）

历史草稿：`chapter6-v1.0-draft` 仍指向 `4c71cdb`，本轮不得移动

> **当前发布状态（最终分支）：** 第 13 节“Task 12 fix round 1：v1.0.1 补丁发布”记录的 v1.0.1 已验收并发布，annotated tag `book-chapter6-v1.0.1` 已冻结；`book-chapter6-v1.0` 与 `chapter6-v1.0-draft` 仍保留且未移动。发布之后，最终分支又加入两道保护：`ChapterSixReleasePortabilityTest.test_immutable_release_hashes_match_version_ledger` 固定 v1.0/v1.0.1 PDF 与版本台账哈希，`DeepSeekCompactionProbeTest.test_live_cli_rejects_canonical_report_paths_and_aliases_before_provider` 阻止 live probe 覆盖三份 canonical offline reports。这些 guard 修订没有改写已发布 PDF 或移动标签。

> **Task 11 当时结论（历史快照）：** Task 11 四视角 Review 与 Fix round 1 均已完成。正文主线、实验边界和配套实现达到可出版草稿水位；3 个原始 P1、4 个选定 P2 及最终复核追加的 2 个 P1、1 个 P2 均已关闭。Task 12 当时尚未启动，等待该轮复核结果被接受。

> 本文件先于任何 Task 11 修订创建。下文“原始位置”均指基线 commit `3d8da24`；修订完成后在“接受的修改”和“验证清单”追加结果，不回写或抹除原始发现。

## 1. 评审范围与证据

本轮按四个镜头独立检查：第一次阅读、Agent 系统专家、实验审稿、编辑与移动端版面。评审对象包括：

- `book/chapter6.md`、第 5 章结尾桥接和总设计/实现计划；
- `chapter6/context_continuity/`、`chapter6/experiments/`、`chapter6/fixtures/`、全部 Chapter 6 测试；
- 固定 JSON、Markdown、JSONL Trace、`chapter6/README.md` 与 `chapter6/reference-answers.md`；
- 七幅 `book/images/fig6-*.svg`、资料台账和 Task 1—10 SDD 报告/ledger；
- `chapter6-v1.0-draft..3d8da24` 的历史差异，确认草稿 tag 未被改写。

基线证据：

- Chapter 4：24 个测试通过；Chapter 5：63 个测试通过；Chapter 6：130 个测试通过，共 217 个；
- 成稿静态门禁为 0 error；CJK 正文 25,534 字，H2/H3 共 30 个，七图各引用一次，练习/答案 14/14，答案分布 4/5/5；
- 固定报告 15 个 case，全部 `sample_count=1`，JSON/Markdown/JSONL 当前 SHA-256 分别为 `50cbbc...6e5e`、`f05fba...e107`、`cbcc12...eb96`；
- 两条脚注均有引用和定义，24 个 Markdown 链接已做本地路径检查；
- 七图已在本地 Chromium 以 1200×675 与 390×219 两档 `<img>` 实际渲染并目视检查；
- 2026-08-17 重新打开 S01—S10 官方页面，OpenAI compaction、Agents SDK Session、Claude Code context/resume/fork、LangGraph Checkpointer/Store 的正文映射未发现事实反转。出版前仍须按台账再次复核快变项。

仓库中没有计划提到的 `book/WRITING_GUIDE.md`，`git log --all -- book/WRITING_GUIDE.md` 也无记录。因此本轮写作标准以 `AGENTS.md`、已批准设计规格、实现计划、前章成稿和 Task 10 出版门禁为准；这是评审输入缺口，不是正文失败。

## 2. P0—P3 发现

### P0：阻断发布

无。没有发现凭据泄漏、报告造数、产品排名或会让读者执行危险操作的阻断问题。

### P1：进入 Task 12 前必须关闭

#### P1-1：ArtifactStore 允许同一 Artifact ID 被不同内容静默覆盖

- 原始位置：`chapter6/context_continuity/stores.py:146-151`。
- 关联承诺：`book/chapter6.md:620` 要求升级不应覆盖同一 `artifact_id`，`book/chapter6.md:664`、`:769`、`:787` 又把旧 Artifact 只读保留和 ID 不复用写成恢复前提。
- 证据：`ArtifactStore.write()` 当前无存在性/内容冲突检查，直接以 `Path.replace()` 覆盖。虽然已提交 Checkpoint 会因保存的 Artifact Digest 不同而失效，但旧 Artifact 本身已经丢失，无法按正文所述回滚或审计。
- 决定：接受。先写 RED 回归，要求相同 ID + 相同内容幂等，相同 ID + 不同内容以稳定 reason `artifact_id_conflict` 拒绝，再修 Store；不扩展成分布式对象存储。

#### P1-2：正文把实验 Grader 的能力写大了一层

- 原始位置：`book/chapter6.md:612`。
- 实现证据：`chapter6/context_continuity/graders.py:71-82` 的保留率只比较 `visible_keys`；Locator 的内容/Workspace 校验在 `chapter6/experiments/common.py:137-158`；结构化再生只在 `chapter6/experiments/generational_drift.py:27-30` 比较整个对象的 canonical bytes/digest。
- 问题：正文声称“第二层比较规范化内容 Digest，第三层比较 source_event_ids”，会让读者误以为固定报告逐字段输出内容漂移和 provenance 漂移指标。当前报告没有这种逐字段测量。
- 决定：接受。保留该四层模型作为生产设计建议，但明确本地报告只测 key 集合、Locator 完整性和整份结构化再生稳定性；逐字段内容/provenance 漂移是未实现的扩展门禁。

#### P1-3：图 2—5 在 390px 下的核心文字不可读

- 原始位置：`book/images/fig6-2-state-surfaces.svg:1-4`、`fig6-3-context-lifecycle.svg:1-5`、`fig6-4-compaction-artifact.svg:1-4`、`fig6-5-dual-continuity-timeline.svg:1-5`。
- 证据：四图都只有 1200×675 桌面布局，没有 media-query mobile group；390px 等比缩放后最小字号约为 3.9—4.2px，多项核心标签也只有约 6px。Chromium 真机尺寸截图确认：整体轮廓可辨，但字段、来源和责任标签无法在不放大的情况下阅读。
- 决定：接受。为图 2—5增加与图 6/7 同合同的 390×219 响应式 mobile group，至少保证核心标签约 10px、来源/边界约 8px；保持七图数量、文件名、桌面视觉和语义不变。图 1 的核心两点数据在 390px 仍清楚，暂不重构。

### P2：本轮选择性修订

#### P2-1：延续性删除分支只有实现，没有同名测试证据

- 原始位置：`chapter6/tests/test_persistence.py:144-163`。
- 证据：测试名是 `missing_or_changed_artifact`，正文也在 `book/chapter6.md:767` 要求删除已提交 Artifact 的恢复演练，但现有测试只篡改文件内容，没有删除文件。
- 决定：接受。新增独立 RED 测试，删除已提交 Artifact 后 `CheckpointStore.latest()` 必须返回 `None`。这是 Task 2 deferred minor 的关闭证据。

#### P2-2：响应式字号测试只用宽度缩放，阈值略显乐观

- 原始位置：`chapter6/tests/test_publication_checks.py:1123-1127`。
- 证据：有效字号使用 `scale * 390 / 1200`，未取 `min(390/1200, 219/675)`。当前差异很小，但测试合同应覆盖实际 `preserveAspectRatio` 的受限轴。
- 决定：接受。把现有响应式合同扩展到图 2—7，并改为最小轴缩放；改动后的定向 RED 首先暴露图 6/7 在受限轴下低于阈值，再修移动布局。这是 Task 8 deferred minor 的关闭证据。

#### P2-3：产品映射有台账，但正文缺少就近的一手来源脚注

- 原始位置：`book/chapter6.md:674-699`。
- 证据：本节只写“S01—S10”，读者必须离开正文打开资料台账，才能判断 Claude Code、Codex/Responses/Agents SDK 与 LangGraph 的公开事实来源。相邻的 OpenAI compaction 与 Lost in the Middle 已采用脚注，产品映射反而证据距离更远。
- 决定：接受。补 Claude Code、Codex loop、Agents SDK Session、LangGraph persistence/short-term memory 四组就近脚注；不把表格每个单元格堆满链接。资料台账追加本轮官方页面复核记录。

#### P2-4：两个超长章节段落缺少移动端阅读锚点

- 原始位置：`book/chapter6.md:703-787`。其中“成本、安全、隐私与审计”约 2,254 个 CJK，“状态应该去哪里”约 3,127 个 CJK，后者同时承载状态归位、Schema 迁移、恢复演练、保留策略和运行信号。
- 决定：接受。增加少量 H3 阅读锚点，同时把三个局部 H3 降为粗体段首，确保全章 H2/H3 仍为 30，不扩大目录或内容范围。

### P3：可保留或后续观察

#### P3-1：开场消融与固定报告的区别出现两次

- 位置：`book/chapter6.md:12` 与 `:590`。
- 决定：拒绝删除。开场短注解决“这是不是固定 JSON 行”的即时疑问，后文详细映射解决实验归因；两处承担不同阅读责任，继续保留。

#### P3-2：图 1 的来源脚注在 390px 下偏小

- 位置：`book/images/fig6-1-context-growth.svg:1-4`。
- 决定：暂不改。两项核心数据、标题和“不补造中间点”仍可读，正文紧邻位置又重复给出数据与来源；把图 1 改成另一套移动布局的收益低于引入视觉回归的成本。

#### P3-3：不把 key-only Grader扩展成新的报告 Schema

- 位置：`chapter6/context_continuity/graders.py:9-90`。
- 决定：拒绝本轮扩展。逐字段内容/provenance 指标值得后续实验，但会改变固定 JSON、图 6、参考哈希与 15-case 期望；本轮通过收窄正文主张保持证据诚实，而不是在总章 review 中新增实验维度。

#### P3-4：不运行可选真实模型探针

- 位置：`chapter6/README.md:80-106`（live probe 与离线报告分离合同）。
- 决定：拒绝作为发布门槛。真实 Provider 探针不改变确定性结论，且本轮目标是四视角 review，不是模型质量评测；保持可选、隔离和不进入离线分母。

## 3. 第一次阅读视角

开场有效：它先让读者看到“步骤恢复正确、任务语义仍错误”，再给出双连续性的答案。第 5 章到第 6 章的桥接也清楚：前者构造一张 Packet，后者管理未来 Packet 的生命周期。七个状态表面、完整追加、滑动窗口、段落摘要、双连续性、Artifact、提交顺序与 Rehydration 形成连续梯度，代码都在概念之后出现，没有用类定义抢跑。

主要阅读问题不是概念缺失，而是后半章密度过高和图 2—5 的手机字号。读者在 `book/chapter6.md:703-787` 连续跨越成本、安全、删除、状态归位、Schema、恢复演练、运维信号，缺少小标题会降低检索性。该问题已列为 P2-4。开场解释略显审稿式，但被压缩为一条短证据说明，后文才展开，当前取舍可接受。

## 4. Agent 系统专家视角

核心边界基本正确：Event Log 是事实历史，ContextPacket 是单轮投影，Workspace 是真实产物，Checkpoint 回答执行位置，Artifact 回答语义交接，Memory 被严格留到第 7 章。authority、trust、sensitivity 和 source IDs 在 Rehydrator 中沿用第 5 章合同；stale Workspace、未知 Schema 与来源 Digest 不匹配都在 Builder 前拒绝。正文也没有把提交顺序写成业务 exactly-once。

最重要的专家问题是 P1-1：正文要求 Artifact ID 不复用，Store 却允许原地覆盖。第二个问题是 P1-2：概念上提出的内容/provenance 漂移检查，比固定 Grader 实际测量多。两项分别需要代码门禁与主张收窄。产品映射经官方页面复核仍成立，且已正确拆开 Codex Harness、Responses API、Agents SDK Session 与 LangGraph Checkpointer/Store，没有把公开行为变成产品内部推断。

## 5. 实验审稿视角

实验合同完整：同一 30 事件 Fixture、固定 `ScriptedRepairPolicy`、固定工具结果，每个变体 `sample_count=1`；报告用布尔、计数、比例和 `null`，没有合成总分。正文明确区分五个实验组与 failure matrix，也纠正了 `early-constraint-loss` 并非结构化基线单字段破坏。`checkpoint-only-v1` 不伪造 Packet 和 resume 指标，`rehydrated-context-v1` 使用真实 Chapter 5 类型和后缀事件验证。

当前数字与 JSON 一致，图 1/6 的所有可见数值与 `context-continuity.json` 对账无差异。可重复性测试验证三份报告不含时间戳和机器路径。审稿意见集中在测量边界：字段 retention 是 key presence，不是语义等价；Locator 与整对象 Digest 是另两项独立检查。P1-2 修订后，Claims/Non-claims 与报告能够一致。

## 6. 编辑与版面视角

篇幅、标题数、图数和练习数均在批准范围内：25,534 CJK、30 个 H2/H3、7 图、14 题。代码块最长 18 行，未出现整文件粘贴；比较表多但都承担边界或实验合同，不是装饰。练习标题与答案完全对齐，答案均含预期推理、常见错误与可检查验收。

桌面七图均无裁切、重叠或错误箭头，图 6/7 的响应式布局在 Chromium 中真实切换。图 2—5 仍是桌面画布缩放，移动端不达精品章可读标准，必须按 P1-3修订。正文后半段标题稀疏按 P2-4重新分配，不增加总标题数。PDF 分页、表格跨页、脚注新页和封面元数据属于 Task 12，本轮不提前判断。

## 7. 接受的修改

以下修改均已完成，且没有扩大固定实验或章节范围：

1. **P1-1，Artifact 身份不可变。** 原实现对同一 ID 总是原子替换；修订后 `ArtifactStore.write` 对相同内容幂等返回，对不同内容抛出 `artifact_id_conflict`，并验证冲突后旧制品仍可读取。稳定回归入口为 `PersistenceTest.test_artifact_store_rejects_same_id_with_different_content`、`PersistenceTest.test_artifact_store_allows_idempotent_same_content_write`、`PersistenceTest.test_concurrent_threads_publish_exactly_one_different_artifact`、`PersistenceTest.test_concurrent_threads_accept_identical_artifact_idempotently`、`PersistenceTest.test_concurrent_processes_publish_exactly_one_different_artifact` 与 `PersistenceTest.test_concurrent_processes_accept_identical_artifact_idempotently`；正文证据位于 `book/chapter6.md` 的“有序压缩提交：先证明 Artifact 存在，再让 Checkpoint 引用”一节。这里不再用插入代码后会漂移的行范围定位证据。
2. **P1-2，测量边界收窄。** 原文把设计上可做的逐字段内容/provenance 检查写成固定 Grader 已做；修订后只声称 `visible_keys` 保留、独立 Locator 完整性和整份 Artifact canonical stability，并把逐字段检查明确列为未实现的生产扩展；正文证据位于“重复压缩与代际漂移：错误怎样逐代固化”一节。报告 Schema、15 个 case 与三个基准 Digest 未改变。
3. **P1-3，图 2—5 真响应式。** 四图新增 390×219 mobile group 与媒体查询；图 4 在小屏改为纵向合同带，避免把三列桌面字段等比压缩。图 6/7 仅微调 mobile scale，使受限轴下核心/来源字号分别不低于 10px/8px。七图在 Chromium 两档实际渲染中无裁切、重叠或错误切组。
4. **P2-1，关闭删除分支证据缺口。** 新测试实际删除已提交 Artifact 文件，再确认 `CheckpointStore.latest()` 返回 `None`；稳定证据入口为 `PersistenceTest.test_checkpoint_with_deleted_artifact_is_not_recoverable`，不再用会随插入测试漂移的行范围代替完整断言。
5. **P2-2，关闭有效字号计算缺口。** 发布测试从仅检查图 6/7 扩为图 2—7，并以 `min(390/1200, 219/675)` 计算 `preserveAspectRatio` 受限轴。稳定证据入口为 `mobile_text_size_violations`、`ChapterSixFigurePublicationTest.test_semantic_figures_have_real_responsive_mobile_layouts` 与 `ChapterSixFigurePublicationTest.test_explicit_mobile_font_size_cannot_escape_threshold`，不再引用易漂移的测试行范围。
6. **P2-3，就近放置一手来源。** 产品责任映射新增 Claude Code、Codex、OpenAI Agents SDK Session 与 LangGraph 官方脚注；资料台账追加 S01—S10 的 2026-08-17 复核记录。原边界“只描述公开行为，不推断内部实现或排名”保持不变。
7. **P2-4，增加移动端阅读锚点。** 新增“成本、延迟与缓存”“五条安全与隐私传播路径”“Schema 演进与恢复演练”三个 H3，同时把三个局部例子降为粗体段首。信息没有移章或扩章，H2/H3 总数仍为 30。

代码缺陷遵循 RED→GREEN：首次定向运行中，同 ID 不同内容写入未抛错，图 2—5 缺少 mobile layout，最小轴计算又暴露图 6/7 的有效字号低于阈值；修订后相同定向测试及全部 Chapter 6 测试通过。Artifact 删除测试在首次加入时已经通过，说明实现原有安全失败行为，本轮补的是缺失的回归证据，而非虚构 RED。

## 8. 拒绝或延期的建议

- 保留开场短证据说明和后文详细消融映射，原因见 P3-1；
- 不重做图 1 mobile layout，原因见 P3-2；
- 不新增逐字段内容/provenance 报告 Schema，原因见 P3-3；
- 不把可选 DeepSeek/真实 Provider 探针变成离线发布门槛，原因见 P3-4；
- 不在 Task 11 生成 PDF、移动 draft tag 或创建 release tag；这些严格属于 Task 12。

## 9. 修订后验证清单

- [x] P1-1：相同 Artifact ID 的同内容重写幂等，不同内容拒绝，RED/GREEN 证据已记录；
- [x] P1-2：正文准确区分 key retention、Locator integrity、整对象 canonical stability 与未实现的逐字段语义检查；
- [x] P1-3：图 2—5 在 Chromium 390×219 中核心文字可读，桌面布局无回归；
- [x] P2-1：删除已提交 Artifact 的独立测试通过；
- [x] P2-2：字号按受限轴计算，图 2—7 responsive 合同通过；
- [x] P2-3：产品事实有就近一手脚注，资料台账记录本轮复核；
- [x] P2-4：H2/H3 为 30，长段落已有阅读锚点；
- [x] Chapter 4/5/6 分别 24/63/133 个测试通过，共 220 个；
- [x] 固定报告连续生成两次且三个 SHA-256 不变：JSON `50cbbc...6e5e`、Markdown `f05fba...e107`、JSONL `cbcc12...eb96`；
- [x] 成稿 publication gate 为 0 error，CJK 25,713，7 图/14 题/14 答案不变；
- [x] 七图 XML、安全、桌面与移动端检查通过；
- [x] 链接、6/6 脚注、Secret、本机路径、产品排名和 bytes/Token 扫描通过；
- [x] `chapter6-v1.0-draft^{}` 仍指向 `4c71cdb`；无 PDF、最终 tag 或 Task 12 文件。

## 10. Fix round 1：最终复核追加发现

状态：**重新阻断 Task 12，待本节三项关闭。** 本节追加于 commit `7ce99a9` 之后；不回写前述首次 Review 的原始发现与验证历史。

### FR1-P1：Artifact ID 的不可变发布仍有 TOCTOU 竞态

- 位置：`chapter6/context_continuity/stores.py:146-160`（commit `7ce99a9`）。
- 证据：`path.exists()` 与后续 `_write_atomically(...replace)` 之间没有原子 create-if-absent 边界。两个并发 Writer 都可能看到目标不存在，再由最后一次 `replace()` 覆盖胜者；顺序测试通过并不能证明进程/线程竞态安全。
- 决定：接受。为 Artifact 单独实现“完整 sibling temp + `fsync` + 原子 no-overwrite publish”；发布输家读取权威 envelope，相同 record 视为幂等，不同 record 返回 `artifact_id_conflict`。Checkpoint 继续保留独立的 replace 语义。用 Barrier 制造并发，而不是依赖碰运气的时间窗口。

### FR1-P1：图 7 mobile group 存在显式 7px 来源标签逃逸

- 位置：`book/images/fig6-7-product-responsibility-map.svg:67-68`（commit `7ce99a9`）。
- 证据：现有测试只读取两个 CSS class 的字号，未遍历 mobile group 中显式 `font-size` 或其他 class/inherited 字号。OpenAI source labels 明写 `font-size="7"`；即使 group scale 后接近阈值，也没有达到声明的 source 8px 合同。
- 决定：接受。先加入可证明显式 7px 会失败的 fixture 回归，再让测试解析 mobile group 每个 `text` 的显式、class 与 inherited/default 字号；核心/来源分别按声明阈值验证。图 7 明确来源标签提升到至少 8px，并在 Chromium 两档复检。

### FR1-P2：删除回归引用使用了漂移且不准确的行范围

- 位置：本文件“接受的修改”第 4 项。
- 证据：`test_checkpoint_with_deleted_artifact_is_not_recoverable` 的定义位于 `chapter6/tests/test_persistence.py:164`，原引用范围 `:164-176` 没有覆盖完整断言，且后续插入并发测试后还会继续漂移。
- 决定：接受。改为稳定测试名引用，不再用脆弱范围代表完整证据。

### Fix round 1 接受的修改与验证

状态：**三项追加发现均已关闭；Task 12 未启动，继续等待复核接受。**

1. **并发不可变发布。** Artifact envelope 先在目标同目录完整写入并 `fsync`，再以 `os.link(temp, destination)` 执行原子 create-if-absent。胜者创建权威目标，输家读取并校验已经发布的 record：完全相同则幂等成功，否则返回 `artifact_id_conflict`；临时文件在 `finally` 清理。Checkpoint 继续走独立的 atomic-replace helper，并新增替换语义回归。正文把承诺限定为支持该原语的单机同文件系统，不外推到网络文件系统、对象存储或分布式事务。
2. **线程与进程 Barrier 证据。** RED 时，20/20 个线程 trial 与 3/3 个 Windows spawn 进程 trial 都观察到不同内容的两名 Writer 同时返回成功。GREEN 后，每个 trial 恰有一个成功、一个冲突，胜者内容保持不变；相同内容的并发 Writer 均幂等成功，最终 envelope 可解析且没有正常路径遗留 temp。冲突用例又独立重复运行三轮，全部通过。
3. **移动字号门禁补全。** 发布测试现在递归遍历图 2—7 mobile group 中的每个 `text`，解析显式 `font-size`、CSS class、inline style、祖先继承与 SVG 默认值；全部文字至少满足 source 8px，被标记为 core/title/system 或显式粗体的文字至少满足 core 10px，缩放继续使用 min-axis。合成回归同时覆盖 explicit/class/inline/inherited 7px 与 core class 9px 逃逸。图 7 两条 OpenAI 来源标签从 7px 提升为 8px，并在 Chromium 1200×675 与 390×219 复检无重叠或裁切。
4. **稳定证据引用。** 删除 Artifact 的证据已改为完整测试名 `PersistenceTest.test_checkpoint_with_deleted_artifact_is_not_recoverable`，不再引用漂移行范围。

最终门禁：Chapter 4/5/6 分别 24/63/140 个测试通过，共 227 个；publication gate 为 0 error；CJK 25,819、H2/H3 30、7 图、14 题/14 答案、6/6 脚注。固定报告两次临时生成与 canonical 生成的三个 SHA-256 仍分别为 JSON `50cbbc...6e5e`、Markdown `f05fba...e107`、JSONL `cbcc12...eb96`。`chapter6-v1.0-draft^{}` 仍指向 `4c71cdb`，没有 PDF、release tag 或 Task 12 文件。

## 11. Fix round 2：证据引用稳定化

状态：**完成。** “接受的修改”中的实现后证据已从当前文件行范围改为稳定符号、完整测试名和章节标题。首次 Review 的“原始位置”以及 Fix round 1 中绑定 commit `7ce99a9` 的历史位置继续保留，因为它们定位的是特定基线，而不是声称指向当前代码。本轮未修改实现、正文、图、报告、PDF 或版本标签。

## 12. Task 12：PDF 出版验收与 v1.0 发布

状态：**通过。** 使用仓库既有 Marked、离线 MathJax、Playwright 和 Microsoft Edge 渲染链生成 A4 预览，没有替换成简化 PDF 生成器。`previewConfig.chapter6` 与 `render:chapter6` 已进入自动门禁。最终 PDF 为 47 页、1,263,153 bytes，预览和不可变版本文件 SHA-256 均为 `211B722B74715C0C139BE4E70266327348DCF2833C61648E055AB8B30D072C1E`。

逐页 QA 记录如下，所有页面都以 1.75 倍栅格化 PNG 检查，并另外用 12 张 2x2 联系表核对跨页节奏：

| 页码 | 检查对象 | 结论 |
| --- | --- | --- |
| 1 | 封面标题、副标题、公式、4 项元数据、页眉页脚 | 无裁切、换行可读，元数据与出版合同一致 |
| 2-10 | 开场案例、章节桥接、图 1-2、状态边界表、Fixture、失败矩阵和实验合同 | 标题无孤行，表格与行内代码无横向溢出；第 10 页下半部留白用于避免把下一页完整实验卡拆开，不是空白页 |
| 11-16 | 实验 6-1 至 6-4、代码块和策略对比表 | 实验卡、命令、代码与表格均完整；长标识符正常换行，无剪裁 |
| 17-24 | 图 3-5、生命周期、Artifact 合同、提交顺序与 Rehydration | 3 张图桌面文字可读，箭头与图注正确；跨页代码和段落连续，无重复图注 |
| 25-34 | 压缩触发、Compact/Reset/Fork、图 6、五组实验、代际漂移与故障矩阵 | 表格表头、指标、failure reason 和图中 390px 声明均清晰，无黑块或重叠 |
| 35-44 | 图 7、产品责任表、成本安全、状态归位、Schema、恢复演练、Claims/Non-claims 和小结 | 图 7 与跨页产品表可读，续页表头存在；脚注引用 1-6 与正文对应，URL 未被裁切 |
| 45 | 14 道分层练习及 `chapter6/reference-answers.md` 引用 | 14 题全部可见，星级、编号和答案路径无错位 |
| 46 | 与第 7 章“记忆”的衔接 | 标题与完整段落同页；短桥接页是章节节奏选择，不是孤立标题或空白页 |
| 47 | 独立脚注页 | 6 条脚注双栏完整，链接可读，回链符号可见，无多余空白页 |

七图分别在第 4、7、17、18、21、28、35 页放大复核；所有图都没有文字裁切、错误切组或比例失真。第 35 页产品责任表跨到第 36 页时表头自动重现。PDF 文本层确认包含中文标题、`Event Log`、`CompactionArtifact`、`Context Rehydration` 和练习路径，没有原始 MathJax 包装、工具 token、占位符、Unicode replacement character、本机工作树路径或凭据。

最终发布门禁：Chapter 4/5/6 分别 24/63/140 项测试通过，共 227 项；Node 渲染门禁 5 项通过；固定报告 JSON、Markdown 和 JSONL Trace 连续生成两次且 SHA-256 分别保持 `50CBBC...6E5E`、`F05FBA...E107`、`CBCC12...EB96`；publication gate 为 0 error；`git diff --check` 通过。`chapter6-v1.0-draft` 未移动，正式版本由 annotated tag `book-chapter6-v1.0` 保存。

## 13. Task 12 fix round 1：v1.0.1 补丁发布

状态：**通过。** 历史决定是保留 v1.0 的 PDF、源码 commit 和 `book-chapter6-v1.0` annotated tag，不移动、不删除、不覆盖。v1.0 在版本台账中标记为 superseded；修订结果以新的不可变 PDF 与 `book-chapter6-v1.0.1` 发布。

### RED 与修复

本轮新增三项发布测试后，首次定向运行共有 3 项失败：补丁 PDF 尚不存在，HTML 仍包含绝对 `<base>` 与作者工作树位置，历史 PDF 与补丁 PDF 的保留关系也无法成立。对 v1.0 PDF annotation 对象的独立扫描确认共有 26 个 URI，其中 16 个是作者本机文件链接，另外 10 个是外部链接。这不是文本层误报，而是 PDF 对象中的真实可点击动作。

修订采用既有 Marked、离线 MathJax、Playwright 与 Microsoft Edge 链：

- `previewConfig.chapter6` 测试现在解析并求值精确对象，再对 `chapter6` 子对象做结构比较，不再依赖任意位置的字符串命中；
- 渲染时将本地 Markdown 链接输出为 `.local-reference` span，保留仓库路径文字但不生成点击动作；外部 HTTPS、HTTP、`mailto:` 与页内锚点仍保留为链接；
- 图片源改为相对 `../../book/images/...`，发布 HTML 移除 `<base>`、绝对 stylesheet/script 路径和运行时 script；MathJax 仍从锁定本地依赖注入浏览器后再生成静态 HTML；
- 搬迁测试把 HTML 与七张 SVG 复制到新的临时仓库形目录，确认所有图片相对路径仍解析；PDF 测试解析 annotation `/URI` 对象，不能只搜文本层；
- 第 23 页的独立粗体段首与正文合并，第 45 页的小结末段收束。H2/H3 仍为 30，没有为版式修复改写章节结构。

GREEN 后，3 项补丁发布测试全部通过。替代 PDF 有 23 个 annotation，其中 10 个 URI 全部为外部 HTTPS，其余为页内动作；本机文件 URI、盘符路径和作者工作树 URI 均为 0。发布 HTML 中没有 `<base>` 或作者本机路径，且恰有 7 个 figure。

### 替代 PDF 全页复核

替代版仍为 47 页。所有页面按 1.75 倍栅格化，并通过 12 张 2x2 联系表逐页检查；高风险页 22-24 与 43-47 又单独放大检查。最终冻结渲染与这 47 张已人工目检 PNG 逐页像素一致。

| 页码 | 修订后结论 |
| --- | --- |
| 1 | 封面标题、副标题、公式、四项元数据、页眉页脚均完整。 |
| 2-10 | 开场、章节桥接、图 1-2、状态表、Fixture 与实验合同无裁切、孤题或异常空页。 |
| 11-16 | 实验 6-1 至 6-4、命令、代码和表格无横向溢出。 |
| 17-21 | 图 3-5、生命周期与 Artifact 合同文字和箭头可读。 |
| 22-24 | 提交顺序与 Rehydration 连续；原第 23 页独立粗体段首不再单独悬挂，修订段在第 24 页以粗体段首和正文同段出现。 |
| 25-34 | 压缩触发、Compact/Reset/Fork、图 6、五组实验、漂移与故障矩阵无重叠或黑块。 |
| 35-42 | 图 7、产品责任表、成本、安全、状态与 Schema 章节可读；跨页表头正确重复。 |
| 43-44 | Claims/Non-claims 与小结完整；原本落到第 45 页的孤行已经回收到第 44 页。 |
| 45 | 直接以分层练习标题开始，14 题与参考答案路径完整。 |
| 46 | 第 7 章桥接标题和完整段落同页；是短桥接页，不是空白或孤题页。 |
| 47 | 6 条脚注独立双栏排版，10 个外部 HTTPS 目标可读，无裁切。 |

### 冻结证据

- 替代 PDF：47 页，1,258,233 bytes，预览和 v1.0.1 不可变文件 SHA-256 均为 `15B08A2679710CE06E0115C46A9457648F782215448F8B03BC28FADF42C73000`；
- 可移植 HTML：151,994 bytes，SHA-256 `F614F4FA6FB824C61954214165CFAE6DE0A0821653FCD39F3F73885F64B6610C`；
- Chapter 4/5/6 分别 24/63/143 项 Python 测试通过，共 230 项；Node 渲染门禁 5 项通过；publication gate 为 0 error；
- 固定报告 run A、run B 与 canonical 三方字节一致，JSON、Markdown、JSONL Trace 的 SHA-256 分别仍为 `50CBBC74C8D938D619DAB131F8D37BBB8443162C1FEA74233C90FD6EB3686E5E`、`F05FBA8F7A4EF7177EA7FE1B1FA18F8CC7528BD9D806D0FEEB1AFF86F87CE107`、`CBCC12216DF02182D9E5B4F64A3A1B29EF9554140877E33CBC986FE69604EB96`；
- PDF 47 页文本层均非空，包含标题、Event Log、CompactionArtifact、Context Rehydration 与答案路径；无 replacement character、原始 TeX 包装、工具 token、占位符、本机路径或 Secret 模式；
- v1.0 历史 PDF 仍为 1,263,153 bytes，SHA-256 `211B722B74715C0C139BE4E70266327348DCF2833C61648E055AB8B30D072C1E`。
