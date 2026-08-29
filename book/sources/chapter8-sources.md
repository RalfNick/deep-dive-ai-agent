# 第 8 章资料台账：RAG 与知识工程

核对日期：2026-08-28。RAG 框架接口、托管检索 API、评估库和产品行为变化很快；出版前必须重新打开标记为“是”的页面。本章的固定实验只验证声明的目录治理、切块、检索、证据和评估边界，不用于比较真实模型、Embedding、Reranker 或产品能力。

## 使用原则

- 算法来源优先引用原始论文或权威教材；产品与框架事实只引用当前官方文档；
- “检索到了”“引用正确”“答案有依据”是三个不同判断，正文和报告分别度量；
- 本章确定性语义编码器不是训练得到的 Embedding，不把它的排序结果外推到真实模型；
- 报告里的字符数、字节数都不是 Token；每个固定案例的 sample_count 为 1，不给出统计成功率；
- 文档是数据，不是指令；权限、状态、版本、时效和撤回必须在模型外强制执行；
- 社交媒体文章只用于发现工程问题和改进讲解，倍数、产品效果与内部案例必须回到官方资料或本地实验；
- 作者旧文与扫描资料只帮助教学编排，快变事实仍以一手来源为准。

## 原始研究与算法

### [S01] Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2005.11401
- 事实使用：论文把参数化生成模型与非参数化外部记忆结合，并在知识密集型任务中讨论联合检索与生成；用于校准 RAG 的历史起点。
- 明确不声称：不把论文中的 2020 年模型结果外推为 2026 年产品表现，也不声称所有“先搜索再回答”都复现了论文架构。
- 最后核对：2026-08-28
- 出版前复核：否

### [S02] Dense Passage Retrieval for Open-Domain Question Answering
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2004.04906
- 事实使用：论文以分别编码问题和段落的双编码器进行稠密检索，用于解释文档向量可预计算、查询时做相似性搜索的基本思路。
- 明确不声称：本章 FrozenSemanticEncoder 不是 DPR，也不复现论文数据集、训练过程或结果。
- 最后核对：2026-08-28
- 出版前复核：否

### [S03] Okapi BM25: a non-binary model
- 类型：Stanford《Introduction to Information Retrieval》在线教材
- URL / 本地路径：https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html
- 事实使用：支持 BM25 的词频饱和、文档长度归一化和逆文档频率解释。
- 明确不声称：教材中的公式不自动给出中文分词、参数选择或本章语料上的最佳配置。
- 最后核对：2026-08-28
- 出版前复核：否

### [S04] Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods
- 类型：原始研究论文与作者公开版本
- URL / 本地路径：https://doi.org/10.1145/1571941.1572114；https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf
- 事实使用：支持 RRF 按多个排序中的名次倒数求和进行融合，不要求直接混合异质量纲分数。
- 明确不声称：RRF 并非在所有语料和指标上都最优，本章只演示其可计算、可复核的融合行为。
- 最后核对：2026-08-28
- 出版前复核：否

### [S05] ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2112.01488
- 事实使用：用于说明稠密检索不只有单向量双编码器，Late Interaction 是检索表达与效率之间的另一种设计。
- 明确不声称：本章没有实现 ColBERTv2，也不比较其与任一 Embedding 或向量数据库的效果。
- 最后核对：2026-08-28
- 出版前复核：否

### [S06] Lost in the Middle: How Language Models Use Long Contexts
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2307.03172
- 事实使用：论文发现受测模型对长上下文中相关信息位置敏感，用于解释“上下文能放下”不等于“信息一定被可靠使用”。
- 明确不声称：不把特定模型和任务结果外推到所有长上下文模型，也不声称 RAG 必然优于全量上下文。
- 最后核对：2026-08-28
- 出版前复核：否

### [S07] RAGAS: Automated Evaluation of Retrieval Augmented Generation
- 类型：原始研究论文
- URL / 本地路径：https://arxiv.org/abs/2309.15217
- 事实使用：支持把 RAG 评价拆成上下文相关性、忠实性和答案相关性等维度的基本动机。
- 明确不声称：本章确定性指标不是对 Ragas 全部指标的复现，也不把 LLM-as-judge 输出当作无误差真值。
- 最后核对：2026-08-28
- 出版前复核：否

## 当前官方工程资料

### [S08] Contextual Retrieval
- 类型：Anthropic 官方工程文章
- URL / 本地路径：https://www.anthropic.com/engineering/contextual-retrieval
- 事实使用：官方文章说明 Contextual Embeddings 与 Contextual BM25 在切块前为块补充文档级上下文，并将稀疏与稠密检索结合。
- 明确不声称：本章的确定性上下文前缀不是 Anthropic 生产实现，也不移植文章中的效果数字。
- 最后核对：2026-08-28
- 出版前复核：是

### [S09] LangChain Retrieval
- 类型：LangChain 官方文档
- URL / 本地路径：https://docs.langchain.com/oss/python/deepagents/retrieval
- 事实使用：当前文档把 RAG 组件拆为加载、切分、Embedding、向量存储和 Retriever，并区分 2-Step、Agentic 与 Hybrid RAG。
- 明确不声称：这些类别不是唯一标准；本章无依赖实现不等同于 LangChain API，也不固化当前类名。
- 最后核对：2026-08-28
- 出版前复核：是

### [S10] LangGraph Agentic RAG
- 类型：LangGraph 官方教程
- URL / 本地路径：https://docs.langchain.com/oss/python/langgraph/agentic-rag
- 事实使用：当前教程用图节点和条件边表达 Agent 是否检索、是否重写查询以及如何生成回答。
- 明确不声称：Agentic 不代表检索质量自动提高；本章不把固定工作流包装成自主模型决策。
- 最后核对：2026-08-28
- 出版前复核：是

### [S11] OpenAI Vector Store Search API
- 类型：OpenAI 官方 API 参考
- URL / 本地路径：https://developers.openai.com/api/reference/python/resources/vector_stores/methods/search
- 事实使用：当前搜索接口支持查询、文件属性过滤、结果数量和排序选项，结果包含文件、内容与分数等字段。
- 明确不声称：不推断托管服务内部索引、Embedding、切块或排序算法；参数和响应字段出版前需复核。
- 最后核对：2026-08-28
- 出版前复核：是

### [S12] Ragas Metrics
- 类型：Ragas 官方文档
- URL / 本地路径：https://docs.ragas.io/en/stable/concepts/metrics/
- 事实使用：当前文档按检索、生成和 Agent 等任务组织指标，并说明部分指标可以使用或不使用参考答案。
- 明确不声称：Ragas 指标不是唯一评估体系；本章不声称无模型固定指标等价于当前库实现。
- 最后核对：2026-08-28
- 出版前复核：是

### [S13] Ragas Context Precision
- 类型：Ragas 官方指标文档
- URL / 本地路径：https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
- 事实使用：支持“相关块应尽量排在前面”的上下文精确度直觉，并用于和简单 Precision@k 区分。
- 明确不声称：本章手算 Precision@k 不等于 Ragas 所有 Context Precision 变体。
- 最后核对：2026-08-28
- 出版前复核：是

### [S14] Ragas Context Recall
- 类型：Ragas 官方指标文档
- URL / 本地路径：https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/
- 事实使用：支持检查参考答案中的声明是否能归因于检索上下文的召回直觉。
- 明确不声称：本章标签式 Recall@k 不等于当前 Ragas 基于声明归因的完整计算。
- 最后核对：2026-08-28
- 出版前复核：是

## 本书实现与作者资料

### [S15] Chapter 8 deterministic RAG lab
- 类型：本地一手实现、固定夹具、报告与脱敏 Trace
- URL / 本地路径：chapter8/knowledge_runtime/；chapter8/fixtures/；chapter8/reports/rag-evidence.json；chapter8/reports/rag-trace.jsonl
- 事实使用：支持 18 篇虚构文档、20 个问题中的目录硬过滤、三种切块、BM25、固定语义编码、RRF、确定性重排、证据包、引用、拒答和分项指标。
- 明确不声称：不证明真实模型、Embedding、Reranker、向量库或产品质量；不测供应商 Token、费用、延迟和生产成功率。
- 最后核对：2026-08-28
- 出版前复核：是

### [S16] 作者 Phase 2 RAG 文章与扫描资料阅读笔记
- 类型：本地作者资料二次整理
- URL / 本地路径：docs/author-sources/phase-2/chapter8-rag-reading-notes.md
- 事实使用：支持本章从具体问题出发、按离线与在线拆解、再用分项评估回查管道的中文教学编排。
- 明确不声称：不沿用旧文里的工具推荐、经验参数、历史分数或未经当前复核的产品事实。
- 最后核对：2026-08-28
- 出版前复核：否

### [S17] 《深入理解 AI Agent：设计原理与工程实践》开源仓库
- 类型：第三方开源书与配套实验，编排参考
- URL / 本地路径：https://github.com/bojieli/ai-agent-book
- 事实使用：参考“正文、插图、代码、练习”协同组织和概念—机制—实验—边界的章节密度。
- 明确不声称：不复制其文字、图片、代码或实验结果；本章技术事实仍回到原始论文、官方文档和本地报告。
- 最后核对：2026-08-28
- 出版前复核：是

## 补充工程资料与编辑来源

### [S18] Sentence Transformers Embedding Quantization
- 类型：Sentence Transformers 官方文档
- URL / 本地路径：https://www.sbert.net/examples/sentence_transformer/applications/embedding-quantization/README.html
- 事实使用：支持 Embedding Quantization 与模型权重量化的边界；说明 float32 Embedding 可按阈值转成打包二值表示，使用 Hamming Distance 召回，并可对扩大后的候选集做重评分。
- 明确不声称：文档中的 32 倍只作为 32 bit/维到 1 bit/维的原始表示比例；不外推为完整索引、端到端服务、任意模型召回或延迟的固定收益。
- 最后核对：2026-08-28
- 出版前复核：是

### [S19] Milvus Binary Vector 与索引说明
- 类型：Milvus 官方文档
- URL / 本地路径：https://milvus.io/docs/binary-vector.md；https://milvus.io/docs/index.md?tab=binary
- 事实使用：支持 Binary Vector 的 bit/byte 表示、维度约束、Hamming/Jaccard 距离，以及浮点、二值和稀疏向量使用不同索引与距离家族。
- 明确不声称：不推断托管版本内部实现，不把支持某种字段或索引类型写成对本章语料的质量保证，也不固化所有版本的索引清单。
- 最后核对：2026-08-28
- 出版前复核：是

### [S20] Akshay Pachaar：检索前的结构化知识单元
- 类型：第三方 X 长文，编辑与问题发现来源
- URL / 本地路径：https://x.com/akshay_pachaar/status/2052743644411765230
- 事实使用：用于补强“检索失败可能起源于索引之前”的讲解，并引出 Source Chunk、派生问答/事实卡、去重、版本归并和治理字段之间的边界。
- 明确不声称：不采用文章中的专有命名作为行业标准，不复刻厂商内部语料、效果倍数或商业产品结论；派生知识单元不能替代可审计原文。
- 最后核对：2026-08-28
- 出版前复核：是

### [S21] Avi Chawla：Binary Quantization RAG 流程
- 类型：第三方 X 长文，编辑与问题发现来源
- URL / 本地路径：https://x.com/_avichawla/status/2040326889928356122
- 事实使用：用于引出“文档 Embedding 与 Query Embedding 采用一致二值转换，再进入二值检索”的教学流程，以及表示压缩与完整 RAG 指标必须分开报告的问题。
- 明确不声称：不复用文章的吞吐、延迟、语料规模或产品效果数字；技术边界以 S18、S19 为准，真实收益必须在本业务语料上消融评估。
- 最后核对：2026-08-28
- 出版前复核：是

## 出版前复核清单

1. 重新打开 S08—S14、S18—S21，核对页面标题、API 字段、类别与版本状态；
2. 检查正文没有把 FrozenSemanticEncoder 写成真实 Embedding，也没有把确定性 rerank 写成 Cross-Encoder；
3. 检查所有图中实验数字都能回到 rag-evidence.json，null 没被改写成 0；
4. 检查版本、状态、时效、权限和撤回过滤都发生在评分前，返回前还有 Catalog 重查；
5. 检查“命中、引用、支持、拒答”没有合并成一个成功率；
6. 检查没有 Secret、作者机器绝对路径、产品排名、单案例成功率或 byte-as-Token 表述；
7. 重新运行 Chapter 8 全部测试并连续生成报告两次，确认字节一致；
8. 核对 Agentic RAG 只是编排选择，不被写成质量保证或最新必选架构。
9. 核对派生知识单元仍能回到 Source Chunk；二值量化的 32 倍没有被写成完整索引、端到端延迟或答案质量承诺。
