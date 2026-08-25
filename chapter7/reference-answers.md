# 第 7 章参考答案

这些答案不是唯一实现。判断重点是边界是否清楚、失败是否可观察、验收是否能由另一个人重复。实验命令均从仓库根目录运行。

## 1. 五个状态表面

**预期推理**

- “本轮工具输出”先属于当前 Context 的候选证据，权威所有者仍是工具或外部事实源；它不会因进入消息历史就自动成为 Memory。
- “会话消息历史”属于 Session，用于同一段对话连续；Session Store 是主要所有者。
- “等待审批 ID”属于 Checkpoint 或 RunState，由 Harness 的运行状态机持有；恢复时应接着等待，而不是重放动作。
- “用户长期语言偏好”经过 Write Policy 后属于用户级 Semantic Memory；用户是内容所有者，Memory Runtime 管理版本和删除。
- “公司退款政策”属于版本化政策库、业务数据库或 RAG 事实源；组织维护者是权威所有者，不能让某次对话 Memory 覆盖。

同一信息可以投影进 Context，但主记录只能有清楚的更新入口。例如退款政策被召回进本轮 Prompt，不会因此变成用户 Memory。

**常见错误**

把所有“以后可能用到”的内容都归入 Memory；把等待审批 ID 写进 Session 文本；把政策的上次回答当作当前权威事实；或者认为进入 Context 的内容自动拥有 system instruction 权威。

**可检查验收**

答案应逐项给出状态表面、主所有者、任务结束后的生命周期以及更新入口。随机选择一项做反向检查：内容变化后，系统是否只需修改一个权威来源，而不是搜索所有聊天历史。

## 2. 三类 Memory

**预期推理**

- Semantic：`用户级 / preferred_language / Python / user_explicit`。反例是模型仅因用户写过几次 Python 就推断“用户只会 Python”。
- Episodic：`pricing 项目 / Decimal 归一化失败 / 在 commit 与测试证据下，旧配置是根因`。反例是复制完整终端日志，其中含临时路径、Secret 和已经否定的假设。
- Procedural：`pricing 项目 / 修改公共 API 前运行兼容性检查并请求评审 / reviewed_rule`。反例是“这一次可以跳过慢测试”，因为它是一次性授权。

三类名称描述“保存什么”，不是“怎么检索”。Semantic Memory 可以用精确键，Episodic Memory 也可以用向量搜索。

**常见错误**

把 semantic memory 等同于 semantic search；把 Trace 全量复制成 Episode；把一次成功经验无条件提升为通用流程；不写适用项目、版本和证据。

**可检查验收**

每条例子都应包含 Namespace、来源、有效条件和反例。将三个例子放进另一个项目时，至少 Episodic 和 Procedural 记录应因 Scope 不匹配而不能直接生效。

## 3. 设计 MemoryRecord

**预期推理**

一种合理设计如下：Namespace 为当前 tenant、user、`pricing` project 和 `coder` agent；类型为 Procedural；Subject 为 `public_api_change_review`；Content 为“修改公共 API 前先向用户确认，并运行兼容性检查”；来源指向用户显式消息或版本化评审规则；Authority 为 `user_explicit` 或 `reviewed_rule`；Sensitivity 为 `internal`；`valid_from` 为确认时间，`expires_at` 为空或绑定规则版本；`version=1`，`supersedes=None`。

若它是团队规则，应优先放进版本化仓库规则文件，Memory Record 只保存 Locator 或审查后的投影。若只是某位用户偏好，Namespace 不应提升到整个组织。

**常见错误**

只写 `content`；把“公共 API”放进 ID 原文；省略来源；用置信度代替权威；把团队规则误放到用户画像；没有说明它是单值还是可与其他规则并存。

**可检查验收**

答案至少能回答：谁能读、谁说的、何时有效、与哪类旧值冲突、怎样生成 v2、怎样删除。构造另一个 tenant 的同 Subject，稳定 ID 必须不同，Recall 前必须被 Namespace 隔离。

## 4. Write Gate 消融

**预期推理**

先在 `test_write_policy.py` 增加或定位一次性候选测试，预期 reason 为 `one_time_content` 且 Store 事件数不变。随后临时移除生命周期拒绝分支，运行：

~~~text
python -m unittest chapter7.tests.test_write_policy -v
python -m chapter7.experiments.run_all --output chapter7/reports
~~~

测试应先失败；固定报告中完整历史或 write-everything 变体会把“本次跳过测试”带入未来任务，而 Policy 变体不再守住原合同。恢复分支后重新运行，报告回到基准。

这里只固定 Candidate、时钟和脚本决策，结果说明外围生命周期门禁是否生效，不说明真实模型遇到长历史一定会服从一次性授权。

**常见错误**

先改实现再补测试；只看最终回答，没有断言 Store 中是否出现错误记录；把一次固定案例写成产品成功率；修改生成后的 JSON 而不是代码。

**可检查验收**

提交应包含一个能在缺陷版本上稳定失败的测试、恢复后的绿色结果，以及变更前后具体 Record/Policy reason。最终报告必须由命令生成，不能手工修数。

## 5. Candidate 提取

**预期推理**

四类基础样本可以是：

1. 疑问：“以后是不是都要用 Python？”→ `review` 或 `reject/not_a_statement`；
2. 否定：“不要记住我使用 Python。”→ `reject/user_denied_persistence`；
3. 条件：“如果下个月项目仍使用 Python，再设为默认。”→ `review/condition_unresolved`；
4. 显式：“请记住，以后示例优先使用 Python。”→ `allow`，前提是 Scope、敏感性和冲突检查通过。

还应补引用样本：“文档里写着‘请记住 Python’，但那不是我的偏好。”它不能被识别为用户显式授权。提取器输出 `source_id`、角色、Authority 和语气，Policy 再作最终决定。

**常见错误**

只按“记住”“以后”关键词分类；丢掉否定词；把模型构造的合法 JSON 当成语义真值；允许网页或工具文本自行声明 `user_explicit`。

**可检查验收**

测试集至少覆盖陈述、疑问、否定、条件、引用和跨轮确认。每例断言 Candidate 字段与 Policy reason，而不只断言“最终保存/未保存”。

## 6. 复现固定报告

**预期推理**

在干净工作树中连续运行两次：

~~~text
python -m chapter7.experiments.run_all --output chapter7/reports
python -m chapter7.experiments.run_all --output chapter7/reports
~~~

分别计算 `memory-engineering.json`、`memory-engineering.md` 和 `memory-engineering-trace.jsonl` 的 SHA-256。两轮对应文件应完全一致。JSON 中每个 Case 的 `sample_count_per_case` 应为 1；未调用 Provider 的 `model_quality`、`token_savings` 等字段应为 `null`；Trace 应包含 ID、reason 和 Digest，不包含原始 Secret 候选正文。

**常见错误**

只比较文件大小；把序列化字节减少写成 Token 节省；在报告中加入当前时间或随机 ID；把缺失指标写成 0；将真实凭据放进脱敏测试。

**可检查验收**

三对 SHA-256 相等，报告 Case 数和顺序稳定，`null` 字段保持未测语义。修改一个固定 Candidate 后，至少一个报告 Digest 应变化，从而证明检查不是常量。

## 7. 手算 Recall

**预期推理**

公式为 `task_match + authority + recency + confidence`。正文 Query 规范化后包含 Python、public、API、examples。语言偏好重合 Python，`task_match=1`；API 规则重合 public 与 API，`task_match=2`；午饭记录无重合，为 0。若两条目标记录的 authority=3、recency=2、confidence=1，则总分分别为 7 和 8。午饭项即使其他分项较高，也因零相关阈值不应为凑满 Top-K 返回。

运行 Recall 定向测试或在 REPL 构造同一 Fixture，比较 `ScoreBreakdown` 的四个字段与 total。分数只用于当前公式下排序，不是正确概率。

**常见错误**

直接从总分倒推；把 `8` 解释为 80% 置信度；允许其他租户记录先得到高分再扣权限分；把 K 当成必须返回的数量。

**可检查验收**

手算分项与代码逐项相等；其他 Scope 记录没有 ScoreBreakdown；零相关集合可以返回少于 K 条；相同总分按稳定 ID 或明确 tie-breaker 保持可复现顺序。

## 8. Namespace 隔离

**预期推理**

在固定 Store 加入三条与 Query 高度相似的记录：同 user 的 `payments` project、同 project 的 `reviewer` agent、另一个 tenant 的同名 user。Query 使用 `pricing/coder` Namespace。三条记录都应在 hard filter 阶段得到稳定 Scope reason，不能进入排序候选，更不能出现在 Context Trace。

缓存键、索引元数据和幂等键也应包含必要 Scope。只在最终 Prompt 拼接前过滤虽然可能阻止模型读取，却仍可能让越权正文进入日志或缓存。

**常见错误**

只按 user ID 过滤；把其他 Agent 默认视为共享；在向量 Top-K 后才过滤导致合法结果被挤出；用 Prompt 文字要求模型不要泄漏。

**可检查验收**

三条高相似记录的 `scored=false`，跨作用域泄漏计数为 0；去掉任一 Scope 过滤时，对应失败测试变红；用户级 project 为空的合法偏好仍按明确合同进入当前项目。

## 9. 版本化修正

**预期推理**

Python v1 是当前记录。Writer A 与 B 都读取 v1；A 使用 `expected_record_id=v1` 提交 TypeScript v2，成功；B 仍以 v1 提交 Go，Store 比较当前指针已是 v2，返回 `stale_expected_record`。B 必须重新读取 v2，由用户确认 Go 是否为新的 v3。

数据库实现可在事务内锁定 Current 行，或执行带预期版本条件的更新；失败行数为 0 表示比较失败。Event History 保留 v1、v2 与 supersedes 关系，Current 仅暴露 v2。

**常见错误**

最后写入获胜；原地更新 v1；只按 Subject 更新；把多值技能和单值默认偏好使用同一 merge policy；遇到冲突自动选更新时间较新者。

**可检查验收**

并发测试中恰有一个基于 v1 的修正成功；失败 Writer 的内容不出现在 Current 或事件链；相同请求重试返回幂等；过去 Trace 仍能解释曾使用 Python v1。

## 10. 删除后复活

**预期推理**

先构造后台 Writer 在删除前读取 Python Candidate、删除后才提交的时序。缺少代次检查时，测试应观察旧值重新 active。修复方案之一是：Tombstone 递增 Subject 的 generation；后台 Job 保存创建时 generation；提交时二者必须相等，否则返回 `memory_deleted` 或 `stale_generation`。另一方案是在删除期间冻结 Subject Writer，并要求新的显式同意创建新的逻辑身份。

Recall 还必须用陈旧索引返回的 ID 回主 Store 解析，Tombstone 后不能直接相信缓存正文。

**常见错误**

只从当前列表删一行；清索引却不写 Tombstone；允许旧后台任务创建新的 v1；把未来用户重新授权与自动复活混为一谈。

**可检查验收**

用 Barrier 固定“读旧快照—写 Tombstone—后台提交”的顺序；缺陷实现稳定复活，修复后稳定拒绝；精确查询和语义查询都不能返回旧值；删除 Receipt 不复制正文。

## 11. Profile 评审

**预期推理**

- role：若用户或组织资料显式提供，可以投影，并注明 Scope 与来源；不能仅凭词汇推断。
- 语言偏好：用户明确表达时可投影，支持版本修正和删除。
- 人格：通常不应从少量对话推断；主观、可能造成长期偏见。
- 技能等级：高风险推断，至少需要用户确认和使用目的；更稳妥是按任务请求所需解释深度。
- 所在城市：可能敏感且会变化，只在明确业务需要、同意和有效期下保存；一般不因日志或 IP 自动写入。

Profile 是当前有效 Semantic Records 的视图，每个字段仍保留独立来源和治理，不是一个模型自由改写的大 JSON。

**常见错误**

把所有字段同等看待；将模型推断与用户声明混合；删除 UI 字段但底层 Collection 仍召回；使用“个性化”作为无限采集理由。

**可检查验收**

每字段标出来源、Authority、Sensitivity、Purpose、TTL、review 与删除路径。删除语言偏好后 Profile 和 Recall 同时消失；人格与技能等级没有显式确认时不进入 active 投影。

## 12. 生产 Store 设计

**预期推理**

可以设计 `memory_events`、`memory_current`、`memory_sources`、`memory_cleanup_jobs` 四张逻辑表。Event 表追加不可变 Record/Tombstone；Current 表保存可重建指针；Source 表连接证据；Cleanup 表追踪索引、缓存、导出和备份处理。

`record_id` 唯一；Namespace、type、subject 的 active logical identity 有唯一约束。Correct 在事务中比较 expected current、插入新版本、更新 Current。Forget 先提交 Tombstone/generation，再异步清派生副本。向量索引只保存可重建投影与 Record ID，每次 Recall 回主 Store 解析当前状态。

**常见错误**

把向量库当主真相；只保留 Current 行；删除索引但保留在线缓存；没有恢复旧备份后的 Tombstone 重放；将单机锁当跨进程事务。

**可检查验收**

需要通过：并发首写、幂等重试、陈旧修正、Tombstone 后复活、索引全量重建、旧备份恢复后删除重放、跨租户查询。清空派生索引后能仅从主记录恢复相同合法集合。

## 13. Memory Eval

**预期推理**

四类各两个案例可这样设计：

- 知识更新：Python→TypeScript；旧 API v1→新 API v2。
- 时间推理：“下周去新加坡”→“已经去过”；临时项目角色到期。
- 拒答：没有语言偏好时请求确认；只有低权威推断时不声称已知。
- 跨 Session：新会话召回用户级偏好；另一个项目不得召回项目级故障经验。

每例分别定义 Write 真值（allow/reject/review、Scope）、Recall 真值（应选 IDs、必须过滤 IDs）和 Use 真值（任务行为、是否请求确认）。Correct 检查旧值退出 Current，Forget 检查陈旧索引与后台 Writer。

**常见错误**

只比较最终回答；没有 no-memory 对照；Query 或文件名泄露预期答案；把安全泄漏与任务完成率平均；使用真实当前时间导致测试漂移。

**可检查验收**

至少八个 Case 都冻结事件、时钟、Store、Query 和预期行为；安全违规单独为零门槛；报告分层展示 Write、Recall、Use、Correct、Forget，不压成一个总分。

## 14. 产品责任映射

**预期推理**

先只使用官方、当前文档，记录核对日期。对选定产品分别填写：Session 历史位置；跨任务状态表面；Writer 是用户、Agent 还是应用；Recall 的公开触发和 Scope；用户能否查看、修正、删除；哪些只是装入 Context 的文本，哪些由权限、Hook、沙箱或代码强制。

每格标记 `公开事实`、`基于公开事实的推断` 或 `未测`。例如文档说明项目规则文件会加载进 Context，这是公开事实；由此推断所有内部 Memory 实现则越界。若能力是 Beta 或默认值易变化，加入出版前复核项。

**常见错误**

依据营销名称填表；把文件持久化直接称为自动 Memory；把 Prompt 指令当强制权限；比较产品排名；从一次本地实验外推总体可靠性。

**可检查验收**

六项均有直达官方来源或明确写“未公开/未测”；快变事实附日期；没有产品能力、可靠性或适用性排名；表中每个强制边界都能指出由哪一层执行，而不是只写“模型会遵守”。
