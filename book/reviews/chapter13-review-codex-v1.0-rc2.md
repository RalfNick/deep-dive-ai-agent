# 第 13 章 v1.0-rc2 双视角复审报告

复审日期：2026-09-26。对象：`book/chapter13.md`、`chapter13/` 实验包、稳定报告 Schema、来源台账、7 幅插图和本地预览。基线：本地 rc1 提交 `74e143d38cb21669b6bf2cce05626a14830de69e`。结论：**GO，可作为更严格的本地候选；本轮不推送、不发布。**

## 本轮复审结论

rc1 已经建立了“最终回复不等于真实结果”的主线，但复审发现有六处证据链仍可加强：数据集 `split` 只是元数据、测试没有真正调用 JSON Schema 校验器、规范 Bootstrap 样本过于整齐、轨迹评分依赖数组位置、任务边界缺少构造期校验，以及 Live Judge 没有收束 Provider 返回值。

这些问题均已修复，并由失败先行测试覆盖。正文主线、12 个任务、7 幅图和 14 道练习没有扩张；修改集中在“让书中声称的评估边界真的由代码和报告执行”。

| 优先级 | 复审发现 | rc2 修订 | 验证证据 |
| --- | --- | --- | --- |
| P1 | `capability / regression / adversarial` 只写进任务元数据，没有进入指标视图或门禁 | 报告新增三类用途视图与 `split_deltas`；Regression 任一下降即阻断发布，Capability 只作为趋势信号 | `test_experiments.py` 与 `test_grading.py` 覆盖三类精确结果和回归下降 |
| P1 | Schema 虽完整，但 pytest 主要在比较 Python 对象，没有证明真实 JSON 可被标准校验器接受 | 锁定 `jsonschema==4.26.0`，用 Draft 2020-12 校验规范报告和正反例 | 错误类型、非法状态、嵌套未知字段和越界差值均被拒绝 |
| P1 | 规范样本的 12 个任务差值全是 20%，Bootstrap 区间必然退化为 `[20%, 20%]` | 保留计分结果，同时增加不参与门禁的异质差值示例，均值 1.67%，95% 区间 `[-5.83%, 9.17%]` | 固定种子 10,000 次重复抽样，区间跨零并标记 `inconclusive` |
| P1 | Trajectory Grader 只依赖事件数组位置，没有验证 Trace 的 `seq` 合同 | 要求 `seq` 为严格递增整数，再判断 observed、write_applied、verification_passed 的因果顺序 | 非单调序列返回 `invalid_event_sequence` |
| P2 | `TaskSpec` 可接受未知 split、绝对路径和 `..` 路径 | 构造期校验 split、允许写入前缀和保护路径；不安全输入 fail-fast | 新增未知 split 与不安全路径反例 |
| P2 | Live Judge 返回原始 Provider 包络，调用者仍需自行猜测字段和标签 | 解析 OpenAI-compatible `choices[0].message.content`，只接受合法 label 与字符串证据列表 | 有效包络解析成功；非法 label、缺失 evidence 和空 choices 均失败关闭 |

## 读者视角

### 本轮改善

1. “任务切片”与“数据用途”不再混为一谈。读者可以先按 basic、edge、safety、recovery 看能力差异，再按 capability、regression、adversarial 决定这些任务如何进入开发流程。
2. Bootstrap 不再只有一个看似过于完美的区间。正文同时展示确定性教学结果与跨零示例，读者能直观看到“有正向均值”为什么仍可能只能得出 `inconclusive`。
3. 报告中的三类用途视图、门禁原因和正文中的发布规则一一对应，读者不必在 prose 与 JSON 之间猜测隐含逻辑。
4. Live Judge 的示例边界更清楚：Provider 响应必须先被解析成小而稳定的本地合同，不能把外部响应格式直接扩散到整套评估系统。

### 可读性判断

正文现有 23,430 个字符，23 个二级标题与 7 个三级标题。新增内容没有引入新的长支线，仍沿着“假成功—证据阶梯—可靠结论—开发门禁”推进。统计部分先给直觉和手算，再给公式与代码；Schema、Judge 和平台映射仍是辅助证据，没有把本章写成工具手册。

## AI 与评估专家视角

### 证据链完整性

- Task 入口现在拒绝未知用途和不安全相对路径，评测夹具不能悄悄扩大文件边界。
- Trial 的事件顺序由显式 `seq` 约束，而不是偶然依赖 JSON 数组顺序。
- Stable Report 从 `chapter13.eval.v1` 升级为 `chapter13.eval.v2`；v1 Schema 保留，v2 新增 split 视图、用途差值和异质 Bootstrap 诊断。
- Release Gate 保持安全、环境与总体退化硬门禁，并新增 Regression 用途零容忍退化。Capability 仍只报告，不用一个任意阈值制造“能力提升”的确定性。
- Schema 验证成为测试的一部分，而不是仅靠人工阅读 JSON 文件。
- Live Judge 仍为显式可选路径，但它的输出先经过本地合同验证；无效响应不会静默变成评分结果。

### 统计解释

规范 baseline/candidate 教学策略在 12 个任务上的差值仍全部为 20 个百分点，因此任务级 Bootstrap 区间 `[20%, 20%]` 是数据的真实结果，不是算法错误。rc2 没有篡改这组计分证据，而是增加一组明确标记为“不参与发布门禁”的异质差值，用来演示小样本下点估计为正、区间仍跨零的情形。这比为了得到漂亮区间而修改任务结果更诚实。

## 验证证据

| 验证 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -B -m pytest chapter13/tests -q` | 38 项通过 |
| 双目录完整实验 | JSON、Markdown、5 组报告和 manifest 逐字节一致 |
| JSON Schema Draft 2020-12 | 规范报告通过；4 类无效变体拒绝；合法负差值通过 |
| 规范报告 | `chapter13.eval.v2`；三类 split 差值均为 0.20；发布结论 `pass` |
| 非计分 Bootstrap 示例 | 均值 1.67%，95% 区间 `[-5.83%, 9.17%]`，结论 `inconclusive` |
| 桌面预览 | 1440px，7/7 图片加载，0 失效锚点，无整页横向溢出 |
| 移动预览 | 390px，7/7 图片加载，图与表局部横向滚动，无整页横向溢出 |
| `.venv\Scripts\python.exe -B -m unittest discover -s tests -q` | 43 项通过 |
| 仓库检查与严格构建 | `scripts.check_repository`、`scripts.build_site`、`mkdocs build --strict` 通过 |
| 公开清单核对 | `site/book/chapter13/index.html` 与 `_web/book/chapter13.md` 均不存在 |

## 仍然成立的限制

- Baseline 与 Candidate 是确定性教学策略，不是真实模型、Claude Code、Codex 或框架能力实验。
- Sentinel 不运行真实 Markdown 解析器、仓库测试进程或敌对代码；目录约束不等同于生产沙箱。
- 12 个任务无法代表生产任务分布；两组 Bootstrap 都只说明给定任务差值的抽样不确定性。
- 异质 Bootstrap 示例是统计教学探针，不进入发布结论；它不能补偿任务代表性不足。
- Judge 标签未经第二位人工评审者独立复核，Live Judge 也未在规范运行中调用网络或真实 Provider。
- OpenAI Evals、LangSmith 与 Inspect AI 只做责任映射，没有进行平台兼容性或性能比较。

## 最终判断

rc2 修复了本轮发现的全部 P1/P2 问题，没有剩余 P0/P1。正文中的关键主张现在分别由任务合同、评分器、稳定 Schema、规范报告和自动测试支撑。它可以作为第 13 章更可靠的本地候选，但仍不等于已经发布，也不能用教学数字评价任何真实 Agent 产品。
