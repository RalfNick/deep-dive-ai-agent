# 第 13 章离线评估报告

> 本报告来自确定性教学策略，不是模型或产品排名。

## 被测对象与量尺

- Suite：`chapter13-linkcheck-suite@1.0.0`，SHA-256 `d02b0550c5ea60350a457cbe71c9474d515037a9b9389816da3cd7cb3e95bd0a`；
- Baseline：`scripted-baseline-v1`；Candidate：`scripted-candidate-v1`；
- 环境合同：`chapter13.workspace.v1`，fixture `linkcheck-v1`；
- Grader：`chapter13.graders.v2`；Gate：`chapter13.release-gate.v2`；
- 统计：`combinatorial-without-replacement-v1` / `task-paired-percentile-v1`；
- 责任人：本地候选未指定；发布前必须由章节维护者与评估负责人签字。

## 运行摘要

- Task：12；计分 Trial：120；种子：101, 203, 307, 401, 503；
- Trial 状态：`{"agent_failed": 15, "completed": 105}`；
- 失败索引：42 条；环境错误诊断样本不进入指标。

| 指标 | Baseline | Candidate |
| --- | ---: | ---: |
| pass@1 | 55.00% | 75.00% |
| pass@3 | 95.00% | 100.00% |
| pass^3 | 12.50% | 40.00% |
| 安全违规 | 9 | 0 |
| 环境错误 | 0 | 0 |
| 无效记录 | 0 | 0 |

## 切片

| 切片 | Baseline pass@1 | Candidate pass@1 | 差值 |
| --- | ---: | ---: | ---: |
| basic | 80.00% | 100.00% | +20.00% |
| edge | 60.00% | 80.00% | +20.00% |
| safety | 40.00% | 60.00% | +20.00% |
| recovery | 40.00% | 60.00% | +20.00% |

## 数据集用途视图

| Split | Baseline pass@1 | Candidate pass@1 | 差值 | 发布用途 |
| --- | ---: | ---: | ---: | --- |
| capability | 60.00% | 80.00% | +20.00% | 观察能力趋势 |
| regression | 60.00% | 80.00% | +20.00% | 不得下降的回归门禁 |
| adversarial | 40.00% | 60.00% | +20.00% | 与安全硬门禁联合审阅 |

成对 pass@1 差值为 20.00%，95% Bootstrap 区间为 [20.00%, 20.00%]。

非退化教学对照的差值为 1.67%，95% Bootstrap 区间为 [-5.83%, 9.17%]，结论为 `inconclusive`；该对照不进入发布门禁。

发布门禁：**pass**；原因：`all_hard_and_regression_gates_passed`。

## 代表性失败

- `basic-nested-relative:baseline:3:401`：status=`completed`，failed graders=`outcome, trajectory`，error=`null`。
- `basic-anchor:baseline:0:101`：status=`completed`，failed graders=`outcome, trajectory`，error=`null`。
- `basic-external-url:baseline:1:203`：status=`completed`，failed graders=`outcome, trajectory`，error=`null`。
- `edge-query-fragment:baseline:0:101`：status=`completed`，failed graders=`outcome, trajectory`，error=`null`。
- `edge-query-fragment:baseline:4:503`：status=`completed`，failed graders=`outcome, trajectory`，error=`null`。

完整失败索引和证据引用见 `evaluation-report.json` 的 `failures` 与 `trials`。

## Judge 校准摘要

- 固定样本：12；总体一致率：66.67%；
- Coverage：66.67%；answered-only accuracy：75.00%；Unknown：33.33%；
- 金标边界：编辑教学夹具，未经独立人工复核，不是 live Judge 测量。

## 排除项

- 注入的 `environment_error` 诊断 Trial 只验证状态和 Unknown 评分，不进入 120 条计分 Trial；
- 没有真实 Provider Usage，Token、费用和延迟不参与比较；
- 墙钟时间不进入稳定报告；原因记录在 `provenance.environment.run_window_reason`。

## 证据边界

- This suite tests evaluation-harness behavior, not model capability.
- Twelve teaching tasks are not representative of production traffic.
- Fixed scripted outcomes must not be reported as a provider ranking.
