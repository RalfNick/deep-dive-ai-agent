# 第 3 章实验：从一次生成到闭环执行

本目录包含一个最小 Agent Loop、5 个编号实验、1 个 Trace 补充实验和 19 项回归测试，全部只依赖 Python 3.11+ 标准库，不需要模型 API Key。实验使用基于结构化观察推进的确定性策略代替真实模型，以隔离并验证 Agent Runtime 的责任边界；它不代表真实模型能力。

## 运行

~~~powershell
cd chapter3
python agent_loop.py
python one_shot_vs_loop.py
python loop_guards_demo.py
python tool_error_demo.py
python verifier_demo.py
python trace_replay_demo.py
python run_all_experiments.py
python -m unittest discover -s tests -v
~~~

每个代码修复实验都在系统临时目录创建独立 `pricing.py` 与 `test_pricing.py`，结束后自动清理，不修改真实项目源文件。

## 实验与结论边界

| 文件 | 可观察内容 | 能支持的结论 | 不能支持的结论 |
| --- | --- | --- | --- |
| `one_shot_vs_loop.py` | 候选代码、文件摘要、真实测试退出码 | 生成候选与环境完成是不同事件 | 所有任务都必须使用 Agent |
| `agent_loop.py` | 观察驱动决策、唯一调用 ID、状态变化与结构化验收 | 最小闭环可拆为 Model/Harness/Environment/Verifier | 确定性策略代表真实 LLM 能力 |
| `loop_guards_demo.py` | 相同动作计数和受控停止 | 最大步数之外还需要进展检测 | 所有重复调用都是错误 |
| `tool_error_demo.py` | 普通超时、先提交后丢响应、永久错误与幂等去重 | 错误类型和幂等键决定安全重试 | 教学账本等价于支付事务系统 |
| `verifier_demo.py` | 自我报告与受保护测试、状态摘要验收的差异 | task completion 应有外部证据 | 单元测试覆盖全部用户意图 |
| `trace_replay_demo.py` | `call_id` 数量、顺序、关联与状态摘要回放 | 事件可用于完整性检查和确定性回放 | 任意外部副作用都可安全重放 |

## 核心实现文件

`agent_loop.py` 同时提供：

- `ToolCall`、`ToolResult`、`Decision`、`Event` 和 `RunResult`；
- 包含规则、命令、退出码、状态摘要和受保护文件检查的 `VerificationResult`；
- 真实临时仓库与测试进程 `PriceRepo`；
- 确定性 `RepairPolicy`；
- 带最大步数、重复动作检测和完成验收的 `AgentLoop`。

`run_all_experiments.py` 会在本地重新运行六个脚本，并将命令、退出码、有限标准输出以及“能证明 / 不能证明”的边界写入 `reports/experiment-results.json`。报告不会记录环境变量、API Key 或临时仓库绝对路径。

生成器默认写入固定的规范快照时间，以保证同一环境连续生成的 JSON 字节一致；调用 `run_all(generated_at=...)` 时仍可显式记录一次独立运行的时间。

真实模型接入时，应只替换 Policy 层，保留参数验证、执行、预算、错误、Trace 和 Verifier 在运行时层。

## 环境与复现

- Python：3.11+；
- 第三方依赖：无；
- 随机性：无；
- 外部网络：无；
- 文件副作用：仅系统临时目录；
- 测试命令：`python -m unittest discover -s tests -v`。

本章开发过程中曾在 Windows 上因根路径未规范化而误拒绝合法子路径。修复后保留了合法读取与 `../secret.txt` 越界拒绝两类测试，避免以删除安全检查换取通过。

## 返回正文

- [第 3 章正文](../book/chapter3.md)
- [第 3 章参考答案](./reference-answers.md)
