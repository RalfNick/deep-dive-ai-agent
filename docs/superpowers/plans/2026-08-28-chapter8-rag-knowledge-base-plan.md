# 第 8 章 RAG 与知识库实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 发布第 8 章“RAG 与知识库”，交付从文档治理到混合召回、重排、引用、拒答和分层评估的可运行教学系统。

**Architecture:** 使用 18 份“星舟工作台”虚构文档建立 Source Catalog；索引层从文档派生结构 Chunk、BM25 和固定教学向量；查询层在排名前执行版本、时效与角色过滤，再做 RRF、确定性重排和 Evidence Packet。规范实验完全离线、固定时钟并字节可复现，真实 Embedding、Reranker、LLM 与 Ragas 只通过可选 Live Probe 接入。

**Tech Stack:** Python 3.11+ 标准库、`unittest`、Markdown、SVG、MkDocs Material；可选 Live Probe 使用 Sentence Transformers、DeepSeek/OpenAI/Anthropic API 和 Ragas，但不进入公共 CI。

**Spec:** `docs/superpowers/specs/2026-08-28-chapter8-rag-knowledge-base-design.md`

## Global Constraints

- `book/` 是简体中文唯一权威正文；不创建英文译文或繁体中文目录。
- 核心 `chapter8/knowledge_runtime/` 只使用 Python 标准库，公共测试不读取 API Key、不下载模型。
- 规范语料固定为 18 份 Markdown，每份必须有同名 `.meta.json`。
- 权限、文档状态、目标版本和生效时间过滤必须发生在 BM25、语义排序和重排之前。
- 固定教学向量与规则 Reranker 只证明运行合同，不声称代表真实模型质量。
- 规范报告使用固定 Query、角色、时间、向量、Tie-break 和 UTF-8/LF 序列化；连续生成必须字节一致。
- 未测真实模型质量、Provider Token、成本与延迟使用 `null`，不得把字节或字符换算成 Token。
- 实验必须逐案例报告，不合成一个“RAG 成功率”，不做厂商或框架排名。
- Git 只精确暂存任务涉及路径；不提交 Secret、`.env`、缓存、Live 输出、PDF/HTML 构建物或作者绝对路径。

---

## 文件结构

- `chapter8/knowledge_runtime/contracts.py`：稳定数据合同、枚举、时间和 Digest。
- `chapter8/knowledge_runtime/catalog.py`：加载 18 组 `.md`/`.meta.json`，解析版本、权限、时效和主源状态。
- `chapter8/knowledge_runtime/chunking.py`：固定字符、结构感知和带语境 Chunk。
- `chapter8/knowledge_runtime/sparse.py`：BM25 索引与可分解分数。
- `chapter8/knowledge_runtime/dense.py`：Embedding Protocol、固定教学向量与余弦排序。
- `chapter8/knowledge_runtime/fusion.py`：RRF、去重和稳定 Tie-break。
- `chapter8/knowledge_runtime/rerank.py`：确定性教学 Reranker。
- `chapter8/knowledge_runtime/retrieve.py`：硬过滤、双路召回、融合、主 Catalog 回查与重排。
- `chapter8/knowledge_runtime/evidence.py`：Evidence Packet、声明引用和拒答。
- `chapter8/knowledge_runtime/evaluation.py`：Retrieval、Citation、Answer、Freshness、Isolation、Safety 指标。
- `chapter8/knowledge_runtime/persistence.py`：规范 JSON、Markdown、JSONL 序列化。
- `chapter8/fixtures/starboard_docs/`：18 份文档和 18 份元数据。
- `chapter8/fixtures/questions.json`：固定问题、相关证据、支持声明和拒答真值。
- `chapter8/experiments/run_all.py`：5 组离线实验生成器。
- `chapter8/reports/`：规范报告。
- `chapter8/live/`：可选真实组件适配和脱敏示例。
- `chapter8/tests/`：单元、消融、报告、图和发布门禁。

---

### Task 1: 冻结文档、Chunk 与 Query 合同

**Files:**
- Create: `chapter8/__init__.py`
- Create: `chapter8/knowledge_runtime/__init__.py`
- Create: `chapter8/knowledge_runtime/contracts.py`
- Create: `chapter8/tests/__init__.py`
- Create: `chapter8/tests/test_contracts.py`

**Interfaces:**
- Produces: `KnowledgeDocument`, `Chunk`, `RetrievalQuery`, `QuestionCase`, `RankedChunk`, `ScoreBreakdown`, `RetrievalHit`, `Citation`, `EvidencePacket`, `AnswerDecision`。
- Produces: `parse_utc_seconds(value: str, reason: str) -> datetime`、`stable_digest(payload: Mapping[str, object]) -> str`。
- Produces: `KnowledgeDocument.valid_at(now: str) -> bool`、`supports_version(target_version: str) -> bool`、`visible_to(role: str) -> bool`，以及 `Chunk.from_document(...) -> Chunk`。

- [ ] **Step 1: 写失败测试，冻结不可变合同和非法输入**

```python
class ContractTests(unittest.TestCase):
    def test_document_rejects_blank_id_invalid_time_and_empty_roles(self):
        with self.assertRaisesRegex(ValueError, "blank_document_id"):
            valid_document(document_id="")
        with self.assertRaisesRegex(ValueError, "invalid_valid_from"):
            valid_document(valid_from="tomorrow")
        with self.assertRaisesRegex(ValueError, "empty_allowed_roles"):
            valid_document(allowed_roles=())

    def test_chunk_id_is_stable_and_keeps_parent_digest(self):
        document = valid_document()
        chunk = Chunk.from_document(document, ordinal=0, heading_path=("SSO",), content="SSO 规则")
        self.assertEqual(chunk.chunk_id, Chunk.from_document(document, ordinal=0, heading_path=("SSO",), content="SSO 规则").chunk_id)
        self.assertEqual(document.content_digest, chunk.document_digest)
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_contracts -v`
Expected: FAIL，原因是 `chapter8.knowledge_runtime.contracts` 尚不存在。

- [ ] **Step 3: 实现最小不可变数据合同**

```python
@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    role: str
    target_version: str
    now: str
    top_k: int = 3
    candidate_k: int = 8

@dataclass(frozen=True)
class ScoreBreakdown:
    lexical: float | None = None
    semantic: float | None = None
    fusion: float | None = None
    rerank: float | None = None
```

枚举固定为 `DocumentStatus(active, retired, withdrawn)`、`Visibility(public, internal)`、`TrustLevel(authoritative, curated, community)`、`AnswerStatus(answer, partial, abstain)`。`QuestionCase` 固定保存 `case_id`、`query`、`relevant_document_ids`、`relevant_chunk_ids`、`required_fact_ids`、`expected_claims` 和 `expected_status`。所有 dataclass 使用 `frozen=True`，时间只接受 UTC 秒级 ISO 8601，Digest 使用键排序规范 JSON。

- [ ] **Step 4: 运行合同测试确认 GREEN**

Run: `python -m unittest chapter8.tests.test_contracts -v`
Expected: PASS，且直接修改 frozen Record 触发 `FrozenInstanceError`。

- [ ] **Step 5: 精确提交**

```powershell
git add -- chapter8/__init__.py chapter8/knowledge_runtime/__init__.py chapter8/knowledge_runtime/contracts.py chapter8/tests/__init__.py chapter8/tests/test_contracts.py
git commit -m "feat: define chapter 8 knowledge contracts"
```

### Task 2: 建立 18 份语料与 Source Catalog

**Files:**
- Create: `chapter8/fixtures/__init__.py`
- Create: `chapter8/fixtures/starboard_docs/*.md`
- Create: `chapter8/fixtures/starboard_docs/*.meta.json`
- Create: `chapter8/fixtures/questions.json`
- Create: `chapter8/knowledge_runtime/catalog.py`
- Create: `chapter8/tests/test_catalog.py`

**Interfaces:**
- Consumes: `KnowledgeDocument`, `RetrievalQuery`。
- Produces: `load_documents(root: Path) -> tuple[KnowledgeDocument, ...]`。
- Produces: `KnowledgeCatalog.current_documents(query: RetrievalQuery) -> tuple[KnowledgeDocument, ...]`。
- Produces: `KnowledgeCatalog.resolve_document(document_id: str, query: RetrievalQuery) -> KnowledgeDocument | None`。

- [ ] **Step 1: 写失败测试，冻结 18 对文件和过滤顺序**

```python
class CatalogTests(unittest.TestCase):
    def test_fixture_has_exactly_eighteen_document_metadata_pairs(self):
        documents = load_documents(FIXTURE_ROOT)
        self.assertEqual(18, len(documents))
        self.assertEqual(18, len(tuple(FIXTURE_ROOT.glob("*.md"))))
        self.assertEqual(18, len(tuple(FIXTURE_ROOT.glob("*.meta.json"))))

    def test_public_32_query_excludes_retired_future_and_maintainer_docs(self):
        catalog = KnowledgeCatalog(load_documents(FIXTURE_ROOT))
        ids = {doc.document_id for doc in catalog.current_documents(public_query())}
        self.assertIn("plans-3.2", ids)
        self.assertNotIn("faq-2.8-sso", ids)
        self.assertNotIn("maintainer-sso-bypass", ids)
        self.assertNotIn("plans-3.3-preview", ids)
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_catalog -v`
Expected: FAIL，原因是语料和 `catalog.py` 尚不存在。

- [ ] **Step 3: 创建确切语料清单并实现加载器**

18 份文档固定覆盖：`plans-2.8`、`plans-3.2`、`faq-2.8-sso`、`faq-3.2-sso`、`release-3.2`、`migration-2x-to-3.2`、`membership-backup`、`install-3.2`、`sso-admin-guide`、`security-overview`、`api-auth`、`incident-sso-loop`、`incident-member-sync`、`community-sso-note`、`community-malicious-note`、`maintainer-sso-bypass`、`plans-3.3-preview`、`withdrawn-draft`。每个 `.meta.json` 使用同一字段集合；加载器拒绝孤立文件、未知字段、Digest 不匹配、非法 UTC 时间和重复 `document_id`。

```python
class KnowledgeCatalog:
    def current_documents(self, query: RetrievalQuery) -> tuple[KnowledgeDocument, ...]:
        return tuple(
            document for document in self._documents
            if document.status is DocumentStatus.ACTIVE
            and document.valid_at(query.now)
            and document.supports_version(query.target_version)
            and document.visible_to(query.role)
        )
```

- [ ] **Step 4: 运行 Catalog 与合同测试**

Run: `python -m unittest chapter8.tests.test_contracts chapter8.tests.test_catalog -v`
Expected: PASS；恶意社区文档可作为低信任公开候选存在，但内部文档与过期文档不合格。

- [ ] **Step 5: 精确提交**

```powershell
$fixturePaths = @(
  'chapter8/fixtures/__init__.py',
  'chapter8/fixtures/questions.json',
  'chapter8/fixtures/starboard_docs/plans-2.8.md', 'chapter8/fixtures/starboard_docs/plans-2.8.meta.json',
  'chapter8/fixtures/starboard_docs/plans-3.2.md', 'chapter8/fixtures/starboard_docs/plans-3.2.meta.json',
  'chapter8/fixtures/starboard_docs/faq-2.8-sso.md', 'chapter8/fixtures/starboard_docs/faq-2.8-sso.meta.json',
  'chapter8/fixtures/starboard_docs/faq-3.2-sso.md', 'chapter8/fixtures/starboard_docs/faq-3.2-sso.meta.json',
  'chapter8/fixtures/starboard_docs/release-3.2.md', 'chapter8/fixtures/starboard_docs/release-3.2.meta.json',
  'chapter8/fixtures/starboard_docs/migration-2x-to-3.2.md', 'chapter8/fixtures/starboard_docs/migration-2x-to-3.2.meta.json',
  'chapter8/fixtures/starboard_docs/membership-backup.md', 'chapter8/fixtures/starboard_docs/membership-backup.meta.json',
  'chapter8/fixtures/starboard_docs/install-3.2.md', 'chapter8/fixtures/starboard_docs/install-3.2.meta.json',
  'chapter8/fixtures/starboard_docs/sso-admin-guide.md', 'chapter8/fixtures/starboard_docs/sso-admin-guide.meta.json',
  'chapter8/fixtures/starboard_docs/security-overview.md', 'chapter8/fixtures/starboard_docs/security-overview.meta.json',
  'chapter8/fixtures/starboard_docs/api-auth.md', 'chapter8/fixtures/starboard_docs/api-auth.meta.json',
  'chapter8/fixtures/starboard_docs/incident-sso-loop.md', 'chapter8/fixtures/starboard_docs/incident-sso-loop.meta.json',
  'chapter8/fixtures/starboard_docs/incident-member-sync.md', 'chapter8/fixtures/starboard_docs/incident-member-sync.meta.json',
  'chapter8/fixtures/starboard_docs/community-sso-note.md', 'chapter8/fixtures/starboard_docs/community-sso-note.meta.json',
  'chapter8/fixtures/starboard_docs/community-malicious-note.md', 'chapter8/fixtures/starboard_docs/community-malicious-note.meta.json',
  'chapter8/fixtures/starboard_docs/maintainer-sso-bypass.md', 'chapter8/fixtures/starboard_docs/maintainer-sso-bypass.meta.json',
  'chapter8/fixtures/starboard_docs/plans-3.3-preview.md', 'chapter8/fixtures/starboard_docs/plans-3.3-preview.meta.json',
  'chapter8/fixtures/starboard_docs/withdrawn-draft.md', 'chapter8/fixtures/starboard_docs/withdrawn-draft.meta.json'
)
git add -- $fixturePaths chapter8/knowledge_runtime/catalog.py chapter8/tests/test_catalog.py
git commit -m "feat: add governed chapter 8 source catalog"
```

### Task 3: 实现三种切分并保留来源

**Files:**
- Create: `chapter8/knowledge_runtime/chunking.py`
- Create: `chapter8/tests/test_chunking.py`

**Interfaces:**
- Consumes: `KnowledgeDocument`。
- Produces: `fixed_character_chunks(document, max_chars, overlap_chars) -> tuple[Chunk, ...]`。
- Produces: `structure_aware_chunks(document, max_chars) -> tuple[Chunk, ...]`。
- Produces: `contextualize_chunks(document, chunks) -> tuple[Chunk, ...]`。

- [ ] **Step 1: 写失败测试，覆盖标题、表格、代码块和来源继承**

```python
def test_structure_chunk_keeps_heading_and_table_together():
    document = document_named("plans-3.2")
    chunks = structure_aware_chunks(document, max_chars=520)
    sso = next(chunk for chunk in chunks if "SSO" in chunk.content)
    self.assertIn("套餐能力", sso.heading_path)
    self.assertIn("团队版", sso.content)
    self.assertEqual(document.content_digest, sso.document_digest)

def test_context_prefix_does_not_change_source_content():
    contextual = contextualize_chunks(document, structure_aware_chunks(document, 520))
    self.assertTrue(all(chunk.context_prefix.startswith("文档：") for chunk in contextual))
    self.assertTrue(all(chunk.content_digest == stable_digest(chunk.content) for chunk in contextual))
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_chunking -v`
Expected: FAIL，原因是切分函数未定义。

- [ ] **Step 3: 实现最小切分状态机**

结构切分按 Markdown 标题维护 `heading_path`，围栏代码和连续表格行不可从中间拆开；超长普通段落再按句子边界切分。`context_prefix` 只作为独立字段加入检索文本，不改写源 `content` 和源 Digest。

- [ ] **Step 4: 运行 Task 1–3 测试**

Run: `python -m unittest chapter8.tests.test_contracts chapter8.tests.test_catalog chapter8.tests.test_chunking -v`
Expected: PASS，固定字符切分测试能稳定暴露限定条件被分离的失败样本。

- [ ] **Step 5: 精确提交**

```powershell
git add -- chapter8/knowledge_runtime/chunking.py chapter8/tests/test_chunking.py
git commit -m "feat: add source-aware chapter 8 chunking"
```

### Task 4: 实现 BM25、固定语义召回、RRF 与重排

**Files:**
- Create: `chapter8/knowledge_runtime/sparse.py`
- Create: `chapter8/knowledge_runtime/dense.py`
- Create: `chapter8/knowledge_runtime/fusion.py`
- Create: `chapter8/knowledge_runtime/rerank.py`
- Create: `chapter8/tests/test_retrieval_primitives.py`

**Interfaces:**
- Produces: `BM25Index.rank(query: str, allowed_chunk_ids: set[str], limit: int) -> tuple[RankedChunk, ...]`。
- Produces: `EmbeddingModel.embed(text: str) -> tuple[float, ...]` Protocol。
- Produces: `FrozenEmbeddingModel` 和 `DenseIndex.rank(...)`。
- Produces: `reciprocal_rank_fusion(rankings: Mapping[str, Sequence[RankedChunk]], rrf_k: int, limit: int) -> tuple[RankedChunk, ...]`。
- Produces: `DeterministicReranker.rank(query: str, chunks: Sequence[Chunk], limit: int) -> tuple[RankedChunk, ...]`。

- [ ] **Step 1: 写失败测试和可手算期望**

```python
def test_bm25_prefers_exact_legacy_saml_term():
    ranked = BM25Index(chunks).rank("legacy_saml 3.2", all_ids, limit=3)
    self.assertEqual("release-3.2", by_chunk(ranked[0]).document_id)

def test_rrf_uses_rank_not_incomparable_raw_scores():
    fused = reciprocal_rank_fusion({"bm25": sparse_rank, "dense": dense_rank}, rrf_k=60, limit=3)
    self.assertEqual(expected_chunk_ids, tuple(item.chunk_id for item in fused))
    self.assertAlmostEqual((1 / 61) + (1 / 62), fused[0].score)

def test_ties_use_chunk_id_for_byte_stability():
    self.assertEqual(sorted(ids), [item.chunk_id for item in tied_results])
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_retrieval_primitives -v`
Expected: FAIL，原因是四个检索模块不存在。

- [ ] **Step 3: 实现四个独立组件**

BM25 使用 `k1=1.5`、`b=0.75`，分词同时保留英文词、中文单字和中文双字；IDF 使用 `log(1 + (N-df+0.5)/(df+0.5))`。固定向量从 `questions.json` 的教学词义表生成，只允许固定 Fixture 使用；未知词落入稳定 Hash Bucket。RRF 不读取原始 BM25/余弦分数。规则 Reranker 只看 Query–Chunk 的版本匹配、必需术语覆盖、标题匹配和可信度标签，保留分项。

- [ ] **Step 4: 运行原语测试并手工核对一个排名**

Run: `python -m unittest chapter8.tests.test_retrieval_primitives -v`
Expected: PASS；测试输出能用三条候选手算 BM25 与 RRF。

- [ ] **Step 5: 精确提交**

```powershell
git add -- chapter8/knowledge_runtime/sparse.py chapter8/knowledge_runtime/dense.py chapter8/knowledge_runtime/fusion.py chapter8/knowledge_runtime/rerank.py chapter8/tests/test_retrieval_primitives.py
git commit -m "feat: build chapter 8 hybrid retrieval stages"
```

### Task 5: 编排安全检索并阻止陈旧索引复活

**Files:**
- Create: `chapter8/knowledge_runtime/retrieve.py`
- Create: `chapter8/tests/test_retrieve.py`

**Interfaces:**
- Consumes: `KnowledgeCatalog`、Chunk、BM25、Dense、RRF、Reranker。
- Produces: `HybridRetriever.retrieve(query: RetrievalQuery) -> tuple[RetrievalHit, ...]`。
- Produces: `RetrievalTrace`，记录过滤数量和各阶段 Chunk ID，不记录内部正文。

- [ ] **Step 1: 写失败测试，证明硬过滤先于任何评分**

```python
def test_internal_retired_and_future_chunks_are_never_scored():
    hits, trace = retriever.retrieve(public_32_query(), include_trace=True)
    forbidden = {"maintainer-sso-bypass", "faq-2.8-sso", "plans-3.3-preview"}
    self.assertTrue(forbidden.isdisjoint(trace.scored_document_ids))
    self.assertTrue(forbidden.isdisjoint(hit.chunk.document_id for hit in hits))

def test_catalog_recheck_blocks_chunk_from_stale_index():
    stale_retriever = build_retriever(indexed_before_withdrawal=True)
    stale_retriever.catalog.withdraw("community-malicious-note")
    hits = stale_retriever.retrieve(public_32_query())
    self.assertNotIn("community-malicious-note", {hit.chunk.document_id for hit in hits})
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_retrieve -v`
Expected: FAIL，原因是 `HybridRetriever` 未定义。

- [ ] **Step 3: 实现过滤—召回—融合—回查—重排顺序**

```python
def retrieve(self, query: RetrievalQuery) -> tuple[RetrievalHit, ...]:
    eligible = self.catalog.current_documents(query)
    allowed = self._chunk_ids_for(eligible)
    sparse = self.sparse.rank(query.text, allowed, query.candidate_k)
    dense = self.dense.rank(query.text, allowed, query.candidate_k)
    fused = reciprocal_rank_fusion({"sparse": sparse, "dense": dense}, 60, query.candidate_k)
    live = [item for item in fused if self.catalog.resolve_document(self._document_id(item), query)]
    return self._to_hits(self.reranker.rank(query.text, self._chunks(live), query.top_k))
```

Trace 明确区分 `filtered_before_score`、`sparse_candidates`、`dense_candidates`、`fused_candidates`、`catalog_recheck_rejected` 和 `final_hits`。

- [ ] **Step 4: 运行检索与全部下层测试**

Run: `python -m unittest chapter8.tests.test_contracts chapter8.tests.test_catalog chapter8.tests.test_chunking chapter8.tests.test_retrieval_primitives chapter8.tests.test_retrieve -v`
Expected: PASS；跨角色泄漏、旧版泄漏、未来文档提前生效均为 0。

- [ ] **Step 5: 精确提交**

```powershell
git add -- chapter8/knowledge_runtime/retrieve.py chapter8/tests/test_retrieve.py
git commit -m "feat: enforce governed chapter 8 retrieval"
```

### Task 6: 建立 Evidence Packet、引用、拒答和分层指标

**Files:**
- Create: `chapter8/knowledge_runtime/evidence.py`
- Create: `chapter8/knowledge_runtime/evaluation.py`
- Create: `chapter8/tests/test_evidence.py`
- Create: `chapter8/tests/test_evaluation.py`

**Interfaces:**
- Produces: `build_evidence_packet(query, hits, required_fact_ids) -> EvidencePacket`。
- Produces: `ScriptedAnswerPolicy.answer(case: QuestionCase, packet: EvidencePacket) -> AnswerDecision`。
- Produces: `precision_at_k`、`recall_at_k`、`mean_reciprocal_rank`、`ndcg_at_k`、`citation_metrics`、`answer_support_metrics`。

- [ ] **Step 1: 写失败测试，冻结“引用不等于支持”和复合问题拒答**

```python
def test_compound_answer_abstains_when_membership_evidence_is_missing():
    packet = build_evidence_packet(query, sso_only_hits, required_fact_ids=("sso-32", "member-preserved"))
    decision = ScriptedAnswerPolicy().answer(compound_case, packet)
    self.assertEqual(AnswerStatus.PARTIAL, decision.status)
    self.assertEqual(("member-preserved",), decision.missing_fact_ids)

def test_wrong_citation_does_not_count_as_supported_claim():
    metrics = citation_metrics(reference_claims, answer_with_wrong_source)
    self.assertEqual(0.5, metrics.precision)
    self.assertEqual(0.5, metrics.recall)
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_evidence chapter8.tests.test_evaluation -v`
Expected: FAIL，原因是 Evidence/Eval 模块不存在。

- [ ] **Step 3: 实现可审计 Evidence 与指标**

Evidence Packet 只接受最终 Hit；Citation ID 使用 `C1`、`C2` 稳定排序并保留 `document_id`、`chunk_id`、版本、来源和内容 Digest。`ScriptedAnswerPolicy` 从 `QuestionCase.expected_claims` 产生固定声明，但只有 `required_fact_ids` 全部存在时才能标为 answer；部分存在返回 partial；完全缺失返回 abstain。

检索指标基于人工标注 Chunk/Document 集；Citation 指标基于声明—证据映射；Freshness、Isolation、Safety 使用独立整数计数。除法分母为 0 时返回 `None`，不伪造 0 分。

- [ ] **Step 4: 运行 Task 1–6 全部测试**

Run: `python -m unittest discover -s chapter8/tests -v`
Expected: PASS；当前测试不得产生 `__pycache__` 提交项。

- [ ] **Step 5: 精确提交**

```powershell
git add -- chapter8/knowledge_runtime/evidence.py chapter8/knowledge_runtime/evaluation.py chapter8/tests/test_evidence.py chapter8/tests/test_evaluation.py
git commit -m "feat: add chapter 8 evidence and evaluation"
```

### Task 7: 生成五组规范实验和可选 Live Probe

**Files:**
- Create: `chapter8/knowledge_runtime/persistence.py`
- Create: `chapter8/experiments/__init__.py`
- Create: `chapter8/experiments/run_all.py`
- Create: `chapter8/live/README.md`
- Create: `chapter8/live/live_probe.py`
- Create: `chapter8/live/live-probe.example.json`
- Create: `chapter8/reports/rag-evidence.json`
- Create: `chapter8/reports/rag-evidence.md`
- Create: `chapter8/reports/rag-evidence-trace.jsonl`
- Create: `chapter8/tests/test_experiments.py`
- Create: `chapter8/tests/test_report_reproducibility.py`

**Interfaces:**
- Produces: `build_report() -> dict[str, object]`，恰好包含 `baseline`、`chunking`、`retrieval`、`governance`、`evidence` 五组。
- Produces: `write_reports(output: Path) -> tuple[Path, Path, Path]`。
- Live Probe 入口：`python -m chapter8.live.live_probe --output <ignored-path>`；无凭据/依赖返回结构化 skipped，不写规范报告。

- [ ] **Step 1: 写失败测试冻结组数、案例数、null 和字节复现**

```python
def test_report_has_exactly_five_groups_and_no_aggregate_success_rate():
    report = build_report()
    self.assertEqual(("baseline", "chunking", "retrieval", "governance", "evidence"), tuple(report["groups"]))
    self.assertNotIn("overall_score", report)
    self.assertIsNone(report["unmeasured"]["real_model_quality"])
    self.assertIsNone(report["unmeasured"]["provider_tokens"])

def test_reports_are_byte_reproducible_and_trace_redacted():
    first = generate_to(temp_a)
    second = generate_to(temp_b)
    self.assertEqual([p.read_bytes() for p in first], [p.read_bytes() for p in second])
    self.assertNotIn(b"maintainer bypass", first[2].read_bytes().lower())
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_experiments chapter8.tests.test_report_reproducibility -v`
Expected: FAIL，原因是生成器和报告不存在。

- [ ] **Step 3: 实现 5 组确定性案例和稳定报告**

五组案例数固定为 `baseline=3`、`chunking=3`、`retrieval=4`、`governance=5`、`evidence=5`，共 20 个 Case。每个 Case 写 `sample_count=1`、独立指标、证据码、支持范围和 Non-claim。规范时钟固定为 `2026-08-27T16:00:00Z`，即北京时间 2026-08-28 00:00；JSON 键排序、缩进 2、LF；Markdown 表格从 JSON 对象生成；Trace 每行只记录 case ID、阶段、Chunk/Document ID、Digest、计数和 reason。

Live Probe 仅读取进程环境变量名称，不把值写入日志；默认输出路径 `chapter8/live-output/` 加入 `.gitignore`。`live-probe.example.json` 的 provider、model、usage、latency、quality 字段全部为说明性 `null`。

- [ ] **Step 4: 生成两次并运行全部 Chapter 8 测试**

Run: `python -m chapter8.experiments.run_all --output chapter8/reports`
Run: `python -m unittest discover -s chapter8/tests -v`
Expected: PASS；连续第二次生成后 `git diff -- chapter8/reports` 为空。

- [ ] **Step 5: 精确提交**

```powershell
git add -- .gitignore chapter8/knowledge_runtime/persistence.py chapter8/experiments/__init__.py chapter8/experiments/run_all.py chapter8/live/README.md chapter8/live/live_probe.py chapter8/live/live-probe.example.json chapter8/reports/rag-evidence.json chapter8/reports/rag-evidence.md chapter8/reports/rag-trace.jsonl chapter8/tests/test_experiments.py chapter8/tests/test_report_reproducibility.py
git commit -m "feat: add chapter 8 rag experiments"
```

### Task 8: 建立来源台账、发布门禁和 8 幅图

**Files:**
- Create: `book/sources/chapter8-sources.md`
- Create: `chapter8/publication_checks.py`
- Create: `chapter8/tests/test_publication_checks.py`
- Create: `chapter8/tests/test_figures.py`
- Create: `book/images/fig8-1-state-boundary.svg`
- Create: `book/images/fig8-2-offline-online-pipeline.svg`
- Create: `book/images/fig8-3-rag-evolution.svg`
- Create: `book/images/fig8-4-chunking-comparison.svg`
- Create: `book/images/fig8-5-retrieval-funnel.svg`
- Create: `book/images/fig8-6-evidence-citations.svg`
- Create: `book/images/fig8-7-governed-index.svg`
- Create: `book/images/fig8-8-evaluation-matrix.svg`

**Interfaces:**
- Produces: `PublicationContract(min_cjk=25000, max_cjk=33000, figure_count=8, exercise_count=14)`。
- Produces: `publication_errors(chapter, answers, sources, image_dir) -> tuple[str, ...]`。

- [ ] **Step 1: 写失败测试冻结来源字段、8 图和安全规则**

```python
def test_exact_eight_figures_are_safe_accessible_svg():
    self.assertEqual(EXPECTED_FIGURES, tuple(sorted(path.name for path in IMAGE_DIR.glob("fig8-*.svg"))))
    for path in IMAGE_DIR.glob("fig8-*.svg"):
        root = ElementTree.parse(path).getroot()
        self.assertEqual("0 0 1200 675", root.attrib["viewBox"])
        self.assertTrue(root.findall("{http://www.w3.org/2000/svg}title"))
        self.assertTrue(root.findall("{http://www.w3.org/2000/svg}desc"))

def test_publication_gate_rejects_secret_paths_rankings_and_byte_token_claims():
    errors = publication_errors(unsafe_chapter(), valid_answers(), valid_sources(), IMAGE_DIR)
    self.assertIn("possible_secret", errors)
    self.assertIn("absolute_author_path", errors)
    self.assertIn("unsupported_product_ranking", errors)
    self.assertIn("offline_bytes_mislabeled_as_tokens", errors)
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `python -m unittest chapter8.tests.test_publication_checks chapter8.tests.test_figures -v`
Expected: FAIL，原因是门禁、来源和图片尚不存在。

- [ ] **Step 3: 创建来源台账和 SVG**

来源条目使用 `S01` 起的稳定编号，每项必须包含标题/机构、URL 或仓库相对路径、类型、事实使用、明确不声称、核对日期、出版前复核。至少覆盖 RAG、DPR、BM25/IIR、RRF、ColBERTv2、Ragas、LangChain/LangGraph、OpenAI、Anthropic，以及作者 Phase 2/6 资料和两份 PDF 的页级用途。

8 幅 SVG 使用 1200×675、统一色板、最小正文显式字体 20px、标题/描述和来源标签；图 5、8 的数值从 `rag-evidence.json` 读取后写入，测试逐项比对。

- [ ] **Step 4: 运行图与门禁合成测试**

Run: `python -m unittest chapter8.tests.test_publication_checks chapter8.tests.test_figures -v`
Expected: synthetic bundle PASS；实际正文 Bundle 测试暂不启用，直到 Task 9 创建正文和答案。

- [ ] **Step 5: 精确提交**

```powershell
git add -- book/sources/chapter8-sources.md book/images/fig8-1-state-boundary.svg book/images/fig8-2-offline-online-pipeline.svg book/images/fig8-3-rag-evolution.svg book/images/fig8-4-chunking-comparison.svg book/images/fig8-5-retrieval-funnel.svg book/images/fig8-6-evidence-citations.svg book/images/fig8-7-governed-index.svg book/images/fig8-8-evaluation-matrix.svg chapter8/publication_checks.py chapter8/tests/test_publication_checks.py chapter8/tests/test_figures.py
git commit -m "docs: add chapter 8 sources and diagrams"
```

### Task 9: 撰写正文、实验 README 与 14 份答案

**Files:**
- Create: `book/chapter8.md`
- Create: `chapter8/README.md`
- Create: `chapter8/requirements.txt`
- Create: `chapter8/reference-answers.md`
- Modify: `chapter8/tests/test_publication_checks.py`

**Interfaces:**
- Consumes: 全部 Runtime、规范报告、8 幅图和来源台账。
- Produces: 第 8 章 2.5–3 万有效中文字符、v0–v7 每版可观察输出、14 道练习与 14 份答案。

- [ ] **Step 1: 先启用实际 Bundle 失败测试**

```python
def test_actual_chapter_bundle_passes_publication_contract():
    root = Path(__file__).resolve().parents[2]
    self.assertEqual((), publication_errors(
        root / "book/chapter8.md",
        root / "chapter8/reference-answers.md",
        root / "book/sources/chapter8-sources.md",
        root / "book/images",
    ))

def test_actual_chapter_has_ordered_v0_to_v7_results():
    chapter = (ROOT / "book/chapter8.md").read_text(encoding="utf-8")
    self.assertEqual(list(range(8)), version_headings(chapter))
    self.assertEqual(8, chapter.count("**运行结果：**"))
```

- [ ] **Step 2: 运行实际 Bundle 测试确认 RED**

Run: `python -m unittest chapter8.tests.test_publication_checks -v`
Expected: FAIL，原因是正文、README 和答案不存在。

- [ ] **Step 3: 按批准主线写完整初稿**

正文顺序必须是失败开场、阅读提示、中文术语表、边界、v0–v7、进阶原理、框架/产品责任映射、生产故障与安全、本章小结、Claims/Non-claims、14 题和第 9 章衔接。每个 v 版本包含输入/核心代码/中间状态/运行结果/修复了什么/仍未证明什么。正文逐图说明从哪里开始读、箭头和颜色分别代表什么。

`chapter8/README.md` 列出准确目录、Python 版本、测试/报告命令、五组实验和边界；`requirements.txt` 为空依赖说明或只含注释；14 份答案逐题包含“预期推理、常见错误、验收标准”。

- [ ] **Step 4: 运行 Chapter 8 全部测试并统计篇幅**

Run: `python -m unittest discover -s chapter8/tests -v`
Run: `python -c "from pathlib import Path; from chapter8.publication_checks import cjk_prose_count; print(cjk_prose_count(Path('book/chapter8.md').read_text(encoding='utf-8')))"`
Expected: 全部 PASS；有效中文字符 25000–33000；8 图、14 题、14 答案、v0–v7 均满足。

- [ ] **Step 5: 精确提交**

```powershell
git add -- book/chapter8.md chapter8/README.md chapter8/requirements.txt chapter8/reference-answers.md chapter8/tests/test_publication_checks.py
git commit -m "docs: write chapter 8 rag knowledge base"
```

### Task 10: 四视角 Review 并修订正文

**Files:**
- Create: `book/reviews/chapter8-review-codex.md`
- Modify: `book/chapter8.md`
- A finding may name an additional exact Runtime、test、figure、answer or source path. Add that path to the Review table before changing it; never stage a whole directory or wildcard.

**Interfaces:**
- Produces: 读者、AI 专家、工程证据、资料时效四视角 Review；每个发现有优先级、证据路径、处理结果和保留限制。

- [ ] **Step 1: 建立 Review 检查表并先记录发现，不先写“通过”**

```markdown
| 优先级 | 视角 | 发现 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| P1/P2/P3 | 读者/专家/工程/来源 | 具体问题 | 文件与测试 | fixed/accepted |
```

读者检查术语密度、段落长度、v0–v7 因果链和代码可跟随性；专家检查 RAG/Memory、过滤/排序、Recall/Rerank、引用/事实边界；工程检查 ID、时效、权限、索引回查、复现和脱敏；来源检查官方页面状态、论文外推和作者素材页级映射。

- [ ] **Step 2: 运行静态统计和测试，形成初审证据**

Run: `python -m unittest discover -s chapter8/tests -v`
Run: `python scripts/check_repository.py --root . --git-history`
Expected: 测试结果、标题数、CJK 数、图数、练习数和报告哈希可写入 Review；若失败，Review 状态为 blocked，不写通过。

- [ ] **Step 3: 修复全部 P1 和选定 P2，并为技术问题先加回归测试**

技术发现按 RED→GREEN 修复；可读性发现优先增加具体示例、分步输出或移动进阶内容，不通过删除边界说明来缩短正文。任何产品事实修订同步更新来源台账和核对日期。

- [ ] **Step 4: 复审并冻结 Review 结论**

Run: `python -m unittest discover -s chapter8/tests -v`
Expected: Review 清楚列出已修复项、未阻塞限制、规范报告哈希和“不支持真实模型/厂商排名”的边界。

- [ ] **Step 5: 精确提交**

```powershell
$reviewPaths = @('book/reviews/chapter8-review-codex.md', 'book/chapter8.md')
# For every fixed finding, append the exact evidence/test/source path recorded in the Review table to $reviewPaths.
git add -- $reviewPaths
git diff --cached --name-only
git commit -m "docs: review and refine chapter 8"
```

暂存清单必须与 Review 表中 `fixed` 行的路径逐项一致；若列表不一致，取消本次提交并先修正清单。

### Task 11: 接入 0.8.0 书库和站点

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `book/README.md`
- Modify: `book/OUTLINE.md`
- Modify: `book/manifest.json`
- Modify: `book/chapter7.md`
- Modify: `docs/EXPERIMENT_STATUS.md`
- Modify: `docs/MIGRATION_MANIFEST.md`
- Modify: `scripts/build_site.py`
- Modify: `mkdocs.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `tests/test_book_manifest.py`
- Modify: `tests/test_build_site.py`
- Modify: `tests/test_experiment_inventory.py`
- Modify: `tests/test_repository_contract.py`
- Modify: `tests/test_workflow_contract.py`

**Interfaces:**
- Manifest: 18 章、8 published、10 planned、版本 `0.8.0`、更新时间 `2026-08-28`。
- Site allowlist: `chapter1`–`chapter8` 正文、实验 README、答案和报告。
- CI: 运行 Chapter 8 测试和规范报告生成器。

- [ ] **Step 1: 先修改仓库合同测试并确认 RED**

```python
def test_manifest_exposes_eight_published_and_ten_unpublished_chapters(self):
    chapters = flatten(validate_manifest(ROOT))
    self.assertEqual(8, sum(item["status"] == "published" for item in chapters))
    self.assertEqual("published", chapters[7]["status"])
    self.assertTrue(all(item["status"] == "planned" for item in chapters[8:]))
```

同时把站点源数量和 CI 必需命令断言扩展到 Chapter 8。

- [ ] **Step 2: 运行仓库测试确认 RED**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL，指出 manifest、站点 allowlist、CI 或导航仍只覆盖 7 章。

- [ ] **Step 3: 更新所有发布表面**

Manifest 第 8 章加入 `source`、`experiment`、`answers` 和 `updated`；根 README 与书 README 增加第 8 章；第 7 章末尾改为第 8 章正文/实验/答案；第 8 章末尾仍指向第 9 章规划；AGENTS 状态改为第 1–8 章已发布；CI 运行 Chapter 3–8 测试并重建 Chapter 8 报告；MkDocs 同步正文和实验导航。

更新 `book/README.md` 后，运行 `python scripts/generate_migration_manifest.py --root . --current-commit 93931cc43b862e525e5c1c77473a2024af09b162 --later-commit faa56e968affe2469ef828b62bf0947c6e9ebdbb --output docs/MIGRATION_MANIFEST.md` 重建 `docs/MIGRATION_MANIFEST.md`，只接受预期文件哈希变化。

- [ ] **Step 4: 运行仓库测试、渲染和严格站点构建**

Run: `python -m unittest discover -s tests -v`
Run: `npm test --prefix book`
Run: `python scripts/build_site.py --root . --output _web`
Run: `python -m mkdocs build --strict`
Expected: 全部 PASS；站点包含 `book/chapter8.md`、`chapter8/index.md`、答案和三份报告。

- [ ] **Step 5: 精确提交**

```powershell
git add -- README.md AGENTS.md book/README.md book/OUTLINE.md book/manifest.json book/chapter7.md docs/EXPERIMENT_STATUS.md docs/MIGRATION_MANIFEST.md scripts/build_site.py mkdocs.yml .github/workflows/ci.yml tests/test_book_manifest.py tests/test_build_site.py tests/test_experiment_inventory.py tests/test_repository_contract.py tests/test_workflow_contract.py
git commit -m "build: publish chapter 8 in the book site"
```

### Task 12: 全量验证、发布与线上验收

**Files:**
- Modify only if verification finds a scoped defect; every fix first adds or updates the narrowest failing test。

**Interfaces:**
- Produces: clean commit history, green local gates, green GitHub CI/Pages, reachable Chapter 8 public URL。

- [ ] **Step 1: 运行第 1–8 章和仓库全量测试**

```powershell
python -m unittest discover -s tests -v
python -m unittest discover -s chapter1/tests -v
python -m unittest discover -s chapter3/tests -v
python -m unittest discover -s chapter4/tests -v
python -m unittest discover -s chapter5/tests -v
python -m unittest discover -s chapter6/tests -v
python -m unittest discover -s chapter7/tests -v
python -m unittest discover -s chapter8/tests -v
```

另运行第 2 章 README 的 7 个离线命令。Expected: 全部退出 0。

- [ ] **Step 2: 连续重建全部规范报告并核对哈希**

Run: CI 中“Regenerate deterministic teaching reports”全部命令，连续两次。
Expected: 第二次后 `git diff -- chapter1/reports chapter2/results chapter3/reports chapter4/reports chapter5/reports chapter6/reports chapter7/reports chapter8/reports book/images/fig2-7-real-sft-curves.svg` 为空；Chapter 8 三份 SHA-256 写入 `docs/EXPERIMENT_STATUS.md` 和 Review。

- [ ] **Step 3: 运行安全、渲染、站点和工作树检查**

```powershell
python scripts/check_repository.py --root . --git-history
npm test --prefix book
python scripts/build_site.py --root . --output _web
python -m mkdocs build --strict
git diff --check
git status --short
```

Expected: 无 Secret、绝对路径、缓存、断链、产品排名、byte-as-Token、未暂存改动或构建物。

- [ ] **Step 4: 精确提交必要的最终元数据并推送**

若 Task 12 没有修复，不创建空提交；否则只暂存实际修复路径。随后运行 `git push origin main`，记录最终 Commit SHA。

- [ ] **Step 5: 等待 CI 和 Pages，并验证线上内容**

```powershell
$commitSha = (git rev-parse HEAD).Trim()
$runs = gh run list --commit $commitSha --json databaseId,workflowName,status,conclusion | ConvertFrom-Json
$runs | Format-Table databaseId,workflowName,status,conclusion
$runs | ForEach-Object { gh run watch $_.databaseId --exit-status }
```

Expected: CI 与 Pages 均 success；公开第 8 章 URL 返回 200，并包含 `v7`、`本章小结`、8 幅图引用以及实验/答案链接，之后才能宣称发布完成。
