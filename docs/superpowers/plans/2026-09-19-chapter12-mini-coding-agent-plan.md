# 第 12 章 Mini Coding Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付通俗易懂的第 12 章候选书稿，以及真正由模型决策、可验证和恢复的 Mini Coding Agent、Pi 源码对照及两套可运行框架重构。

**Architecture:** Python 手写实现先建立模型、工具网关、状态、隔离执行和独立验收之间的边界。LangGraph 与 OpenAI Agents SDK 复用边界组件，但各自由真实框架控制编排；Pi 只作固定提交的源码参照。程序和实验先形成证据，正文及七幅图随后解释实际实现。

**Tech Stack:** Python 3.11、标准库、OpenAI Python 客户端的 Chat Completions 兼容接口、LangGraph + SQLite checkpointer、OpenAI Agents SDK、pytest、Docker 兼容容器运行时、现有 Markdown/Playwright/MkDocs 预览工具链。Task 1 解析并锁定实际可安装版本，不将未经安装的版本号写成实测结果。

**Spec:** [已确认的书面设计](../specs/2026-09-19-chapter12-mini-coding-agent-design.md)

状态：设计已确认；本计划待审阅和执行方式选择。这里的命令、测试和结果条件是实施合同，不是已执行证据。

## Global Constraints

- 目标 20,000–30,000 中文字符、约 30–36 个二三级标题、7 幅图、5 组实验、14 道练习。
- Python 手写实现为主线，Pi 为核心源码参照，保留 LangGraph 与 OpenAI Agents SDK 的重构对照。
- 第一版单次执行一个工具，不引入并发写操作。
- 只有验收器通过才能写入 completed；模型请求结束不直接产生 completed。
- 只允许单写者运行，通过本地锁或等价机制拒绝两个运行器同时写同一教学目录。
- trusted_local 仅用于本书生成的可信夹具和离线教学；container 用于模型驱动的代码执行实验。
- 真实模型示例默认要求通过环境预检的隔离后端，不能因容器不可用而静默降级到宿主执行。
- 凭据从环境读取，不进入工作区、提示词、图片、规范报告或 Trace。
- 框架重构必须执行真实框架代码；缺包不能以自动跳过伪装成验证通过。
- 规范报告采用固定输入与逻辑事件序号；真实模型证据另存脱敏观察，不修改原始结果来制造成功。
- 保留第 1–11 章、旧图、旧 Review、旧提交和 tag；第 12 章采用独立候选历史，不直接发布。
- 不更改公开 manifest、网站导航或已发布章节数，不推送，不部署，不生成英文版、繁体版及 PDF/EPUB。
- 所有交付保存在书籍工程目录。执行时使用明确工作目录；作者机器路径和凭据不写入受版本控制的材料。
- 本地依赖安装限书籍项目虚拟环境。启动系统服务、安装容器平台或修改机器设置另取授权。

## Review Focus

1. Windows 盘符、UNC、反斜杠、符号链接和目录替换不能绕过相对路径限制；Task 2/4 拒绝并验证无外部写入。
2. 重用 call_id、旧批准配新参数、恢复时文件变动不能借用旧授权；Task 3/8 分别拒绝冲突、失效批准并防重复副作用。
3. 损坏/截断状态库和另一进程占锁不能变成“新任务重新执行”；Task 3 显式失败，保留可诊断证据。
4. 超长日志、UTF-8 跨块字符、取消和期限同时发生不能使读取阻塞或进程残留；Task 4/7 真实进程测试并给出确定停止原因。
5. 测试零发现、stdout 伪造成功、恒空实现和验收后文件变更不能成为完成证据；Task 5/7 在宿主判定并绑定最终版本。

---

## 执行地图与约定

先读仓库 `AGENTS.md`、`book/WRITING_GUIDE.md`、上述 spec。本计划中的路径全部相对书籍仓库根目录。实现使用 `codex/chapter12-mini-agent` 隔离分支；若需要工作树，执行阶段按 using-git-worktrees 技能创建，不复制未提交改动。当前设计分支的文档历史不重写。

所有 Python 命令在项目虚拟环境激活后从仓库根目录运行；不依赖学习工程其他 phase。所有测试使用 `python -B -m pytest`。框架集成及容器测试分开列命令，但最终不能遗漏任何一组。目录分工：

| 文件/目录 | 职责 |
| --- | --- |
| `chapter12/contracts.py`、`preflight.py` | 严格协议、配置和环境检查 |
| `chapter12/fixtures/`、`prepare.py` | 自包含有缺陷仓库及可重建教学工作区 |
| `chapter12/tools.py`、`executor.py` | 五个工具、路径策略和执行网关 |
| `chapter12/backends.py`、`sandbox/` | 受限进程/容器执行、固定镜像及探针 |
| `chapter12/state.py`、`trace.py` | 单写者、检查点、动作账本和事件 |
| `chapter12/verifier.py`、`acceptance/` | 独立只读验收资产与宿主验收决定 |
| `chapter12/context.py`、`providers/` | 模型输入视图、回放和真实模型适配 |
| `chapter12/runtime.py`、`services.py` | 手写调度、可复用单步服务，禁止框架反向调用手写循环 |
| `chapter12/adapters/` | LangGraph、Agents SDK 编排和窄版本适配层 |
| `chapter12/quickstart.py`、`experiments.py` | CLI、故障注入和规范报告 |
| `chapter12/exercise_solutions.py`、`reference-answers.md` | 14 题的执行/解释反馈 |
| `chapter12/tests/`、`reports/`、`preview.py` | 验证、固定报告及本地预览 |
| `book/chapter12.md`、`book/sources/chapter12-sources.md` | 权威正文与来源台账 |
| `book/images/chapter12/`、`infographic/chapter12/` | 七幅正式图、技术草图、提示词与修订说明 |
| `book/reviews/chapter12-review-codex-v1.0-rc1.md`、`book/versions/chapter12-v1.0-rc1.md` | 自审、证据和候选历史 |

本章私有临时运行目录为 `chapter12/.runs/`；Task 1 加入 `.gitignore`。真实运行原始记录在 `chapter12/live-reports/`，现有忽略规则已覆盖；公开可审查摘要放 `chapter12/reports/live-observation.md`，须显式脱敏后才能暂存。

### 统一接口词典

所有公共记录是可 JSON 序列化的 dict，标注为 `Record = dict[str, Any]`；按以下必需字段严格验证，不接受额外动作字段。测试可用普通 dict，不伪称有静态类型安全。时间值为秒，大小值为 UTF-8 bytes，服务端 usage 原样单列。

| 名称 | 必需字段与含义 |
| --- | --- |
| ToolCall | `call_id: str, name: str, arguments: Record`；name 仅五工具 |
| Decision | `kind: tool/plan/final, text: str, call: ToolCall或null`；plan/final 禁带工具 |
| ToolResult | `call_id, ok: bool, data: Record, error: str或null, truncated: bool` |
| PreparedPatch | `path, before_hash, after_hash, old, new, workspace_hash, action_id`；意图存于候选目录外 |
| Approval | `run_id, action_id, arguments_hash, workspace_hash, approved: bool` |
| RunState | `schema_version=1, run_id, status, goal, constraints, messages, plan, pending, evidence, counters, deadline, backend, workspace_hash, reason, provider_state`；provider_state 保存回放 cursor 等非敏感恢复信息 |
| Event | `seq, run_id, kind, call_id或null, action_id或null, payload`；单调序号，先落盘后展示 |
| ExecResult | `returncode, stdout, stderr, truncated, timed_out, cancelled, duration_seconds` |
| Verdict | `passed, discovered, failed_cases, protected_ok, workspace_hash, evidence` |
| ModelConfig | `base_url, model, key_env, timeout_seconds`；不存密钥本身 |

函数签名中的 `Path`、`Any`、`Callable`、`Event` 分别来自 pathlib、typing、threading；threading.Event 为取消信号，区别于上表事件记录。各 task 的实现代码为应落实的关键算法，不表示已存在文件；无自动执行或成功保证。完整实现必须满足接口表和列出的反例，不只让单个 happy-path 断言通过。

## Task 1: 建立协议、依赖与不可静默降级的预检

**Files:** 创建 `chapter12/__init__.py`、`contracts.py`、`preflight.py`、`requirements.in`、`requirements.txt`、`requirements-frameworks.in`、`requirements-frameworks.txt`、`requirements-dev.txt`、`tests/test_contracts.py`、`tests/test_preflight.py`；修改 `.gitignore`。

**Interfaces:** 产出 `validate_call(value: Record) -> Record`、`new_state(run_id: str, goal: str, backend: str, now: float) -> Record`；`preflight.check(backend: str, live: bool, probe: Callable[[], Record]) -> Record`。probe 返回 `available, image_pinned, isolation_passed` 三个 bool；live+trusted_local 必须拒绝。工具 schema 用同一常量 `TOOL_SCHEMAS` 提供给验证器和模型。

- [ ] 写失败测试：协议拒绝未知工具、额外字段、bool 冒充整数、空 call_id；预检拒绝回退。

```python
import pytest
from chapter12.contracts import validate_call
from chapter12.preflight import check

def test_no_live_fallback():
    result = check('container', True, lambda: dict(
        available=False, image_pinned=False, isolation_passed=False))
    assert result['ready'] is False
    assert result['backend'] == 'container'

def test_unknown_tool():
    with pytest.raises(ValueError, match='unknown_tool'):
        validate_call(dict(call_id='c1', name='shell', arguments={}))
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_contracts.py chapter12/tests/test_preflight.py -q`；首次应因模块缺失失败。
- [ ] 实现 new_state 的全部字段默认值：status=ready，列表/字典独立初始化，deadline=now+300，计数为零，pending=null；schema 递归验证键集合、长度、枚举、数值范围。

```python
def check(backend, live, probe):
    if backend not in {'trusted_local', 'container'}:
        raise ValueError('unknown_backend')
    if backend == 'trusted_local':
        return dict(backend=backend, ready=not live, reason='trusted_fixtures_only')
    facts = probe()
    ready = all(facts.get(k) is True for k in
                ('available', 'image_pinned', 'isolation_passed'))
    return dict(backend=backend, ready=ready, reason='ready' if ready else 'isolation_unverified')
```

- [ ] 在项目 venv 解析 `openai`；框架组解析 `langgraph`、`langgraph-checkpoint-sqlite`、`openai-agents`；测试组解析 pytest。使用 pip-tools 的 `pip-compile --generate-hashes` 生成精确依赖锁，记录 Python/解析器版本；不直接复用宿主已装包。运行 `python -m pip check`。从已安装 SDK 检查 Model、Runner、RunState 的真实签名，记录到来源台账的“版本合同”段，不凭记忆写兼容层。
- [ ] 重跑两测试文件全部通过；检查无网络/无 key 的 core import 可用；预检只报告布尔值不读取或回显 secret。
- [ ] 精确暂存本 task 文件与 `.gitignore`；提交 `feat(chapter12): define tool contracts and fail-closed preflight`。

## Task 2: 自包含教学仓库与五工具的文件侧行为

**Files:** 创建 `chapter12/fixtures/link-checker/src/linkcheck.py`、`fixtures/link-checker/tests/test_existing.py`、`fixtures/link-checker/docs/guide/start.md`、`fixtures/link-checker/docs/target.md`、`fixtures/link-checker/legacy/check_links.py`、`fixtures/link-checker/notes.txt`、`prepare.py`、`tools.py`、`tests/test_tools.py`。

**Interfaces:** `prepare.create_workspace(destination: Path) -> Path`（目标已存在则拒绝）；`tools.safe_path(root: Path, relative: str) -> Path`；`read_file(root, path, start=1, end=200) -> Record`；`search(root, query, directory='.') -> Record`；`prepare_patch(root, call: Record) -> Record`；`write_patch(root, patch: Record) -> Record`；`show_diff(root) -> Record`。所有 root 均 Path。版本是原始字节 SHA-256，初次新文件使用 `before_hash='absent'`，old 必须空，只允许 `tests/test_agent_*.py` 新文件。

- [ ] 写 read/search 行号、字节截断、新文件、非唯一替换、过期版本、受保护 notes/legacy、路径逃逸测试。夹具故意把相对链接按仓库根而非文档父目录解析；既有根目录测试通过，嵌套回归失败。

```python
import pytest
from chapter12.tools import safe_path, read_file, prepare_patch

@pytest.mark.parametrize('name', ['../escape', '/etc/passwd', 'C:/secret', '//host/share', r'..\escape'])
def test_path_escape(tmp_path, name):
    with pytest.raises(ValueError, match='path_denied'):
        safe_path(tmp_path, name)

def test_stale_patch(tmp_path):
    (tmp_path / 'src').mkdir()
    p = tmp_path / 'src/linkcheck.py'
    p.write_text('old\n', encoding='utf-8')
    version = read_file(tmp_path, 'src/linkcheck.py')['version']
    p.write_text('external\n', encoding='utf-8')
    call = dict(call_id='c1', name='apply_patch', arguments=dict(
        path='src/linkcheck.py', version=version, old='old', new='new'))
    with pytest.raises(ValueError, match='stale_version'):
        prepare_patch(tmp_path, call)
    assert p.read_text(encoding='utf-8') == 'external\n'
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_tools.py -q`，首次应为模块/函数缺失。
- [ ] 实现路径算法：拒绝盘符/绝对/UNC/反斜杠/NUL/冒号/点点路径；逐祖先 lstat 拒绝 symlink/reparse；resolve 后要求相对 root；写入前重新检查。明确这不是对抗宿主并发恶意进程的完整安全保证，容器隔离承担进程权限边界。

```python
from hashlib import sha256

def replacement_bytes(current: bytes, old: str, new: str) -> bytes:
    needle = old.encode('utf-8')
    if not needle or current.count(needle) != 1:
        raise ValueError('non_unique_match')
    return current.replace(needle, new.encode('utf-8'), 1)
```

补丁先形成 before/after hash 与工作区清单 hash，不立即写入；write_patch 在 Task 8 网关批准后调用，临时文件 fsync 后原子替换，拒绝扩展到其他目录。read/search 不跟随链接、不遍历 `.git`、固定最大文件/输出 bytes，truncated 独立字段。show_diff 关闭 external diff/textconv、禁 shell，固定 cwd，仅比较允许文件与创建时基线；不执行仓库配置命令。fixture Git 初始化不依赖用户全局 hook/template。
- [ ] 在 Windows 和 WSL 分别测试可创建的 reparse/symlink 越界样本；权限不支持时单列未验证而非声称全覆盖。重跑工具测试；diff 仅包含本 task 文件。
- [ ] 提交 `feat(chapter12): add bounded repository tools and repair fixture`，仅暂存上表路径。

## Task 3: 持久状态、单写者、动作账本与 Trace

**Files:** 创建 `chapter12/state.py`、`trace.py`、`tests/test_state.py`、`tests/test_trace.py`。

**Interfaces:** `Store(path: Path)`，方法 `save(state: Record) -> None`、`load(run_id: str) -> Record`、`intent(run_id: str, call: Record, patch: Record) -> Record`、`receipt(action_id: str, result: Record) -> None`、`action(action_id: str) -> Record`、`approve(approval: Record) -> None`、`approval(action_id: str) -> Record或None`、`append_event(run_id: str, kind: str, payload: Record, call_id: str或None=None, action_id: str或None=None) -> Record`、`events(run_id: str) -> list[Record]`。`workspace_lock(root: Path)` 为跨平台上下文管理器。`trace.export(store: Store, run_id: str) -> list[Record]` 只读脱敏。

- [ ] 测试事务保存、call_id 冲突、损坏库、进程锁释放、相同 intent 幂等返回、导出绝不执行工具。

```python
import pytest
from chapter12.state import Store
from chapter12.contracts import new_state

def test_corrupt_database_is_not_a_new_run(tmp_path):
    p = tmp_path / 'state.sqlite'
    p.write_bytes(b'broken sqlite')
    with pytest.raises(RuntimeError, match='state_corrupt'):
        Store(p).load('r1')

def test_events_survive_reopen(tmp_path):
    p = tmp_path / 'state.sqlite'
    db = Store(p)
    db.save(new_state('r1', 'repair', 'trusted_local', 0))
    db.append_event('r1', 'started', {})
    assert Store(p).events('r1')[0]['seq'] == 1
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_state.py chapter12/tests/test_trace.py -q`，期望先失败。
- [ ] SQLite 建 runs/actions/approvals/events 表；actions 的 `(run_id, call_id)` 唯一；同时存规范参数摘要。所有状态与对应事件在同事务提交。hash 算法如下，重复 id 的参数不同报 `call_id_conflict`，不得新建动作。

```python
import hashlib, json

def canonical_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
```

DB 使用 WAL + busy_timeout + synchronous=FULL；数据库坏掉时保留原文件并报错，不自动删除重建。锁使用 POSIX flock/Windows msvcrt 锁定同一运行目录外的锁文件，进程退出由 OS 释放；两个真实子进程竞争测试，不以线程代替。Trace 采用字段白名单，不导出 auth/header/env；即使可见模型文本出现 secret 模式也脱敏，不采集隐藏思维链。
- [ ] 重跑测试，增加截断 DB 和同 action 重复回执不得覆盖冲突结果断言。
- [ ] 提交 `feat(chapter12): persist actions and traces with single-writer recovery`，暂存四个文件。

## Task 4: 有限执行后端与真实容器边界

**Files:** 创建 `chapter12/backends.py`、`sandbox/Dockerfile`、`sandbox/image-lock.json`、`sandbox/probes.py`、`tests/test_backends.py`、`tests/test_container.py`。

**Interfaces:** `run_preset(root: Path, preset: str, backend: str, timeout_seconds: float, output_bytes: int, cancel: threading.Event) -> Record`；preset 仅 `candidate_tests`、`acceptance` 和宿主专用 `probe_*`；`probe_container() -> Record` 兼容 Task 1 probe；`bounded_decode(chunks: list[bytes], limit: int) -> Record` 返回 text/truncated。外部参数不允许自由 argv/shell。Docker 映射路径在后端转换，业务工具不拼接 shell。

- [ ] 写 UTF-8 截断与长日志读取测试；实际容器测试检查非 root、根只读、网络拒绝、无宿主凭据/socket、内存/PID/时间/输出边界和取消后无活动容器。

```python
from chapter12.backends import bounded_decode

def test_utf8_output_budget():
    got = bounded_decode([b'\xe4', b'\xb8\xad', b'x' * 100], 3)
    assert got == {'text': '中', 'truncated': True}
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_backends.py -q`；容器组另运行 `python -B -m pytest chapter12/tests/test_container.py -q`。缺运行时应明确失败/预检退出，不写 skip 后算通过。
- [ ] 输出收集使用增量 UTF-8 解码，达到存储上限仍排空管道或终止任务，不停读导致子进程死锁。全部日志也设置硬上限。trusted_local 只接收 create_workspace 生成的可信回放，不能执行模型产生的代码。实现固定容器命令构建与任务名到参数数组映射，关键约束如下：

```text
docker run --name <task-owned-id> --network none --read-only
  --user 65534:65534 --cap-drop ALL --security-opt no-new-privileges
  --pids-limit 64 --memory 256m --cpus 1
  --tmpfs /tmp:rw,nosuid,nodev,size=32m
  --mount type=bind,src=<only-this-workspace>,dst=/work
  --mount type=bind,src=<host-acceptance>,dst=/acceptance,readonly
  --workdir /work <sha256-pinned-image> <fixed-preset-argv>
```

镜像不安装运行时网络依赖，基础镜像固定 digest、记录构建版本。host API key 不传入容器 env。取消/超时先终止指定容器，再 wait/inspect 确认退出；只清理当前任务持有的容器 id，禁宽泛 prune。trusted_local 使用进程组或 Windows Job Object 终止子进程树。期限到达与取消同时发生时优先已观测到的取消，记录另一事实。
- [ ] 记录各探针真实结果；WSL 或 bwrap 存在不等于已满足 container 合同。若系统安装需授权，只暂停容器相关验收，继续不依赖它的任务，不改成宿主 fallback。
- [ ] 提交 `feat(chapter12): enforce bounded execution and container probes`，只暂存此 task 源码、测试和无机器路径的 image lock。

## Task 5: 独立验收与假完成反例

**Files:** 创建 `chapter12/acceptance/cases.json`、`acceptance/runner.py`、`verifier.py`、`tests/test_verifier.py`。

**Interfaces:** `verify(root: Path, backend: str, baseline: Record, cancel: threading.Event) -> Record` 返回 Verdict；`capture_baseline(root: Path) -> Record` 包含受保护文件 hash 与允许修改清单。verify 调用 Task 4 固定 acceptance preset，不信任候选声明的 discovered 或 passed。

- [ ] 覆盖根/嵌套有效、嵌套缺失、外部链接；原bug及恒空实现均失败；零测试、伪造 stdout、修改 notes、篡改验收程序均拒绝。

```python
from threading import Event
from chapter12.prepare import create_workspace
from chapter12.verifier import capture_baseline, verify

def test_always_empty_is_not_a_repair(tmp_path):
    root = create_workspace(tmp_path / 'repo')
    baseline = capture_baseline(root)
    (root / 'src/linkcheck.py').write_text(
        'def broken_links(document, root):\n    return []\n', encoding='utf-8')
    verdict = verify(root, 'trusted_local', baseline, Event())
    assert verdict['passed'] is False
    assert 'nested_missing' in verdict['failed_cases']
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_verifier.py -q`，先失败。
- [ ] host 保管预期值和验收输入；runner 在 container 读取只读资产，逐样本导入候选函数并返回原始输出；host 校验用例集合/数量/类型/结果、退出状态、超时、文件保护和运行前后版本。一致性判据：

```python
def accepted(result, expected_ids, protected_ok, before_hash, after_hash):
    cases = result['cases']
    return (result['returncode'] == 0 and not result['timed_out']
            and set(cases) == set(expected_ids) and len(cases) > 0
            and all(item['matches'] for item in cases.values())
            and protected_ok and before_hash == after_hash)
```

候选不能直接写验收回执；混杂 stdout 不当回执解析，使用独立受控结果通道及严格 schema。说明 Python 同进程导入不构成抗主动恶意候选的完整可信计算，不能据此宣称对抗安全；测试重点是教学误修与明显伪造。模型新增回归测试与只读独立验收各自显示，不混为同一项。
- [ ] 重跑含正常修复的全套验收测试，记录 discovered 精确值；执行中改变文件版本必须得到失败而非陈旧成功。
- [ ] 提交 `feat(chapter12): reject false completion with independent acceptance`。

## Task 6: 上下文视图与真实模型协议

**Files:** 创建 `chapter12/context.py`、`providers/__init__.py`、`providers/replay.py`、`providers/chat.py`、`tests/test_context.py`、`tests/test_provider.py`。

**Interfaces:** `build_context(state: Record, max_bytes: int) -> list[Record]`；`ReplayModel(decisions: list[Record]).next(messages: list[Record]) -> Record`；`ChatModel(config: Record, client: Any).next(messages: list[Record]) -> Record`；`parse_response(value: Record) -> Record`。ReplayModel 的 cursor 显式持久化，不在恢复时归零。ChatModel 仅适配协议，不含案例路径/修复模板。

- [ ] 测试保留目标/限制/审批/验收/最后失败证据/当前版本、完整调用结果对；预算容纳不下强制项时显式 context_budget_exhausted；拒绝 length 截断和多工具并发结果。

```python
import pytest
from chapter12.providers.chat import parse_response

def test_truncated_arguments_are_never_executed():
    response = {'choices': [{'finish_reason': 'length', 'message': {
        'content': None, 'tool_calls': [{'id': 'c1', 'type': 'function',
        'function': {'name': 'apply_patch', 'arguments': '{"path":'}}]}}]}
    with pytest.raises(ValueError, match='truncated_response'):
        parse_response(response)
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_context.py chapter12/tests/test_provider.py -q`，先失败。
- [ ] 使用 OpenAI-compatible Chat Completions 的五工具 schema，`parallel_tool_calls=False`；服务端不支持该参数时按其官方文档配置并仍在本地强制单调用。只有完整 JSON 参数经 validate_call 后才能成为 ToolCall；空响应/无 id/多调用/拒绝/超时形成明确错误，不猜补 JSON。正文把计划作为简短可见工作说明，不要求 chain-of-thought。

```python
def complete_groups(messages):
    groups = []
    index = 0
    while index < len(messages):
        item = messages[index]
        if item.get('tool_calls'):
            if len(item['tool_calls']) != 1 or index + 1 >= len(messages):
                raise ValueError('unpaired_tool_call')
            result = messages[index + 1]
            if result.get('tool_call_id') != item['tool_calls'][0]['id']:
                raise ValueError('unpaired_tool_call')
            groups.append([item, result])
            index += 2
        else:
            if item.get('role') == 'tool':
                raise ValueError('orphan_tool_result')
            groups.append([item])
            index += 1
    return groups
```

压缩按完整 group 移出旧观察，持久 state/Trace 不删除。pending 调用在完成结果前不作为半条历史送模型，审批保留在强制状态摘要。摘要明确区分磁盘事实、用户要求、模型计划。HTTP 使用 mock transport 测试请求体、usage、异常，不带真实 key；真实调用留 Task 11。
- [ ] 验证相同 state 两次输入视图相同，压缩后原始 history 不变；扫描适配器不得包含 linkcheck 修复内容。
- [ ] 提交 `feat(chapter12): separate context views from model protocol adapters`。

## Task 7: 手写循环、统一网关和完成协议

**Files:** 创建 `chapter12/executor.py`、`services.py`、`runtime.py`、`quickstart.py`、`tests/test_runtime.py`；更新 `contracts.py` 的边界实现。

**Interfaces:** `Services(root: Path, store: Store, model: Any, backend: str, cancel: threading.Event)`；方法 `decide(state) -> Record`、`propose(state, call) -> Record`、`execute(state) -> Record`、`observe(state, result) -> Record`、`finish(state) -> Record`、`fail(state, reason: str) -> Record`、`stopped(state) -> bool` 均以 Record state 为单位，不内部循环；call/result 为 Record。`runtime.run(state: Record, services: Services) -> Record`；`executor.dispatch(root: Path, call: Record, backend: str, cancel: threading.Event) -> Record` 只由网关调用。`quickstart.main(argv: list[str]或None=None) -> int`。

- [ ] 测试 final 不等于完成、未知工具零副作用、失败结果进入下一轮、预算/取消状态、最终版本变动重新验收。补丁此 task 只进入 awaiting_approval，Task 8 完成恢复。

```python
from threading import Event
from chapter12.contracts import new_state
from chapter12.prepare import create_workspace
from chapter12.providers.replay import ReplayModel
from chapter12.services import Services
from chapter12.state import Store
from chapter12.runtime import run

def test_model_cannot_announce_success(tmp_path):
    root = create_workspace(tmp_path / 'repo')
    db = Store(tmp_path / 'state.sqlite')
    model = ReplayModel([dict(kind='final', text='完成了', call=None)])
    state = new_state('r1', 'repair', 'trusted_local', 0)
    state['deadline'] = 10**12
    result = run(state, Services(root, db, model, 'trusted_local', Event()))
    assert result['status'] != 'completed'
    assert any(e['kind'] == 'verification_failed' for e in db.events('r1'))
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_runtime.py -q`，先失败。
- [ ] 实现运行骨架；每次 decide/execute 前检查取消、绝对期限、模型轮数/工具数（默认 30/60），计数及 deadline 跨进程保留。模型超时默认 45s 但不得超过剩余期限。连续失败有限重试且耗预算；永久错误不自动重试。

```python
def run(state, services):
    while not services.stopped(state):
        try:
            decision = services.decide(state)
        except (ValueError, TimeoutError) as error:
            return services.fail(state, str(error))
        if decision['kind'] == 'final':
            state = services.finish(state)
        elif decision['kind'] == 'plan':
            state['plan'] = decision['text']
            services.store.save(state)
        else:
            state = services.propose(state, decision['call'])
            if state['status'] == 'awaiting_approval':
                return state
            if state['pending'] is not None and not services.stopped(state):
                state = services.observe(state, services.execute(state))
    return state
```

execute 返回 ToolResult；observe 添加完整调用/结果对并清 pending。propose 对非法动作也生成 ToolResult，再经 observe 进入错误观察并保持 pending=null；不得让上面骨架执行被拒绝动作。ReplayModel 耗尽抛 ValueError('replay_exhausted')，fail 保存 failed 状态和具名事件。finish 只能在 verify 通过且现场 hash 仍相同时 completed；失败回传具名证据让模型继续。stopped 对 awaiting_approval 与 completed/failed/cancelled/budget_exhausted 返回真，对 verifying 执行中的校验不误停。decide 必须持久化 provider_state cursor，并让相同决策及其 action 在恢复时保持一致。
- [ ] CLI 支持 `start`、`resume`、`approve`、`reject`、`trace`，run_id/workdir/state path 必须关联校验；当前先测试 start/trace/help。真实模型启动先通过 Task 1 预检再调用 API，失败不计成模型能力差。
- [ ] 提交 `feat(chapter12): implement model-driven loop and completion protocol`。

## Task 8: 具体动作审批、跨进程恢复与崩溃窗口

**Files:** 修改 `chapter12/services.py`、`state.py`、`quickstart.py`；创建 `chapter12/recovery.py`、`tests/test_recovery.py`。

**Interfaces:** `recover(root: Path, store: Store, state: Record) -> Record`；`resolve_approval(state: Record, store: Store, approved: bool) -> Record`；Services 增加 `resume(state: Record) -> Record`。批准对象必须包含 run_id/action_id/arguments_hash/workspace_hash，CLI 不接受 approve-all。

- [ ] 真实两个子进程测试 start→paused→退出→approve→resume；故障点固定枚举 `after_intent`、`after_write_before_receipt`，只在测试环境注入。校验两个补丁写事件而非仅最后内容，不能因为第二次替换无匹配就宣称未重复执行。

```python
from chapter12.recovery import classify

def test_crash_recovery_is_three_way():
    assert classify('before', 'after', 'after') == 'record_receipt'
    assert classify('before', 'after', 'before') == 'recheck_approval'
    assert classify('before', 'after', 'external') == 'uncertain'
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_recovery.py -q`，先失败。
- [ ] 实现并公开 `classify(before_hash: str, after_hash: str, current_hash: str) -> str`：

```python
def classify(before_hash, after_hash, current_hash):
    if before_hash == after_hash:
        raise ValueError('no_op_patch')
    if current_hash == after_hash:
        return 'record_receipt'
    if current_hash == before_hash:
        return 'recheck_approval'
    return 'uncertain'
```

实际恢复还要检查除目标外文件与预期清单一致；不能只看到目标后态就忽略无关改动。后态匹配补记 receipt 不重写；前态匹配且原审批参数/版本仍成立才继续；第三态 failed/uncertain，保留状态不回滚用户编辑。过期批准显式返回 approval_stale；拒绝返回 approval_denied，让模型可在余量内提出替代。写前持久 intent，写后 receipt+工具消息的 DB 事务避免重复追加观察。
- [ ] 对每个 crash 点分别重启，再重启一次；断言每 action 最多一条有效回执、一次实际写入、同 call 不重复计模型轮数。改参数、跨run偷批准、外部编辑和锁冲突必须失败。
- [ ] 提交 `feat(chapter12): bind approvals and recover interrupted patches safely`。

## Task 9: LangGraph 真正接管编排

**Files:** 创建 `chapter12/adapters/__init__.py`、`adapters/langgraph_agent.py`、`tests/test_langgraph.py`、`tests/framework_cases.py`。

**Interfaces:** `run_graph(state: Record, services: Services, checkpoint: Path, approval: bool或None=None) -> Record`；`framework_cases.run_scenario(adapter: str, scenario: str, directory: Path) -> Record` 返回 `status, writes, events, backend, framework_version, orchestration`。scenario 枚举 complete/approval_restart/tool_error/false_finish；后续 Task 10 添加 agents_sdk 分支。该帮助程序只建夹具、回放决策和运行真实适配器，不自己执行修复步骤。

- [ ] 写四场景合同和“手写循环不可达”测试：

```python
from chapter12.tests.framework_cases import run_scenario

def test_graph_does_not_wrap_manual_runtime(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('manual loop reached')
    monkeypatch.setattr('chapter12.runtime.run', forbidden)
    result = run_scenario('langgraph', 'approval_restart', tmp_path)
    assert result['status'] == 'completed'
    assert result['orchestration'] == 'langgraph'
    assert result['framework_version']
    assert result['writes'] == 2
```

两次写分别为新增回归测试和源码修复，测试夹具脚本明确给出这两个动作，不能硬编码最终报告。normal 同样走人工/测试驱动的具体批准，不全局跳过审批。
- [ ] 运行 `python -B -m pytest chapter12/tests/test_langgraph.py -q`，先失败；框架缺失失败而非 skip。
- [ ] StateGraph 包含 decide/propose/approval/execute/observe/verify 节点；条件边选择下一节点，END 对应 paused/terminal，SQLite checkpointer 持久存储。审批节点结构为：

```python
from langgraph.types import interrupt

def approval_node(graph_state):
    decision = interrupt(graph_state['run']['pending']['approval_request'])
    return {'approval_decision': bool(decision)}
```

该节点前后都不写候选文件；独立 execute 节点经恢复账本落地。checkpoint 采用固定 run_id/thread_id，resume 用 Command(resume=approved)。Services 的单步调用可复用，但不得调用 runtime.run。Graph state 至少有 run/decision/result/approval_decision 四字段，各节点全量替换 run，防列表 reducer 重复消息。
- [ ] 真实 subprocess 验证 SQLite 跨进程恢复；记录 interruption 节点会重新执行的事实，并测试多次 resume 不重复副作用。对应官方文档见来源段。
- [ ] 提交 `feat(chapter12): orchestrate the coding task with durable LangGraph nodes`。

## Task 10: OpenAI Agents SDK 真正接管模型与工具循环

**Files:** 创建 `chapter12/adapters/sdk_agent.py`、`adapters/sdk_compat.py`、`adapters/sdk_replay_model.py`、`tests/test_agents_sdk.py`；修改 `tests/framework_cases.py`。

**Interfaces:** `run_sdk(state: Record, services: Services, snapshot: Path, approval: bool或None=None) -> Record`；`sdk_compat.dump_state(value: Any) -> str`、`load_state(agent: Any, text: str) -> Any`；`sdk_replay_model.make_model(decisions: list[Record]) -> Any` 返回实际 SDK Model 的测试实现。dump/load 内部签名以 Task 1 安装的 RunState 源码为准，由测试固定，不对外泄漏版本差异。

- [ ] 四场景合同外再测试原生 interruption roundtrip、工具 guard 不能绕过、SDK final_output 被独立验收拒绝。以 mock 把手写 runtime.run 替成异常，仍须完整运行。

```python
from chapter12.tests.framework_cases import run_scenario

def test_sdk_native_pause_survives_process_exit(tmp_path):
    result = run_scenario('agents_sdk', 'approval_restart', tmp_path)
    assert result['status'] == 'completed'
    assert result['writes'] == 2
    assert result['orchestration'] == 'agents_sdk'
    assert any(e['kind'] == 'sdk_interruption' for e in result['events'])

def test_sdk_final_output_is_not_acceptance(tmp_path):
    result = run_scenario('agents_sdk', 'false_finish', tmp_path)
    assert result['status'] != 'completed'
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_agents_sdk.py -q`，先失败；安装依赖后不得绕到自写 SDK 模拟器。
- [ ] 注册五个 function tools，apply_patch 使用原生 needs_approval=True，tool body 调 Task 7/8 网关重验具体批准；SDK 同意不替代版本检查。由 Runner.run 执行模型工具循环。原生批准流程遵循：

```python
result = await Runner.run(agent, sdk_input, context=services)
if result.interruptions:
    paused = result.to_state()
    # 本次先持久化 paused 与绑定具体动作的批准请求，然后向调用者返回。
    serialized = dump_state(paused)
```

sdk_input 是任务消息或 load_state 返回对象。下一进程重建相同 agent/tools/model、加载 paused、校验工作区和具体 Approval，然后对对应 interruption approve/reject，继续 Runner.run；不得把恢复变成新用户任务。make_model 实现已装 Model 抽象接口，将回放 Decision 转成 SDK 原生模型结果项，注册真实工具调度可观测计数，不自己调用工具。

SDK 工具调用的 call_id 从已装版本支持的 tool/run context 获取；若无公共入口，sdk_compat 从原生 run items 提取并明确测试，不能生成脱离原调用的 id。取消、轮数、工具次数、期限由 SDK 配置与共享网关双重约束；默认关闭外部 tracing 导出，保留本地脱敏 Trace。SDK 提前 final 后由独立 verifier 验收；失败证据作为下一次 continuation 输入，由 SDK 再决定，不在应用循环中替它选择工具。
- [ ] 测试 snapshot 不含 key、恢复不额外发送旧工具、禁止调用 runtime.run；记录框架控制步骤与自写安全步骤的归属。
- [ ] 提交 `feat(chapter12): run native SDK tool cycles with durable approval state`。

## Task 11: 五组实验、规范报告与真实运行证据

**Files:** 创建 `chapter12/experiments.py`、`reports/offline-canonical.json`、`reports/framework-comparison.json`、`reports/live-observation.md`、`README.md`、`tests/test_experiments.py`；更新 `quickstart.py`。

**Interfaces:** `experiments.run_group(group: int, directory: Path) -> Record`；`canonicalize(report: Record) -> Record`；`experiments.main(argv: list[str]或None=None) -> int`。输出包含 decision_source/orchestration/backend/scenarios/evidence/limits，不能只有总体成功率。

- [ ] 固定全部输入和逻辑序号，两目录重跑比较规范记录；跨平台因素显式分字段，不用删失败结果来求一致。

```python
from chapter12.experiments import run_group, canonicalize

def test_reports_are_reproducible(tmp_path):
    left = canonicalize(run_group(2, tmp_path / 'one'))
    right = canonicalize(run_group(2, tmp_path / 'two'))
    assert left == right
    assert left['decision_source'] == 'replay'
    assert left['scenarios']['false_finish']['accepted'] is False
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_experiments.py -q`，先失败。
- [ ] 实验逐项覆盖 spec 的 12-1 到 12-5；每项返回预期行为、观测结果、通过判据、不能证明的内容。规范化采用字段白名单，保留状态/错误/次数/版本，不替换证据：

```python
def canonicalize(report):
    keys = ('schema_version', 'decision_source', 'orchestration',
            'backend', 'scenarios', 'evidence', 'limits')
    return {key: report[key] for key in keys}
```

规范 evidence 用相对路径和逻辑事件；真实时间、耗时、usage 不装入 canonical 文件。报告生成默认拒绝覆盖已有版本，需要先保存旧候选目录并明确 --replace，不能破坏历史。
- [ ] 执行 `python -B -m chapter12.experiments --group all --output chapter12/.runs/check-one` 与第二目录 check-two；逐组比较规范报告。组 4 的真实容器结果单列，不把回放策略拒绝混成操作系统探针。
- [ ] 真实运行前只查配置变量是否存在并询问/遵守实际调用预算，默认最多 30 模型轮、60 工具、300s 累计期限；不得从旧对话拷贝 key。容器预检通过后运行 `python -B -m chapter12.quickstart start --model live --backend container --run-id live-01`，逐动作审批。至少保留一次完整真实运行；若失败如实记录并调查，不把 ReplayModel 成功替代。脱敏摘要记录模型/API/依赖版本、日期、用量、人工介入、红到绿证据或实际停止原因和报告校验 hash。
- [ ] 提交 `docs(chapter12): record reproducible experiments and sanitized live evidence`，仅暂存源码/测试/README/三个审查后的报告，禁止暂存 `.runs` 和原始 live-reports。

## Task 12: 固定 Pi 源码阅读和产品来源台账

**Files:** 创建 `book/sources/chapter12-sources.md`、`chapter12/pi-source-study.md`、`chapter12/tests/test_sources.py`。

**Interfaces:** 资料记录统一字段 `id, title, official_url, checked_at, commit_or_version, local_claim, evidence_kind`；不把文档阅读写成实测。Pi 五阅读点给完整 commit permalink；书稿引用用来源 id。

- [ ] 先写来源结构测试：

```python
from pathlib import Path
import re

def test_pi_links_are_commit_pinned():
    text = Path('chapter12/pi-source-study.md').read_text(encoding='utf-8')
    links = re.findall(r'https://github.com/earendil-works/pi/blob/([^/]+)/', text)
    assert len(links) >= 5
    assert all(re.fullmatch(r'[0-9a-f]{40}', revision) for revision in links)
    assert '源码阅读，不是产品运行记录' in text
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_sources.py -q`，文件未创建时失败。
- [ ] 只读取得 Pi 当前 commit，读取该 commit 的项目 README、Agent Core、agent-loop.ts、SDK、containerization 五处；记录对应 package.json 版本和更名/namespace。引用五个问题：模型适配和运行时分层；上下文转换；工具完整参数/失败/事件；会话与资源加载；默认权限及外部隔离。短片段就近引用，图文用自己的解释；明确默认工具与可选工具，Pi 不成为 Python 实现依赖。
- [ ] 复核下方官方来源的 Task 9/10 API，安装版本与网页不一致时以已装版本+对应官方源码为实现依据并记差异；更新台账，不强行升级到未测试新接口。重跑来源测试并人工点检每条永久链接能支持对应结论。
- [ ] 提交 `docs(chapter12): pin Pi source study and framework references`。

## Task 13: 14 道分层练习与完整答案

**Files:** 创建 `chapter12/exercise_solutions.py`、`reference-answers.md`、`tests/test_exercises.py`。

**Interfaces:** `solve(number: int) -> Record`；CLI `python -B -m chapter12.exercise_solutions --all`。解释/设计题返回要点和判据，实验题实际运行局部机制，不能只返回“应观察到”。

- [ ] 测试编号完整、每题判据非空、数值题可复算，至少七题调用真实实现而非硬编码成功字符串。

```python
from chapter12.exercise_solutions import solve

def test_budget_answer_is_computable():
    answer = solve(10)
    assert answer['input'] == {'total_seconds': 120, 'elapsed_seconds': 35, 'single_call_cap': 45}
    assert answer['remaining_seconds'] == 85
    assert answer['next_timeout_seconds'] == 45
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_exercises.py -q`，先失败。
- [ ] 题目固定为：①提议与执行；②读日志定位失败；③增加只读查询；④补丁唯一匹配；⑤过期版本；⑥批准绑定；⑦崩溃后三态；⑧上下文完整对；⑨零测试假绿；⑩预算计算；⑪隔离探针；⑫Graph重入；⑬SDK最终输出；⑭手写/Pi/框架职责设计。数值实现：

```python
def budget_answer(total_seconds, elapsed_seconds, single_call_cap):
    remaining = max(0, total_seconds - elapsed_seconds)
    return {'remaining_seconds': remaining,
            'next_timeout_seconds': min(remaining, single_call_cap)}
```

③用独立练习入口扩展只读工具，不改变正文五工具合同；⑪缺容器明确未验证，--all 分机制答案和环境实测，不吞失败；⑫⑬运行真实框架。答案包含目录/完整命令/关键输出/错误原因/边界，不用未定义变量。
- [ ] 执行 --all 并逐题对照答案；保存非敏感固定结果于规范实验记录，不另造手填成功证据。
- [ ] 提交 `docs(chapter12): add fourteen exercises with runnable solutions`。

## Task 14: 按读者路线写完整正文并自审

**Files:** 创建 `book/chapter12.md`、`book/reviews/chapter12-review-codex-v1.0-rc1.md`、`chapter12/tests/test_manuscript.py`。

**Interfaces:** 正文只引用已实现路径/已观察实验；图片暂用普通文字的制作标记而非不存在的 Markdown 图片链接，Task 15 接上正式资源后删除标记。章节状态明确候选。

- [ ] 写结构测试：

```python
from pathlib import Path
import re

def test_manuscript_depth_and_exercises():
    text = Path('book/chapter12.md').read_text(encoding='utf-8')
    assert 20000 <= len(re.findall(r'[\u4e00-\u9fff]', text)) <= 30000
    assert 30 <= len(re.findall(r'^#{2,3} ', text, re.M)) <= 36
    assert len(re.findall(r'^\*\*练习 \d+', text, re.M)) == 14
```

练习使用加粗段首而非全部三级标题；正文标题口径保持 30–36。不得为了测试通过把答案并入正文凑字。
- [ ] 运行 `python -B -m pytest chapter12/tests/test_manuscript.py -q`，先失败。
- [ ] 按 spec 四段 26 个主题展开：第一段约 3k–4k 字，看运行与职责；第二段约 6k–8k，五工具与循环；第三段约 6k–8k，验收/审批/隔离/恢复/压缩/停止/Trace；第四段约 5k–7k，Pi与两框架/取舍/练习/衔接。最终整体不超总字数目标。每节写具体输入→过程→输出→失败反例，正文只展示关键代码，长协议放进阶材料。
- [ ] 完整显示一次真实运行与一次离线回放的区别；来源脚注就近放置；引用自己的实际 API 名称，不把 SDK 开发指南复制成主体。至少 3 张比较表用于易混概念，不为凑数量重复安全声明。26 个主题中必要位置细分三级标题得到 30–36 个，练习题不新增标题层级。
- [ ] 从新读者角度逐节标注“此处尚未解释的词/跳步/例子不完整”，再从工程角度检查 completion/approval/sandbox/framework 边界。review 写出实际问题、修改位置、残留限制，不只评分；重跑结构测试，人工验清晰度不能由字数替代。
- [ ] 提交 `docs(chapter12): write the mini coding agent chapter with evidence-led review`。

## Task 15: 七幅原创图、本地预览和移动端检查

**Files:** 创建 `book/images/chapter12/01-boundary.png`、`02-tools.png`、`03-loop.png`、`04-approval.png`、`05-context.png`、`06-sandbox.png`、`07-responsibilities.png`；创建 `infographic/chapter12/technical-brief.md`、`prompts.md`、`review.md`、`chapter12/preview.py`、`requirements-preview.txt`、`book/check_chapter12_preview.mjs`、`chapter12/tests/test_preview.py`；修改正文图片引用。

**Interfaces:** `preview.build_preview(root: Path) -> Path`，输出 `chapter12/preview-pages/index.html`；浏览器检查截图在 `chapter12/preview-pages/screenshots/`，均为本地忽略产物。预览沿用 chapter11 版式但不导入其正文数据；不改变公开站点 allowlist。

- [ ] 测试图片引用七个、目标存在、预览标题和语言、相对资源能解析。

```python
from pathlib import Path
from chapter12.preview import build_preview

def test_candidate_preview_has_seven_figures():
    page = build_preview(Path.cwd())
    text = page.read_text(encoding='utf-8')
    assert '第 12 章' in text and '本地候选' in text
    assert text.count('<figure>') == 7
```

- [ ] 运行 `python -B -m pytest chapter12/tests/test_preview.py -q`，先失败。
- [ ] 执行前读取适用的 imagegen 技能；按技术草图逐幅生成，米白纸感/手绘线条/蓝绿紫橙/中文为主。七题严格对应 spec；03 call_id 与 action_id 不混；04 含后态补回执与第三态停止；06 宿主 key 不进容器；07 明示 Pi 仅源码参照。图中只放读者需要的字段，避免密集海报。提示词与生成来源入工程，保留迭代版本，不复制参考图。
- [ ] 预览实现使用现有 Markdown extra/toc、figure caption、表格横向容器及响应式 CSS；图片链接支持原图查看，手机难读图提供分区说明。Playwright 检查 1440×1000 和 390×844：资源无404、主页面无溢出、图中文字可辨、箭头与图注一致；人工看七图及截图，不用尺寸断言代替阅读。
- [ ] 执行 `python -B -m chapter12.preview`、`node book/check_chapter12_preview.mjs` 与 preview 测试；review.md 逐图记录缺字/错箭头/字号修正情况。
- [ ] 提交 `docs(chapter12): add seven illustrated explanations and candidate preview`，精确暂存图/提示词/源码/正文，排除 HTML 和截图构建物。

## Task 16: 全量验收、历史保留与本地候选交付

**Files:** 创建 `book/versions/chapter12-v1.0-rc1.md`、`chapter12/tests/test_delivery.py`；修改 `AGENTS.md` 的实验包范围及候选状态、`book/reviews/chapter12-review-codex-v1.0-rc1.md`。不改 public manifest，不更改旧版本台账条目。

**Interfaces:** 版本记录含正文/代码/图资源校验 hash、依赖锁、准确命令与计数、live/容器/框架状态、已知限制、review 结论；candidate 不写成 published。

- [ ] 用当前提交对照设计逐条验收；增加测试检查无 Chapter 12 公开 allowlist，旧章节文件和 tag 无变化。任何环境未完成项写“未验证”，不能用 core 测试通过代替。

```python
import subprocess
from pathlib import Path

def test_public_manifest_stays_at_existing_release():
    baseline = subprocess.check_output(['git', 'show', '3384ce6:book/manifest.json'])
    current = Path('book/manifest.json').read_bytes()
    assert current.replace(b'\r\n', b'\n') == baseline.replace(b'\r\n', b'\n')
```

该测试允许 manifest 原有 planned 章节继续存在，只禁止把候选偷偷变成公开发布。浅克隆缺基线提交时显式提示获取历史，不改测试为无条件通过。
- [ ] 首先保存基线 `git diff --name-status 3384ce6`，确认只有本计划列出的新增/允许修改路径；人工核对没有旧书稿重写。
- [ ] 完整运行并保留真实输出：

```text
python -B -m pytest chapter12/tests -q
python -B -m chapter12.experiments --group all --output chapter12/.runs/final-a
python -B -m chapter12.experiments --group all --output chapter12/.runs/final-b
python -B -m chapter12.exercise_solutions --all
python -B -m chapter12.preview
node book/check_chapter12_preview.mjs
python -B -m unittest discover -s tests -q
python -B -m scripts.check_repository
python -B -m scripts.build_site
python -B -m mkdocs build --strict
git diff --check
```

构建器会清理自身既有输出，运行前确认 `_web`、`site` 位于本书项目内且为构建目录；不将绝对宽泛目录作为输出。没有容器/key 时对应任务仍未验收；报告中分离已完成与缺口。额外运行敏感字串/作者路径扫描及 Git 暂存检查，不输出发现的 secret 值。
- [ ] 执行方式为 Native 时在全部任务完成后按计划进行一次独立全分支审查；按审查发现补测试和修订，不仅转述“通过”。读者review关注有没有从一个能读懂的例子走到系统，专家review关注证据边界与实际调用链。保留 rc1 文稿、图、报告、review 的 Git 历史；若修订成 rc2，先提交 rc1 再追加 rc2 版本说明。
- [ ] 精确暂存版本记录、AGENTS候选状态和review；提交 `docs(chapter12): record verified local candidate and preserved history`。同步用户指定 D 盘书籍目录前检查两侧HEAD与dirty状态，使用可快进的本地 Git 同步，不覆盖用户改动；需权限时走审批。
- [ ] 最终提供正文、预览、实验README、review、版本记录的项目路径，说明未发布；不能因候选完成而自行 push/deploy。只有设计所有必需验收实实在在完成才声明第 12 章交付完成。

## 官方资料与版本核验入口

以下页面已于 2026-09-19 用于规划核验；实际实现仍须记录已安装版本及源码合同。

- [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk)：SDK 管循环，应用仍负责工具、存储与部署。
- [Guardrails and human review](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)：function_tool、needs_approval、interruptions、to_state 与恢复同一次运行；不继承 Codex 产品的审批设置。
- [Results and state](https://developers.openai.com/api/docs/guides/agents/results)：最终输出、下一轮历史与暂停快照不是同一对象。
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：持久 checkpointer、thread_id、Command(resume=...)；恢复会重进 interrupt 所在节点。
- [Pi 官方仓库](https://github.com/earendil-works/pi)：Task 12 固定五处源码到同一个 commit，不以 main 链接作为最终证据。

## 计划自查与实施交接

覆盖映射：案例/工具 Task 1–2；持久状态/Trace Task 3；隔离 Task 4；独立验收 Task 5；上下文/模型 Task 6；运行控制 Task 7；审批恢复 Task 8；两框架 Task 9–10；五实验及真实运行 Task 11；Pi/来源 Task 12；14题 Task 13；书稿及读者review Task 14；七图/移动预览 Task 15；历史/最终验收 Task 16。Review Focus 五项分别有具体拥有任务，不另建只报成功的“安全总测试”。

自查执行时还须检查公共函数命名与参数、错误返回是否确实重新进入观察、SDK snapshot 对象不能用普通消息历史替代、两个框架不能导入手写 run。计划中的期望输出必须由运行生成；Task 4 与 Task 11 的环境缺口不能因文字已经写好而注销。

建议 Native：由当前任务顺序实现，再做一次独立全分支复核。理由是三个编排版本共享较多接口，连续维护有利于代码、实验和教学术语一致。另一方式是 Subagent-driven：逐任务使用独立实现者与审查者，审查更密集但上下文与调用成本更高。用户审阅本计划并选择后再开始实现。
