---
references:
  - ref_id: 01
    filename: refs/01-ref-visual-system.png
    usage: style
layout: linear-progression
style: hand-drawn-edu
aspect_ratio: "16:9"
language: zh
backend: imagegen
---

Use case: infographic-diagram
Asset type: 第 8 章网页与电子书主信息图
Primary request: 创作一张中文原创教育信息图《RAG 如何工作》，用上下双泳道解释离线知识加工和在线证据回答。参考图只用于沿用暖白背景、分区卡片、清晰层级和柔和配色，不复制其 LLM 构图或文字。
Input images: Image 1 is a style and visual-system reference only, not an edit target.

Canvas and composition: 16:9 landscape. Large title on top. Two wide horizontal lanes below. Upper blue lane flows left to right for offline processing. Lower green lane flows left to right for online answering. A vertical bridge connects the dual indexes in the upper lane to hybrid retrieval in the lower lane. At the bottom place four compact responsibility badges.

Style: clean hand-drawn educational infographic, professional and highly legible. Warm cream background, deep navy text and outlines. Pastel blue for offline, mint for online, lavender for evidence, orange for answer boundaries. Rounded cards, subtle paper texture, clear arrows, small concrete illustrations instead of generic rectangles.

Required visual content:
Upper lane: a stack of source documents → parsing and chunking → traceable Source Chunk cards → Catalog governance shield showing status/version/permission/time → sparse and dense representations → two indexes labeled BM25 and Vector.
Lower lane: user question plus identity card → Catalog filtering shield → hybrid retrieval funnel fed by both indexes → RRF fusion → Reranker → Return Gate → a sealed Evidence Packet containing facts, conflicts and citations → LLM → three possible outputs: cited answer, partial answer, refusal.
Bottom badges connect to their location in the flow: Catalog eligibility, Retriever relevance, Evidence Gate support, Answer Policy expression.

All visible text must be rendered verbatim in Simplified Chinese. Use only the following text; do not invent extra captions:
Title: “RAG 如何工作”
Subtitle: “让 Agent 先查证，再回答”
Upper lane title: “离线：把知识变成可检索对象”
Upper labels: “原始文档”, “解析与切块”, “Source Chunk”, “Catalog 治理”, “状态 · 版本 · 权限 · 时间”, “稀疏表示”, “稠密表示”, “BM25”, “Vector”
Lower lane title: “在线：从问题到证据回答”
Lower labels: “问题 + Actor”, “版本 + 时间”, “Catalog 过滤”, “混合召回”, “RRF 融合”, “Reranker”, “Return Gate”, “Evidence Packet”, “事实 · 冲突 · 引用”, “LLM”, “引用回答”, “部分回答”, “拒答”
Bottom heading: “四道责任边界”
Bottom labels: “Catalog：资格”, “Retriever：相关”, “Evidence Gate：证据”, “Answer Policy：表达”

Constraints: exact Chinese text; no misspellings; no garbled characters; no dense paragraphs; no tiny footnotes; no logos; no watermarks; no vendor names. The diagram must not imply that vector similarity proves truth. Source Chunk remains the citation anchor. Indexes are derived structures, not the source of truth.
