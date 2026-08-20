# 第 6 章练习参考答案

答案用于核对推理过程，不要求逐字照抄。涉及代码的题目应先增加失败测试，再修改实现；所有离线数字以 [`reports/context-continuity.json`](./reports/context-continuity.json) 为准。

## 基础题 1：双连续性边界

**预期推理：** 执行连续性回答“Runtime 从哪个步骤继续”，对应 `RunCheckpoint.next_step`、游标和 Workspace 版本；语义连续性回答“模型带着哪些目标、约束、决定、失败与证据继续”，对应 Artifact、Working Set 与 Rehydration。要分开两个证据：开场的 `run-tests` 是策略消融，它保留 Goal 与公共签名约束，却拿掉被否定假设和失败验证，所以进入 `repeat_rounding_attempt`；固定报告的 `checkpoint-only-v1` 在事件 24 声明 `next_step=apply-compatible-patch`，只得到 Goal 锚点，决策为 `unsafe_signature_change`。二者都是“执行点存在、语义不足”，但不是同一记录。反向例子是语义字段仍在一段文本里，却没有可提交 Checkpoint，进程退出后不知道从哪个节点恢复。

**常见错误：** 把两者都解释为“保存聊天记录”，或把 `resume_correct` 当作业务副作用 exactly-once。

**可检查验收：** 答案必须分别给出“位置/步骤”和“目标/约束/未决状态”两个问题；同时写出开场消融的 `run-tests → repeat_rounding_attempt` 和固定报告的 `apply-compatible-patch → unsafe_signature_change`，不得另造不存在的步骤名。

## 基础题 2：七个状态表面

**预期推理：** 目标在当前调用进入 ContextPacket，跨压缩副本进入 CompactionArtifact，原始来源留在 Event Log；最新失败需要高分辨率留在 Working Set；源代码属于 Workspace；恢复游标属于 RunCheckpoint；跨独立任务仍需复用且经过治理的偏好才是 Memory 候选。Session/History 保存交互生命周期，但并不自动拥有上述真实状态。

**常见错误：** 因为某条信息“很重要”就同时复制到所有状态，忽略所有者、生命周期、验证和删除合同。

**可检查验收：** 五类信息均有唯一主所有者；至少解释一次“文件存在不等于模型已看见”和“History 存在不等于可以恢复执行”。

## 基础题 3：Artifact 不变量

**预期推理：** 至少应列出 Goal、acceptance criteria、constraints、decisions、rejected hypotheses、open issues、verification state、evidence locators、next intent 中六类，并补充来源范围、Source Digest、Workspace Digest 和 Schema 版本。Open Issue 是待解决状态；若混入“进度良好”的自然语言，压缩器可能把失败改写成完成，无法做字段级对账。

**常见错误：** 只列 `summary`、`created_at` 和文件路径，或者认为“语句里提到失败”就等于结构化保留。

**可检查验收：** 六类语义字段必须可独立枚举；Open Issue 必须带来源事件，且不能被 `verification_state=passed` 隐式覆盖。

## 基础题 4：Compact 与 Reset

**预期推理：** Compact 在同一任务中用较小制品替换旧历史；Reset 开新窗口；Fork 复制某一历史点形成分支；Subagent Isolation 使用隔离 Context 执行受限子任务；按需重载从受控来源取回证据。Reset 不继承隐含会话线索，所以 handoff 必须显式包含目标、验收、约束、决定、失败、Workspace 版本和下一动作。

**常见错误：** 把 Fork 写成 Workspace 的自动复制，或认为 Subagent 返回天然可信。

**可检查验收：** 五种动作分别写出“保留什么”和“一项新增风险”；Reset 的交接字段不少于六类。

## 实验题 5：复现五组报告

**预期推理：** 从仓库根目录运行两次离线生成，把第一次产物复制到临时目录，再逐文件比较。命令：

```powershell
python -m chapter6.experiments.run_all --output chapter6/reports
$first = Get-ChildItem chapter6/reports/context-continuity* | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{ Name = $_.Name; Hash = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash }
}
python -m chapter6.experiments.run_all --output chapter6/reports
$second = Get-ChildItem chapter6/reports/context-continuity* | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{ Name = $_.Name; Hash = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash }
}
$difference = Compare-Object $first $second -Property Name,Hash
if ($difference) { $difference | Format-Table; throw 'Chapter 6 reports are not byte-identical' }
$second | Format-Table -AutoSize
```

预期 `$difference` 为空，三个文件的 SHA-256 分别保持：JSON `50CBBC74C8D938D619DAB131F8D37BBB8443162C1FEA74233C90FD6EB3686E5E`，Markdown `F05FBA8F7A4EF7177EA7FE1B1FA18F8CC7528BD9D806D0FEEB1AFF86F87CE107`，JSONL Trace `CBCC12216DF02182D9E5B4F64A3A1B29EF9554140877E33CBC986FE69604EB96`。JSON 中 15 个 case 的 `sample_count` 都为 1，未测字段为 `null`，Markdown 显示为 `—`。

**常见错误：** 只比较控制台文本，或把 `null` 改成 0 后再声称“恢复失败”。

**可检查验收：** 保存三个文件的字节比较证据；报告 `run_status=passed`，且没有把 `serialized_bytes` 称为 Provider Token。

## 实验题 6：滑动窗口消融

**预期推理：** 先在 [`tests/test_experiments.py`](./tests/test_experiments.py) 增加一个声明窗口边界与预期可见 key 的失败测试，再调整实验参数或新增变体。运行：

```powershell
python -m unittest chapter6.tests.test_experiments -v
python -m chapter6.experiments.run_all --output chapter6/reports
$report = Get-Content -Raw chapter6/reports/context-continuity.json | ConvertFrom-Json
$report.cases | Where-Object experiment -eq 'sliding_window' | Format-List
```

当前八事件基线预期 `constraint_retention=0.5`、`open_issue_retention=0.0`，决策为 `unsafe_signature_change`。扩大窗口后，应报告公共签名约束第一次重新出现的具体事件边界，而不是笼统写“窗口越大越好”。

**常见错误：** 修改固定基线却不更新期望，或把规范化 UTF-8 字节阈值写成 Token 阈值。

**可检查验收：** 提交前后各有一个可复现测试结果；记录窗口、visible keys、constraint retention 和 decision kind。

## 实验题 7：Checkpoint-only 对照

**预期推理：** 命令：

```powershell
python -m chapter6.experiments.run_all --output chapter6/reports
$report = Get-Content -Raw chapter6/reports/context-continuity.json | ConvertFrom-Json
$report.cases | Where-Object experiment -eq 'checkpoint_vs_rehydration' | Format-List
python -m unittest chapter6.tests.test_rehydrator chapter6.tests.test_experiments -v
```

预期 checkpoint-only 为 583 B、约束保留 0.0，Packet、恢复和重复工作均未测；rehydrated 为 3,447 B、约束保留 1.0、`resume_correct=true`、`duplicate_work_count=0`、`packet_contract_passed=true`。前者不是“恢复失败”的统计样本，而是只测声明下一步的控制组。

**常见错误：** 把 checkpoint-only 中的未测字段当作 false，或比较两个变体的单一总分。

**可检查验收：** 四类指标逐项列出，`null` 保持未测；能够解释两个变体为何共享 Checkpoint 却得到不同下一动作。

## 实验题 8：故障注入

**预期推理：** 运行：

```powershell
python -m chapter6.experiments.run_all --output chapter6/reports
$report = Get-Content -Raw chapter6/reports/context-continuity.json | ConvertFrom-Json
$report.cases | Where-Object experiment -eq 'failure_matrix' | Format-Table variant,decision_kind
python -m unittest chapter6.tests.test_rehydrator chapter6.tests.test_experiments -v
```

预期 Workspace 变体得到 `rejected_stale_workspace_digest`，未知 Schema 得到 `rejected_artifact_schema`，来源损坏得到 `rejected_artifact_source_digest_mismatch`。三者都应在 `ContextBuilder.build()` 前结束，不返回半份 Packet。

**常见错误：** 捕获所有异常后统一返回空摘要，导致原因消失并让下游继续运行。

**可检查验收：** 三个 reason code 均在报告或 Trace 中出现；测试能证明 Builder 未被调用或没有 Packet 产出；日志不含 Secret 正文。

## 实验题 9：多代漂移

**预期推理：** 运行：

```powershell
python -m chapter6.experiments.run_all --output chapter6/reports
$report = Get-Content -Raw chapter6/reports/context-continuity.json | ConvertFrom-Json
$report.cases | Where-Object experiment -eq 'generational_drift' | Format-List
python -m unittest chapter6.tests.test_experiments chapter6.tests.test_compaction -v
```

当前第一代摘要为 843 B，第二代为 16 B，后者只保留目标 key；结构化变体从冻结 Event Log 重新生成，为 3,579 B 且字段完整、字节稳定。第三代测试应对第二代结果再执行一个显式、确定性的变换，并声明预期 key；它用于展示规则的累积损失，不模拟真实模型平均表现。

**常见错误：** 把每代都从原始 Event Log 生成，却称为 summary-of-summary；或只比较长度不检查字段。

**可检查验收：** 测试同时断言来源、可见 key、至少三项保留率和字节稳定性；正文结论仍限定在受控变换。

## 设计与批判题 10：生产压缩策略

**预期推理：** 阶段边界优先在稳定步骤后生成 Artifact；阈值作为硬兜底，并预留一次压缩调用和输出空间；空闲时间只预压缩已冻结游标。防抖可使用高低水位或最短间隔，失败时继续使用最近已提交 Checkpoint/Artifact，不能引用孤儿制品。慢工具完成前后要区分 pending receipt 与已观察结果。

**常见错误：** 用“每十轮压缩”替代任务阶段，或压缩失败后覆盖最后有效恢复点。

**可检查验收：** 方案含三类触发、一个防抖机制、明确预算余量、失败回退和至少两个监控指标；未把教学字节数当作生产 Token 阈值。

## 设计与批判题 11：Secret 与来源污染

**预期推理：** 恶意工具输出保留 `authority=NONE` 与不可信 provenance，不能因为被摘要改写就升级；Secret 在进入模型和 Artifact 前最小化，执行凭据只在受信 Runtime 注入；lifecycle Trace 只写原因码、稳定标识与必要 Digest；Action Gateway 仍重新校验工具提议和资源范围。四层分别保护身份、泄漏、审计与副作用。

**常见错误：** 依赖摘要 Prompt 删除 Secret，或认为 Trace 脱敏就能替代执行沙箱。

**可检查验收：** Fixture、Packet、Artifact、Trace、异常和报告中均不存在 Secret 正文；恶意内容 authority 不变；危险提议在 Gateway 被拒绝并留下原因码。

## 设计与批判题 12：多分支 Workspace

**预期推理：** Fork 应绑定独立 branch/worktree 或不可冲突的命名空间；每个分支拥有自己的 run、event cursor、Workspace Digest、Artifact 与 Checkpoint。父任务只接收带来源、基准提交和验证证据的子结果。合并后计算新的 Workspace Digest，旧分支 Locator 全部重新验证，冲突未解决前不得沿用旧 Artifact 宣布完成。

**常见错误：** 两个 Agent 共用同一工作目录和 `artifact_id`，只靠聊天约定避免覆盖。

**可检查验收：** 图或状态表明确两条分支的唯一标识、提交关系、合并门禁和 stale 处理；至少包含一次冲突与回退路径。

## 设计与批判题 13：产品映射审查

**预期推理：** 八个维度是历史所有者、压缩触发者、压缩产物、执行恢复状态、语义重建来源、跨任务状态、可观测证据和已知限制。每项先写官方文档公开事实，再单列自己的工程推断；查不到的项写“未公开/未测”，不能用本书 Artifact 字段补空。

**常见错误：** 把产品、API、SDK 和框架混为同一层，最后得出能力或可靠性排名。

**可检查验收：** 八行均有直接官方链接和核对日期；推断使用明确措辞；没有产品总分、排名或未来源化的内部实现描述。

## 设计与批判题 14：Memory 候选评审

**预期推理：** “本次失败测试”属于当前 RunState/Artifact，不升为 Memory 候选；“临时根因假设”在未验证前只属于事件与 Working Set；“仓库兼容规则”优先进入版本化仓库文件；“用户偏好”若未来独立任务仍需复用、来源与作用域明确，可以标记为第 7 章继续评审的 Memory 候选。第 6 章在候选判断处停止，不设计 Write、Recall、Forget 或 Correct。

**常见错误：** 把所有压缩摘要自动写入向量库，导致猜测、失败状态和敏感信息跨任务传播。

**可检查验收：** 四条信息分别给出当前所有者、当前生命周期、验证状态和“是否成为候选”的结论；至少一条被明确拒绝成为 Memory 候选，并且答案不提前实现候选的写入、召回、遗忘或纠错流程。
