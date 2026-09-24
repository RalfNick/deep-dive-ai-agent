# 第 13 章实验包：Agent 评估

这是《深入浅出 AI Agent》第 13 章的自包含配套工程。它用 12 个 Coding Agent 教学任务、两套确定性策略和 5 个固定种子，展示如何从最终回复逐步建立 Outcome、Trajectory、多评分器、可靠性指标、成对统计和发布门禁。

本实验包验证的是 **Evaluation Harness 的机制**，不是模型能力。`baseline` 与 `candidate` 的决策和成功日程已经冻结；报告中的 55%、75% 等数字是教学夹具，不得写成模型、供应商或框架排名。

## 环境与依赖

运行时代码只使用 Python 标准库。测试固定使用 Python 3.11 与 pytest；本地 HTML 预览另外使用 Markdown。

```powershell
# 在仓库根目录执行
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes `
  -r chapter13/requirements-dev.txt
.venv\Scripts\python.exe -m pip install `
  -r chapter13/requirements-preview.txt
.\.venv\Scripts\Activate.ps1
```

不要把 API Key 写入仓库。本章所有规范实验与参考答案均离线运行，也不会读取任何模型环境变量。

## 最短运行路径

以下命令假设已执行上面的 `Activate.ps1`。如果当前 PowerShell 禁止加载激活脚本，也可以把每条命令开头的 `python` 替换为 `.venv\Scripts\python.exe`。

```powershell
python -B -m pytest chapter13/tests -q
python -B -m chapter13.experiments --group all --output chapter13/.runs/reader-first
python -B -m chapter13.exercise_solutions --all
python -B -m chapter13.preview
```

实验输出目录已经存在时，命令默认拒绝覆盖。若确实需要替换，可显式添加 `--replace`；旧目录会重命名为相邻的 `.previous-N`，不会被删除。

## 12 个任务和四个切片

| 切片 | 数量 | 评估重点 |
| --- | ---: | --- |
| `basic` | 3 | 嵌套相对链接、锚点和外部链接 |
| `edge` | 3 | query/fragment、图片与空格、多文件回归 |
| `safety` | 3 | 受保护测试、隐藏答案和工作区边界 |
| `recovery` | 3 | 超时、暂时错误和步骤预算 |

每道任务都有明确的写入范围、受保护路径、步骤预算和工具调用预算。每个 Trial 都从独立工作区开始；稳定报告只保存初始内容指纹，不保存临时绝对路径。

## 五组实验

| 组 | 核心问题 | 主要证据 |
| --- | --- | --- |
| 13-1 | 同一句“修复完成”为何可能一真一假 | final answer、Outcome、Trajectory、受保护路径 |
| 13-2 | 测试篡改、隐藏答案和越界怎样被发现 | 策略违规事件、文件完整性、独立状态分类 |
| 13-3 | 多个 Grader 怎样组合 | Outcome、Trajectory、Safety、Efficiency 与硬否决 |
| 13-4 | 一次成功为何不能代表可靠 | `pass@1`、`pass@k`、`pass^k`、切片和 Bootstrap |
| 13-5 | 新版本是否可以发布 | 成对回归、Judge 校准、三态门禁 |

规范结果位于 `chapter13/reports/`。它包含全部 120 条 Trial 的稳定 JSON、便于阅读的 Markdown 摘要和五组实验报告。

## 报告合同

- `TaskSpec`：任务、夹具、标签、数据切分、成功条件、写入边界、预算和种子策略。
- `TrialRecord`：一次具体尝试的环境指纹、Outcome、事件、用量和评分。
- `GraderResult`：`pass / fail / unknown / not_applicable`、原因码和证据。
- `EvaluationReport` / `evaluation-report.json`：版本化总报告、切片指标、可靠性指标、置信区间、失败清单和发布结论。

稳定 JSON 的正式合同位于 `schemas/evaluation-report-v1.schema.json`。新增或改名字段必须发布新的 schema 版本，不能在同一个 `chapter13.eval.v1` 下静默改变含义。

`environment_error` 不进入能力指标分母，但会单独计数并阻止发布。没有 Provider Usage 时，Token 和费用字段保持 `null`，不会根据字符数伪造。

## 可选 Live Judge

`chapter13/judge.py` 提供显式的 OpenAI-compatible 调用边界，但规范实验不会调用它。只有应用代码主动调用 `run_live_judge()` 时，函数才读取指定的环境变量并发起请求。API Key、模型名、真实响应和 live 报告不得进入版本库。

## 代码阅读顺序

1. `contracts.py`、`dataset.py`：稳定数据合同与 12 任务集。
2. `runner.py`：隔离教学工作区和固定策略。
3. `grading.py`：四类 Grader 与发布硬门禁。
4. `metrics.py`：`pass@k`、`pass^k` 与任务级成对 Bootstrap。
5. `judge.py`：固定金标校准和显式 live 边界。
6. `experiments.py`：五组实验、稳定报告与防覆盖策略。
7. `exercise_solutions.py`：计算题与实验题可执行，设计题输出结构化参考答案；状态字段不代表自动证明设计题正确。

## 证据边界

- 12 道任务是教学夹具，不代表生产流量。
- 固定策略结果只证明评估管线能区分预先设计的边界。
- 工作区隔离是目录级教学机制，不是容器或敌对代码沙箱。
- Bootstrap 描述当前任务样本的不确定性，不证明任务具有代表性。
- 离线 Judge 校准只展示协议，不证明任何真实 Judge 已达到上线质量。
