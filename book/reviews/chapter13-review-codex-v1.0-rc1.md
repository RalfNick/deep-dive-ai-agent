# 第 13 章 v1.0-rc1 双视角审稿报告

审稿日期：2026-09-24。对象：`book/chapter13.md`、`chapter13/` 实验包、7 幅插图、来源台账和本地预览。结论：**GO，可作为本地发布候选；本轮不推送、不发布。**

## 结构核对

- 正文 22,987 个字符，23 个二级标题、7 个三级标题，共 30 个二至三级标题。
- 5 组递进实验、12 个教学任务、4 个任务切片、14 道分层练习。
- 7 幅原创图、6 张比较表；正文图号顺序与引用一致。
- 主线遵循“假成功—证据阶梯—可靠结论—开发门禁”，没有提前展开第 14 章的公共 Benchmark、生产 Trace 平台和线上成本诊断。

## 读者视角

### 有效之处

1. 开篇用“同一句修复完成、不同结果与轨迹”建立冲突，读者不必先理解评估术语。
2. Task、Trial、Outcome、Trajectory、Grader、Evaluation Harness 和 Suite 都在第一次实验附近定义，并能回到真实代码路径。
3. `pass@k` 与 `pass^k` 先用五次试验手算，再进入全量报告；图 13-4 同时呈现“至少一次成功”和“每次都成功”，降低了公式阅读门槛。
4. 正文不把 55% 与 75% 写成模型排名，而是反复声明其为固定教学策略产生的信号。
5. 运行路径、报告阅读顺序、参考答案和证据边界都在读者真正需要的位置出现。

### 已修复问题

| 优先级 | 原问题 | 修订结果 |
| --- | --- | --- |
| P1 | Markdown 报告过于简略，无法独立审阅 | 加入 suite、subjects、environment、grader、gate、公式、切片、失败索引、Judge 校准和排除项 |
| P1 | 开篇可能让读者误以为实验运行了真实 Markdown 解析器 | 在第一次实验前披露 Sentinel 的真实边界：真实目录、写入、摘要与评分器，但没有真实解析器或测试进程 |
| P1 | OOM 示例混淆 Trial 状态与 Grader 的 `unknown` | 改为先归因，再设置 `environment_error` 或 `agent_failed`；`unknown` 只属于评分结论 |
| P1 | 练习 7、11 只返回预设答案 | 改为真实构造 Trial、修改 Judge 预测并执行对应评分与矩阵比较 |
| P1 | fresh clone 后的命令没有激活虚拟环境 | README、正文和答案均加入 `Activate.ps1`，同时提供显式解释器回退 |
| P2 | 移动端技术图缩得过小 | 390px 视口内使用 760px 图宽和图内横向滚动，并给出滑动提示 |
| P2 | Markdown 报告显示 Python `None` 且省略门禁原因 | 改为 JSON `null`，并展示 release decision 的 reasons |

## AI 与评估专家视角

### 有效之处

1. Evaluation Harness 与 Agent Harness 的职责分离清楚：前者设计任务、重复运行、评分、聚合和决策，后者负责单次任务运行。
2. 能力分母排除了 `environment_error` 与 `invalid`，但发布门禁对两者 fail-closed，避免把基础设施故障误算成能力下降或直接忽略。
3. Outcome、Trajectory、Safety 和 Efficiency 四类评分器分别保留证据，安全违规不被平均分抵消。
4. Safety Grader 同时核对允许写入范围、受保护路径摘要、工作区 containment 与策略事件；缺少完整性或 containment 证据时失败，而不是放行。
5. 多次试验同时报告 `pass@1`、`pass@3` 和 `pass^3`；任务级成对 Bootstrap 使用固定种子，并明确只描述当前 12 个任务的差值不确定性。
6. Judge 校准报告 agreement、coverage、answered-only accuracy、Unknown 和混淆矩阵；固定标签被准确限定为未经独立人工复核的编辑教学夹具。
7. 稳定 JSON 包含版本化 Schema、环境指纹、suite 摘要、被测对象、grader/gate/formula provenance 和显式失败清单。

### 已修复问题

| 优先级 | 原问题 | 修订结果 |
| --- | --- | --- |
| P1 | 环境错误进入能力分母；可用次数少于 k 时指标不成立 | 排除环境/无效记录，`usable < k` 时返回 `null`，任一侧环境错误或无效记录阻断发布 |
| P1 | Safety Grader 没有真正使用允许路径，缺证据时可能放行 | 使用任务边界与保护路径，路径归一化，缺失完整性/containment 证据时 fail-closed |
| P1 | Judge fixture 被误写成独立人工金标，且只给总体一致率 | 改为编辑教学标签，补 coverage 与 answered-only accuracy |
| P1 | 报告缺少来源和决策合同 | 补 suite hash、subjects、environment、graders、gate、公式与限制 |
| P1 | Schema 只限制顶层，嵌套对象和状态可漂移 | 为所有稳定嵌套对象设置类型、枚举、必填字段和 `additionalProperties: false`；差值另用 [-1,1] 的 `deltaMap` |
| P2 | 固定种子没有影响确定性成功日程 | 使用基于 SHA 的固定排序选择成功种子，并验证 trial index/seed 配对 |
| P2 | Bootstrap 结论容易被读成总体模型不确定性 | 正文明确它是当前五次试验聚合后的任务级区间，不传播任务内随机不确定性 |

## 验证证据

- 第 13 章测试：33 项通过。
- 全书现有单元回归：43 项通过；仓库检查通过。
- 两个独立输出目录中的 JSON、Markdown、五组报告和 manifest 逐字节一致。
- JSON Schema：规范报告通过；错误类型、非法状态、嵌套未知字段和小于 -1 的差值被拒绝；合法的 -0.12 差值通过。
- 预览：1440px 与 390px 均加载 7/7 图片，0 个失效锚点，无整页横向溢出；宽表格和移动端图在局部容器滚动。
- 严格站点构建通过；`site/book/chapter13/index.html` 与 `_web/book/chapter13.md` 均不存在，第 13 章没有进入公开 allowlist。

## 仍然成立的限制

- 两种被测策略是确定性教学夹具，不是真实模型、Claude Code、Codex 或框架能力实验。
- Sentinel 使用真实临时目录、文件写入和摘要，但不运行真实 Markdown 解析器、仓库测试进程或敌对代码。
- 工作区边界是教学级目录约束，不是容器、虚拟机或生产沙箱。
- Judge 标签未经第二位人工评审者独立复核，本章只证明校准协议可运行。
- 12 道任务不代表生产任务分布；Bootstrap 区间不能替代外部代表性验证。
- 图 13-4/13-5 的内部资产前缀沿用生成顺序，与读者可见图号不同；不影响渲染和引用，后续统一资产命名时再处理。

## 最终判断

正文、实验、统计、图示和证据边界相互一致，没有剩余 P0/P1。第 13 章达到了本地 `v1.0-rc1` 候选标准，但“可作为本地候选”不等于“已发布”，也不等于这些教学数字能够评价任何真实 Agent 产品。
