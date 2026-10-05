# 第 12 章实验包：从零实现一个可恢复的 Coding Agent

配套正文：[手写一个 Mini Coding Agent](../book/chapter12.md)。

这是《深入浅出 AI Agent》第 12 章的自包含配套工程。它先用手写循环暴露模型、工具、审批、执行、验证和状态之间的边界，再用真实 LangGraph 1.2.11 与 OpenAI Agents SDK 0.20.0 重构同一任务。

当前代码和离线实验可运行。容器部分只用于说明生产隔离合同和参考命令形状，完整探针编排与真实模型运行不属于本章的可运行验收范围。因此这里不会把 `trusted_local` 子进程称为沙箱，也不会用 ReplayModel 的成功代替真实模型证据。

## 先建立可复现环境

本章的手写 Loop 主要使用标准库，但完整测试还会真正加载 LangGraph、SQLite checkpointer、OpenAI Agents SDK 与 pytest。fresh clone 不能直接沿用系统 Python；请在书籍仓库根目录用 Python 3.11 建立虚拟环境，并始终用同一个解释器安装和运行：

```powershell
# Windows PowerShell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes `
  -r chapter12/requirements-dev.txt
```

```bash
# Linux / macOS
python3.11 -m venv .venv
.venv/bin/python -m pip install --require-hashes \
  -r chapter12/requirements-dev.txt
```

`requirements-dev.txt` 是带哈希的完整测试锁；不要用一个解释器安装、另一个解释器运行。若只需生成本地 HTML 预览，再用同一解释器安装可选的 `chapter12/requirements-preview.txt`。容器与真实模型仍不属于这条离线路径。

## 最短运行路径

以下示例中的 `python` 均指刚创建的虚拟环境解释器；Windows 未激活环境时可直接替换为 `.venv\Scripts\python.exe`：

```powershell
# 全部行为测试
python -B -m pytest chapter12/tests -q

# 两个新目录分别生成五组离线报告
python -B -m chapter12.experiments --group all --output chapter12/.runs/check-one
python -B -m chapter12.experiments --group all --output chapter12/.runs/check-two
```

报告目录已经存在时默认拒绝覆盖。确需重跑可显式添加 `--replace`；旧目录会改名为相邻的 `.previous-N`，不会被删除。

## 手动观察审批与恢复

仓库已经提供经过审阅的规范 Replay，可以直接启动教学工作区：

```powershell
python -B -m chapter12.quickstart start `
  --workspace chapter12/.runs/manual/repo `
  --run-id manual-01 `
  --model replay `
  --replay chapter12/fixtures/replay/canonical.json
```

返回 `awaiting_approval` 后，复制输出中的具体 `action_id`：

```powershell
python -B -m chapter12.quickstart approve `
  --workspace chapter12/.runs/manual/repo `
  --run-id manual-01 `
  --action-id <具体 action_id>

python -B -m chapter12.quickstart resume `
  --workspace chapter12/.runs/manual/repo `
  --run-id manual-01 `
  --model replay `
  --replay chapter12/fixtures/replay/canonical.json
```

审批不是 `approve-all`：它同时绑定 run、action、参数摘要和工作区版本。文件在暂停期间变化会得到 `approval_stale`，不会覆盖外部编辑。

`trusted_local` 会在宿主机执行候选测试，而 Replay 可以提议创建 `tests/test_agent_*.py`。因此只有仓库内置的规范 Replay 默认受信；自定义 Replay 会先返回 `trusted_replay_confirmation_required`。确认你已经逐项审阅并信任它以后，才可显式添加 `--trust-replay-file`。这个参数只是信任声明，不会检查 Replay 是否安全；不要对下载或模型临时生成的未知 JSON 使用它。

## 五组实验

| 组 | 核心问题 | 当前证据 |
| --- | --- | --- |
| 12-1 | 从读取、红灯、补丁到独立验收是否闭环 | 离线 Replay 完成；live 延后 |
| 12-2 | 错工具、错参数、截断、旧补丁和假完成如何失败 | 均有明确错误与零副作用检查 |
| 12-3 | 审批后崩溃是否重复写 | 正常恢复、过期审批、写后未回执均覆盖 |
| 12-4 | 上下文与隔离是不是同一件事 | 压缩和宿主边界通过；容器探针未运行、隔离未验证 |
| 12-5 | 框架究竟接管了什么 | 手写、LangGraph、Agents SDK 共用任务与 Verifier |

规范输出见 [offline-canonical.json](reports/offline-canonical.json)，框架对照见 [framework-comparison.json](reports/framework-comparison.json)。它们只记录稳定字段，不含临时绝对路径、墙钟耗时或随机 ID。

## 真实模型入口为什么当前会停止

真实模型只能与 `container` 后端组合：

```powershell
python -B -m chapter12.quickstart start `
  --workspace chapter12/.runs/live/repo `
  --run-id live-01 `
  --model live `
  --backend container `
  --model-name <明确的模型名>
```

程序先做隔离预检。当前环境会返回 `isolation_unverified`，且不会创建候选工作区、读取 API Key 或发起模型请求。本章没有实现完整的容器探针编排，这个入口用于表达“隔离证据不足时必须停止”的控制原则，不是可直接用于不可信代码的生产沙箱教程。生产实现只有在非 root、只读根、禁网、无凭据、资源限制和取消清理等属性都经过真实探针验证后，才应继续。

## 代码阅读顺序

1. `contracts.py`、`tools.py`：五工具协议与文件边界。
2. `state.py`、`recovery.py`：动作账本、具体审批和三态恢复。
3. `services.py`、`runtime.py`：手写 decide → propose → execute → observe → verify。
4. `verifier.py`、`acceptance/`：候选测试之外的独立完成证据。
5. `adapters/langgraph_agent.py`：图节点、`interrupt` 与 SQLite checkpoint。
6. `adapters/sdk_agent.py`：Runner、真实 function tools、原生 RunState interruption。
7. `experiments.py`：五组报告怎样由真实执行记录归纳而来。

## 证据边界

- `trusted_local` 只适用于可信夹具与可信 Replay；Replay 能写入候选测试，因此它不是“不执行任意代码”的强制边界。
- 同进程验收能抓住教学误修与明显伪造，不宣称抵抗主动恶意代码。
- 三种编排的共同通过只证明这套固定任务与合同，不构成框架排名。
- 当前未发生模型 API 调用，用量为零。真实运行状态与停止原因见 [live-observation.md](reports/live-observation.md)。
