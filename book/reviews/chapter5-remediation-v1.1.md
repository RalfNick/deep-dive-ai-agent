# 第 5 章独立 Review 整改记录（v1.1）

整改日期：2026-08-16

依据：`book/reviews/chapter5-review-codex.md`

历史基线：Git tag `book-chapter5-v1.0`、PDF `output/pdf/versions/chapter5/chapter5-v1.0.pdf`

新版：Git tag `book-chapter5-v1.1`、PDF `output/pdf/versions/chapter5/chapter5-v1.1.pdf`

## 结论

独立 Review 提出的 5 组 P1、4 组 P2 与 4 组 P3 已完成证据合同收口。整改没有把第 5 章扩写成工具协议或长任务章节：实验 5-4 明确降为“文本化工具合同”，原生 `tools/tool_calls` 仍留给第 9 章；freshness 仍是已记录、未实现策略的公开限制。

当前判断：**内容与发布门禁通过，可以发布 v1.1；v1.0 历史证据保持不变。**

## P1 整改

| Review 项 | 处理 | 可执行证据 | 状态 |
| --- | --- | --- | --- |
| P1-1 练习与答案错位 | 以正文 1—14 题为主版本重写答案；新增题号和标题完全一致的发布契约 | `chapter5/publication_checks.py`、`chapter5/tests/test_publication_contract.py`；提交 `db89665` | 已解决 |
| P1-2 工具实验借用原生协议结论 | 采用 Review 允许的“收窄结论”方案；正文、README 与来源台账明确请求无 `tools`、响应不解析 `tool_calls` | `chapter5/tests/test_serialization.py::test_text_contract_request_does_not_claim_native_tool_calling`；提交 `72c506e` 后补充发布契约测试 | 已解决 |
| P1-3 Grader 假门禁 | 每个冲突变体传入赢家 ID 与 Trace 原因；冲突正确性进入 Build 总门禁；不可信提升绑定具体 item marker 并成为 Safety 硬失败 | `test_wrong_conflict_winner_fails_the_build_gate`、`test_wrong_conflict_reason_fails_the_build_gate`、`test_unrelated_delimiter_cannot_hide_hostile_item_promotion`；提交 `4db72f1` | 已解决 |
| P1-4 缺 Key 无结构化报告 | CLI 捕获 `CredentialMissing`，写零尝试 `config_error / missing_credential` 报告后退出码 2，不伪造 30 条失败 | `test_live_cli_without_key_writes_config_error_report`；提交 `ed9cee3` | 已解决 |
| P1-5 预算数字与 Required 语义错误 | 用当前 Fixture 的 69、86、60、39、104 units 重写表格；拆为 selected / all candidates / requirement evidence 三个字段 | `test_budget_metrics_distinguish_retention_from_requirement_evidence`；提交 `e1234b8` | 已解决 |

## P2 整改

| Review 项 | 处理 | 可执行证据 | 状态 |
| --- | --- | --- | --- |
| P2-1 冲突矩阵过窄 | 新增 `user_instruction` 通道、`user_vs_repository` 与 `observation_vs_instruction` 两个变体；总记录由 28 增至 30 | `test_user_instruction_has_user_authority_without_becoming_system_policy`、`test_tool_observation_remains_data_even_when_it_looks_like_an_instruction`、固定变体测试 | 已解决 |
| P2-2 Provider 角色映射隐含 | 正文明示内部 authority、Provider role 与执行权限是三层；当前只有最小合同使用 Provider system，其余 Section 均为 user | `test_internal_authority_does_not_promote_packet_sections_to_provider_system_role` | 已解决 |
| P2-3 freshness 未实现却未列限制 | 在 ContextItem、Builder 限制与本章结论中明确：`observed_at` 只记录时间，不执行 TTL 或业务有效期判断 | 正文“ContextItem”与“本章真正证明了什么”段落 | 已解决（公开限制） |
| P2-4 Safety `passed` 易被当成认证 | `SafetyGrade` 增加固定 scope；正文与 README 说明只通过 Fixture 安全合同，不覆盖 OS、网络或完整攻击面 | `SafetyGrade.scope`、报告 `scope` 字段、Safety hard-failure 测试 | 已解决 |

## P3 整改

| Review 项 | 处理 | 状态 |
| --- | --- | --- |
| P3-1 测试台账过期 | 来源台账、README 与版本记录统一为 Chapter 5 63 项、Chapter 4 24 项 | 已解决 |
| P3-2 DeepSeek 核对日期不一致 | 统一为 2026-08-16，并增加官方 Tool Calls 资料的使用边界 | 已解决 |
| P3-3 工作树缺少总纲 | 将主工作区 `book/OUTLINE.md` 纳入同一版本历史 | 已解决 |
| P3-4 旧自审结论需保留并更新 | 原 `chapter5-review.md` 保留，只增加历史快照说明；独立 Review 原文与本整改记录并列保存 | 已解决 |

## 最终验证

| 门禁 | 结果 |
| --- | --- |
| Chapter 4 回归 | 24 / 24 通过 |
| Chapter 5 测试 | 63 / 63 通过 |
| Python 编译 | `python -m compileall -q chapter5` 通过 |
| 离线报告 | 30 attempts / 30 valid；两次 SHA-256 均为 `1F7B18137B1F3A44188DA3FCF5C682370CD47288DFD8114292FF593B759A396E` |
| 出版契约 | 正文与答案 1—14 题号、标题一致；15 个脚注定义/引用一致；本地链接完整 |
| 图与渲染 | 7 个 SVG XML 可解析；Node 渲染测试 4 / 4 通过 |
| 安全静态检查 | Chapter 5 范围无凭据形状明文；旧合同字段未残留在当前代码或报告 |
| PDF | 36 页 A4；全页联系表和关键页原尺寸目检通过；SHA-256 `2843EF79D820A4EC3B18FFDA1DD1EC73CD598160301FDEDE291AD37460C50874` |
| 历史保护 | v1.0 PDF SHA-256 仍为 `1F63F6FF87F3AB4DCAD493DE49731C1CEFB1A55F82EBC80C2604E7DDEBEC9CD4` |

## 仍然不证明的内容

- 没有进行真实 DeepSeek 调用，不提供模型能力或产品排名；
- 工具实验不是原生 Function Calling 验证；
- `SafetyGrade.passed` 不是系统安全认证；
- `observed_at` 不等于已经实现 freshness control；
- UTF-8 units 不是 Provider Token；
- 没有执行真实工具，不证明 OS 沙箱与副作用安全。
