# 第 18 章 Multi-Agent 与最终系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一章通俗、证据可复算的收官书稿及自包含离线实验包，解释何时协作、怎样交接、如何汇合与验收，不把 Agent 数量当成能力。

**Architecture:** 四幕正文围绕三个独立教学场景展开。固定决策策略驱动独立 Worker，由共同网关管理授权、全局预算和控制权；知识证据与代码提议分别汇合，最终由主控验收。五组二十案例派生规范报告，真实教学补丁与冻结测试证明有限业务合同。

**Tech Stack:** Python 3.11 标准库；既有 pytest 9.0.2、jsonschema 4.26.0、Markdown 3.10.2；既有 SVG/Tldraw 图源、Node 24.15.0、Playwright 1.62.1、Edge 和 MkDocs 1.6.1。不安装新框架。

**Spec:** [已确认设计规格](../specs/2026-10-01-chapter18-multi-agent-final-system-design.md)。规格提交 `2882508`；用户随后回复“native 执行”，确认书面设计并指定执行方法。该历史规格不回写；本计划等待用户审阅，尚未实施。

## Global Constraints

- 工作仓库为本书独立仓库，分支 `codex/chapter18-multi-agent-final-system`；第 17 章 RC3 基线为 `c2cd958912a5a2c0f750ef31617927c694903979`。所有用户交付物留在本仓库。
- 选定 **native**：本会话逐任务实施，最后一次新上下文整分支只读审稿；不逐任务派实现代理。审稿时保留实际模型，不能声称用了不可用的模型。
- 标题为“第 18 章 Multi-Agent 与最终系统：不是 Agent 越多越好”；四幕、三个场景，2.2–2.8 万叙述汉字、28–36 个二/三级标题、7 图、4–5 表、5 组实验、至少 4 类失败、13 题。
- 叙述汉字和含代码/Markdown 的总字符数分开记录；不得以 Schema、重复警告或长日志填充正文。实验框采用 `> **实验 18-N ★★：...**`。
- Runtime 仅标准库，无 Live Provider、环境密钥读取和默认联网；固定策略结果不是模型能力、真实速度或经济收益。无 Provider Usage 时不填 Token/费用。
- 逻辑并行示例为 7、11、5 单位：串行 23；理想关键路径 11，加委派 2、汇总 3 等于 16。逻辑时间不是实测秒数。
- 默认在途 3、深度 2、Handoff 4、每 Worker 决策 4、暂时错误额外重试 1；全局工具 16，其中最终验证保留 2，子任务和重试共用剩余 14。保留额不是额外额度。
- 最终状态限 `answer / verified / unknown / blocked / conflict / needs_approval / stopped`；Worker 的 `done` 不是主控验收。Schema 为 `chapter18.team.v1`。
- 规范包固定九文件：`group-1.json` 至 `group-5.json`、`team-report.json`、`summary.md`、`exercise-results.json`、`manifest.json`；新输出目录仅在 `chapter18/.runs/` 或 `chapter18/reports/` 下，禁止覆盖。
- 知识路径为显式事实索引与来源治理，不称真实 Embedding/Reranker或自动语义蕴含；代码路径实际改可信夹具、跑冻结测试与独立行为核对，不执行任意读者命令。
- 不动态导入旧章节 Runtime；图形可复用现有通用 Scene 渲染器，但不得修改旧图源。上下文和目录隔离不称操作系统沙箱。
- 不改第 1–17 章正文、代码、图、报告及历史记录；公开 manifest 保持 `0.14.0`，第 18 章不进入 allowlist。不推送、合并、部署、创建 PR/tag、翻译、生成 PDF、运行 Docker 或真实 Provider。
- 新增本地 `v1.0-rc1`；最后仅更新本地状态、版本账及迁移账中版本账的派生字节数/哈希。真实安全、恶意并发目录替换、企业部署不在本轮证明范围。

## Review Focus

1. 有效资料互相矛盾，不只是新旧版本过滤：两份均合格仍须 `conflict`，拒绝多数拼接；Task 2、5 的断言覆盖。
2. 子任务请求更宽工具/来源或更换身份：授权只能缩小，缺必要上下文为 `unknown`；Task 1–3 覆盖，低权限报告不能带受限引句。
3. 晚到、重复或归属错误结果：不接纳错误 task/attempt，停止后不复活，取消后已发生写入保留回执；Task 3–4 覆盖。
4. 重试、交接和部分超时：共同预算不能重置，验证额度保留，部分覆盖显式暴露，循环有限停止；Task 3、5 覆盖。
5. 路径/reparse、半成品报告与复现污染：拒绝边界外写入和已存在目录，报告不合格不能发布完整包，两次输出无真实时间/机器路径；Task 4、7、10 覆盖。

---

## File Structure 与依赖顺序

以下路径相对于本书仓库。预览、截图与实际实验工作区是忽略的本地输出；测试内部临时目录不是交付物。

| 责任 | 新建文件/目录 |
| --- | --- |
| 合同、材料与固定输入 | `chapter18/__init__.py`、`contracts.py`、`fixtures.py`、`fixtures/knowledge.json`、`fixtures/knowledge/` 原始 Markdown、`fixtures/cases.json`、`fixtures/link-checker/{src,tests}/`、`requirements-dev.txt`、`requirements-preview.txt` |
| 来源治理与上下文 | `chapter18/evidence.py`、`context.py` |
| 独立决策、预算、协作 | `chapter18/policy.py`、`budget.py`、`runtime.py` |
| 可信工作区、统一写入、验收 | `chapter18/workspace.py`、`integration.py`、`verifier.py` |
| 场景与最小入口 | `chapter18/cases.py`、`system.py`、`quickstart.py` |
| 答案、报告、读者入口 | `chapter18/exercise_solutions.py`、`reference-answers.md`、`reporting.py`、`output.py`、`experiments.py`、`schemas/report-v1.schema.json`、`README.md`、`IMPLEMENTATION.md`、`reports/reference-rc1/` |
| 原创图 | `infographic/chapter18/__init__.py`、`generate_diagrams.py`、`README.md`、七份 `.tldr`；`book/images/chapter18/` 七份 SVG |
| 书稿、来源、审稿、版本 | `book/chapter18.md`、`book/sources/chapter18-sources.md`、`book/reviews/chapter18-review-codex-v1.0-rc1.md`、`book/versions/chapter18-v1.0-rc1.md` |
| 本地预览 | `chapter18/preview.py`、`book/check_chapter18_preview.mjs`；忽略输出 `chapter18/preview-pages/` |
| 测试 | `chapter18/tests/test_contracts.py`、`test_fixtures.py`、`test_evidence.py`、`test_context.py`、`test_budget.py`、`test_runtime.py`、`test_integration.py`、`test_verifier.py`、`test_cases.py`、`test_exercises.py`、`test_reporting.py`、`test_output.py`、`test_schema.py`、`test_diagrams.py`、`test_manuscript.py`、`test_sources.py`、`test_preview.py`、`test_delivery.py` |

仅修改 `.gitignore` 的第 18 章本地运行忽略项，以及最终 `AGENTS.md`、`book/versions/CHAPTER_VERSIONS.md`、`docs/MIGRATION_MANIFEST.md` 的限定字段。不新增根构建系统。

## Shared Interfaces（由 Task 1 定义）

`JsonObject = dict[str, object]`；`CaseResult`、`TeamReport`、`ExerciseReport` 为该类型别名，编码前显式递归转换 dataclass/tuple。`Scalar = str | int | bool | None`；`FinalStatus` 是 Global Constraints 中七值 Literal。下列记录除 `RunState` 外为 frozen dataclass，集合用 tuple/frozenset；不能在 frozen 内嵌可变字典。JSON 报告是交付编码，不作为 Worker 可共享修改的状态。

- `BudgetLimits(tool_calls: int = 16, verifier_reserve: int = 2, inflight: int = 3, depth: int = 2, handoffs: int = 4, worker_decisions: int = 4, extra_retries: int = 1)`：所有值非负，保留额不大于总额；额度可收紧。
- `TaskPacket(task_id: str, parent_id: str | None, worker_id: str, goal: str, principal: str, target_version: str, input_refs: tuple[str, ...], allowed_sources: frozenset[str], allowed_tools: frozenset[str], allowed_writes: frozenset[str], output_requirements: tuple[str, ...], base_hashes: tuple[tuple[str, str], ...], limits: BudgetLimits, depth: int)`。
- `SourceDoc(source_id: str, location: str, version: str, principals: frozenset[str], eligible: bool, text: str, facts: tuple[tuple[str, str], ...], digest: str)`；事实键/值是夹具明确标注的教学真值，不自动从自然语言推导。
- `EvidenceRef(source_id: str, location: str, digest: str, version: str, eligible: bool, quote: str)`；`Claim(key: str, value: str, evidence: tuple[EvidenceRef, ...])`。
- `ContextSnapshot(task_id: str, principal: str, target_version: str, sent: tuple[tuple[str, str], ...], sent_digest: str, source_digests: tuple[tuple[str, str], ...])`：`sent` 的规范 JSON 摘要与原资料字节摘要分别保存。
- `ToolCall(call_id: str, tool: str, arguments: tuple[tuple[str, str], ...])`；`ToolOutcome(call_id: str, status: Literal['ok', 'transient_error', 'permanent_error', 'timeout', 'denied'], data: tuple[tuple[str, Scalar], ...])`；`Decision(kind: Literal['tool', 'result', 'delegate', 'handoff'], call: ToolCall | None, result: WorkerResult | None, packet: TaskPacket | None, next_controller: str | None)`：各 kind 的字段组合须校验，禁止含糊兼具执行与完成。
- `WorkerResult(task_id: str, attempt_id: str, worker_id: str, state: Literal['done', 'unknown', 'failed', 'cancelled'], claims: tuple[Claim, ...], missing: tuple[str, ...], patch_ids: tuple[str, ...], decisions: int, tool_calls: int)`；`WorkerObservation(outcomes: tuple[ToolOutcome, ...], results: tuple[WorkerResult, ...])`。
- `Event(event_id: str, kind: str, task_id: str, attempt_id: str, parent_event_id: str | None, data: tuple[tuple[str, Scalar], ...])`：复杂证据通过稳定引用关联不可变结果/回执，规范事件 ID 由输入序号派生，不用 UUID。
- `RunState(controller: str, principal: str, tasks: dict[str, TaskPacket], attempts: dict[str, str], results: tuple[WorkerResult, ...], shared_version: str, tool_calls: int, handoffs: int, pending_approval: str | None, status: FinalStatus | None, reason_code: str | None, receipts: tuple[ActionReceipt, ...], acceptance: tuple[str, ...], events: tuple[Event, ...])`。
- `PatchProposal(proposal_id: str, action_id: str, task_id: str, path: str, before_digest: str, replacement: str)`；`Verification(passed: bool, tests_passed: int, tests_total: int, behavior_passed: bool, evidence: tuple[str, ...], reason_code: str)`。
- `ActionReceipt(proposal_id: str, action_id: str, path: str, allowed_writes: tuple[str, ...], before_digest: str | None, after_digest: str | None, executed: bool, verification: Verification | None, status: FinalStatus, reason_code: str)`。
- `EvidenceVerdict(status: FinalStatus, claims: tuple[Claim, ...], distinct_sources: tuple[str, ...], missing: tuple[str, ...], reason_code: str)`。

JSON 跨任务合同：`CaseResult` 必含 `case_id/group/status/reason_code/input_proof/trajectory/worker_results/receipts/metrics/acceptance/limits`；`input_proof` 分别保存原文件 `source_digests`、真实发送 `context_digests` 和实际授权 `packets`。`metrics` 必含 `coverage_numerator/coverage_denominator/duplicate_tasks/distinct_eligible_sources/unresolved_conflicts/policy_refusals/stale_patch_refusals/duplicate_writes/decisions/tool_calls/budget_limit/budget_remaining/verifier_calls/security_violations`，计数全为非负int、预算守恒，来源数量不能替代证据有效性。`TeamReport` 必含 `schema_version/groups/summary/limits`，`groups` 为按1–5排序的五个 `{group: int, cases: list[CaseResult]}`，summary是逐案metrics的归约。`ExerciseReport.answers` 每条含 `exercise_id/kind/answer/computation/evidence_refs/rubric`，不存在的代码证据不能填通过。

### Task 1: 固定材料、身份合同与可信夹具

**Files:** 创建 File Structure 中合同/材料文件及 `test_contracts.py`、`test_fixtures.py`；修改 `.gitignore` 加 `chapter18/.runs/`。测试锁文件复制第 17 章现有完整哈希锁，预览锁固定 Markdown 3.10.2。

**Interfaces:** 输出上述类型；`validate_packet(packet: TaskPacket, parent: TaskPacket | None = None) -> None`；`load_sources(root: Path) -> tuple[SourceDoc, ...]`；`load_case_specs(root: Path) -> tuple[JsonObject, ...]`；`create_workspace(root: Path, destination: Path) -> Path`。实际工作区仅在新的 `chapter18/.runs/` 子目录；测试可用包含同样相对树的临时仓库。

- [ ] 写测试：`BudgetLimits().tool_calls == 16`、`verifier_reserve == 2`、`inflight == 3`、`depth == 2`、`handoffs == 4`、`worker_decisions == 4`、`extra_retries == 1`；`len(load_case_specs(root)) == 20`；每组四个 ID 唯一。非十六进制 SHA-256、绝对/父级路径、负额度、保留额大于总额须 `ValueError`。
- [ ] 写 `test_child_cannot_expand_scope_or_change_principal`，用 `dataclasses.replace` 将子包 sources/tools/writes 各扩大一次、principal 改一次，四类均 `pytest.raises(ValueError)`；缺授权来源不创建任何秘密副本。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_contracts.py chapter18/tests/test_fixtures.py -q`，预期缺模块/类型的收集错误（RED）。
- [ ] 实现合同校验和固定材料。`knowledge.json` 仅为索引/事实标签，原文位于 `fixtures/knowledge/{public-current,public-old,restricted-current,conflict-a,conflict-b,parallel-product,parallel-support}.md`；`SourceDoc.digest` 取各原始文件真实字节 SHA-256。两份 conflict 资料均有效。链接夹具固定四个 unittest（基线三过一败），回归覆盖外链、根相对路径、无链接；唯一待修复行为为嵌套文件相对链接。允许修改 `src/linkcheck.py` 与供独立修改案例使用的 `src/policy.py`，测试始终受保护。
- [ ] 用同一测试命令确认 GREEN；记录锁版本与可信夹具摘要，不能把夹具预期失败当本章测试失败。
- [ ] 精确暂存上述文件及 `.gitignore`，本地提交 `feat(chapter18): define scoped collaboration contracts and fixtures`。

### Task 2: 最小上下文与可核对知识证据

**Files:** 创建 `chapter18/context.py`、`evidence.py`、`test_context.py`、`test_evidence.py`。

**Interfaces:** 消费 Task 1 类型与 `load_sources`。输出 `assemble_context(packet: TaskPacket, sources: tuple[SourceDoc, ...]) -> ContextSnapshot`；`check_claims(packet: TaskPacket, claims: tuple[Claim, ...], sources: tuple[SourceDoc, ...]) -> EvidenceVerdict`；`knowledge_tool(packet: TaskPacket, call: ToolCall, sources: tuple[SourceDoc, ...]) -> ToolOutcome`，工具只限读取允许的事实键与原文片段。

- [ ] 写测试：公开包 `snapshot.sent` 不含受限文本；改变未发送资料不改变 `sent_digest`，改变发送片段改变它；`sent_digest` 不借用整份文件 digest；目标版本缺片段时结果缺项而非编造。
- [ ] 写测试：三个相同引用 `distinct_sources == ('public-current',)`；不存在来源、引句不在原文、内容摘要变化均为 `unknown`；两个同时 eligible/current 的相反事实 `status == 'conflict'`；返回前权限失效为 `blocked` 且 verdict 无受限 quote。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_context.py chapter18/tests/test_evidence.py -q`，预期缺实现（RED）。
- [ ] 实现可见资料过滤与规范片段摘要，核对来源、原字节、版本、授权、引句与显式事实字段。原文引用与事实验证分别记录，避免写成自动语义蕴含；同源投票不得使无依据 Claim 获得 `answer`。
- [ ] 同命令及 Task 1 测试确认 GREEN；检查错误日志/结果不泄露被拒绝原文。
- [ ] 精确暂存这四个文件，本地提交 `feat(chapter18): preserve scoped context and check source evidence`。

### Task 3: 独立 Worker、委派/Handoff 与共同运行预算

**Files:** 创建 `chapter18/policy.py`、`budget.py`、`runtime.py`、`test_budget.py`、`test_runtime.py`。

**Interfaces:** `DecisionPolicy.next(self, packet: TaskPacket, observation: WorkerObservation) -> Decision` 为 Protocol；`ScriptedPolicy(script: tuple[Decision, ...])` 实现它。`BudgetLedger(limits: BudgetLimits)` 提供 `charge(self, *, purpose: Literal['worker', 'verifier']) -> bool`、只读 `used: int`、`remaining: int`。`TeamRuntime(state: RunState, ledger: BudgetLedger, executor: Callable[[TaskPacket, ToolCall], ToolOutcome])` 提供 `start(packet: TaskPacket, policy: DecisionPolicy, *, attempt_id: str) -> None`、`step(task_id: str) -> None`、`accept_result(result: WorkerResult) -> bool`、`handoff(target: str, *, task_id: str) -> bool`、`cancel(reason: str) -> None`；`state`、`observations`、`ledger` 可读。

- [ ] 写测试：委派返回后 `controller == 'manager'`；Handoff 后 `controller == 'expert'` 且 principal 未变；两个 Worker 的观察历史不相同也不互相注入；任务4步、在途3、深度2均严格限额。
- [ ] 写测试：14 次 worker charge 为真，第15次为假；两次 verifier charge 为真，第三次为假；最终 `used == 16`、`remaining == 0`。收紧 total8/reserve2，暂时错误一次重试计费，两次错误后不再重试且只读实际账本。
- [ ] 写测试：结果 task/attempt/worker 任一错配均 `accept_result(...) is False`；同一结果重复接收不增结果数；cancel 后有效晚到结果不得改变 `status == 'stopped'`；A→B→A 在第5次交接提议停止，`handoffs == 4`。超时不得填“全覆盖”。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_budget.py chapter18/tests/test_runtime.py -q`，预期缺 Runtime（RED）。
- [ ] 实现有限状态推进、共同计费和因果事件。工具 gateway 先验授权，再执行；实际调用含暂时失败/重试消费额度，被政策拒绝而未调用不伪造调用。逻辑完成顺序由输入 schedule 控制；ScriptedPolicy只提议结果，Runtime以账本的实际 decisions/tool_calls冻结最终WorkerResult，不采信脚本自报用量，不伪造墙钟。
- [ ] 同命令和已有本章测试确认 GREEN；按两种完成顺序核对相同接受结果与主控结论。
- [ ] 精确暂存六个文件，本地提交 `feat(chapter18): control delegation handoffs and shared budgets`。

### Task 4: 独立补丁、单写入者、批准与真实验收

**Files:** 创建 `chapter18/workspace.py`、`integration.py`、`verifier.py`、`test_integration.py`、`test_verifier.py`。

**Interfaces:** `snapshot_workspace(root: Path, source: Path, destination: Path) -> Path`；`propose_patch(packet: TaskPacket, workspace: Path, *, path: str, replacement: str, proposal_id: str, action_id: str) -> PatchProposal`；`verify_workspace(workspace: Path, *, fixture_root: Path) -> Verification`；`IntegrationGateway(workspace: Path, packet: TaskPacket, state: RunState, ledger: BudgetLedger, *, fixture_root: Path)` 提供 `apply(proposal: PatchProposal, *, approved: bool) -> ActionReceipt`。Gateway 的幂等账本随本次 RunState 维护，不能每次调用新建后忘掉回执；验证前为冻结测试和行为核对分别 charge 一次 verifier，额度不够不能开始验收或标 verified。

- [ ] 写测试：未批准 `executed is False` 且 `status == 'needs_approval'`；修改 `tests/test_existing.py`、越界或 reparse 路径为 `blocked`；第一提议执行后第二旧基线提议为 `conflict`/`stale_patch` 且保留第一次实际字节。
- [ ] 写测试：重复 action_id/同内容仅一次真实写入，回执重放；同 action_id 不同内容拒绝；不同源码路径合并后仍须四个冻结测试与行为验收，不能仅因路径不冲突标 `verified`。
- [ ] 写测试：可信基线 `tests_passed == 3`、`tests_total == 4`、`passed is False`；修复后四过及 `behavior_passed is True`，Gateway 使用同一 ledger 且验证消耗2次；篡改工作区测试副本不能绕过 fixture_root 的冻结测试摘要。cancel 发生在写入后 `state.receipts` 保留 executed 回执、运行仍 stopped。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_integration.py chapter18/tests/test_verifier.py -q`，预期缺 Gateway/Verifier（RED）。
- [ ] 实现单一写入入口的路径/授权/批准/基线/幂等检查，保存独立提议，不准 Worker 直接改集成源码。可信测试只通过 `sys.executable -B -m unittest discover` 执行固定夹具，另核对嵌套相对链接行为；测试过程消耗最后验证预算，调用与通过分开。
- [ ] 同命令及已有本章测试确认 GREEN；将实际 before/after digest、四测试与独立行为证据连到 ActionReceipt；明确目录隔离不是 OS 沙箱。
- [ ] 精确暂存五个文件，本地提交 `feat(chapter18): integrate approved patches with independent verification`。

### Task 5: 二十个案例与最小知识/代码入口

**Files:** 创建 `chapter18/cases.py`、`system.py`、`quickstart.py`、`test_cases.py`；Task 1 的 `fixtures/cases.json` 仅补具体合法参数，不改下列 ID/数量。

**Interfaces:** `run_case(case_id: str, *, root: Path, workdir: Path, order: tuple[str, ...] = ()) -> CaseResult`；`run_group(group: int, *, root: Path, workdir: Path) -> tuple[CaseResult, ...]`；`run_system(kind: Literal['knowledge', 'repair'], packet: TaskPacket, *, root: Path, workdir: Path, approved: bool = False) -> CaseResult`；quickstart 的 `main(argv: list[str] | None = None) -> int` 支持 `--mode knowledge|repair --workdir ...`，repair 只有显式 `--approve` 可执行。

| 组 | 固定 ID |
| --- | --- |
| 1 | `single-sufficient`, `parallel-separated`, `serial-dependency`, `duplicate-research` |
| 2 | `delegation-return`, `handoff-transfer`, `context-not-forwarded`, `scope-escalation` |
| 3 | `source-version-conflict`, `same-source-three-votes`, `stale-patch`, `disjoint-patches` |
| 4 | `one-worker-timeout`, `global-budget-exhausted`, `cancel-late-result`, `handoff-cycle` |
| 5 | `kb-verified-answer`, `kb-permission-denied`, `repair-verified`, `repair-needs-approval` |

- [ ] 写逐案测试：每组恰四案且覆盖全部 ID；`parallel-separated` 的 schedule 计算 `serial_units == 23`、`parallel_units == 16`；`same-source-three-votes` 的 distinct eligible sources为1、无依据结论 unknown；矛盾案 conflict、旧补丁拒绝而非覆盖。
- [ ] 写测试：预算耗尽案显式 total8/reserve2，worker调用不得超过6；超时案保留 missing 与已完成项；knowledge 公共路径 answer，受限路径 blocked 且公开结果不含秘密；repair批准路径真实 diff + verified，无批准路径 needs_approval且无写入。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_cases.py -q`，预期缺案例入口（RED）。
- [ ] 实现案例由政策/工具/事件驱动，状态与计数来自 Runtime。不同完成顺序的事件先后可不同，规范报告按稳定因果拓扑排序；保留 schedule为输入，不声称实测并发。危险“后写覆盖”的对照仅在内存字典，不关闭真实 Gateway。
- [ ] 同命令和现有本章测试确认 GREEN；运行两条 quickstart（用两个新 workdir），留可复核知识引用、实际补丁及测试输出，不输出 API Key 指引。
- [ ] 精确暂存四个文件及有变化的案例夹具，本地提交 `feat(chapter18): exercise twenty collaboration cases and final paths`。

### Task 6: 十三道可复算答案

**Files:** 创建 `chapter18/exercise_solutions.py`、`reference-answers.md`、`test_exercises.py`。

**Interfaces:** `solution_payload(*, root: Path, workdir: Path) -> ExerciseReport`，顶层 `schema_version='chapter18.exercises.v1'`、`answers` 含十三条；`main(argv: list[str] | None = None) -> int` 支持 `--all --output ...`，独立 JSON 只写新 `chapter18/.runs/` 路径。与实验同根但单独工作区执行代码题；Task 7 统一实现拒绝覆盖写出。

- [ ] 写测试：`len(answers) == 13`；第3题计算给23、16及协调成本反转条件；第9题默认worker可用14、验证2、总16；代码题第8/10/11/12包含实际案例的 evidence refs；设计题第13含身份/数据/动作/持久性/预算/回滚判据，不按术语数评分。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_exercises.py -q`，预期缺答案实现（RED）。
- [ ] 实现计算/代码题实际复算，完整题目顺序为：边界、可拆分、排程、任务说明、缺上下文、同源意见、矛盾来源、旧补丁、额度、取消、权限、验收、生产取舍。答案 Markdown 给过程、命令和错误判据，非一句“参见正文”。
- [ ] 同命令确认 GREEN；独立两次 `solution_payload` 规范编码一致。CLI 写出验证并入 Task 7，避免本任务先实现另一套输出边界。
- [ ] 精确暂存三个文件，本地提交 `docs(chapter18): add thirteen computed exercise solutions`。

### Task 7: 派生指标、Schema 与安全规范包

**Files:** 创建 `chapter18/reporting.py`、`output.py`、`experiments.py`、`schemas/report-v1.schema.json`、`test_reporting.py`、`test_schema.py`、`test_output.py`；接通 Task 6 CLI；生成 `chapter18/reports/reference-rc1/` 九文件。

**Interfaces:** `build_report(groups: tuple[tuple[CaseResult, ...], ...]) -> TeamReport`；`validate_report(report: TeamReport) -> None`；`canonical_json(payload: object) -> bytes`；`write_bundle(root: Path, destination: Path, report: TeamReport, exercises: ExerciseReport) -> tuple[Path, ...]`；`write_answer(root: Path, destination: Path, exercises: ExerciseReport) -> Path`；`run_all(*, root: Path, workdir: Path) -> TeamReport`；实验 `main(argv: list[str] | None = None) -> int` 支持 `--group all|1..5 --output ...`，单组输出明确 partial、不伪装九文件完整版。

- [ ] 写测试：总报告5组20案，schema_version精确；coverage给分子/分母，distinct sources按资格去重，权限/旧补丁拒绝/重复写入/调用/余量/验证证据由逐案事件派生。注入违规回执后安全违规计数必须增加，不能写死0；删除验收证据使 verified报错。
- [ ] 写测试：JSON Schema 与跨记录校验拒绝缺组、重复caseID、错误预算算术、错因果ID和不存在的 evidence refs。总 used+remaining==limits，verification reserve含在总额内；只有 executed但验收失败不能保持verified。
- [ ] 写测试：两份 fresh bundle `len(files) == 9` 且逐字节相同；manifest校验八份其他文件SHA-256；已存在空目录也拒绝、外部/父级/reparse路径拒绝；无效report不得创建完整输出。monkeypatch网络入口和环境密钥读取为raise，完整离线运行仍通过。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_reporting.py chapter18/tests/test_schema.py chapter18/tests/test_output.py -q`，预期缺报告入口（RED）。
- [ ] 实现排序规范UTF-8/LF、稳定因果归约和来源证明；报告内不含绝对路径/真实时钟/UUID。先验证目标与报告，再创建目录、`xb`写文件，manifest最后写；失败不留下 manifest宣称完成。真实工作区在 sibling `chapter18/.runs/<output-name>-workspaces/`，不混进九文件规范包；名字冲突直接拒绝。
- [ ] 接通答案CLI同一边界；两次全实验/答案运行复核一致，再首次写新 `reports/reference-rc1/`。若冻结前发现缺陷，使用新报告目录并明确候选选择，不静默覆盖既有包。
- [ ] 全部 `chapter18/tests` GREEN；精确暂存新增文件、修改的答案CLI及规范目录，本地提交 `feat(chapter18): emit reproducible team evidence and safe reports`。

### Task 8: 七幅可控文字的原创协作图

**Files:** 创建 `infographic/chapter18/{__init__.py,generate_diagrams.py,README.md}`、`01-boundaries.tldr`、`02-dependencies.tldr`、`03-delegation-handoff.tldr`、`04-task-context.tldr`、`05-integration.tldr`、`06-lifecycle.tldr`、`07-final-system.tldr`；在 `book/images/chapter18/` 生成七份同名 SVG；创建 `test_diagrams.py`。

**Interfaces:** 复用已有 `infographic.chapter14.generate_diagrams` 的 `Scene/Node/Edge/_svg/_tldraw`，不改共享源码；新增 `build_scenes() -> tuple[Scene, ...]`、`generate(root: Path) -> tuple[Path, ...]`。开始绘图前读取 `tldraw-skill` 及其要求，保留用户指定浅纸/手绘蓝绿紫橙风格，不照搬深色默认。

- [ ] 写测试：七图和七可编辑源、唯一ID、无script/远程图依赖；排程图可见23/16与“逻辑单位”；handoff箭头区分返回/接管；生命周期图总16内含保留2；每label坐标在画布安全区且重复生成字节相同。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_diagrams.py -q`，预期无图（RED）。
- [ ] 生成规格中的七主题与README设计/生成记录；避免图内大段Schema。最后全景清楚区分知识answer与代码approval→execute→verify，不让工具返回直连“已完成”。
- [ ] 逐图查看真实渲染，核对中文、箭头与图说顺序；不能以XML测试替代可读性检查。
- [ ] 同测试GREEN；精确暂存新图源/七图/测试，本地提交 `docs(chapter18): illustrate collaboration boundaries and final system`。

### Task 9: 四幕完整书稿、来源与读者材料

**Files:** 创建 `book/chapter18.md`、`book/sources/chapter18-sources.md`、`chapter18/README.md`、`IMPLEMENTATION.md`、`test_manuscript.py`、`test_sources.py`。

**Interfaces:** 正文五实验逐一对应 `run_group(1..5)`；引用 Task 7 规范包，七图对应 Task 8，十三题对应 Task 6。来源记录URL、作者/机构、日期或论文版本、核对日、用途与不能支持的外推；本地证据独立于外部产品描述。

- [ ] 写内容合同测试：标题精确、28–36个二/三级标题、7图链接、5实验框、13题、5张比较表（概念、委派/交接、失败、六维产品责任、生产验收），相对目标/锚点存在；叙述汉字22000–28000独立于总字符。产品主张有来源，不声称Docker/真模型/全书Runtime整合已完成。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_manuscript.py chapter18/tests/test_sources.py -q`，预期缺正文/来源（RED）。
- [ ] 复核规格六项官方/论文来源具体段落、论文版本与重定向；仅引用可支持责任映射的内容，记录核对日。OpenAI资料按openai-docs流程先查本地，再官方来源；不安装SDK或将文档示例当实测。
- [ ] 写第一幕“多票同源的假可靠”与单Agent/Workflow边界、7/11/5排程；第二幕从两句中文任务说明进到TaskPacket、委派与handoff；第三幕依次复盘重复/缺上下文/有效证据冲突/旧补丁/预算取消；第四幕先知识后代码，讲共同验收、生产限制与全书学习路线。每幕先可读例子再机制，正文代码小片段附中间输出。
- [ ] 写README环境/四个标准入口和两路quickstart、IMPLEMENTATION已实现/未实现对照。逐条核对命令、图号、数值、报告摘录与失败原因；完整Schema和长Trace链接配套包，不塞正文。
- [ ] 内容测试及完整本章测试GREEN；作者自审读者能复述每幕与专家能界定实验结论。精确暂存六个文件，本地提交 `docs(chapter18): write reader-first multi-agent finale and sources`。

### Task 10: 本地桌面/移动预览与交付合同

**Files:** 创建 `chapter18/preview.py`、`book/check_chapter18_preview.mjs`、`test_preview.py`、`test_delivery.py`；只在 `chapter18/preview-pages/` 生成忽略的HTML、截图。

**Interfaces:** `build_preview(root: Path, *, output: Path | None = None) -> Path` 仅允许该预览目录；Node检查器无参数，以文件所在仓库为root，使用既有Edge/Playwright，截图命名 `chapter18-rc1-{width}x{height}-top.png`。

- [ ] 写测试：新本地预览不改manifest/nav；7本地SVG加载、图片路径存在，完整练习答案/报告链接可用；外部输出和reparse拒绝。当前交付引用必须存在，旧章内容摘要与spec基线相同。
- [ ] 运行 `python -B -m pytest chapter18/tests/test_preview.py chapter18/tests/test_delivery.py -q`，预期缺预览（RED）。
- [ ] 适配第17章纸张CSS/表格局部滚动/图说/锚点模式，不改原预览。实现只用于本地的文件链接，不让preview成为公开发布入口。
- [ ] 运行 `python -B -m chapter18.preview` 与 `node book/check_chapter18_preview.mjs`。在1440×1000、390×844核对7图、5表、破损锚点0、页面错误0、远程Runtime请求0、整页横溢0；移动图/表可局部横滑。
- [ ] 查看实际桌面/移动截图，尤其总览与委派图文字；本章测试GREEN。精确暂存四个源码/测试，不暂存预览物，本地提交 `docs(chapter18): add responsive local preview and delivery checks`。

### Task 11: 审稿、最终复验与 RC1 本地冻结

**Files:** 创建 `book/reviews/chapter18-review-codex-v1.0-rc1.md`、`book/versions/chapter18-v1.0-rc1.md`；只修改 `AGENTS.md` 本地状态、`book/versions/CHAPTER_VERSIONS.md` 追加行、`docs/MIGRATION_MANIFEST.md` 版本账派生值。若审稿修复触及新章文件，精确列出，不改旧章。

**Interfaces:** Review区分作者读者/专家自审与一次独立整分支复审；版本记录环境、命令、实际结果、canonical九文件hash、字数/图表、冻结点及已证/未证结论。迁移账canonical仅将CRLF转换LF，更新版本账实际字节与SHA-256，不改来源标签/提交。

- [ ] 作者双视角逐节审稿：首次读者能理解控制权与证据，专家检查授权/身份、取消账本、保留预算、source去重与意义边界。问题给路径、级别、事实依据和已修状态。
- [ ] 保存首个完整候选本地提交作为审稿基点；按已选native流程调用一次新上下文只读整分支Reviewer，审稿范围本章全交付与基线保护，禁止其直接写稿、消息其他聊天或发布。
- [ ] 对必须修复项先补失败测试再修复；记录RED/GREEN实际证据。首版正式冻结前只更新候选；若已有冻结RC1后再改，先保留旧稿图报告并升版本，不回写历史。
- [ ] 运行两次全实验：`python -B -m chapter18.experiments --group all --output chapter18/.runs/final-a` 与 `...final-b`；九文件逐字节与manifest哈希一致，输出目录均须全新。
- [ ] 运行两次独立答案输出：`python -B -m chapter18.exercise_solutions --all --output chapter18/.runs/answers-final-a.json` 与 `...answers-final-b.json`，逐字节比较；CLI拒绝覆盖/离线测试仍有效。
- [ ] 在既有 `.venv-chapter15` Python运行 `python -B -m pytest chapter18/tests -q`、`python -B -m pytest chapter15/tests chapter16/tests chapter17/tests tests -q`；分别记本章与相关矩阵，不能称全书全部测试。
- [ ] 运行 `npm --prefix book test`、`python -B scripts/check_repository.py --root . --git-history`；若检查失败定位新引入项与既有项，不用删历史或豁免所有旧目录来“清零”。
- [ ] 重新生成/检查桌面移动预览。使用既有MkDocs环境先组装**新的** `.runs/site-sources-rc1/`：`python -B scripts/build_site.py --root . --output chapter18/.runs/site-sources-rc1`。用apply_patch在本章忽略目录新建 `mkdocs-rc1.yml`，继承原配置，docs_dir为绝对新源路径、site_dir为绝对新输出路径；继承文件与绝对路径仅为本地验证，不提交。运行 `python -B -m mkdocs build --strict --config-file chapter18/.runs/mkdocs-rc1.yml`，预期exit0/strict成功。不改公开mkdocs.yml，不覆盖既有 `_web`/site；所有具体输出先验证位于本书仓库且尚不存在。
- [ ] 若运行根目录裸pytest仍遇旧依赖/同名模块收集错误，记具体数量与原因，不安装无关依赖，也不以相关矩阵掩盖；以仓库基线与当前diff判断是否新回归。
- [ ] 将第18章标本地RC1，纠正AGENTS旧段第17章RC2为RC3。追加版本账、仅刷新相应迁移行；核对公开manifest仍0.14.0、allowlist无18、旧正文/图/代码/报告无变化。将规范哈希、字数和所有验证实绩写入版本记录，不写预估通过数。
- [ ] 重跑受账本变化影响的根合同/安全检查，`git diff --check`；精确暂存本章修复及上述五个状态/审稿文件，本地提交 `docs(chapter18): freeze reviewed local rc1 candidate`。最后仓库干净；无push/merge/deploy。

## 精确暂存与本地提交

每个Task的提交步骤使用下表 `git add`，再独立运行该Task列出的 `git commit -m`。不使用全仓库暂存；Task11若另有审稿修复，先列出实际新章文件再单独暂存，不能把未知改动混入。

| Task | 精确暂存命令 |
| --- | --- |
| 1 | `git add .gitignore chapter18/__init__.py chapter18/contracts.py chapter18/fixtures.py chapter18/fixtures chapter18/requirements-dev.txt chapter18/requirements-preview.txt chapter18/tests/test_contracts.py chapter18/tests/test_fixtures.py` |
| 2 | `git add chapter18/context.py chapter18/evidence.py chapter18/tests/test_context.py chapter18/tests/test_evidence.py` |
| 3 | `git add chapter18/policy.py chapter18/budget.py chapter18/runtime.py chapter18/tests/test_budget.py chapter18/tests/test_runtime.py` |
| 4 | `git add chapter18/workspace.py chapter18/integration.py chapter18/verifier.py chapter18/tests/test_integration.py chapter18/tests/test_verifier.py` |
| 5 | `git add chapter18/cases.py chapter18/system.py chapter18/quickstart.py chapter18/tests/test_cases.py chapter18/fixtures/cases.json` |
| 6 | `git add chapter18/exercise_solutions.py chapter18/reference-answers.md chapter18/tests/test_exercises.py` |
| 7 | `git add chapter18/reporting.py chapter18/output.py chapter18/experiments.py chapter18/schemas/report-v1.schema.json chapter18/tests/test_reporting.py chapter18/tests/test_schema.py chapter18/tests/test_output.py chapter18/exercise_solutions.py chapter18/reports/reference-rc1` |
| 8 | `git add infographic/chapter18 book/images/chapter18 chapter18/tests/test_diagrams.py` |
| 9 | `git add book/chapter18.md book/sources/chapter18-sources.md chapter18/README.md chapter18/IMPLEMENTATION.md chapter18/tests/test_manuscript.py chapter18/tests/test_sources.py` |
| 10 | `git add chapter18/preview.py book/check_chapter18_preview.mjs chapter18/tests/test_preview.py chapter18/tests/test_delivery.py` |
| 11 | `git add book/reviews/chapter18-review-codex-v1.0-rc1.md book/versions/chapter18-v1.0-rc1.md AGENTS.md book/versions/CHAPTER_VERSIONS.md docs/MIGRATION_MANIFEST.md` |

## Self-Review 与执行交接

规格覆盖对应：目标/四幕→Task9；合同/离线/预算→Task1–4；20案例/业务路径→Task5；十三题→Task6；九文件/复现→Task7；七图→Task8；预览→Task10；双视角、native复审、历史/公开边界→Task11。五条Review Focus均有明确 owning tests，不以“注意边界”替代断言。

接口仅在Shared Interfaces及各Task输出块定义；实现按前置依赖推进，不能为凑代码题提前创建另一套report/write边界。资料事实、逻辑时钟、运行回执和外部产品说明分别记账。现有环境可复用，但本计划中的命令与预计通过条件均尚未执行，不能当验收成绩。

用户已选native，无需再次选择。按 `writing-plans` 要求，本计划保存并自检后交用户审阅；确认捕捉了预期再用 `superpowers:executing-plans` 逐项实施。本轮只保存计划和本地计划提交，不生成书稿/实验代码/图，不推送或发布。
