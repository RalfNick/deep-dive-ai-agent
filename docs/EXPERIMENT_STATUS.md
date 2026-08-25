# 实验验证状态

核对日期：2026-08-25。以下结果来自独立书稿仓库的本地离线运行；它们验证代码合同和固定夹具，不代表模型能力、线上稳定性或厂商排名。

## 逐章状态

| 章节 | 公共离线入口 | 原工程基线 | 迁移后结果 | 报告重建 | 公共 CI 边界 |
| --- | --- | ---: | ---: | --- | --- |
| 第 1 章 | `python -m unittest discover -s chapter1/tests -v` | 9 | 10 通过 | `python chapter1/generate_report.py` | 不调用远程模型；新增 1 项规范时间戳复现测试 |
| 第 2 章 | 依次运行 README 中 7 个脚本 | 7 个命令 | 7/7 退出码为 0 | `python chapter2/real_sft_evidence.py` | 真实微型 NumPy 梯度实验，不等价于大模型训练；不需要 GPU/API Key |
| 第 3 章 | `python -m unittest discover -s chapter3/tests -v` | 19 | 20 通过 | `python chapter3/run_all_experiments.py` | 确定性 RepairPolicy，不代表真实 LLM；新增 1 项规范时间戳复现测试 |
| 第 4 章 | `python -m unittest discover -s chapter4/tests -v` | 24 | 24 通过 | `python -m chapter4.experiments.boundary_matrix_demo` | 固定边界案例，不是样本成功率或 SDK 排名 |
| 第 5 章 | `python -m unittest discover -s chapter5/tests -v` | 63 | 63 通过 | `python -m chapter5.experiments.run_all --output chapter5/reports/context-experiments.json` | 公共 CI 只运行离线夹具；DeepSeek live probe 与凭据不进入仓库 |
| 第 6 章 | `python -m unittest discover -s chapter6/tests -v` | 146 | 143 通过 | `python -m chapter6.experiments.run_all --output chapter6/reports` | 原基线中的 4 项 PDF 发布测试随本地 PDF 一并排除；新增 1 项跨平台受保护报告路径测试 |
| 第 7 章 | `python -m unittest discover -s chapter7/tests -v` | 新增章节 | 64 通过 | `python -m chapter7.experiments.run_all --output chapter7/reports` | 固定 Candidate、时钟与决策策略；验证 Write、Recall、Correct、Forget、隔离和报告合同，不调用真实模型 |

第 1、3 章迁移后各多 1 项测试，用于冻结规范报告时间戳。第 6 章排除了 4 项只验证未迁移 PDF 发布物、版本台账和二进制哈希的测试，同时增加 1 项跨平台路径保护回归；Markdown、图表、实验、来源、Claims/Non-claims 与发布门禁仍在公共测试中。

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
| `chapter1/reports/experiment-results.json` | `4e1d17e99a22c7bb0f7d67ae94538a8fe6c35e60a7734643f6800175461cd4e5` |
| `chapter2/results/real_sft_summary.json` | `31cc2dd823137d615e83c2e47691ec8c5e736c87d648e9ee7b94d82e889deb5d` |
| `chapter2/results/real_sft_curves.csv` | `016f0af5f8838ee7a35ce9dc76a1fe9da2cba1744fbf5ef5e52f403f50bfb545` |
| `book/images/fig2-7-real-sft-curves.svg` | `0715b12ff1a874c87e9dbe87a0e6bf0e8cc8f591b688e0b75737cad02117a855` |
| `chapter3/reports/experiment-results.json` | `0f7a6307d332b55ce7c54f8cbe41c4f7eca3d7df4b7a595a265c2ae25d958f6e` |
| `chapter4/reports/harness-boundary-matrix.json` | `b44c21ce2d9ff2db5b9fa1c85e2edc0241773d922dd8b78481a20d42441b68bb` |
| `chapter5/reports/context-experiments.json` | `fa41d7e471f01f50e8557ca74df7f6e6d9af62ebd94a81deaf556846963c4c7a` |
| `chapter6/reports/context-continuity.json` | `50cbbc74c8d938d619dab131f8d37bbb8443162c1fea74233c90fd6eb3686e5e` |
| `chapter6/reports/context-continuity.md` | `f05fba8f7a4ef7177ea7fe1b1fa18f8cc7528bd9d806d0feeb1aff86f87ce107` |
| `chapter6/reports/context-continuity-trace.jsonl` | `cbcc12216df02182d9e5b4f64a3a1b29ef9554140877e33cbc986fe69604eb96` |
| `chapter7/reports/memory-engineering.json` | `7a9feb8f9253ee2f1c409c710658daf23b9b0b609d2114e1b38a6e65dacea0a3` |
| `chapter7/reports/memory-engineering.md` | `06eb7ee156b4acd50b48a42564dd99405eaeaa53f984c3e19ed431d8746bd781` |
| `chapter7/reports/memory-engineering-trace.jsonl` | `8d25258e75c8b9670875d6ae5e2466d1c3922ad20cf343031f75b8434e1da0ea` |

第 1–7 章的规范离线生成器已连续运行两次；上述 13 个产物的第二次哈希与第一次一致。所有规范文本报告显式写入 UTF-8/LF；第 1、3、7 章只记录稳定运行合同，不记录操作系统、主机名或 Python 补丁版本。第 2 章的逐字节复现结论仍只限同一已记录数值环境；第 5 章 `deepseek-live.example.json` 只是脱敏结构示例，不计入离线规范报告。

## 明确不声称

- `serialized_bytes`、字符数或 JSON 长度不是 Token 数；离线报告不得把它们换算成 Token 节省率。
- 固定夹具只隔离所测边界，不能比较 Claude Code、Codex、DeepSeek 或任何 SDK 的整体能力。
- 测试全绿不代表生产安全、成本、延迟或用户目标已经被完整覆盖。
- 未在公共 CI 中执行真实 provider、浏览器、GPU 或 PDF 二进制发布验收。

来源冻结点：第 1–4 章为 `93931cc43b862e525e5c1c77473a2024af09b162`；第 5–6 章为 `faa56e968affe2469ef828b62bf0947c6e9ebdbb`。
