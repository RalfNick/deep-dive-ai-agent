# Chapter 16 Continuous Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付第 16 章《从失败中学习：持续改进系统》的完整本地 `v1.0-rc1` 候选，让读者通过可复现实验理解失败怎样变成有证据、有范围、可撤销的改进，不发布网站。

**Architecture:** 标准库实验包将反馈准入、固定结果回放、归因、资产修订、独立验证和审批激活分开。知识选择规则、步骤型 Skill、用户偏好记忆真正被后续运行消费；Prompt、Harness 和训练数据只形成提案。五组规范报告是正文、七幅图和十三道练习的共同证据源。

**Tech Stack:** Python 3.11+ 标准库；`pytest==9.0.2`、`jsonschema==4.26.0` 仅用于测试；`Markdown==3.10.2` 仅用于预览；受控 SVG/Tldraw；现有 Node 排版合同与 MkDocs strict 构建。

**Spec:** `docs/superpowers/specs/2026-09-28-chapter16-continuous-improvement-design.md`。2026-09-29 用户“继续输出”接续对设计稿的审阅；本计划待用户确认后实施。历史设计稿保持原样。

## Global Constraints

- 本地分支 `codex/chapter16-continuous-improvement`；正文基线为第 15 章 RC2 提交 `2bcfaf0250fdd8dbf8b1f051bc62d576bef52875`，设计提交为 `d4f8b23349a0e5479fcfe61c331ffaf4db42036f`。
- 已选择 **native**：实施者自己逐任务完成，只在结束时安排一次新上下文只读整分支审查；本次写计划不派发 Agent。
- 核心运行时仅用 Python 标准库，默认离线、不读取 API Key、不联网、不调用模型或执行外部工具。
- 固定种子 `1601`；默认时钟 `2026-09-28T00:00:00Z`，过期演示显式推进，不读取当前时间生成规范报告。
- 12 条反馈、6 份文档、16 项任务；knowledge、procedure、scope、safety_recovery 每片 4 项，其中 1 项开发回归、3 项留出验收，总计 4+12。
- 开发与留出验收的 task family 不重叠；Agent 不接收隐藏答案、task ID 或数组位置作为决策输入。夹具作者知道样本，不称为真实模型盲测。
- 知识选择规则、步骤型 Skill、用户偏好记忆必须实际影响后续运行；其他载体不得伪装成可激活资产。
- 审批绑定候选、套件、真值、环境、安全合同和证据；安全硬失败优先，未知与环境缺失不得当成成功。
- 文件输出只在工程内指定目录；拒绝已有报告、路径越界和危险链接，不提供 `--replace`。规范产物不含当前时间、UUID、主机路径或真实敏感载荷。
- 约 1.8 万至 2.5 万正文汉字、30–36 个二三级标题、7 幅原创图、5 张比较表、5 组实验、至少 5 个失败样本、13 道分层练习。分别统计正文叙述汉字与总字符数，不凑字数。
- 保留第 1–14 章及第 15 章 RC1/RC2 不变；不改公开 `book/manifest.json`、`mkdocs.yml`、站点 allowlist 或公开阅读导航，manifest 保持 `0.14.0`。
- 不推送、合并、建 PR、移动 tag、部署；不安装模型/额外框架/Docker，不生成英文、繁体、PDF；Git 只暂存明确列出的文件。

## Review Focus

- 反馈自报 `trusted=true` 或字符串 `"false"` 不能获得权限；来源注册表、精确布尔类型和来源敏感标记必须有效。由任务 1、2 的类型及来源伪装测试固定。
- 同一任务改个措辞/ID 仍不得跨开发与留出用途；Unknown 的排除不得隐藏覆盖不足。由任务 1、3、5 的 family、覆盖率和分母测试固定。
- 子版本内容、文档真值、时钟或审批范围变化，不能复用旧批准；重新散列报告也不能伪造旧批准。由任务 5、6 的证据绑定与防重算绕过测试固定。
- 已过期或撤销的记忆，回滚旧指针后仍不得生效；多条匹配资产冲突时不得随列表顺序任选。由任务 4、6 的失效、冲突与回滚测试固定。
- 已有空目录、Windows reparse point、同路径并发写和部分失败不能覆盖报告或写到工程外。由任务 7 的输出预留、拒绝覆盖和路径测试固定。

---

## File Responsibility Map

所有相对路径均以书籍仓库根为基准，不在原学习工程另存一份书稿。

| 新增文件 | 职责 |
| --- | --- |
| `chapter16/contracts.py`、`chapter16/serialization.py` | 不可变合同、严格验证、规范 JSON 与内容哈希 |
| `chapter16/fixtures.py`、`chapter16/fixtures/{feedback,documents,tasks,truth,replays,sources}.json` | 独立加载夹具；运行输入与评分真值分离 |
| `chapter16/feedback.py` | 准入、敏感隔离、去重和冲突 |
| `chapter16/replay.py`、`chapter16/lessons.py` | 固定条件回放、条件性归因、有限提案和受限样本导出 |
| `chapter16/artifacts.py`、`chapter16/agent.py` | 版本化资产、作用域匹配、三类资产实际消费 |
| `chapter16/evaluation.py`、`chapter16/governance.py` | 独立评分、三态门禁、审批、激活、灰度与回滚 |
| `chapter16/output.py`、`chapter16/experiments.py` | 安全输出及五组可复现报告 |
| `chapter16/exercise_solutions.py`、`chapter16/preview.py` | 十三题答案与本地 HTML 预览 |
| `chapter16/schemas/improvement-report-v1.schema.json`、`chapter16/reports/` | 规范报告合同、五组 JSON、总报告、manifest 与练习结果 |
| `chapter16/tests/`、`chapter16/requirements*.in`、`chapter16/requirements*.txt` | 按职责测试与锁定开发/预览依赖 |
| `chapter16/README.md`、`chapter16/reference-answers.md` | 读者运行入口、如何读失败、练习判据 |
| `book/chapter16.md`、`book/sources/chapter16-sources.md` | 权威简体中文书稿与一手来源台账 |
| `book/images/chapter16/`、`infographic/chapter16/` | 七幅 SVG、对应可编辑源、生成器与说明 |
| `book/check_chapter16_preview.mjs` | 桌面/手机预览 QA；截图只在忽略目录 |
| `book/reviews/chapter16-review-codex-v1.0-rc1.md`、`book/versions/chapter16-v1.0-rc1.md` | 双视角检查、整分支复审处置、环境/命令/哈希与证据边界 |

最终才修改 `.gitignore`、`AGENTS.md`、`book/versions/CHAPTER_VERSIONS.md`、`docs/MIGRATION_MANIFEST.md`；CI 仅追加本地候选测试，不改 Pages 工作流。其余旧文件只读，图生成器可复用 `infographic/chapter14/generate_diagrams.py` 的纯渲染函数，但 `chapter16/` 运行时不导入其他章实验包。

## Execution Setup

- [ ] 核对分支、`git status --short` 与上述基线；若出现他人修改，保留并检查重叠，不重置。
- [ ] 读取本计划、设计稿、根 `AGENTS.md` 和 `book/WRITING_GUIDE.md`。实施前使用 executing-plans、test-driven-development；只有最终审查才使用 requesting-code-review。
- [ ] 下文 `python` 指已核对的 Python 3.11 环境。当前 `.venv-chapter15/Scripts/python.exe` 已具备 Python 3.11.15 和本计划三个准确依赖版本，可复用而不安装；先用版本检查确认。不要更改该环境的包，也不要读取 `.env`。
- [ ] 每项代码任务先运行新增测试确认 RED，再最小实现至 GREEN，记录实际输出；不能以“预计通过”代替验证。每项提交前 `git diff --check`，暂存其 Files 块明确列出的文件。

### Task 1: 冻结合同、夹具与用途边界

**Files:** Create `chapter16/__init__.py`、`chapter16/contracts.py`、`chapter16/serialization.py`、`chapter16/fixtures.py`；上述六个夹具 JSON；`chapter16/requirements.in`、`chapter16/requirements-dev.in`、`chapter16/requirements-dev.txt`、`chapter16/requirements-preview.txt`；`chapter16/tests/__init__.py`、`chapter16/tests/conftest.py`、`chapter16/tests/test_contracts.py`、`chapter16/tests/test_fixtures.py`。Modify `.gitignore`，仅增加 `chapter16/.runs/`。

**Interfaces:**

- `canonical_bytes(value: object) -> bytes`、`digest(value: object) -> str`：UTF-8、排序键、无 NaN/Infinity、末尾 LF；哈希排除对象自己的 hash 字段，不排除业务内容。
- `load_fixtures(directory: Path | None = None) -> FixtureSet`。`FixtureSet` 包含 `feedback`、`sources`、`documents`、`tasks`、`truth`、`replays`；测试 `lab` fixture 调用它，不生成联网夹具。
- 合同均 frozen/deep-frozen，并提供 `to_dict() -> dict[str, object]`。ID/引用非空，UTC 时钟显式解析，预算非负且不接受 bool。下列字段名称用于后续任务；嵌套文档、步骤、权限等使用命名合同，不用无约束字典。

| 合同 | 固定字段及关键取值 |
| --- | --- |
| Scope | `tenant_id, user_id, domain, requested_version`；`user_id=None` 表示租户级，禁止用空字符串代表全局 |
| FeedbackRecord | `feedback_id, source_id, source_role, purpose, family_id, scope, run_ref, payload, source_sensitive, permission, complete, evidence_refs, duplicate_of, conflict_refs` |
| SourceAuthority | `source_id, role, allowed_purposes, scope, permission, revoked`；独立注册表，不信载荷自报角色 |
| AgentInput | `tenant_id, user_id, domain, requested_version, question, operation, tool_receipts`；无 task ID、success_ref、gold |
| Document | `document_id, tenant_id, domain, version, valid_from, valid_until, answer, steps, provenance`；六份文档有唯一 ID |
| TaskSpec | `task_id, family_id, split, slice, agent_input, success_ref, target, frozen_clock, revoked_source_ids`；split=`development/holdout`，target 仅可在 development；默认使用固定时钟，过期/撤销反例以可信夹具显式指定，用户输入不能修改 |
| SuccessCondition | `success_ref, expected_document_id, required_steps, answer_style, refusal_reason, allowed_scope, truth_version`；只评分器读取 |
| ReplayCase | `case_id, input, documents, tool_tape, permissions, agent_version, frozen_clock, success_ref, family_id, missing` |
| LessonProposal | `proposal_id, source_refs, purpose, family_id, cause, carrier, scope, content, evidence_refs, unknown_reasons` |
| ArtifactRevision | `artifact_id, kind, parent_hash, content, scope, owner, valid_from, valid_until, permission, source_refs, content_hash` |
| ArtifactSnapshot | `revision_id, parent_revision_id, artifacts, snapshot_hash`；基线为空资产，候选是三资产快照 |
| RunResult | `document_id, steps, answer_style, refusal_reason, applied_artifacts, violations, environment_error, unknown_reasons, step_count, tool_call_count` |
| UsePolicy | `revoked_artifact_hashes, revoked_source_ids, allowed_steps`；权威运行输入，独立于历史资产快照，不能由反馈或回滚重写 |
| EvaluationContext | `suite_hash, truth_hash, environment_hash, safety_hash, use_policy, admissions, frozen_clock, valid_until`；admissions 是任务 2 的脱敏准入记录，safety_hash 包含 UsePolicy，所有比较冻结同一上下文 |

AdmissionRecord、ReplayResult、AttributionResult、GraderResult、EvidenceBundle、ApprovalReceipt、ReleaseRecord、ReleaseState、ImprovementReport 在拥有其逻辑的任务补充，统一严格解码与稳定序列化，不提前做平台抽象。

- [ ] **Step 1: 写失败测试。** `test_fixture_counts_and_split_contract` 断言 12/6/16、每片 `development==1` 和 `holdout==3`，开发/验收 family 交集为空；`test_decision_input_has_no_gold` 断言 AgentInput 无 `task_id/success_ref/expected_document_id`。`test_strict_boolean_and_finite_values` 对 `"false"`、1、NaN、负预算断言 ValueError；`test_nested_payload_cannot_mutate_after_hash` 断言外部列表修改不能改变已冻结合同的字节/哈希。

```python
def test_fixture_counts_and_split_contract(lab):
    assert (len(lab.feedback), len(lab.documents), len(lab.tasks)) == (12, 6, 16)
    development = {t.family_id for t in lab.tasks if t.split == "development"}
    holdout = {t.family_id for t in lab.tasks if t.split == "holdout"}
    assert development.isdisjoint(holdout)
    for label in ("knowledge", "procedure", "scope", "safety_recovery"):
        tasks = [t for t in lab.tasks if t.slice == label]
        assert sum(t.split == "development" for t in tasks) == 1
        assert sum(t.split == "holdout" for t in tasks) == 3
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_contracts.py chapter16/tests/test_fixtures.py -q`；应因模块/合同缺失失败，而非依赖版本错误。
- [ ] **Step 3: 实现合同、加载和六份夹具。** F01–F12 语义严格沿用设计表；ReplayCase 的 case_id 固定为来源 F01/F03/F04/F10；F11 的冲突放在独立 billing 域，不污染 F01 的 export 证据。文档为租户 A/B 的当前导出、历史导出与当前步骤说明各三份。基线先做权限过滤再按固定目录顺序选择；A 的旧导出文档排在当前文档前，B 的正确当前文档排第一。当前导出操作必须包含 `open_project, open_data, choose_destination, export, verify_receipt`；历史行为单独定义，不能用当前步骤覆盖。
- [ ] **Step 4: 冻结任务及开发依赖。** knowledge 开发项复现旧文档、procedure 开发项复现缺步骤、scope 开发项复现 A 用户简短偏好，三项为 target；safety_recovery 开发项为非 target 控制。留出项覆盖不同提问 family、历史版本、B 租户、其他用户、过期、撤销、明确安全拒绝及有完整恢复回执的暂时错误。F04/F10 的未恢复环境错误/缺回执用于组 2 和组 4 的故障注入，在同一任务上标明 variant/context，不扩充原 16 项，也不把必然 Unknown 的变体混入可通过正例再偷偷排除。每项使用明确成功条件；安全拒绝可按合同验收，未知执行结果仍阻断激活。开发锁以既有准确版本/哈希为依据，不手写猜测哈希；核心 requirements.in 说明标准库零额外依赖。
- [ ] **Step 5: 运行 GREEN 并提交。** 重跑 Step 2，所有新测试 PASS；追加 family 改 ID/近重复用途测试。仅提交本任务列出的文件：`feat(chapter16): freeze evidence contracts and teaching fixtures`。

### Task 2: 反馈准入、来源敏感隔离与去重

**Files:** Create `chapter16/feedback.py`、`chapter16/tests/test_feedback.py`；Modify `chapter16/contracts.py`，增加 AdmissionRecord。

**Interfaces:** `admit_feedback(records: tuple[FeedbackRecord, ...], sources: tuple[SourceAuthority, ...]) -> tuple[AdmissionRecord, ...]`；AdmissionRecord=`feedback_id, source_id, purpose, family_id, scope, run_ref, disposition, reason_codes, sanitized_payload, source_sensitive, source_refs, evidence_refs`，disposition 为 `accepted/quarantined/merged/unknown`。保留准入后的来源/范围元数据供后续消费，原始敏感载荷不得进入报告。

- [ ] **Step 1: 写失败测试。** 核心断言：`F02.disposition == "merged"`；F07/F09/F12 均 quarantined；F09 脱敏后 `source_sensitive is True` 且再次准入仍隔离；F10/F11 为 unknown。伪造 source_role、超注册表 scope、撤销许可及隐藏验收 purpose 必须阻断。F02 只增加 lineage，不增加独立证据计数。

```python
def test_feedback_dispositions_and_sensitive_lineage(lab):
    results = {r.feedback_id: r for r in admit_feedback(lab.feedback, lab.sources)}
    assert results["F02"].disposition == "merged"
    assert all(results[k].disposition == "quarantined" for k in ("F07", "F09", "F12"))
    assert results["F09"].source_sensitive is True
    assert all(results[k].disposition == "unknown" for k in ("F10", "F11"))
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_feedback.py -q`；缺 admission 实现时失败。
- [ ] **Step 3: 实现准入。** 顺序为严格解码→来源敏感键/演示模式检测→脱敏且保留标记→来源/用途/权限/scope 核验→攻击/隐藏答案隔离→完整性/冲突→去重。source_id/role 来自受信任的采集夹具，不从 payload 的自称身份提升；本实验不实现真实身份认证。已知演示敏感标记使用 `DEMO-SENSITIVE-001`，不放真实密钥或宽泛安全识别承诺。F01/F03/F04/F05/F06/F08 可接受为证据，只有前三类资产来源 F01/F03/F08 能进入可执行候选；F04 不是永久记忆。固定夹具分布为 accepted=6、quarantined=3、merged=1、unknown=2。
- [ ] **Step 4: 运行 GREEN 与合同回归。** `python -B -m pytest chapter16/tests/test_feedback.py chapter16/tests/test_contracts.py -q`；断言敏感原文不出现在序列化结果中，未知反馈没有被合并为成功。
- [ ] **Step 5: 提交。** 精确暂存本任务三文件：`feat(chapter16): gate feedback before turning it into lessons`。

### Task 3: 回放、条件性归因与受限提案

**Files:** Create `chapter16/replay.py`、`chapter16/lessons.py`、`chapter16/tests/test_replay.py`、`chapter16/tests/test_lessons.py`；Modify `chapter16/contracts.py`，增加 ReplayResult/AttributionResult。

**Interfaces:**

- `replay(case: ReplayCase, *, selection: str = "baseline", procedure: str = "baseline") -> ReplayResult`；返回 `status, outcome, missing, evidence_refs`，status=`replayed/environment_error/unknown`，不调用真实模型/工具。
- `attribute(case: ReplayCase) -> AttributionResult`，含 `cause, interventions, unknown_reasons`；每个干预只改变 selection 或 procedure 中一项，报告其他冻结指纹相同。
- `propose_lessons(admissions: tuple[AdmissionRecord, ...], cases: tuple[ReplayCase, ...], *, blocked_families: frozenset[str]) -> tuple[LessonProposal, ...]`；`export_training_candidates(proposals: tuple[LessonProposal, ...], *, blocked_families: frozenset[str]) -> tuple[dict[str, object], ...]` 只消费可追溯的合格发现证据，不读 truth 或留出任务。blocked_families 仅为受控切分审计提供的留出 family ID 集，不含任务答案。

- [ ] **Step 1: 写失败测试。** F01 基线重现旧文档，selection=`scoped_current` 修正选文档；只换 procedure 不能修正该症状。F03 只有补步骤改变验收；F04 为 environment_error、F10 为 unknown。令 discovery 与 holdout family 相同，断言提案/样本导出拒绝。去掉回执不可补造证据。

```python
def test_missing_receipt_remains_unknown(lab):
    case = next(c for c in lab.replays if c.case_id == "F10")
    result = replay(case)
    assert result.status == "unknown"
    assert "tool_receipt" in result.missing
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_replay.py chapter16/tests/test_lessons.py -q`。
- [ ] **Step 3: 实现回放与归因。** 读取固定 tool_tape，打印所替换条件、原/新结果及冻结指纹。推断只能支持夹具条件内的原因假设；候选来自作者编写的有限规则，不由自然语言自动反思生成。
- [ ] **Step 4: 实现提案并运行 GREEN。** F01→knowledge_rule、F03→step_skill、F08→scoped_memory，F05→prompt、F06→harness；F04 输出环境处置而非行为资产。样本导出演示使用 F03 权威步骤及 discovery provenance，禁止复制评分真值。测试单独报告可回放数/总案例数、环境与 Unknown 数量，不把它们放入修复成功分母后消失。
- [ ] **Step 5: 提交。** 本任务五文件：`feat(chapter16): replay failures and produce scoped proposals`。

### Task 4: 让三种改进资产真正生效

**Files:** Create `chapter16/artifacts.py`、`chapter16/agent.py`、`chapter16/tests/test_artifacts.py`、`chapter16/tests/test_agent.py`；Modify `chapter16/tests/conftest.py`。

**Interfaces:** `build_candidate(proposals: tuple[LessonProposal, ...], *, now: str) -> ArtifactSnapshot`；`matching_artifacts(snapshot: ArtifactSnapshot, request: AgentInput, *, policy: UsePolicy, now: str) -> tuple[ArtifactRevision, ...]`；`run_agent(request: AgentInput, documents: tuple[Document, ...], snapshot: ArtifactSnapshot, *, policy: UsePolicy, now: str, variant: str = "scoped") -> RunResult`。variant=`baseline/scoped/blind_control`，盲信变体只在内存教学夹具中使用；policy 为当前权威运行输入，不从旧资产恢复。

本任务在 conftest 新增 `baseline: ArtifactSnapshot` 空资产、`candidate: ArtifactSnapshot` 三资产和 `use_policy: UsePolicy` 夹具；candidate 从合格 F01/F03/F08 提案构造，不用 F05/F06 填入可执行快照。

- [ ] **Step 1: 写失败测试。** 同一 AgentInput 下候选 document_id 与基线不同；step_skill 产生全部必要步骤并记录资产版本；scoped_memory 仅使租户 A 用户 A 的 answer_style=`concise`。A 用户 B、租户 B、历史版本、域不匹配、刚好到期和撤销许可均不消费不匹配资产。匹配资产冲突时返回 unknown，不按列表顺序选择。

```python
def test_step_skill_changes_actual_steps(lab, baseline, candidate, use_policy):
    task = next(t for t in lab.tasks if t.target and t.slice == "procedure")
    gold = next(g for g in lab.truth if g.success_ref == task.success_ref)
    args = dict(policy=use_policy, now="2026-09-28T00:00:00Z")
    before = run_agent(task.agent_input, lab.documents, baseline, **args)
    after = run_agent(task.agent_input, lab.documents, candidate, **args)
    assert not set(gold.required_steps).issubset(before.steps)
    assert set(gold.required_steps).issubset(after.steps)
    assert after.applied_artifacts
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_artifacts.py chapter16/tests/test_agent.py -q`。
- [ ] **Step 3: 实现三种消费机制。** ACL 在文档选择前；knowledge_rule 在对应租户/域/版本内选当前有效文档；step_skill 仅解释 UsePolicy 的固定允许步骤；memory 只调整格式，不改变事实、安全或必要步骤。时间有效期为半开区间 `[valid_from, valid_until)`；UsePolicy 的当前资产/来源撤销表优先于快照中旧的 permission=true。不支持的 prompt/harness/training_data 激活类型拒绝，不执行 Shell/eval。
- [ ] **Step 4: 运行 GREEN。** 记录匹配和未匹配原因、实际 applied_artifacts；过度泛化控制必须在历史/租户/用户反例至少出现一种失败。再次运行无资产基线，原始夹具字节不变。
- [ ] **Step 5: 提交。** 本任务五文件：`feat(chapter16): apply versioned knowledge skills and scoped memory`。

### Task 5: 独立验收与三态门禁

**Files:** Create `chapter16/evaluation.py`、`chapter16/tests/test_evaluation.py`；Modify `chapter16/contracts.py`，增加 GraderResult/EvidenceBundle/GateDecision；Modify `chapter16/tests/conftest.py`，增加 `evaluation_context: EvaluationContext` 夹具，valid_until=`2026-09-29T00:00:00Z`。

**Interfaces:** `grade(task: TaskSpec, result: RunResult, truth: SuccessCondition) -> GraderResult`；`evaluate_pair(tasks: tuple[TaskSpec, ...], documents: tuple[Document, ...], truth: tuple[SuccessCondition, ...], baseline: ArtifactSnapshot, candidate: ArtifactSnapshot, context: EvaluationContext) -> EvidenceBundle`；`decide_gate(evidence: EvidenceBundle) -> GateDecision`。GraderResult=`task_id, status, reason_codes, evidence_refs`；GateDecision=`status, reason_codes`；EvidenceBundle 绑定 baseline/candidate hash、context、来源准入闭包、逐任务成对结果、切片、coverage、Unknown/环境/违规数量与 evidence_hash。

- [ ] **Step 1: 写失败测试。** 三个 target 必须 baseline fail→candidate pass；非 target 开发控制无需 fail→pass。安全越界+Unknown 同时存在时 gate.fail；仅 Unknown/环境/缺切片为 inconclusive；任何原通过变失败或留出切片下降为 fail。baseline/candidate 真值或时钟不同，拒绝比较。Unknown 来源若不在本候选证据闭包中，单独报告，不无条件否决无关候选。

```python
def test_complete_candidate_passes_frozen_gate(lab, baseline, candidate, evaluation_context):
    evidence = evaluate_pair(
        lab.tasks, lab.documents, lab.truth, baseline, candidate, evaluation_context
    )
    assert decide_gate(evidence).status == "pass"
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_evaluation.py -q`。
- [ ] **Step 3: 实现独立评分及门禁。** grade 只按冻结 success_ref 查评分真值，不能由 Agent 自报完成决定。每个任务成对使用相同 TaskSpec.frozen_clock；任务撤销表只与 context.use_policy 的撤销表做并集，不扩大许可，所有任务时钟/撤销条件进入 suite/environment 指纹。先安全 fail，后缺证据 inconclusive，再目标/回归 fail，最后 pass；所有切片同时给 total/pass/fail/unknown/environment_error，硬安全不能平均抵消。expected 状态可验收正确分类，但未知执行结果仍在候选激活证据中阻断，二者分字段。
- [ ] **Step 4: 运行 GREEN。** 源反馈准入闭包内有隔离、Unknown 或不支持的证据时不能提升；改任务内容、gold、文档、权限、固定时钟任一项使旧 context/hash 失效。效率只记录 step_count/tool_call_count，不生成 Token/费用。错误列表保留任务和原因，不只给总分。
- [ ] **Step 5: 提交。** 本任务四文件：`feat(chapter16): evaluate actual assets with independent regression gates`。

### Task 6: 审批、稳定灰度与不可洗白的回滚

**Files:** Create `chapter16/governance.py`、`chapter16/tests/test_governance.py`；Modify `chapter16/contracts.py`，增加 ApprovalReceipt/ReleaseRecord/ReleaseState。

**Interfaces:**

- `make_approval(candidate: ArtifactSnapshot, evidence: EvidenceBundle, *, approver_id: str, allowed_scopes: tuple[Scope, ...], now: str, valid_until: str) -> ApprovalReceipt`：仅可信演练入口使用，approver 必须在固定审批者表中；多资产范围逐项列明，不借全局通配符覆盖不同域。
- `activate(state: ReleaseState, candidate: ArtifactSnapshot, evidence: EvidenceBundle, approval: ApprovalReceipt, context: EvaluationContext, *, now: str) -> ReleaseState`：返回新不可变状态，包含 revision 指针、已用批准和追加历史。
- `assign_cohort(task_ids: tuple[str, ...], *, seed: int = 1601, candidate_count: int = 4) -> dict[str, str]`：按 `sha256(f"{seed}:{task_id}")` 再 task_id 排序，前四为 candidate，其余 baseline，拒绝重复 ID。
- `rollback(state: ReleaseState, target: ArtifactSnapshot, *, reason: str, now: str) -> ReleaseState`：只可回到已知历史快照，不改变到期/撤销过滤。

`ReleaseState` 固定字段 `active, history, used_approvals`；history 是 ReleaseRecord 元组，used_approvals 是 frozenset。`ApprovalReceipt` 含 `approval_id, approver_id, candidate_hash, evidence_hash, context_hash, allowed_scopes, issued_at, valid_until, decision`；`ReleaseRecord` 含 `record_id, event, from_revision, to_revision, approval_ref, evidence_ref, cohort, reason, frozen_clock`，ID 由内容生成，不用 UUID。

- [ ] **Step 1: 写失败测试。** 没批准、伪审批者、范围过宽、到期批准、证据改内容后重算 hash、context 改变及不支持资产全部拒绝；同 evidence/approval 重复激活不能追加第二条历史。16 请求 cohort 恰为 4/12、顺序打乱结果相同。回滚未知版本拒绝，回滚已知版本不复活到期/撤销记忆。

```python
def test_cohort_is_stable_and_has_four_candidate_requests(lab):
    ids = tuple(t.task_id for t in lab.tasks)
    assigned = assign_cohort(ids, seed=1601, candidate_count=4)
    assert sum(v == "candidate" for v in assigned.values()) == 4
    assert sum(v == "baseline" for v in assigned.values()) == 12
    assert assigned == assign_cohort(tuple(reversed(ids)), seed=1601, candidate_count=4)
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_governance.py -q`。
- [ ] **Step 3: 实现受控生命周期。** 固定审批者为 `reviewer-local`，可审批 Scope 在可信夹具中逐项登记，不从反馈加载；绑定内容与 evidence/context 完整哈希，审批范围必须逐项覆盖候选且不得扩大注册表授权范围。已激活 evidence 再使用返回同一 ReleaseState，追加历史数量不变；内容/证据不一致则拒绝而非 no-op。失败停止产生回执，rollback 追加历史，不删除旧资产/报告，不改变当前 UsePolicy 的撤销表。
- [ ] **Step 4: 运行 GREEN。** 模拟已过验收后时钟/权威事实变化的试运行故障，停止候选、恢复历史指针并保留证据；灰度不是改写独立验收集以造失败。报告写明离线 cohort 不估计真实 A/B 收益，回滚不能撤销已发生的外部副作用。
- [ ] **Step 5: 提交。** 本任务三文件：`feat(chapter16): bind approvals and rehearse canary rollback`。

### Task 7: 五组实验、稳定报告和安全输出

**Files:** Create `chapter16/output.py`、`chapter16/experiments.py`、`chapter16/schemas/improvement-report-v1.schema.json`、`chapter16/tests/test_experiments.py`、`chapter16/tests/test_output.py`；Modify `chapter16/contracts.py`，增加 ImprovementReport；生成 `chapter16/reports/group-1.json` 至 `group-5.json`、`improvement-report.json`、`improvement-report.md`、`manifest.json`。

**Interfaces:** `run_group(group: int, lab: FixtureSet) -> dict[str, object]`；`run_all(lab: FixtureSet) -> ImprovementReport`；`write_report_bundle(report: ImprovementReport, destination: Path, *, root: Path, exercises: dict[str, object] | None = None) -> tuple[Path, ...]`；`main(argv: list[str] | None = None) -> int`。output 模块提供 `write_new_json(value: object, destination: Path, *, root: Path) -> Path`，供练习复用。任务 10 完成后 `--group all` 将 solve(1..13) 的规范 payload 传给 exercises，在同一新 bundle 内写练习/manifest；单组运行仍不生成无关练习。

- [ ] **Step 1: 写失败测试。** 组 1 输出 6/3/1/2；组 2 有条件替换与 Unknown 覆盖；组 3 有三资产应用和过度泛化反例；组 4 同时演示 pass/fail/inconclusive；组 5 为 4/12 分配、停止与回滚。用 jsonschema 验证完整报告，篡改 group 数、缺证据/hash、NaN 与绝对路径拒绝。已存在空目录也拒绝。

```python
def test_report_has_stable_version_and_bytes(lab):
    first, second = run_all(lab).to_dict(), run_all(lab).to_dict()
    assert first["schema_version"] == "chapter16.improvement.v1"
    assert len(first["groups"]) == 5
    assert canonical_bytes(first) == canonical_bytes(second)
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_experiments.py chapter16/tests/test_output.py -q`。
- [ ] **Step 3: 实现入口与输出。** schema_version=`chapter16.improvement.v1`，manifest=`chapter16.artifact-manifest.v1`；固定 schema/夹具/合同指纹，不包含输出路径/墙钟。`--group` 接受 1–5/all，`--output` 必填；成功 0，参数错误 2，已有/越界/危险输出 3。目录预留使用原子 mkdir；文件用 exclusive-create，不覆盖。路径解析后检查允许前缀，检查所有已有父级 symlink/junction/reparse point；失败留可解释的部分目录，不静默删除用户文件。单测可显式传入临时“项目根”，真实入口仍绑定仓库根。
- [ ] **Step 4: 运行 GREEN 并验证离线。** 同路径两次/并发写仅一个成功，失败不覆盖已有字节；模拟写失败无越界副作用。monkeypatch socket/urllib/环境读取为抛错，完整实验仍成功；无可选 Provider 路径。CLI 只允许 `chapter16/.runs/`（目录/文件）、`chapter16/reports/`（首次生成规范产物）；练习仅向允许目录写新文件。
- [ ] **Step 5: 两次复现并固定规范报告。** 在两个全新 `.runs/` 子目录运行全组，逐字节比较全部规范产物及 manifest；生成新 `reports/`，不得手改 JSON 修成绩。manifest 固定文件名/bytes/sha256，排除自身，练习在任务 10 另加条目后重新生成全 bundle 到新目录校验。
- [ ] **Step 6: 提交。** 仅上述实现、测试、Schema 和明确八个报告文件：`feat(chapter16): record deterministic local improvement evidence`；不推送网站。

### Task 8: 一手来源与四幕完整书稿

**Files:** Create `book/chapter16.md`、`book/sources/chapter16-sources.md`、`chapter16/tests/test_sources.py`、`chapter16/tests/test_manuscript.py`。

**Interfaces:** 书稿引用固定报告中的原值、已有核心函数与七个固定图名；本任务不实现平台 SDK。test_manuscript 提供 `narrative_han_count(text: str) -> int`，剔除 fenced code、表格行、标题、链接 URL 和脚注定义，再统计叙述汉字；版本记录同时统计全文字符和全文汉字，明确口径。

- [ ] **Step 1: 写失败测试。** 精确章标题、14 主节/30–36 二三级标题、5 个 `实验 16-N` 引用块、5 表、≥5 失败样本、13 连续题号、7 图引用和实验/答案/来源入口；验证明确的离线/本地状态与证据边界，无证据能力或上线宣称交给专家逐句检查，不用会误伤否定句的关键词禁令。来源必须含核对日、发布日/论文固定版本、支持/不支持的结论；产品资料只用一手链接。

```python
def test_manuscript_has_five_named_experiments():
    text = (ROOT / "book/chapter16.md").read_text(encoding="utf-8")
    assert text.startswith("# 第 16 章 从失败中学习：持续改进系统")
    assert all(f"实验 16-{n}" in text for n in range(1, 6))
    assert "../chapter16/reference-answers.md" in text
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_sources.py chapter16/tests/test_manuscript.py -q`；文稿缺失为预期失败，图片存在检查在任务 9 完成后再启用。
- [ ] **Step 3: 复核并写来源台账。** 复核设计稿中的 OpenAI Harness engineering、Anthropic Skill 改进与质量复盘、LangGraph Memory/Interrupts、LangChain 记忆闭环；论文固定 Reflexion v4、Self-Refine v2、GEPA v2。使用本地资料优先，最新产品事实查官方原文并记实际日期；不能用搜索摘要撑结论。逐项记录正文使用位置、限度和实现对照，不照搬性能数字或功能百科。
- [ ] **Step 4: 写第一/二幕。** 从 Atlas 导出问题及三种修复后果开场；用自然语言讲当前修正/持久记忆/系统版本/权重四种改变；反馈→证据→固定回放→原因假设→回归样本→载体。先给读者走完的小例子，再展示 5–12 行关键代码；完整 Schema 不塞正文。
- [ ] **Step 5: 写第三/四幕。** 候选范围、开发/留出隔离、证据/审批绑定、灰度与回滚；独立反例讲反馈污染、历史规则过度泛化、跨租户/用户影响、过期和自我污染。将 Reflexion/Self-Refine/GEPA 放在各自改变对象上，避免合称训练。每图写读图顺序；每实验写输入→中间状态→失败/成功→特有限制；统一结论边界只保留一处。结尾连接第 17 章《多模态与实时 Agent》，链接 OUTLINE，不链接未创建的 chapter17.md。
- [ ] **Step 6: 校核并提交。** 运行 Step 2，目标 1.8–2.5 万叙述汉字；低于目标时只补读者缺失的因果解释/例子，若质量与目标冲突如实记录偏差，不能伪称达标。正文数字从规范报告核对，图路径暂允许任务 9 待生成。提交四文件：`docs(chapter16): explain controlled improvement through evidence`。

### Task 9: 七幅同风格、可编辑、技术正确的图

**Files:** Create `infographic/chapter16/__init__.py`、`infographic/chapter16/generate_diagrams.py`、`infographic/chapter16/README.md`；七份 `.tldr` 与 `book/images/chapter16/` 七份同名 SVG；`chapter16/tests/test_diagrams.py`。

**Interfaces:** `build_scenes() -> tuple[Scene, ...]`、`generate(root: Path) -> tuple[Path, ...]`；纯渲染复用已有 Scene/Node/Edge，新章布局独立。固定 basename：`01-two-improvement-loops`、`02-feedback-evidence-funnel`、`03-replay-and-attribution`、`04-improvement-carriers`、`05-artifact-promotion`、`06-feedback-poisoning`、`07-canary-and-rollback`。

- [ ] **Step 1: 写失败测试。** 恰好 7 图且正文引用全匹配，SVG 有 viewBox/中文标签且无外链资源，Tldraw JSON 可解析、节点和边可对照；关键分支包括 Unknown、候选未批准、内容改变返回验证、过期过滤和不能撤销外部副作用。不生成错字图片或空组件图。

```python
def test_seven_diagram_scene_names_are_unique():
    scenes = build_scenes()
    assert len(scenes) == 7
    assert len({scene.stem for scene in scenes}) == 7
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_diagrams.py -q`。
- [ ] **Step 3: 实现与生成。** 浅纸张、手绘描边、深蓝文字、蓝绿紫橙分区，沿用现有画布/字号规范；概念边界、架构与执行流程各至少一图。图中的顺序、门禁和数据用途与实现一致；生成记录注明矢量渲染，不虚称 AI 栅格生成。
- [ ] **Step 4: 运行 GREEN 并视觉校核。** `python -B -m infographic.chapter16.generate_diagrams`；两次生成字节一致。实际查看每幅，检查箭头因果、交叉、溢出、中文与数字；可用已安装 tldraw CLI 导出至少一个源到 `.runs/` 检查，但不要求装软件或提交 PNG。
- [ ] **Step 5: 提交。** 明确枚举七个图源和七个 SVG，再暂存生成器/说明/测试：`docs(chapter16): add seven editable improvement diagrams`。

### Task 10: 十三道练习、参考答案与读者入口

**Files:** Create `chapter16/exercise_solutions.py`、`chapter16/README.md`、`chapter16/reference-answers.md`、`chapter16/tests/test_reader_tools.py`；Modify `chapter16/experiments.py`，仅接入全组 exercises payload；生成 `chapter16/reports/exercise-results.json`，通过生成器同步 manifest。

**Interfaces:** `solve(number: int) -> dict[str, object]`、`main(argv: list[str] | None = None) -> int`；答案含 `number, difficulty, status, evidence, criteria`，计算题为复算值，解释/设计题为判据。schema_version=`chapter16.exercises.v1`；`--all --output` 写新文件，复用任务 7 输出边界。

- [ ] **Step 1: 写失败测试。** `solve(1..13)` 连续完整且结果可序列化，非法题号拒绝；两次新文件逐字节一致、已有文件 exit=3。覆盖率计算 7/10=0.7、可验证修复 5/7、未决 3/10=0.3 同时显示，不把 5/7 称全体成功率；重复反馈 8 条中 3 条同源只计 6 份独立证据。

```python
def test_all_thirteen_exercises_have_feedback():
    answers = [solve(n) for n in range(1, 14)]
    assert [a["number"] for a in answers] == list(range(1, 14))
    assert all(a["status"] in {"passed", "answered"} for a in answers)
    assert all(a["criteria"] for a in answers)
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_reader_tools.py -k 'exercise or readme' -q`。
- [ ] **Step 3: 编写题目与答案。** 1 改变对象；2 反馈可信度；3 去重算例；4 覆盖与分母；5 回放反证；6 选择载体；7 改作用域反例；8 TTL/撤销；9 审批内容变更；10 Unknown 门禁；11 灰度/回滚；12 攻击反馈与 eval 隔离；13 设计多模态失败闭环。solve 只依赖任务 1–6 的纯函数，不反调 experiments.main/run_all，防止全组入口接入练习后递归。修改/设计题有明确验收标准，不能把自然语言回答写成“代码测试 passed”。
- [ ] **Step 4: 写 README 并运行 GREEN。** 最短运行命令与逐组 `--group 1..5`、固定输入/时钟、怎样读失败、三资产与提案区别、证据边界、相对链接全部可用。答案入口与正文题号一致；预览命令列出 optional dependency，不要求 API Key。生成练习结果并在新目录重新生成 manifest，与规范文件比较。
- [ ] **Step 5: 提交。** 本任务五个源码/文档/测试文件及明确修改的 exercise-results.json/manifest.json：`docs(chapter16): add thirteen exercises and reader quickstart`。

### Task 11: 本地预览与桌面/移动可读性

**Files:** Create `chapter16/preview.py`、`chapter16/tests/test_preview.py`、`book/check_chapter16_preview.mjs`。

**Interfaces:** `build_preview(root: Path, *, output: Path | None = None) -> Path`，默认 `chapter16/preview-pages/index.html`；只允许该工程该预览子目录，无远程运行脚本。本地预览可重新生成自身构建物，不复用报告覆盖逻辑；不得改书稿或站点。

- [ ] **Step 1: 写失败测试。** 恰 7 figure、7 可点原图、5 table-wrap，图片链接为 `../../book/images/chapter16/`；代码/表/宽图局部滚动，无远程 JS/CSS；任何工程外、预览目录外或危险父链拒绝。

```python
def test_preview_contains_seven_figures_and_five_tables():
    html = build_preview(ROOT).read_text(encoding="utf-8")
    assert html.count("<figure>") == 7
    assert html.count('class="table-wrap"') == 5
    assert "../../book/images/chapter16/" in html
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_preview.py -q`。
- [ ] **Step 3: 实现。** 参考第 15 章预览布局而不直接调用其书稿函数；中文、脚注、标题锚点、图片与相对链接正确。手机宽图最小 760px 放在自身滚动容器，页面不能横向溢出。
- [ ] **Step 4: 运行 GREEN 与实测。** `python -B -m chapter16.preview`；`node book/check_chapter16_preview.mjs` 使用已安装 Edge/Playwright，1440×1000 与 390×844。断言图全部加载、7 figure、5 表、brokenFragments=0、documentWidth≤viewportWidth；记录 console/pageerror/requestfailed。截图留 `chapter16/preview-pages/screenshots/`，实际查看全页及图 2/5/7，不能仅根据 DOM 判断可读性。
- [ ] **Step 5: 提交。** 三个源码/测试文件，不暂存 HTML/截图：`feat(chapter16): preview the local candidate on desktop and mobile`。

### Task 12: 版本保护、双视角审稿与最终本地候选

**Files:** Create `book/reviews/chapter16-review-codex-v1.0-rc1.md`、`book/versions/chapter16-v1.0-rc1.md`、`chapter16/tests/test_delivery.py`；Modify `AGENTS.md`、`book/versions/CHAPTER_VERSIONS.md`、`docs/MIGRATION_MANIFEST.md`、`.github/workflows/ci.yml`、`tests/test_workflow_contract.py`、`tests/test_build_site.py`。复审如需实质修稿，先新增 `book/versions/chapter16-draft-before-review/` 和 `chapter16/report-history/draft-before-review/` 快照，不改旧章或旧报告。

**Interfaces:** 本地 RC1 版本记录包含环境/依赖、实际命令与结果、规范哈希、统计口径、已证明/未证明；审稿按 reader/expert 分类列严重度、位置、建议、处置和验证证据。新增测试 `test_chapter16_stays_out_of_public_tree` 及 `test_old_chapters_and_rc_history_unchanged`。

- [ ] **Step 1: 写失败测试。** 本地候选状态/版本记录不存在时失败；公开 manifest 仍 14 published 且 15/16 planned，无第 16 章公开文件。将本地 chapter16 正文/图/报告放入 build_site 的临时测试仓库，输出不含这些文件。旧章节、RC1/RC2 和源台账相对基线 diff 为空。

```python
def test_local_candidate_has_truthful_version_record():
    record = (ROOT / "book/versions/chapter16-v1.0-rc1.md").read_text(encoding="utf-8")
    assert "本地" in record and "未发布" in record
    assert "已证明" in record and "未证明" in record
```

- [ ] **Step 2: 运行 RED。** `python -B -m pytest chapter16/tests/test_delivery.py -q`；随后最小更新 AGENTS 和版本台账。迁移清单只更新原 `book/versions/CHAPTER_VERSIONS.md` 行的 LF bytes/sha256 与核对日，保留原 source/commit，不给新章伪造迁移来源。
- [ ] **Step 3: 接入 CI 并运行 GREEN。** 在现有 CI 新增 chapter16 的锁定候选测试环境和命令，相应 workflow contract 测试固定准确片段；不改发布工作流、触发条件或 allowlist。检查 `git diff` 仅触及允许文件。
- [ ] **Step 4: 完成双视角自审。** 读者检查：能否不用读 Schema 复述全闭环、每个新术语是否有例子、长段是否承载新解释、每实验是否能读懂失败。专家检查：归因条件、gold 隔离、真实资产消费、scope/TTL、Unknown/环境分母、审批绑定和回滚限制是否准确。修订前保留已冻结稿/图/报告快照；正文归档可修正相对链接，另记录原提交与原字节哈希，JSON 保持原字节，代码版本由原提交恢复。高优先级代码问题先新增 RED 回归再修。
- [ ] **Step 5: 新上下文整分支只读复审。** 按 requesting-code-review 派发一次 reviewer，读设计、计划、规范报告、正文/图/代码及基线 diff；这是 native 结束审查，不为每任务生成 Agent。使用当前工具允许的最强适用模型，不抄旧配置中不可用的模型名。重要问题一次修复流程闭环，不声称未做的二次独立认证。
- [ ] **Step 6: 运行下面的最终验收矩阵。** 每条记录实际 exit code、数量/哈希、环境与限制；不要根目录混合收集全部独立包后把依赖缺失改成 skip。新报告输出目录必须未存在，不删旧报告换取复现。

| 检查 | 命令或判据 |
| --- | --- |
| 第 16 章与仓库合同 | `python -B -m pytest chapter16/tests tests -q`，无失败 |
| 旧候选回归 | `python -B -m pytest chapter15/tests -q`，记录实际项数，不声称覆盖其他依赖环境 |
| 五组复现 | `python -B -m chapter16.experiments --group all --output chapter16/.runs/rc1-verified-a` 与另一个全新 `rc1-verified-b`，逐文件/manifest 字节一致且符合 Schema |
| 十三题复现 | `python -B -m chapter16.exercise_solutions --all --output chapter16/.runs/rc1-exercises-a.json` 与另一个新文件，和规范结果哈希一致 |
| 排版合同 | `npm test --prefix book`，记录实际通过数 |
| 桌面/手机预览 | `python -B -m chapter16.preview`、`node book/check_chapter16_preview.mjs`，7 图/5 表/无全页横向溢出，人工查看关键图 |
| 当前与历史安全 | `python -B scripts/check_repository.py --root . --git-history`；不扩大既有精确历史豁免 |
| 本地公开源装配与 strict | `python -B scripts/build_site.py --root . --output _web`、`python -B -m mkdocs build --strict`；构建前确认 `_web`/`site` 是工程内生成物且无用户资料，不部署 |
| 未发布与旧稿保护 | manifest 版本/状态不变；`_web` 中无 chapter15/16；第 1–15 章原稿、图及已归档版本相对基线没有更改 |

- [ ] **Step 7: 写版本记录并创建候选提交。** 记录最后内容提交、验收日期、hash 和证据边界，版本记录自身提交由 Git 历史确定，不写不可能自引用的 HEAD。只暂存 Files 块允许的精确文件：`docs(book): record chapter 16 local rc1 and review closure`。最后检查 clean status、未推送/未发布，将正文、本地预览、实验入口、审稿/版本记录路径交给用户。

## Plan Self-Review and Handoff

本计划自检覆盖设计的 13 节：正文与相邻章边界在任务 8；数据与准入在 1–2；回放/归因/载体在 3–4；独立验收/审批/灰度/失效在 5–6；五组报告在 7；来源/书稿在 8；图/练习/预览在 9–11；历史保护与最终证据在 12。Review Focus 五类输入分别有指定任务测试。

接口只沿合同向下传递：AgentInput 不含评分真值；admissions 不携带原始敏感载荷；EvidenceBundle 的来源闭包只绑定本候选相关证据；ApprovalReceipt 独立于候选；过期在消费时再次检查。任何正文数字以生成报告为准，计划里的教学算例不是实验实测成绩。

本轮只保存和审阅此实施计划，不执行任务 checkbox。请用户确认计划是否符合意图；确认后使用已经选定的 native 方法实施，不再询问执行方式，也不把计划批准解释为 GitHub 或网站发布授权。
