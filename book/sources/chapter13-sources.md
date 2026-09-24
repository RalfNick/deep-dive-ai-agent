# 第 13 章来源与版本台账

核对日期：2026-09-24。本章优先引用论文、官方文档和本地可运行实验。产品接口会变化，正文只采用稳定概念；具体页面以本台账记录的核对日期为边界。

## 核心方法

### anthropic-evals

- Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 2026-01-09。
- 用途：Task、Trial、Grader、Transcript/Trajectory、Outcome、Evaluation Harness、Agent Harness 与 Suite 的术语边界；代码、模型、人工评分器的组合；能力评测与回归评测；人工阅读轨迹和校准 Judge 的必要性。
- 边界：文章中的团队经验与客户案例不能直接外推为所有 Agent 的最优实践；其中“20–50 个初始任务”是经验建议，本章的 12 个任务只是教学夹具。

### anthropic-infra-noise

- Anthropic, [Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise), 2026-02-05。
- 用途：说明 CPU、内存、超时、并发、运行时和基础设施错误属于评测条件；小分差在环境未对齐时不能直接解释为能力差异。
- 边界：文中具体百分点来自 Terminal-Bench 2.0 与 SWE-bench 的特定实验，本章只采用“环境是一级实验变量”这一方法论，不复用其数值结论。

### humaneval

- Mark Chen et al., [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374), 2021。
- 用途：HumanEval 与 `pass@k`；当每题运行 `n` 次、有 `c` 次通过时，使用组合数形式的无偏估计。
- 本地映射：`chapter13/metrics.py::pass_at_k`。

### tau-bench

- Shunyu Yao et al., [τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html), ICLR 2025；[arXiv 版本](https://arxiv.org/abs/2406.12045)。
- 用途：通过最终数据库状态而不是声明判断结果；`pass^k` 衡量同一任务连续 `k` 次全部成功的可靠性。
- 本地映射：`chapter13/metrics.py::pass_all_k`。

### mt-bench-judge

- Lianmin Zheng et al., [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685), 2023。
- 用途：LLM Judge 的可扩展性，以及位置、冗长、自我增强和推理能力等偏差。
- 边界：论文中的一致率属于其模型、任务和人工偏好数据，不代表任意 Judge 在本书任务上的准确率。

### g-eval

- Yang Liu et al., [G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment](https://arxiv.org/abs/2303.16634), 2023。
- 用途：分步骤评价标准、结构化表单和模型评分；同时提醒模型评分可能偏爱模型生成文本。
- 边界：本章不复现论文相关系数，只采用“Rubric 必须校准”的设计原则。

## 框架与产品映射

### openai-evals

- OpenAI, [Working with evals](https://developers.openai.com/api/docs/guides/evals)，核对于 2026-09-24。
- 用途：数据集、Eval、运行与 Grader 的平台化组织。

### openai-agent-evals

- OpenAI, [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals)，核对于 2026-09-24。
- 用途：Agent 工作流评估、数据集与评测运行的组合。

### openai-trace-grading

- OpenAI, [Trace grading](https://developers.openai.com/api/docs/guides/trace-grading)，核对于 2026-09-24。
- 用途：将 Trace 作为诊断与评分输入。生产 Tracing 的展开留给第 14 章。

### openai-graders

- OpenAI, [Graders API Reference](https://platform.openai.com/docs/api-reference/graders)，核对于 2026-09-24。
- 用途：字符串、模型标签等 Grader 形态。正文不绑定具体请求字段。

### langsmith-evaluation

- LangChain, [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types)，核对于 2026-09-24。
- 用途：离线 Benchmark、单元测试、回归测试、回测与成对评估；在线监控；代码、Judge、组合、汇总和成对 Evaluator。
- 边界：本章只做概念映射，不需要 LangSmith 账号或 SDK。

### inspect-tasks

- UK AI Security Institute, [Inspect AI Tasks](https://inspect.aisi.org.uk/tasks.html)，核对于 2026-09-24。
- 用途：`Task = Dataset + Solver + Scorer` 的核心组合，以及 Sandbox、Limits、Error handling 等任务选项。
- 边界：本章实验没有安装 Inspect AI，只把本地接口映射到其稳定概念。

## 本地证据

### local-contracts

- `chapter13/contracts.py`、`dataset.py`、`fixtures/tasks.json`。
- 用途：12 个教学任务、TaskSpec、TrialRecord 与 GraderResult 的唯一数据合同。

### local-runner

- `chapter13/runner.py`、`grading.py`、`metrics.py`、`experiments.py`。
- 用途：确定性策略、真实临时工作区、四类评分器、`pass@k`、`pass^k`、成对 Bootstrap 和发布门禁。

### local-judge

- `chapter13/judge.py`、`fixtures/judge-calibration.json`。
- 用途：12 个固定编辑教学标签（未经独立人工复核）、离线预测、一致率、混淆矩阵和 `Unknown`；可选 Live Judge 只在显式调用时读取环境变量。

## 引用原则

- 本章报告中的 55%、75%、95%、100%、12.5%、40%、66.67% 等数字只描述固定教学策略和固定夹具。
- 不将这些数字解释为任何真实模型、Claude Code、Codex、OpenAI Evals、LangSmith 或 Inspect AI 的能力排名。
- 未运行真实模型时，Token 与费用保持 `null`，不使用估算值冒充 Provider Usage。
- 第 14 章再讨论公共 Benchmark、Trace 平台、生产采样、延迟、Token、费用与线上诊断。
