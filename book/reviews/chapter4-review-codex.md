# 第 4 章 Review：Harness Engineering

Review 日期：2026-08-12。

Review 对象：

- `book/chapter4.md`
- `chapter4/harness/`
- `chapter4/experiments/`
- `chapter4/tests/`
- `chapter4/reports/harness-ablation.json`
- `chapter4/reference-answers.md`
- `book/sources/chapter4-sources.md`

## 总体结论

第四章方向合理、叙事成立，但目前应判定为**条件通过**，还不建议视为完成复审。

章节的主问题、贯穿案例、概念边界和产品映射已经具备正式书稿质量。主要问题不在知识结构，而在几处“正文结论强于实验实际证明”：审批恢复实验没有真正进入 Receipt 去重分支；所谓消融实验实际由多个不同边界案例组成；状态图和审批版本绑定包含尚未实现的能力；教学路径守卫被命名成了 Sandbox。

综合评价约为 **7.5/10**。完成本文列出的 P1 修改后，可以继续进入复审。

## 验证结果

本次实际运行：

```powershell
python -m pytest chapter4/tests chapter3/tests -q
python chapter4/experiments/inline_loop_demo.py
python chapter4/experiments/permissions_sandbox_demo.py
python chapter4/experiments/approval_resume_demo.py
python chapter4/experiments/failure_semantics_demo.py
python chapter4/experiments/ablation_demo.py --output chapter4/reports/harness-ablation.json
```

结果：

- 第 4 章 21 项测试通过；
- 第 3 章 6 项回归测试通过；
- 共 27 项测试通过；
- 5 组实验均正常退出；
- 消融 JSON 可以由当前代码重新生成；
- 8 个 SVG 均可通过 XML 解析；
- 正文约 2.75 万字符，包含 39 个二、三级标题、8 张图和 15 道正文练习。

测试全绿说明代码满足现有测试合同，但不能消除下面的论证与实现不一致。

## P1：必须修改

### 1. 审批恢复实验没有真正证明 Receipt 去重

正文把“两次 `resume` 后只写一次”归因于执行回执：

- `book/chapter4.md:420`
- `book/chapter4.md:431`
- `chapter4/README.md:66`

但第二次调用 `resume` 时，检查点中的运行状态已经是 `COMPLETED`。运行时在发现状态不是 `WAITING_APPROVAL` 后直接返回：

- `chapter4/harness/runtime.py:111`
- `chapter4/harness/runtime.py:113`

因此第二次恢复没有执行到 `_execute_with_receipt()`，也没有查询 Receipt。当前实验实际证明的是：

> 已完成运行再次恢复时，不会重新执行。

它没有证明：

> 动作已经执行并保存回执、但最终状态尚未落盘时，恢复能够依靠 Receipt 避免重复副作用。

#### 建议修改

增加一个明确的崩溃注入点：

```text
执行副作用
  → 保存 Receipt
  → 模拟进程崩溃
  → 保留旧的 WAITING_APPROVAL Checkpoint
  → 创建新 Runtime 并恢复
  → 查询 Receipt
  → 发出 action_deduplicated
  → 写入次数仍为 1
```

测试除了断言 `write_count == 1`，还必须断言出现 `action_deduplicated`，并证明恢复路径确实查询了已有回执。

### 2. 当前“消融实验”实际上是多个边界故障案例

正文已经说明各变体不是同一条生产轨迹：

- `book/chapter4.md:622`

但章节标题、图表和 README 仍容易让读者理解为“固定任务、固定决策，只移除一个组件”。实际实现如下：

- `without_policy` 改成读取 `.env`；
- `without_checkpoint` 通过删除检查点模拟恢复失败；
- `without_receipts` 直接执行两次不同的补丁；
- `without_verifier` 只运行一个过早 final；
- `without_trace` 没有运行真正的无 Trace Runtime，而是复制完整 Harness 指标后将 Trace 完整率设为 `0.0`。

相关实现：

- `chapter4/harness/reporting.py:120`
- `chapter4/harness/reporting.py:187`
- `chapter4/harness/reporting.py:216`
- `chapter4/harness/reporting.py:248`
- `chapter4/harness/reporting.py:281`

这组实验可以证明不同合同各自会怎样失败，但不是严格意义上的单变量消融。

#### 建议修改

优先采用下面两种方案之一。

**方案 A：改名。**

将“消融实验”改为“边界故障实验矩阵”或“责任缺失实验矩阵”。每一行只回答一个明确的边界问题，不再暗示各行来自完全相同的轨迹。

**方案 B：实现严格消融。**

所有变体运行相同任务、相同初始仓库、相同决策序列和相同工具参数，只通过能力开关移除 Policy、Checkpoint、Receipt、Verifier 或 Recorder。

另外，每个指标现在通常只有一个确定性案例，使用 `acceptance_rate=1.0` 容易被理解为统计结果。建议改为：

- `accepted: true/false`；
- `false_completed: true/false`；
- `recovery_succeeded: true/false`；
- `trace_contract_passed: true/false`。

如果保留“率”，至少同时报告 `passed/total` 和样本数。

### 3. 状态图和审批版本绑定超出了当前实现

正文状态机包含 `VERIFYING`：

- `book/chapter4.md:346`
- `book/chapter4.md:351`

但 `RunStatus` 没有 `VERIFYING`：

- `chapter4/harness/contracts.py:9`

审批时序图还写有：

```text
approval_requested(state_digest, action_id)
```

实际 `approval_requested` 事件只记录 `action_id`：

- `chapter4/harness/runtime.py:224`

暂停前 `RunState.state_digest` 也没有保存当前环境摘要，恢复时不会检查环境是否变化。正文在后文承认“过期审批”尚未实现，这是正确的；问题是前面的状态表和时序图把目标设计画成了现有能力。

#### 建议修改

建议直接补齐主线实现：

1. 增加 `VERIFYING` 或明确说明它只是瞬时概念状态；
2. 请求审批前保存当前环境摘要；
3. 审批事件包含 `action_id` 和 `state_digest`；
4. 恢复时重新计算环境摘要；
5. 摘要变化时进入 `APPROVAL_STALE`、重新规划或重新请求审批；
6. 为上述路径增加测试和失败输出。

如果暂时不实现，图中的未实现路径必须改为虚线，并标注“生产目标设计，本章代码未实现”。

### 4. `WorkspaceSandbox` 不是操作系统级 Sandbox

当前实现仅规范化路径，并检查结果是否仍位于工作区根目录之下：

- `chapter4/harness/sandbox.py:10`
- `chapter4/harness/sandbox.py:14`

这是有价值的应用层路径守卫，但不是操作系统级沙箱，不能限制：

- 子进程；
- 网络访问；
- 凭据访问；
- 符号链接竞态；
- Windows junction；
- 挂载点和其他系统资源；
- 更完整的 TOCTOU 问题。

正文后半部分已经对此做出免责声明，但 README 仍称其为“操作系统文件路径边界”。

#### 建议修改

- 将类名改为 `WorkspacePathGuard`；
- 将实验输出改为 `path_guard: blocked`；
- 将实验结论改为“软策略与应用层执行守卫可以独立失败”；
- OS、容器或虚拟机 Sandbox 只作为生产系统映射；
- 不用本地路径检查宣称已经证明了强制系统隔离。

真实产品也明确区分权限策略和 OS 级执行隔离。可参考：

- [Claude Code 权限文档](https://code.claude.com/docs/en/permissions)
- [Claude Code 沙箱文档](https://code.claude.com/docs/en/sandboxing)

## P2：应当修改

### 5. 参考答案没有完整对应正文题目

最明显的是正文第 15 题与参考答案第 15 题不一致：

- 正文要求反驳“直接使用最强模型，就不需要 Harness Engineering”；
- 参考答案回答的是“什么时候不应该自建 Harness”。

位置：

- `book/chapter4.md:796`
- `chapter4/reference-answers.md:67`

其他不完整项：

- 第 3 题要求解释 `call_id`、`action_id`、业务幂等键和执行回执，并判断哪些可以相同；答案只重点解释了前两个；
- 第 5 题要求分别给出三层完成协议不一致的例子，答案没有逐项举例；
- 第 11 题要求覆盖动作、参数、状态版本、风险、回滚和过期条件，答案没有完整对应；
- 第 14 题要求分别判断文件读取、发邮件、数据库更新和支付，答案只给出一般原则。

#### 建议修改

为每道题建立“题目要求—答案覆盖点”清单，逐项核对。参考答案不必很长，但必须完整回答题目中显式要求的每个部分。

### 6. “Schema 校验”实际上只有必填字段检查

当前代码只判断必需字段集合是否为参数键集合的子集：

- `chapter4/harness/gateway.py:21`
- `chapter4/harness/gateway.py:39`
- `chapter4/harness/gateway.py:42`

它没有检查：

- 未知字段；
- 字段类型；
- 空值；
- 枚举或数值范围；
- 更复杂的参数约束。

因此正文直接称其为 Schema validation 会让读者高估实现能力。

#### 建议修改

本章可以统一改称“最小必填字段校验”，并明确严格 JSON Schema 与工具合同留给第 9 章。也可以补充严格验证，但不建议在本章展开完整 Schema 系统。

### 7. 正文存在 Context Builder，配套代码中却没有该组件

正文将 Context Builder 列为 Harness 的核心责任，结尾还说下一章“只替换或扰动 Context Builder”：

- `book/chapter4.md:154`
- `book/chapter4.md:167`
- `book/chapter4.md:831`

但 `chapter4/harness/` 中没有 `ContextBuilder` 或 `ContextPacket`。

#### 建议修改

优先增加一个最小实现，只负责装配：

- 当前任务；
- 运行状态；
- 最近工具观察；
- 待审批动作；
- 剩余预算；
- 完成条件。

这样第 5 章可以保持其他 Harness 责任不变，只替换上下文选择策略。如果不准备现在实现，结尾应改为“下一章将新增 Context Builder”。

### 8. 与第 3 章仍有可压缩的重复

第 3 章已经较完整地解释：

- Tool Call 是提议；
- `call_id` 与幂等；
- 聊天、环境和运行状态的区别；
- 模型 final 不等于任务完成；
- Trace 与副作用回放；
- 错误结构化、超时和停止。

对应位置从 `book/chapter3.md:180` 延续到 `book/chapter3.md:526`。

第四章应重点回答这些能力怎样成为可替换、可持久、可暂停恢复和可独立测试的 Harness 责任，而不是再次完整解释概念本身。

#### 建议修改

将重复部分压缩约 20%—30%，采用以下过渡句式：

> 第 3 章已经证明 X；本章进一步解决 X 由谁拥有、怎样持久化、怎样独立测试，以及失败后进入什么状态。

预计可以减少约 2000—3500 字，让“权限—隔离—状态—审批—恢复”成为更清晰的章节中心。

## 写得好的部分

以下内容已经达到较好的书稿质量，建议保留：

1. 用“相同完成声明、不同系统状态”开场，问题具体且有张力；
2. 明确限定实验是 deterministic boundary conformance，而不是模型或产品排名；
3. 正确区分运行时 Harness 与更广义的仓库 Harness；
4. 用“Policy 判断应该，Sandbox 限制能够”建立清晰边界；
5. 对未知结果、exactly-once、TOCTOU、事务型 outbox 和 approval fatigue 的限制说明较成熟；
6. Claude Code 与 Codex 使用六维责任模型映射，没有写成功能百科；
7. 上下文和压缩只建立责任边界，没有完全吃掉第 5、6 章；
8. “什么时候不必自建 Harness”避免把复杂架构写成默认正确答案；
9. 对本地实验不能证明什么交代得较完整；
10. 图、实验、练习和资料台账的数量符合本书写作标准。

## 快变技术事实抽查

抽查未发现以下事实写反：

- Claude Code 当前权限规则顺序确实为 `deny → ask → allow`；
- Claude Code 权限规则与 OS 级文件、网络沙箱属于不同层；
- LangGraph Interrupt 恢复要求使用相同 thread ID；
- LangGraph 恢复时，中断所在节点会从头重新执行，因此中断前副作用需要幂等。

参考：

- [Claude Code Configure permissions](https://code.claude.com/docs/en/permissions)
- [Claude Code Sandboxing](https://code.claude.com/docs/en/sandboxing)
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

产品命令、默认模式、规则语法和协议字段仍属于快变事实，出版前需要重新核对。

## 建议修改顺序

1. 修复 Receipt 去重实验，使它真正覆盖“回执已写、终态未写”的恢复窗口；
2. 将消融改为严格单变量实验，或者更名为边界故障矩阵；
3. 对齐状态机、审批摘要、过期审批和图中的实现状态；
4. 将教学路径检查从 Sandbox 概念中降级为 `WorkspacePathGuard`；
5. 修正参考答案与正文题目的逐项对应；
6. 调整 Schema validation 的表述；
7. 增加最小 Context Builder，或修正与第 5 章的代码衔接承诺；
8. 压缩与第 3 章重复的内容；
9. 重新运行 27 项测试和 5 组实验；
10. 重新生成报告、图表、预览 PDF，并更新原有 `chapter4-review.md` 的结论。

## 复审通过条件

满足以下条件后，可以将第四章继续标记为“复审稿”：

- Receipt 测试确实进入回执查询与去重分支；
- 实验名称和因果声明与实际设计一致；
- 图中已实现能力与目标设计有明确区分；
- 不再把路径守卫称为完整 Sandbox；
- 15 道参考答案全部覆盖正文要求；
- 正文、README、代码、报告和插图中的术语保持一致；
- 第 3、4 章全部测试通过，报告由当前代码重新生成；
- 更新后的预览版本不存在图表、代码块和跨页排版问题。
