# 第 15 章实验包：Agent 的后训练

配套正文：[Agent 的后训练：什么时候 Prompt 已经不够](../book/chapter15.md)。

这是《深入浅出 AI Agent》第 15 章的自包含教学工程。它用五类失败、24 条确定性轨迹、有限状态动作策略、固定回放和单状态奖励更新，回答什么时候不该训练、怎样把 Trace 变成可信数据，以及为什么安全门禁不能被结果分抵消。当前为本地 `v1.0-rc2` 候选，未发布。

本实验包验证的是数据与发布机制，不是模型排行榜。它不会下载模型、读取 API Key、访问网络或启动 GPU 训练。

## 环境与依赖

运行时代码只使用 Python 标准库；测试依赖 Python 3.11、pytest 与 `jsonschema`，本地 HTML 预览额外使用锁定版本的 Markdown。

```powershell
# 在仓库根目录执行
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --require-hashes `
  -r chapter15/requirements-dev.txt
.\.venv\Scripts\Activate.ps1
```

规范实验离线运行。不要把生产密钥、未经授权的 Trace、真实用户输入或未脱敏工具参数复制到夹具中。

## 最短运行路径

```powershell
python -B -m pytest chapter15/tests -q
python -B -m chapter15.experiments --group all --output chapter15/.runs/reader-all
python -B -m chapter15.exercise_solutions --all
python -B -m chapter15.preview
```

输出目录已存在时默认拒绝覆盖。实验需要重建时显式传入 `--replace`；练习答案始终拒绝覆盖，避免不知情地抹掉读者结果。

## 五组实验

| 组 | 核心问题 | 命令 |
| --- | --- | --- |
| 15-1 | 失败是否真的需要训练 | `python -B -m chapter15.experiments --group 1 --output chapter15/.runs/intervention` |
| 15-2 | 成功轨迹是否有资格进入训练集 | `python -B -m chapter15.experiments --group 2 --output chapter15/.runs/data-audit` |
| 15-3 | SFT 会怎样学习干净与污染示范 | `python -B -m chapter15.experiments --group 3 --output chapter15/.runs/sft` |
| 15-4 | DPO 的 margin 与 loss 怎样复算 | `python -B -m chapter15.experiments --group 4 --output chapter15/.runs/dpo` |
| 15-5 | 奖励投机为何需要硬门禁 | `python -B -m chapter15.experiments --group 5 --output chapter15/.runs/reward-gates` |

规范报告位于 [reports](reports/)：五组局部 JSON、`post-training-report.json`、人类可读摘要和 SHA-256 清单使用稳定 Schema，不写时间戳、主机路径、密钥或供应商响应。

## 失败应该怎样读

实验失败不是统一的“模型不行”。按以下顺序定位：

1. `missing_facts_confirmed`：先修 RAG 或 Context；
2. `deterministic_boundary_available`：先修权限、幂等、重试或 Harness；
3. `instruction_ambiguity_unresolved`：先修 Prompt、Skill 和任务合同；
4. `model_capacity_gap_verified`：先验证模型路由；
5. `policy_bias_repeats_across_tasks` 且上游反事实均排除：才进入后训练候选。

数据审计中的 `protected_write`、`hidden_answer_access`、`missing_tool_result`、敏感内容、未知来源、重复和跨 split 泄漏是隔离原因，不应通过修改 outcome 或清零脱敏后的载荷标记来“洗白”。审计同时检查原始敏感标记、人工 `family_id` 和规范化文本指纹；该指纹不是语义相似度模型。

DPO 加载器与 SFT 共用窄规则脱敏检测，先保留来源敏感证据，再检查两侧数据资格与上下文。调用方未标记的已知敏感键和演示凭据模式也会被拒绝；这不是通用 PII 检测或人工再审批流程。

实验 15-3 消费审计生成的 5 条 train 样本；污染示范是审计后的明确标签故障注入。15-4 核验 chosen 和人工 rejected 分支的任务、上下文、状态、动作与数据用途；后者不执行工具，手算概率不冒充模型测量。

15-5 的 `variants` 是静态对照：前两种奖励各有 200 次违规。`policy_updates` 才是固定种子的 200 次单状态策略更新，探索期间违规次数分别为 191、175、0；`budget_demo` 在 12 步总预算下只更新 3 次、消耗 9 步。两者不能混为成功率比较，报告的 pass 仅验证静态门禁合同，不是学后独立评测或真实模型发布许可。

## 代码阅读顺序

1. `fixtures/failure-cases.json` 与 `intervention.py`：最小干预路由；
2. `contracts.py`：轨迹、偏好、奖励与报告合同；
3. `dataset.py`、`audit.py`：夹具、脱敏、隔离、切分与 SFT 样本；
4. `policy.py`、`objectives.py`：有限策略、交叉熵和 DPO 手算；
5. `reinforcement.py` 与 `simulator.py`：奖励驱动更新、预算，以及单独的静态对照和门禁；
6. `experiments.py`：五组实验与稳定产物；
7. `tests/`：可以执行的章节论证边界。

## 练习、答案与预览

[参考答案](reference-answers.md) 为 13 道题提供计算结果或设计评价准则。机器可检查版本由 `exercise_solutions.py` 生成：

```powershell
python -B -m chapter15.exercise_solutions `
  --all `
  --output chapter15/.runs/exercise-results.json
```

执行 `python -B -m chapter15.preview` 会在被忽略的 `chapter15/preview-pages/index.html` 生成本地候选预览。预览只读取本章 Markdown 与本地图，表格支持横向滚动，不加载远程脚本或样式，也拒绝写出仓库目录。

真实模型迁移前请阅读 [真实训练迁移指南](real-training-guide.md)；资料核对和固定来源见 [第 15 章来源台账](../book/sources/chapter15-sources.md)。

## 证据边界

规范报告采用 `chapter15.post-training.v2`；[RC1 报告](report-history/v1.0-rc1/post-training-report.md)与 `schemas/post-training-report-v1.schema.json` 保留，不改写旧结果。

- 24 条轨迹和 200 次 episode 都是确定性教学夹具，不代表生产分布；
- 有限状态动作策略不是 Transformer，也没有执行真实模型训练；
- 步骤数不是 Token、时延、GPU 小时或供应商费用；
- 固定哈希证明同一环境内报告可重复，不证明结论可跨模型外推；
- 本地安全门禁只覆盖枚举行为，不是完整安全认证；
- 任何平台映射都不构成 Provider 兼容性或可用性声明。
