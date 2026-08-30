# RAG 如何工作

## Overview

RAG 不是把文档直接丢进向量库，而是用离线知识加工和在线证据回答两条管道，让 Agent 先查证，再回答。

## Learning Objectives

读者将理解：

1. 什么对象有资格进入索引；
2. 一次请求能使用哪些证据；
3. 为什么最后还需要 Citation、Verifier 和拒答。

---

## Section 1: 离线知识加工

**Key Concept**: 原始来源必须先变成有身份、有版本、有权限并可追踪的 Source Chunk，再建立索引。

**Content**:

- “原始文件不会直接跳进向量库。”
- “系统先解析结构、建立 Source Chunk，再处理重复内容、版本关系和治理字段，最后才生成稀疏或稠密索引。”
- “真正用于 Citation 和最终验收的仍是当前有效的 Source Chunk。”

**Visual Element**:

- 文档堆 → 结构解析与切块 → Catalog 盾牌 → 关键词卡与向量点云 → BM25 / Vector 双索引
- Catalog 卡片显示：状态、版本、权限、时间

**Text Labels**:

- Headline: “离线：把知识变成可检索对象”
- Labels: “原始文档”, “解析与切块”, “Source Chunk”, “Catalog 治理”, “稀疏表示”, “稠密表示”, “BM25”, “Vector”

---

## Section 2: 在线证据回答

**Key Concept**: 先过滤合法范围，再召回、融合、重排和验收证据，最后才交给 LLM。

**Content**:

- “Actor、目标版本和查询时间先进入 Catalog 过滤，合法候选才参加混合召回。”
- “融合与重排之后还要经过 Return Gate，最终形成 Evidence Packet。”
- “Answer Policy 只表达被覆盖的事实。”

**Visual Element**:

- 用户问题与身份卡 → 盾牌过滤 → 双路检索漏斗 → RRF + Reranker → Evidence Packet → LLM 回答卡
- 回答卡分出：有引用的回答、部分回答、拒答

**Text Labels**:

- Headline: “在线：从问题到证据回答”
- Labels: “问题 + Actor”, “版本 + 时间”, “Catalog 过滤”, “混合召回”, “RRF 融合”, “Reranker”, “Return Gate”, “Evidence Packet”, “LLM”, “引用回答”, “部分回答”, “拒答”

---

## Section 3: 四道责任边界

**Key Concept**: 资格、相关性、证据充分性和表达边界不能由一个相似度分数代替。

**Content**:

- “Catalog 管‘有没有资格’”
- “Retriever 管‘与问题是否相关’”
- “Evidence Gate 管‘能否支持声明’”
- “Answer Policy 管‘此刻应该说多少’”

**Visual Element**:

- 底部四枚彩色责任徽章，分别与主流程中的位置连线

**Text Labels**:

- Headline: “四道责任边界”
- Labels: “Catalog：资格”, “Retriever：相关”, “Evidence Gate：证据”, “Answer Policy：表达”

---

## Data Points (Verbatim)

### Key Terms

- “Source Chunk”
- “Catalog”
- “BM25”
- “Vector”
- “RRF”
- “Reranker”
- “Evidence Packet”
- “Citation”

---

## Design Instructions

### Style Preferences

- 暖白背景、深蓝标题，蓝色表示离线加工，绿色表示在线回答，紫色表示证据，橙色表示输出边界
- 圆角卡片与清晰图标，轻手绘但保持专业

### Layout Preferences

- 16:9 横向双泳道
- 上方离线知识加工从左到右，下方在线证据回答从左到右
- 双索引向下连接混合召回；Catalog 同时覆盖入库和查询过滤

### Other Requirements

- 中文必须准确、足够大
- 不出现“相关 = 真实”的视觉暗示
- 不出现品牌 Logo、水印或宣传语
