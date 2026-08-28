# 第 8 章 Review：RAG 与知识库

核对日期：2026-08-28
初审基线：`3e3da5f`（`docs: write chapter 8 rag and knowledge base`）
复审基线：`19569c5`（`build: publish chapter 8 in the book site`）
审阅范围：`book/chapter8.md`、`chapter8/` 实验、8 幅插图、练习与答案、资料台账和规范报告。

## 结论

通过，综合评价 **9.3/10**。本章已经达到“可以独立阅读、可以复现实验、可以核对证据”的出版状态。

它最重要的优点不是列出了多少 RAG 术语，而是让同一个复合问题沿 v0—v7 逐步暴露失败：从无证据回答、全量塞入、无身份切块，演进到权限与时效前置过滤、混合召回、重排、Evidence Packet、引用、拒答和索引回查。读者能够看见每一层解决什么问题，也能看见它没有解决什么问题。

复审发现的 P1 已全部修复：原报告有 5 个 `expected_status` 与 `answer_status` 不一致，其中 2 个是无答案夹具合同不完整导致的错误回答，另外 3 个是正文承认、报告却未显式分类的假阴性。v1.1 修复前者，并把后者标为 `failure_probe / false_abstain`；所有符合性案例现在都匹配预期，意外状态偏差和错误放行均为 0。检索指标也统一为“唯一文档 + 固定 K 分母”。旧版不改写，由 `book-chapter8-v1.0` 保存。

## 发现与处理

| 优先级 | 视角 | 发现 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| P1 | 工程/专家 | 11 个同时含预期与实际状态的案例中有 5 个不一致，报告却没有通过/失败语义；正文还把部分相反结果写成“证明” | `chapter8/reports/rag-evidence.json`；`chapter8/experiments/run_all.py` | fixed：新增逐案例 `outcome`、`expectation_mode`、`classification` 与 `outcome_summary`；10 个符合性案例全部通过，3 个失败探针明确暴露假阴性 |
| P1 | 工程 | `retrieval-noise` 与 `evidence-correct-abstain` 没有 required fact，任意无关 Citation 都会触发 `answer`；`evidence-missing-members` 只声明缺失事实，因此无法进入 `partial` | `chapter8/fixtures/questions.json`；`evidence.py`；原报告 | fixed：为两个无答案问题声明语料不存在的待验证 fact；Partial 案例同时声明 SSO 与成员事实；新增回归测试 |
| P2 | 专家/读者 | 指标以唯一文档计算，但 Precision@K 曾除以实际返回数；正文公式却以 K 为分母，图 8-8 因而显示 1.00 | `evaluation.py`；`run_all.py`；`book/chapter8.md`；图 8-8 | fixed：Precision@K 固定除以 K，空缺位置视为不相关；报告加入 `metric_contract`，正文解释 Chunk 数与文档数差异，图中值改为 0.33 |
| P2 | 来源/排版 | LangChain Retrieval 旧 URL 已跳转；BM25 参数仍用普通圆括号而非行内数学 | [S09]；`book/chapter8.md` | fixed：更新到当前官方 canonical URL，并统一 `\(...\)` 数学排版 |
| P2 | 读者 | 少量行内代码带有字面反斜杠，且候选预算段有一处“增大”错字，都会影响精读体验 | `book/chapter8.md`；发布合同测试 | fixed：清理 Markdown 转义和错字，并重新运行排版合同 |
| P2 | 读者/工程 | 实现阅读顺序只写 `catalog.py` 等短文件名，脱离当前目录后定位不够清楚 | `book/chapter8.md`“实验复现” | fixed：改为 `chapter8/knowledge_runtime/...` 和 `chapter8/experiments/run_all.py` |
| P2 | 来源 | RAG 原始论文、本地确定性实验、作者资料和 RAGAS 原始论文虽已入台账，但正文中的用途落点不够直接 | `book/chapter8.md`；`book/sources/chapter8-sources.md` | fixed：补入 [S01]、[S07]、[S15]、[S16]，同时保留“不复刻论文结果、不沿用旧产品事实”的限制 |
| P3 | 读者 | 正文有 42 个二、三级标题，已到合同上限，第一次阅读可能感觉信息密度高 | `book/chapter8.md`；`chapter8/publication_checks.py` | accepted：保留“第一次只沿 v0—v7”阅读提示；进阶层可跳读，不再增加平级标题 |
| P3 | 专家 | `FrozenSemanticEncoder` 和教学 Reranker 不能代表真实 Embedding、Cross-Encoder 或供应商能力 | `chapter8/knowledge_runtime/dense.py`；`rerank.py`；正文 Non-claims | accepted：这是确定性边界实验；正文、报告和台账均禁止外推为模型质量或产品排名 |
| P3 | 来源 | [S17] 只作为开源书的组织方式参考，没有对应技术事实声明 | `book/sources/chapter8-sources.md` | accepted：保留为编辑来源，不为了“用满引用”而制造正文技术引用 |

## 读者视角

### 做得好的地方

1. 开头不是从向量数据库定义起步，而是用“3.2 版、旧 SAML、成员上限”复合问题建立阅读动机。即使读者没做过 RAG，也能判断答案缺了哪条证据。
2. v0—v7 每次只增加一组能力，失败与修复因果关系清楚。特别是 v4 把“合法性”放在“相关性”之前，v6 把“检索结果”与“可回答证据”分开，降低了概念混淆。
3. 8 幅图覆盖概念边界、知识生命周期、Chunk 身份、治理检索、权限执行、证据合同、索引更新和分层评估；它们不是装饰图，均对应正文中的一个判断。
4. 正文给出运行结果、报告路径和实现阅读顺序，读者可以从解释进入代码，而不必猜示例是否真的执行过。
5. 14 道练习由概念辨析逐步进入策略设计和故障注入，答案不是关键词列表，适合作为自学闭环。

### 仍需提醒读者的地方

BM25、向量、RRF、重排和 Ragas 集中在进阶层，第一次不应逐公式啃完。正文已有两层阅读提示，建议正式排版时继续通过侧栏或背景色强化“主线/进阶”的视觉差异。

## AI 专家视角

本章的关键边界基本正确：

- RAG、Context、Memory、Tool 与模型参数没有混为一谈；
- Catalog 是当前事实目录，Index 是可过期的派生结构；
- 权限、状态、版本和时效是硬约束，发生在评分之前，且返回前还有 Catalog 重查；
- Sparse、Dense、Fusion、Rerank 分工明确，原始分数没有被直接当作真实性概率；
- Citation 是声明到稳定来源片段的定位，不是句尾装饰；
- Answer、Partial、Abstain 由证据充分性决定，而不是由模型语气决定；
- Retrieval、Citation、Answer、Freshness、Isolation 和 Safety 没有压成一个总分；
- Agentic RAG 被描述为编排选择，没有被写成质量保证或默认最先进方案。

专家层面最值得保留的是“先治理、再召回、后重排、再成证”的顺序。它避免了两个常见错误：先把无权内容算出相似度再隐藏，以及命中一个相关 Chunk 就直接宣布复合问题可回答。

## 工程证据视角

实验不是伪代码展示，而是一套可重复的边界符合性实验：

- 18 篇虚构知识文档和 20 个类型化问题；
- 5 组实验覆盖检索、治理、复合证据、拒答/注入和索引新鲜度；
- Document、Chunk、Query、Hit、Citation、Evidence 均有不可变合同和稳定 ID；
- Trace 只记录 ID、摘要和因果关系，不写文档正文；
- 报告使用固定时钟、稳定排序和规范序列化；
- Live Probe 与公共规范报告隔离，dry-run 不需要 API Key；
- `python -m unittest discover -s chapter8/tests -v`：60 项通过；
- `python scripts/check_repository.py --root . --git-history`：退出码 0；
- 发布合同：有效中文 25,645 字，二/三级标题 42 个，插图 8 幅，练习 14 道，答案 14 道，来源 17 条。
- 状态合同：13 个可比较案例中，10 个符合性案例匹配预期，3 个失败探针均暴露假阴性，意外状态偏差 0，错误放行 0；这些计数不是统计准确率。

规范报告 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `chapter8/reports/rag-evidence.json` | `FA711B9F6203D97602612C8A017B82FC6B275E5CF02083F4981837D2236317EB` |
| `chapter8/reports/rag-evidence.md` | `2D53AE220A48466701D9DFA2B507E3D6339DB6AACEB8CDC588CE1927C099259A` |
| `chapter8/reports/rag-trace.jsonl` | `A6C6BA9F668173A1C3A9DBFC4246A2402ACA127D261C6B2D1C80EB9B38F18C9C` |

这些证据支持 Harness 边界、治理顺序、拒答行为、Catalog 回查和报告复现，不支持真实模型效果、厂商排名、生产吞吐或成本结论。

## 资料与时效视角

资料结构合理：算法概念优先使用 RAG、DPR、RRF、ColBERTv2、Lost in the Middle 和 RAGAS 的原始研究或权威教材；产品与框架行为使用 Anthropic、LangChain/LangGraph、OpenAI 和 Ragas 当前官方资料；本地实现与作者资料单列，不拿旧文章替代当前产品事实。

每条资料都有“事实使用”“明确不声称”“最后核对”和“出版前复核”。这比只列参考链接更有价值，因为它让读者和作者都知道来源能支持到哪里。S08—S14 属于快变资料，出版或大版本发布前仍需重新打开核对；本次核对日期不应被理解为长期有效保证。

## 最终评分

| 维度 | 分数 | 说明 |
| --- | ---: | --- |
| 通俗性与阅读路径 | 9.0 | 具体问题驱动，主线清楚；进阶层仍有一定密度 |
| 技术准确性与边界 | 9.5 | 治理、检索、证据、评估边界完整；状态与指标口径已显式化，Non-claims 充分 |
| 实验与可复现性 | 9.6 | 真实代码、失败探针、状态分类、稳定报告和脱敏 Trace 形成闭环 |
| 来源质量与时效 | 9.0 | 一手来源为主，用途和限制明确；快变页面需出版前复核 |
| 练习与教学闭环 | 9.0 | 分层练习覆盖理解、实现、诊断和设计 |

综合评价：**9.3/10，建议发布 v1.1。**

发布时应继续保留两条醒目边界：第一，固定实验比较的是 Harness 与知识治理边界，不是模型或供应商能力；第二，任何真实业务上线仍需用本组织语料、权限模型、查询分布和风险等级重新评估。
