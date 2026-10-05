# 实验验证状态

## 2026-10-05 全书 `0.18.0` 发布

公开清单收录第 1–18 章和附录 A，正文使用读者路径修订与去话术版本。第 15/16/18 章保留 RC2 规范实验，第 17 章保留 RC3 规范包，附录 A 保留 RC1 规范包。历史日期下的测试数、哈希和“未发布”描述仍是当时记录，不回写成当前结论。

本轮实际验证、环境与限制见[统一发布记录](../book/versions/book-v0.18.0.md)。公共 CI 按章独立运行，并补入第 17/18 章与附录 A；没有把默认整库 pytest 的历史收集问题描述成已经修复，没有调用真实模型、训练大模型或验证生产容器隔离。

## 2026-09-27 第 15 章 v1.0-rc1 本地候选

第 15 章已形成“Agent 的后训练：什么时候 Prompt 已经不够”本地候选：24 条固定轨迹、5 组离线实验、7 幅原创图、13 道练习与答案。候选将独立运行第 15 章锁定依赖和测试；公开 manifest 仍为 `0.14.0`，第 15 章保持 `planned`，正文、图片和报告均不进入网站。实验只验证干预路由、数据审计、有限动作 SFT/DPO 算式、奖励投机与发布门禁；没有训练真实模型，也没有供应商兼容性结论。完整命令、哈希和审稿记录见 `book/versions/chapter15-v1.0-rc1.md`。

## 2026-09-27 第 11–14 章 v1.0 发布

第 11–14 章已经进入公开 manifest、站点 allowlist 与 CI。发布基线分别通过 26、210、38、69 项章节测试；仓库合同、Node 排版合同、发布安全扫描和 MkDocs strict 构建作为共同门禁。四章继续保留候选记录中的 Non-claims：未用固定夹具评价真实模型或产品，第 12 章没有把理论容器合同写成隔离实测，第 13–14 章没有把教学任务、Trace 或成本单位外推到生产分布。

## 2026-09-09 第十章 v1.1

第十章发布 v1.1。42 项章节测试通过：在 v1.0 基础上新增 4 个幂等/准入回归测试方法和 1 个完整 quickstart 命令测试；五组实验与三份规范报告仍可重复生成。发布门禁同时覆盖仓库合同、已发布章节回归、Node 排版合同、MkDocs strict 构建和仓库安全检查。下方记录给出本章精确边界，不把固定夹具结果解释为真实模型或分布式系统评测。

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
| 第 10 章 | `python -m unittest discover -s chapter10/tests -v` | v1.1 发布版 | 42 通过 | `python -m chapter10.experiments --write` | 5 组标准库实验；验证目录/加载、发现边界、有限并发、可恢复持久作业与故障语义；新增完整 quickstart 与晚到重试回归；不含真实模型、外部 SDK、HTTP 服务或分布式 exactly-once |
| 第 11 章 | `python -B -m unittest discover -s chapter11/tests -v` | v1.0-rc2 | 26 通过 | `python -B -m chapter11.experiments --output chapter11/reports` | 固定操作序列与可信教学仓库；验证调查、红灯、补丁版本、验收与证据失效，不代表 Codex/Claude Code 实际能力或沙箱安全 |
| 第 12 章 | `python -B -m pytest chapter12/tests -q` | v1.0-rc2 | 210 通过 | `python -B -m chapter12.experiments --group all --output <new-dir>` | Replay 驱动；真实加载 LangGraph 与 Agents SDK，但未执行真实模型；容器只保留理论合同与参考配置 |
| 第 13 章 | `python -B -m pytest chapter13/tests -q` | v1.0-rc2 | 38 通过 | `python -B -m chapter13.experiments --group all --output <new-dir>` | 12 个固定任务、2 个确定性策略、120 条 Trial；验证评估机制，不代表真实模型或平台排名 |
| 第 14 章 | `python -B -m pytest chapter14/tests -q` | v1.0-rc2 | 69 通过 | `python -B -m chapter14.experiments --group all --output <new-dir>` | 72 条确定性教学 Trace 与虚构成本单位；验证可比性、观测合同和诊断方法，不代表生产流量 |

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

2026-09-09，v1.1，已发布。`python -B -m unittest discover -s chapter10/tests -v`：42 项通过；新增 4 个幂等/准入回归测试方法与 1 个 quickstart 子进程测试。预览依赖可用时同时验证 Markdown 页面；未安装时只跳过该预览测试。

五组实验涵盖工具目录/加载、发现边界、有限并发、持久作业与故障注入；`python -B -m chapter10.experiments --write` 可重复生成。JSON / Markdown / JSONL 的 SHA-256 分别为 `c4d87ae7bd46108ba0ea7e9b6ec4498299eb2cfadd120e0cf9cd6651e3f8732b`、`d7bfe620418d766e1399ab8ead4d9cd03c8787fc1f19036ef90521352966265d`、`f59f1bfce22f759b774570ef54460a194bc0a39cfcf9fa95d976f736fc174ade`。

目录 300/可发现 299/加载 2；全量 93,644 字节，按需载荷 1,412 字节；有限并发峰值 2；八月报表 3 条、6,000 分。测量口径与限制见 `chapter10/README.md`。这些字节数不是 Token 或生产成本。

## 第 11–14 章发布验证

2026-09-10，v1.0-rc1。17 项章节检查，其中一项预览检查依赖可选 Markdown 包；本机已安装并运行。五组实验分别覆盖修复、项目指令清单、过期补丁、验收反例和旧证据失效。规范 JSON 与 Markdown 经两次生成并与仓库文件逐字节比较。

入口：`python -B -m chapter11.quickstart`；完整检查：`python -B -m unittest discover -s chapter11/tests -v`。不需要 API Key；操作来自固定序列，产品遵循、模型质量、沙箱安全字段不伪填得分。

2026-09-10，v1.0-rc2 修订：章节检查增至 26 项，新增工作台 Review 回归 4 项和练习 CLI 检查 5 项；原有文稿检查加强脚注双向与片段校验。结果与 stdout/stderr 分流，保留断言差异，未知测试数不记为零；目标红灯确认后才冻结并修复。练习 6–10 各有独立临时现场，第 9 题支持预先声明缺失链接验收合同。规范报告重新运行并逐字节复现；rc1 的报告、正文和代码历史保留。详见 [rc2 复核](../book/reviews/chapter11-review-rc2.md)。未执行产品端修复。

第 12 章以 v1.0-rc2 为发布基线：210 项测试通过，离线规范报告两次重建一致；真实模型运行未执行，容器隔离未验证。第 13 章以 v1.0-rc2 为发布基线：38 项测试通过，报告 Schema、任务切片、成对区间、Judge 校准与三态门禁均由固定输入验证。第 14 章以 v1.0-rc2 为发布基线：69 项测试通过，Trace 结构、关键路径、采样隐私顺序、反证与消融诊断均由确定性夹具验证。完整环境、哈希和 Non-claims 见各章 [正式版本记录](../book/versions/) 与 rc2 历史记录。

## 统一证据边界

- `serialized_bytes`、字符数或 JSON 长度不是 Token 数；离线报告不得把它们换算成 Token 节省率。
- 固定夹具只隔离所测边界，不能比较 Claude Code、Codex、DeepSeek 或任何 SDK 的整体能力。
- 测试全绿不代表生产安全、成本、延迟或用户目标已经被完整覆盖。
- 未在公共 CI 中执行真实 provider、浏览器、GPU 或 PDF 二进制发布验收。

来源冻结点：第 1–4 章为 `93931cc43b862e525e5c1c77473a2024af09b162`；第 5–6 章为 `faa56e968affe2469ef828b62bf0947c6e9ebdbb`；第 7–14 章为独立书库新增实现，来源与非声明边界分别记录在对应章节资料台账中。第 9、10、11、13、14 章的快变资料分别按各自来源台账记录的核对日期冻结；正式发布不承诺产品文档此后保持不变。
