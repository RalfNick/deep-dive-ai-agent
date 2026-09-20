# 第 12 章插图生成提示词

执行方式：Codex 内置 imagegen；用户提供的信息图作为风格参考，不作为编辑目标。七幅初稿均为新构图；图 12-2 在独立复核后以自己的初稿为编辑目标，定向修正了写入箭头。

## 共用风格前缀

Use case: scientific-educational. Asset type: Chinese technical book diagram. Warm ivory paper texture, hand-drawn navy ink outlines, rounded panels, subtle colored-pencil grain, blue/green/purple/orange accents, generous whitespace, large readable Chinese typography, simple icons, clear thick arrows. Original composition; use the reference only for visual language. No logo, no watermark, no footer, no decorative microtext.

## 01 Boundary

Title: “模型只提议，宿主才执行”. Left-to-right main flow: “上下文” → “模型” → “工具提议” → “策略与审批” → “执行器” → “观察” → “Verifier” → “完成”. Put “Trace” as a long ledger strip below connected to every stage. A visible gate between proposal and execution. Exact text only.

## 02 Tools

Title: “五个工具围绕代码库工作”. Center repository folder “代码库”. Around it: blue `read_file` and `search` with arrows from repository to model; orange `apply_patch` with a gate “版本 + 审批” before arrow into repository; green `run_tests`; purple `show_diff`. Bottom conclusion: “观察减少不确定性，写入必须受控”.

## 03 Loop

Title: “一轮 Agent Loop”. Clockwise six stages: “决策” → “工具提议” → “具体审批” → “执行” → “观察” → “独立验收”. Show `call_id` as a blue tag joining proposal and observation. Show `action_id` as a separate orange tag joining approval, execution and receipt. Branches: approval can “暂停”; verification can “完成 / 继续 / 失败”.

## 04 Approval

Title: “批准之后，恢复前先看事实”. Top timeline: “动作意图” → “具体批准” → “文件写入” → “执行回执”. Below, three columns: “前态 before：重新核对后执行”; “后态 after：不再写，只补回执”; “第三态 other：停止，交给人”. Emphasize third state in orange warning color.

## 05 Context

Title: “上下文是状态的有界投影”. Left large archive “持久状态” containing goal, constraints, approval, receipts, verification and full Trace. Middle funnel with “权威摘要” and “完整消息组”. Right compact card “模型本轮看到的上下文”. Show old dialogue being compacted but facts and tool-call/result pairs preserved. Bottom line: “压缩视图，不删除事实”.

## 06 Sandbox

Title: “策略不是沙箱”. Upper control plane: “Schema” → “策略” → “具体审批”. Lower execution plane: sealed container with “非 root”, “只读根”, “禁网”, “资源限制”, “可写工作区”. Outside container, host vault labeled “API Key 留在宿主” with a red no-entry arrow toward the container. Add badge “真实探针：未验证”.

## 07 Responsibilities

Title: “框架接管编排，宿主守住边界”. Four upper cards: “手写 Loop：while + Services”; “Pi：源码参照”; “LangGraph：图 + checkpoint”; “Agents SDK：Runner + RunState”. All four point down to one foundation “宿主应用”, containing four blocks “策略”, “隔离”, “副作用账本”, “独立验收”. Add exact note beside Pi: “仅源码阅读，未运行”.

## 03 Loop 迭代记录

- 候选 v1 使用环形布局，但视觉箭头形成了“工具提议 → 观察”，没有按编号经过审批与执行，拒绝采用。
- 候选 v2 改成上下两行，顺序成为 1 → 2 → 3 → 4 → 5 → 6；但蓝色 `call_id` 连接线同时碰到了第 3 步，仍可能让读者混淆调用身份和动作身份。
- 最终 v3 只改蓝色连接：`call_id` 只连接第 2 步“工具提议”和第 5 步“观察”；橙色 `action_id` 保持连接第 3 步“具体审批”、第 4 步“执行”和“回执”。其余布局与文字保持不变。

## 02 Tools 修订记录

- 首个候选的中央橙色箭头视觉上是“代码库 → 版本 + 审批 → apply_patch”，与技术简报要求的写入方向相反，不能依靠图注解释。
- 最终修订只替换两根橙色箭头：`apply_patch → 版本 + 审批 → 代码库`，箭头统一向上；其余文字、图标、布局、观察分支和手绘风格保持不变。
