# 实验验证状态

核对日期：2026-08-20。以下结果来自迁移仓库的本地离线运行；它们验证代码合同和固定夹具，不代表模型能力、线上稳定性或厂商排名。

## 逐章状态

| 章节 | 公共离线入口 | 原工程基线 | 迁移后结果 | 报告重建 | 公共 CI 边界 |
| --- | --- | ---: | ---: | --- | --- |
| 第 1 章 | `python -m unittest discover -s chapter1/tests -v` | 9 | 10 通过 | `python chapter1/generate_report.py` | 不调用远程模型；新增 1 项规范时间戳复现测试 |
| 第 2 章 | 依次运行 README 中 7 个脚本 | 7 个命令 | 7/7 退出码为 0 | `python chapter2/real_sft_evidence.py` | 真实微型 NumPy 梯度实验，不等价于大模型训练；不需要 GPU/API Key |
| 第 3 章 | `python -m unittest discover -s chapter3/tests -v` | 19 | 20 通过 | `python chapter3/run_all_experiments.py` | 确定性 RepairPolicy，不代表真实 LLM；新增 1 项规范时间戳复现测试 |
| 第 4 章 | `python -m unittest discover -s chapter4/tests -v` | 24 | 24 通过 | `python -m chapter4.experiments.boundary_matrix_demo` | 固定边界案例，不是样本成功率或 SDK 排名 |
| 第 5 章 | `python -m unittest discover -s chapter5/tests -v` | 63 | 63 通过 | `python -m chapter5.experiments.run_all --output chapter5/reports/context-experiments.json` | 公共 CI 只运行离线夹具；DeepSeek live probe 与凭据不进入仓库 |
| 第 6 章 | `python -m unittest discover -s chapter6/tests -v` | 146 | 142 通过 | `python -m chapter6.experiments.run_all --output chapter6/reports` | 原基线中的 4 项 PDF 发布测试随本地 PDF 一并排除；live probe 仅保留显式入口 |

第 1、3 章迁移后各多 1 项测试，用于冻结规范报告时间戳。第 6 章减少的 4 项仅验证未迁移的 PDF 发布物、版本台账和二进制哈希；Markdown、图表、实验、来源、Claims/Non-claims 与发布门禁仍在公共测试中。

## 第 2 章七个命令

~~~powershell
python chapter2/sft_mask_demo.py
python chapter2/real_sft_evidence.py
python chapter2/preference_demo.py
python chapter2/sampling_demo.py
python chapter2/reasoning_budget_demo.py
python chapter2/structured_output_demo.py
python chapter2/model_selection_demo.py
~~~

这些命令在核对日期均退出 0。`real_sft_evidence.py` 使用固定 seed 和 NumPy `2.2.6`；跨 Python、NumPy 或 BLAS 环境的浮点末位差异需要重新记录，不能假定跨平台逐字节一致。

## 规范产物 SHA-256

| 产物 | SHA-256 |
| --- | --- |
| `chapter1/reports/experiment-results.json` | `9e076c3dbfd80fa9aaba8d87c2d14804fa3a35ef63c9f87a2624e62469e182f4` |
| `chapter2/results/real_sft_summary.json` | `6652e64d004a8dd96d60fa7562a0a78d45fac86172fcff282f1c50b88e23b06a` |
| `chapter2/results/real_sft_curves.csv` | `fad971bddfc0eca99e2fcaa6a995ecd7572b5abc54838af291202096e64e82d0` |
| `book/images/fig2-7-real-sft-curves.svg` | `f43edcebf010fb3acd631200ba66113b40f2c5ef985876ce95bf940473dc5fa5` |
| `chapter3/reports/experiment-results.json` | `84fe812bee9bb30e4a033ba3cbe5f1021e70119debc3d2ccf58496e72dcabef5` |
| `chapter4/reports/harness-boundary-matrix.json` | `b9f164feb7593debb860fdafc48b3e45b773bd463805c2ced14a056875a136c1` |
| `chapter5/reports/context-experiments.json` | `1f7b18137b1f3a44188da3fcf5c682370cd47288dfd8114292ff593b759a396e` |
| `chapter6/reports/context-continuity.json` | `50cbbc74c8d938d619dab131f8d37bbb8443162c1fea74233c90fd6eb3686e5e` |
| `chapter6/reports/context-continuity.md` | `f05fba8f7a4ef7177ea7fe1b1fa18f8cc7528bd9d806d0feeb1aff86f87ce107` |
| `chapter6/reports/context-continuity-trace.jsonl` | `cbcc12216df02182d9e5b4f64a3a1b29ef9554140877e33cbc986fe69604eb96` |

第 1、3、4、5、6 章的规范离线生成器已连续运行两次；上述产物的第二次哈希与第一次一致。第 5 章 `deepseek-live.example.json` 只是脱敏结构示例，不计入离线规范报告。

## 明确不声称

- `serialized_bytes`、字符数或 JSON 长度不是 Token 数；离线报告不得把它们换算成 Token 节省率。
- 固定夹具只隔离所测边界，不能比较 Claude Code、Codex、DeepSeek 或任何 SDK 的整体能力。
- 测试全绿不代表生产安全、成本、延迟或用户目标已经被完整覆盖。
- 未在公共 CI 中执行真实 provider、浏览器、GPU 或 PDF 二进制发布验收。

来源冻结点：第 1–4 章为 `93931cc43b862e525e5c1c77473a2024af09b162`；第 5–6 章为 `faa56e968affe2469ef828b62bf0947c6e9ebdbb`。
