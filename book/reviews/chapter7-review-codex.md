# 第 7 章 Review：记忆——不是把聊天记录全部塞回去

Review 日期：2026-08-25

范围：`book/chapter7.md`、`chapter7/`、7 幅 SVG、14 道练习及答案、来源台账、站点与 CI 接入。
结论：**通过。** 初审发现的 4 项重要问题和 3 项一般问题已经修复；当前没有阻塞发布的 Critical 或 Important 项。

## 一、读者视角

### 做得好的地方

1. 开篇只跟踪一条“Python → TypeScript → 删除”的偏好，读者先看见失败，再理解 Write、Recall、Correct、Forget，没有从分类百科开始。
2. Context、Session、Checkpoint、Memory、RAG 用“谁拥有、任务结束后是否仍有效、到哪里更新”区分，比只背定义更容易迁移到真实系统。
3. 代码阅读被拆成 `contracts → policy → store → recall → runtime → experiments`，每一步只增加一种责任，符合“从最小部件逐层搭建”的教学节奏。
4. 每组实验都同时写“支持什么”和“不支持什么”，能防止读者把确定性夹具误读成模型能力测试。
5. 14 道题不是概念复述，覆盖消融、隔离、并发修正、删除复活、生产 Store 与产品责任映射；答案均包含预期推理、常见错误和可检查验收。

### 初稿可读性问题与修订

初稿有 61 个二三级标题、约 1.6 万有效中文字符，概念被切得太碎。修订后收束为 35 个二三级标题，并扩充到约 2.5 万有效中文字符。新增内容集中在完整历史为何失败、Record 字段怎样对应事故问题、Write Gate 逐条走查、Recall 手算与故障定位、污染事故复盘、删除请求闭环和代码阅读路线，没有横向堆叠更多框架。

7 幅图已分别渲染为 1200×675 与 390×219 检查。桌面和手机尺寸均未观察到裁切、重叠或核心文字不可辨；图 6 保留独立指标而没有合成总分，图 7 只做公开责任映射。

## 二、AI Agent 专家视角

### 边界与架构

本章正确把 Memory 定义为“经过策略治理、可供未来独立任务复用的信息”，而不是 Session 历史或向量库的别名。Write 与 Recall 分开评估；Store 区分 Event History 和 Current Projection；Correct 使用连续版本和预期 Record；Forget 使用 Tombstone 阻止陈旧索引直接复活。Harness、事实源、RAG 和 Memory 的职责没有互相替代。

教学 Recall 先做 Namespace、状态、有效期、类型和敏感级别硬过滤，再做可分解排序。公式只是可手算的教学函数，正文明确不把分数解释成概率，也不声称权重或 Top-K 最优。实验冻结 Candidate、时钟和决策策略，因此只支持外围边界符合性，不支持真实模型质量或产品排名。

### 初审发现并已修复的重要问题

1. **未来记录提前生效。** `MemoryStore.current()` 与 `all_current()` 原来只检查 `expires_at`，没有拒绝 `valid_from > now`。这与正文“有效时间是硬边界”矛盾。现已在 Current Projection 层同时检查起始与结束时间，并由 `test_future_record_is_not_current_before_valid_from` 冻结边界。
2. **Namespace 主键碰撞。** 旧键用 `_` 表示 `project_id=None`，与真实项目 ID `_` 相同。现改为字段齐全的规范 JSON 键，`test_global_namespace_does_not_collide_with_literal_underscore_project` 证明全局与字面项目不会碰撞。
3. **工具观察权威过高。** 旧 Policy 自动允许 `tool_observed`，与正文低信任工具输出边界不一致。现改为 `observed_memory_requires_review`；只有用户显式、人工已审或仓库已验证来源能在相应合同下自动提交。
4. **人工批准冒充仓库验证。** 旧实验把审批后的模型推断改成 `repository_verified`。现增加 `human_reviewed` Authority 和稳定 reason，保留“人审过”与“仓库证据已验证”的语义差异。

### 已修复的一般问题

1. 来源台账原来只检查字段非空；现在逐项验证分号分隔的仓库相对路径真实存在。
2. `test_records_are_frozen` 原来只触发一次字段校验异常，没有证明不可变；现直接断言 `FrozenInstanceError`。
3. Codex `AGENTS.md` 官方旧地址已重定向；正文与台账已更新到当前 ChatGPT Learn 官方页面。

## 三、实验与证据视角

五组 15 个案例分别覆盖：

- 无 Memory、完整历史、结构化 Memory；
- 全写、Policy Gate、Gate 加人工复核；
- 全局扫描、Scope 过滤、Scope 加排序；
- 原地覆盖、版本修正、陈旧 Writer；
- 陈旧索引、回主 Store 解析、跨租户探针。

每个 Case 都有精确指标期望和证据码；`sample_count_per_case=1` 被写入报告。JSON、Markdown、脱敏 JSONL 连续重建保持字节一致。三个规范哈希为：

- JSON：`7a9feb8f9253ee2f1c409c710658daf23b9b0b609d2114e1b38a6e65dacea0a3`
- Markdown：`06eb7ee156b4acd50b48a42564dd99405eaeaa53f984c3e19ed431d8746bd781`
- JSONL：`8d25258e75c8b9670875d6ae5e2466d1c3922ad20cf343031f75b8434e1da0ea`

报告把真实模型质量、Token 节省、Provider 延迟和生产成功率保留为 `null`。Trace 不含 Memory 正文或 Secret，序列化字节不被换算为 Token。

## 四、资料与时效视角

来源台账共 20 项。2026-08-25 重新打开并核对了以下快变官方页面：

- [LangChain Memory overview](https://docs.langchain.com/oss/python/concepts/memory) 与 [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)：thread/checkpointer 与 cross-thread Store 的公开职责仍支持正文映射；
- [Claude Code memory](https://code.claude.com/docs/en/memory)：`CLAUDE.md` 与 auto memory 仍明确区分，二者进入 Context 而非强制配置，auto memory 可查看、编辑和删除；
- [OpenAI Agents SDK agent memory](https://openai.github.io/openai-agents-python/sandbox/memory/) 与 [Sessions](https://openai.github.io/openai-agents-python/sessions/)：跨运行 Lessons 与会话历史仍明确分开，sandbox agent memory 仍标记为 Beta；
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)：公开页面仍说明按全局、项目和当前目录层级发现并合并项目指令。

正文没有固化 Claude Code 当前加载阈值、目录默认和版本号等易变细节，也没有从公开文件表面反推未公开内部实现。

## 五、保留限制

这些限制已经在正文 Claims/Non-claims 和 README 中公开，不阻塞教学发布：

- 固定 Fixture 直接提供 Candidate 来源与 Authority，没有实现自然语言提取和来源身份认证；
- `RLock` 与 JSONL 只验证单进程合同，不提供跨进程事务、复制和灾难恢复；
- Tombstone 只建立在线停止召回边界，不证明缓存、备份或第三方副本已完成法规删除；
- 关键词 Recall 不是 Embedding 或混合检索 Benchmark；
- 没有调用真实 LLM，因此不报告模型质量、Usage、成本或延迟；
- 官方产品事实会变化，标记为“出版前复核：是”的页面需要再次核对。

## 六、最终判断

从读者角度，本章已经从“概念密集”改成“沿一条记录逐步搭建”；从工程角度，关键状态变更都有稳定合同和失败测试；从专家角度，来源、作用域、时间、版本、删除和实验外推边界基本诚实。

建议状态：**通过，进入第 8 章前保留为第 7 章发布门禁稿。** 后续只有在引入真实提取器、数据库或向量召回时，才应新增对应 live/eval 分支，不要修改当前离线基线来冒充更广覆盖。
