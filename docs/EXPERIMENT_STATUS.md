# 实验验证状态

## 2026-09-08 第十章 v1.0

第十章由 v1.0-rc1 候选发布为 v1.0。37 项章节检查通过，其中 36 项验证标准库运行与答案合同，1 项验证可选 HTML 预览；五组实验与三份规范报告可重复生成。发布门禁同时覆盖仓库合同、已发布章节回归、Node 排版合同、MkDocs strict 构建和仓库安全检查。下方记录给出本章精确边界，不把固定夹具结果解释为真实模型或分布式系统评测。

## 2026-09-07 第八章 v1.4

第八章 71 项测试通过，比 rc1 增加 9 项：片段归属 2 项、标注边界 3 项、最终回查 2 项、请求 CLI 1 项、历史图兼容门禁 1 项。根级 43 项测试通过。真实请求可运行 `python -m chapter8.experiments.inspect_request`；不需要 API Key。该结果随 v1.4 发布，未执行真实模型质量评估。

报告 schema_version=2：单查询字段从 mrr 更名 reciprocal_rank；固定 20 个案例的实际状态不变，仍为 10 个符合性案例、3 个故意失败探针。新标注改变了证据支持的内部传递，不能因状态未变而跳过反例测试。下方旧日期的哈希与测试数属于历史记录，不代表当前产物。

## 2026-09-07 editorial-v1 发布回归

本轮读者路径修订随主分支发布。发布前第 1、3、4、5、6、7、8、9 章分别通过 10、20、24、63、143、65、71、47 项测试，共 443 项。新增 BM25/RRF 手算核对入口；第九章正文与 FAQ 分离，字数门槛对齐写作指南，其余门禁保留。未运行付费 API，也未重新执行第二章训练脚本。

下面保留此前的逐章运行记录与产物摘要，不把历史报告哈希冒充本轮重建结果。

核对日期：2026-09-01。以下结果来自独立书稿仓库的本地离线运行；它们验证代码合同和固定夹具，不代表模型能力、线上稳定性或厂商排名。

## 逐章状态

| 章节 | 公共离线入口 | 原工程基线 | 迁移后结果 | 报告重建 | 公共 CI 边界 |
| --- | --- | ---: | ---: | --- | --- |
| 第 1 章 | `python -m unittest discover -s chapter1/tests -v` | 9 | 10 通过 | `python chapter1/generate_report.py` | 不调用远程模型；新增 1 项规范时间戳复现测试 |
| 第 2 章 | 依次运行 README 中 7 个脚本 | 7 个命令 | 7/7 退出码为 0 | `python chapter2/real_sft_evidence.py` | 真实微型 NumPy 梯度实验，不等价于大模型训练；不需要 GPU/API Key |
| 第 3 章 | `python -m unittest discover -s chapter3/tests -v` | 19 | 20 通过 | `python chapter3/run_all_experiments.py` | 确定性 RepairPolicy，不代表真实 LLM；新增 1 项规范时间戳复现测试 |
| 第 4 章 | `python -m unittest discover -s chapter4/tests -v` | 24 | 24 通过 | `python -m chapter4.experiments.boundary_matrix_demo` | 固定边界案例，不是样本成功率或 SDK 排名 |
| 第 5 章 | `python -m unittest discover -s chapter5/tests -v` | 63 | 63 通过 | `python -m chapter5.experiments.run_all --output chapter5/reports/context-experiments.json` | 公共 CI 只运行离线夹具；DeepSeek live probe 与凭据不进入仓库 |
| 第 6 章 | `python -m unittest discover -s chapter6/tests -v` | 146 | 143 通过 | `python -m chapter6.experiments.run_all --output chapter6/reports` | 原基线中的 4 项 PDF 发布测试随本地 PDF 一并排除；新增 1 项跨平台受保护报告路径测试 |
| 第 7 章 | `python -m unittest discover -s chapter7/tests -v` | 新增章节 | 65 通过 | `python -m chapter7.experiments.run_all --output chapter7/reports` | 固定 Candidate、时钟与决策策略；验证 Write、Recall、Correct、Forget、隔离和报告合同，不调用真实模型 |
| 第 8 章 | `python -m unittest discover -s chapter8/tests -v` | v1.4 复审优化 | 71 通过 | `python -m chapter8.experiments.run_all --output chapter8/reports` | 18 篇虚构文档、20 个固定问题和确定性检索策略；验证治理、召回、证据、拒答与索引回查；状态结果区分符合性案例与失败探针，不比较真实模型或供应商 |
| 第 9 章 | `python -m unittest discover -s chapter9/tests -v` | v1.0.3 发布版 | 47 通过 | `python -m chapter9.experiments.run_all --output chapter9/reports` | 5 组 21 个规范 Case；验证 Schema、策略、执行、回执、Loop 与 MCP SDK 合同；锁定 `mcp==2.1.1`，进程内 MCP 测试不代表模型质量或远程生产部署 |
| 第 10 章 | `python -m unittest discover -s chapter10/tests -v` | v1.0 发布版 | 37 通过 | `python -m chapter10.experiments --write` | 5 组标准库实验；验证目录/加载、发现边界、有限并发、持久作业与故障语义；不含真实模型、外部 SDK、HTTP 服务或分布式 exactly-once |

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
| `chapter8/reports/rag-evidence.json` | `fa711b9f6203d97602612c8a017b82fc6b275e5cf02083f4981837d2236317eb` |
| `chapter8/reports/rag-evidence.md` | `2d53ae220a48466701d9dfa2b507e3d6339db6aaceb8cdc588ce1927c099259a` |
| `chapter8/reports/rag-trace.jsonl` | `a6c6ba9f668173a1c3a9dbfc4246a2402aca127d261c6b2d1c80eb9b38f18c9c` |
| `chapter9/reports/tool-mcp-evidence.json` | `554d3e7e8014f050ca00de3cc4121b0c48b5390c0d4a8a7063dd57dc49ae1951` |
| `chapter9/reports/tool-mcp-evidence.md` | `10001477ec6f5a0340a69b63d560da1c05075b9bf5446ebd4ea4cf928229beca` |
| `chapter9/reports/tool-mcp-trace.jsonl` | `b0c85fc0167ed69f7821e350fa798dd15a22055081a618edcff60a671758e349` |
| `chapter10/reports/tool-jobs-evidence.json` | `c4d87ae7bd46108ba0ea7e9b6ec4498299eb2cfadd120e0cf9cd6651e3f8732b` |
| `chapter10/reports/tool-jobs-evidence.md` | `d7bfe620418d766e1399ab8ead4d9cd03c8787fc1f19036ef90521352966265d` |
| `chapter10/reports/job-events.jsonl` | `f59f1bfce22f759b774570ef54460a194bc0a39cfcf9fa95d976f736fc174ade` |

第 1–10 章的规范离线生成器已连续运行两次；上述 22 个产物的第二次哈希与第一次一致。所有规范文本报告显式写入 UTF-8/LF；第 1、3、7、8、9、10 章只记录稳定运行合同，不记录操作系统、主机名或 Python 补丁版本。第 2 章的逐字节复现结论仍只限同一已记录数值环境；第 5 章 `deepseek-live.example.json` 只是脱敏结构示例，不计入离线规范报告。

## 第 10 章发布验证

2026-09-08，v1.0，已发布。`python -B -m unittest discover -s chapter10/tests -v`：37 项通过，其中 36 项标准库运行/答案测试、1 项可选 Markdown 预览测试。未安装预览依赖时只跳过该预览测试。

五组实验涵盖工具目录/加载、发现边界、有限并发、持久作业与故障注入；`python -B -m chapter10.experiments --write` 可重复生成。JSON / Markdown / JSONL 的 SHA-256 分别为 `c4d87ae7bd46108ba0ea7e9b6ec4498299eb2cfadd120e0cf9cd6651e3f8732b`、`d7bfe620418d766e1399ab8ead4d9cd03c8787fc1f19036ef90521352966265d`、`f59f1bfce22f759b774570ef54460a194bc0a39cfcf9fa95d976f736fc174ade`。

目录 300/可发现 299/加载 2；全量 93,644 字节，按需载荷 1,412 字节；有限并发峰值 2；八月报表 3 条、6,000 分。测量口径与限制见 `chapter10/README.md`。这些字节数不是 Token 或生产成本。

## 明确不声称

- `serialized_bytes`、字符数或 JSON 长度不是 Token 数；离线报告不得把它们换算成 Token 节省率。
- 固定夹具只隔离所测边界，不能比较 Claude Code、Codex、DeepSeek 或任何 SDK 的整体能力。
- 测试全绿不代表生产安全、成本、延迟或用户目标已经被完整覆盖。
- 未在公共 CI 中执行真实 provider、浏览器、GPU 或 PDF 二进制发布验收。

来源冻结点：第 1–4 章为 `93931cc43b862e525e5c1c77473a2024af09b162`；第 5–6 章为 `faa56e968affe2469ef828b62bf0947c6e9ebdbb`；第 7–10 章为独立书库新增实现，来源与非声明边界分别记录在对应章节资料台账中；第 9 章来源于 2026-09-01 复核，第 10 章来源于 2026-09-07 复核。
