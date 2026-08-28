# 第 8 章“RAG 与知识库”设计说明

状态：已由作者于 2026-08-28 确认。

## 目标

第 8 章回答一个具体问题：当 Agent 需要依赖持续更新的外部资料时，怎样把“搜索到相似文本”升级成“找到当前、合法、足以支持回答的证据”。

本章采用从失败逐步构建的教学路径。读者先看到模型凭参数知识回答的风险，再依次加入文档身份、结构感知切分、稀疏与语义召回、混合融合、重排、引用、拒答、更新和评估。每增加一种能力，都必须由前一个版本的可观察失败引出。

目标读者已经完成第 1–7 章，但不要求学过信息检索。正文先用可手算例子解释概念，再显示公式和代码；框架 API、向量数据库选型和前沿变体放在主线之后。

## 核心判断

RAG 不是“把文档放进向量数据库”，而是一条证据供应链：

1. 知识源提供可追溯文档；
2. 索引管道把文档转成可检索的派生结构；
3. 查询管道先执行权限、版本和时效边界，再召回与排序；
4. Context Builder 只装配足以回答问题的证据；
5. Answer Policy 要求逐条引用，证据不足时拒答；
6. Eval 分开判断检索、引用和答案，不用一个总分掩盖故障位置。

## 与相邻章节的边界

- 第 5 章负责一次模型调用前的 Context 装配；第 8 章说明哪些外部证据有资格进入 Context。
- 第 6 章负责长任务压缩、Artifact、Checkpoint 与恢复；RAG 索引不是运行恢复状态。
- 第 7 章 Memory 负责历史交互中形成的可复用信息；第 8 章知识库负责由明确来源维护的外部事实。
- 第 9 章再把检索能力包装成工具与 MCP；本章只建立 `retrieve` 合同，不展开通用工具协议。
- 第 12 章再让 Coding Agent 自主决定何时检索；本章主实验采用可预测的两阶段 RAG，Agentic RAG 只做升级地图。
- 第 13–14 章系统讲 Agent Eval、Tracing 和生产诊断；本章只实现定位 RAG 组件故障所需的最小指标。

GraphRAG、多模态 RAG、SQL/结构化检索、训练专用 Retriever 和大规模向量数据库调优只做进阶地图，不在本章实现完整系统。

## 贯穿案例：开源软件产品知识库

贯穿案例是一款虚构的开源团队协作工具“星舟工作台”。知识库不是一份规整 FAQ，而是由多种真实团队常见资料组成：

- 面向所有用户的安装手册和使用指南；
- 按版本维护的 FAQ 与 Release Notes；
- 从 2.x 升级到 3.2 的迁移指南；
- 社区故障记录和已修复问题；
- 仅维护者可见的内部排障 Runbook；
- 已废弃但仍可能残留在索引中的旧文档；
- 一份包含恶意指令的低信任社区文档，用于演示知识污染和 Prompt Injection。

贯穿问题是：

> 我们准备从 2.8 升级到 3.2。团队版还能继续使用旧 SSO 配置吗？现有成员会不会被移除？

正确回答需要同时找到最新版套餐说明、3.2 Release Notes 和迁移指南；旧 FAQ 中的答案已经过期；内部 Runbook 包含普通用户无权看到的绕过步骤；任何单个 Chunk 都不足以完整回答问题。

这组语料必须完全虚构并随代码进入仓库，以便稳定标注版本、权限、相关 Chunk 和参考答案。它不冒充真实产品政策，也不承担医疗、法律或金融领域的高风险事实责任。

## 资料使用分层

### 可控教学语料

`chapter8/fixtures/starboard_docs/` 固定保存 18 份 Markdown 文档；每份文档都配一个同名 `.meta.json`，描述 `document_id`、版本、生效时间、可见范围、来源类型、状态和内容摘要。固定评估集标注问题、相关文档、相关 Chunk、支持的答案要点和应拒答条件。相邻 JSON 让核心实现只用 Python 标准库即可解析，并能在测试中精确冻结缺失字段和非法时间。

### 作者已有资料

写作时参考用户提供的《大模型入门.pdf》《AI学习资料.pdf》，以及原工程 `docs/phase-2/`、`phase-2-rag/` 和 Phase 6 企业知识库实现。旧代码和旧 Benchmark 只作为待审计素材：未经复现的数字不进入本章 Claims，旧文章不直接复制到新正文。

### 论文、教材和官方资料

经典原理优先使用 RAG、DPR、BM25、RRF、ColBERT/两阶段检索等论文，以及《Introduction to Information Retrieval》等教材。快变实现只引用官方资料：LangChain Retrieval、LangGraph Agentic RAG、OpenAI Vector Store/File Search、Anthropic Contextual Retrieval、Ragas 指标文档。所有资料写入 `book/sources/chapter8-sources.md`，记录事实用途、限制、核对日期和出版前是否复核。

## 教学主线：v0–v7

### v0：模型凭参数知识回答

模型可以给出流畅答案，却无法证明自己使用的是 3.2 当前规则。运行结果必须显示答案缺少引用，并混入旧版 SSO 结论。

### v1：把全部资料塞进 Context

整库输入让当前证据存在于窗口中，但旧版、内部资料和低信任指令也同时进入。运行结果显示模型或固定决策策略选择了错误版本或越权内容。这里与第 5 章连接：容量充足不等于证据选择正确。

### v2：文档身份与结构感知切分

先建立 `KnowledgeDocument` 和 `Chunk`。文档保留来源、版本、生效时间、可见范围与内容 Digest；Chunk 保留标题路径、页/段位置和父文档身份。对比固定字符切分、结构感知切分和带文档语境的 Chunk，观察表格、标题和限定条件是否被切断。

### v3：稀疏召回和语义召回

手写 BM25 的最小版本，解释词频、文档频率与长度归一化；使用固定的教学向量或可选真实 Embedding 演示语义召回。正文明确：固定向量只验证召回合同和相似度计算，不代表真实模型质量。

### v4：权限和时效过滤先于混合召回

查询先按主体权限、文档状态、生效时间和版本线过滤，再分别运行 BM25 与语义召回。用 RRF 按名次融合，不直接相加不可比的原始分数。运行结果显示精确术语由 BM25 找回，口语表达由语义通道补回，而旧版和内部文档根本没有进入候选集。

### v5：两阶段召回与重排

第一阶段宽召回保证候选覆盖，第二阶段使用固定教学 Reranker 评估 Query–Chunk 对。可选 Live Probe 接真实 Cross-Encoder。正文解释 Bi-Encoder、Cross-Encoder 和 Late Interaction 的速度/质量位置，不把 Reranker 当成新的事实源。

### v6：Evidence Packet、引用与拒答

把最终 Chunk 组成结构化 `EvidencePacket`，保留引用 ID、来源、版本和支持范围。固定 Answer Policy 只输出证据能支持的声明；每个声明必须绑定引用；复合问题缺少任一关键证据时输出部分回答或拒答，不让模型用常识补齐。

### v7：更新、污染与分层评估

模拟 2.8 文档下线、3.2 文档生效、索引延迟、权限变化和恶意文档写入。主 Store/Source Catalog 是事实源，索引是可重建派生物。评估分别报告 Retrieval、Citation、Answer、Freshness、Isolation 和 Safety，不合成一个“RAG 成功率”。

## 核心数据模型

`KnowledgeDocument` 至少包含：

- `document_id`、`title`、`content`；
- `source_uri`、`source_type`、`content_digest`；
- `product_version`、`valid_from`、`valid_until`、`status`；
- `visibility`、`allowed_roles`；
- `trust_level`、`updated_at`。

`Chunk` 至少包含：

- 稳定 `chunk_id` 与父 `document_id`；
- `heading_path`、`ordinal`、`content`；
- 父文档的权限、版本、时效和 Digest 投影；
- 可选 `context_prefix`，用于解释 Chunk 在整篇文档中的位置。

`RetrievalQuery` 包含问题、调用者角色、目标产品版本、查询时间、Top-K 和允许来源。`RetrievalHit` 分别保留 lexical、semantic、fusion 和 rerank 分项，不把最终分数解释成概率。

`EvidencePacket` 保存有序证据、引用表、缺失证据类型和拒答原因。规范报告不保存 Secret、作者机器路径或未脱敏的内部正文。

## 实现边界与文件职责

`chapter8/knowledge_runtime/` 采用小文件、清晰接口：

- `contracts.py`：文档、Chunk、Query、Hit、Evidence 与评估合同；
- `catalog.py`：源文档身份、当前状态、版本与权限解析；
- `chunking.py`：固定字符和结构感知切分；
- `sparse.py`：可手算 BM25；
- `dense.py`：固定教学向量接口与可替换 Embedding Protocol；
- `fusion.py`：RRF 和候选去重；
- `rerank.py`：确定性教学 Reranker 接口；
- `retrieve.py`：硬过滤、双路召回、融合和重排编排；
- `evidence.py`：引用装配、声明支持与拒答；
- `evaluation.py`：检索、引用、答案、时效、隔离和安全指标；
- `persistence.py`：规范 JSON/JSONL 报告和稳定序列化。

核心包只使用 Python 标准库，保证公共 CI 无 API Key、无模型下载也能完整运行。真实 Embedding、Cross-Encoder、LLM 生成和 Ragas 通过 `chapter8/live/` 的可选适配层接入，不成为规范报告的前置条件。

## 五组实验

### 实验一：无检索、整库 Context 与受控 RAG

固定同一回答策略，比较无知识、全部文档和 Evidence Packet。观察引用完整性、旧版内容使用、内部资料泄漏和拒答行为。

### 实验二：切分策略消融

比较固定字符、结构感知和带语境 Chunk。问题覆盖标题限定、表格行、跨段条件和代码块。报告 Chunk 数、相关 Chunk 是否可独立解释、Context Precision/Recall，不把字符数称为 Token。

### 实验三：BM25、语义、RRF 与 Rerank

在精确版本号、同义表达、复合问题和噪声问题上比较四个阶段。报告 Precision@K、Recall@K、MRR、NDCG@K 和各阶段候选顺序；每个配置有明确样本数，不把单问题结果写成平均成功率。

### 实验四：版本、时效和权限故障注入

分别移除版本过滤、有效期过滤、角色过滤和主 Catalog 回查。观察旧版泄漏、未来文档提前生效、内部资料泄漏和陈旧索引复活。

### 实验五：引用、拒答与知识污染

加入无来源声明、错引、证据不足、冲突证据和恶意社区文档。报告 Citation Precision/Recall、受支持声明比例、正确拒答数、错误拒答数和不可信指令进入 Answer Context 的数量。

所有规范实验固定语料、Query、时钟、角色、教学向量、排序 Tie-break 和序列化格式。JSON、Markdown 和脱敏 JSONL 连续生成必须字节一致。未测真实模型质量、Provider Token、成本与延迟使用 `null`。

## 可选真实实验

可选 Live Probe 允许使用本地 Sentence Transformers 或环境变量提供的 DeepSeek/OpenAI/Anthropic 凭据：

- 真实 Embedding 替换固定教学向量；
- 真实 Cross-Encoder 替换确定性 Reranker；
- LLM 根据 Evidence Packet 生成带引用答案；
- Ragas 评估 Faithfulness、Context Precision 和 Context Recall。

Live Probe 缺少依赖或凭据时必须显式跳过；输出写入被 Git 忽略的目录，不覆盖规范报告。仓库只提交脱敏结构示例和运行说明，不提交 Key、请求收据或模型生成的不可复现基准。

## 图表

计划 8 幅原创 SVG：

1. Context、Memory、RAG、长上下文和 Fine-tuning 的边界；
2. 离线索引与在线问答双通道架构；
3. v0–v7 从流畅猜测到证据回答的演进；
4. 固定字符、结构感知和带语境切分对照；
5. BM25、语义召回、RRF 与重排漏斗；
6. Evidence Packet、声明、引用和拒答关系；
7. 版本、权限、时效和索引派生关系；
8. 分层 Eval 与故障定位矩阵。

每张图使用统一 SVG 设计语言，包含可访问标题和描述；桌面 1200×675 与移动端约 390px 宽度均需渲染检查。正文必须说明读图顺序，图不能只是装饰。

## 正文章节结构

正文目标 2.5 万至 3 万有效中文字符、20–35 个二三级标题。第一次阅读只沿 v0–v7 主线；BM25 公式、Embedding/HNSW、Reranker、框架映射、Agentic/Graph/Multimodal RAG 和生产选型放入进阶层。

正文顺序：

1. 一个“答案很像对的，却引用了旧规则”的失败；
2. 阅读提示、全章短答案和五个中文先行术语；
3. RAG、搜索、Memory、长上下文和 Fine-tuning 边界；
4. v0–v7 贯穿实验；
5. 进阶原理与框架/产品责任映射；
6. 失败模式、安全、更新、成本和生产选择；
7. 本章小结；
8. Claims 与 Non-claims；
9. 14 道分层练习、参考答案和第 9 章衔接。

## 可读性门禁

- 每个抽象名词第一次出现前给出星舟工作台的具体例子；
- 主线每版显示输入、核心调用、关键中间结果和运行输出；
- 公式之前先用三到五条候选手算排名；
- “稀疏/语义”“召回/重排”“来源/引用”“检索正确/答案忠实”等易混概念使用对照表；
- 一个小节最多引入两个新核心概念；
- 完整代码留在 `chapter8/`，正文片段保持一屏可读；
- 每个实验同时写明支持的结论和不支持的结论；
- 第一次阅读可在 v7 后直接进入本章小结，不必先读框架百科。

## 安全与治理

权限、租户和时效过滤必须发生在排名前；不能先从全库召回再依赖模型删除越权内容。文档正文按低信任数据处理，其中的“忽略系统指令”不能改变 Harness Policy。索引必须携带源 Digest 和索引版本，查询时可回查 Catalog，避免已撤回文档重新进入 Context。

知识更新使用新版本与状态变更，不原地覆盖到无法解释过去。删除或撤回文档后，在线门禁立即停止使用；物理索引清理由后台完成。引用只证明答案来自某段文本，不自动证明文本真实、最新或有权威。

## 练习与答案

设计 14 道练习，覆盖：概念边界、Chunk 设计、BM25 手算、RRF 手算、召回消融、版本过滤、权限隔离、引用验证、拒答、Prompt Injection、RAGAS 指标选择、生产索引、Agentic RAG 设计和产品责任映射。

`chapter8/reference-answers.md` 对每题给出预期推理、常见错误和可检查验收；涉及代码修改的题先要求添加失败测试。

## 发布物与仓库同步

实现完成时新增或修改：

- `book/chapter8.md`；
- `book/images/fig8-1-*.svg` 至 `fig8-8-*.svg`；
- `book/sources/chapter8-sources.md`；
- `book/reviews/chapter8-review-codex.md`；
- `chapter8/README.md`、`requirements.txt`、`reference-answers.md`；
- `chapter8/knowledge_runtime/`、`fixtures/`、`experiments/`、`reports/`、`tests/`；
- `README.md`、`book/README.md`、`book/manifest.json`、`docs/EXPERIMENT_STATUS.md`；
- `scripts/build_site.py`、`mkdocs.yml`、仓库合同测试和第 7 章下一章链接。

Manifest 更新为 8 章已发布、10 章规划中，版本更新为 `0.8.0`。不创建英文翻译或繁体中文目录。

## 测试与完成条件

实现遵循 TDD：先让仓库合同接受第 8 章文件，再为每个 Runtime 边界写失败测试，最后写正文和发布接入。至少验证：

- 数据合同、Front Matter、稳定 ID 和非法时间/权限；
- 结构感知切分与来源继承；
- BM25、教学向量、RRF、去重和 Tie-break；
- 排名前权限/版本/时效硬过滤；
- Rerank、Evidence Packet、引用支持和拒答；
- 旧版泄漏、陈旧索引、跨角色泄漏和恶意文档；
- 5 组实验、规范报告复现、Trace 脱敏；
- 正文字数、8 幅图、14 道练习、14 份答案和来源字段；
- 第 1–7 章回归、渲染器、严格 MkDocs 构建和 Git 历史安全扫描。

完成标准是正文、实验、报告、图、练习、答案、来源、Review、导航和状态台账全部一致；规范报告连续生成字节一致；所有公开测试与 GitHub CI 通过；Pages 页面能读取正文、实验和答案；工作树无 Secret、作者绝对路径、缓存、Live 输出和构建物。

## Non-goals

本章不声称固定教学向量等价于真实 Embedding，不声称规则 Reranker 代表 Cross-Encoder 质量，不使用单一小语料比较厂商或框架，不把 Ragas 分数当成人工真值，不把引用等同于事实正确，也不证明教学实现具有生产数据库、分布式索引或法规合规能力。
