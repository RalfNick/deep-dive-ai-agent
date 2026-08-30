---
title: "RAG 如何工作"
topic: "technical educational"
data_type: "dual-lane process"
complexity: "complex"
point_count: 11
source_language: "zh"
user_language: "zh"
---

## Main Topic

把 RAG 分成离线知识加工与在线证据回答两条生命周期，强调知识治理、检索、证据和回答边界，而不是把 RAG 简化成“文档进向量库”。

## Learning Objectives

读者看完后应该理解：

1. 离线管道怎样把原始文档变成可治理、可检索的对象；
2. 在线管道怎样在权限、版本和时间边界内召回并组织证据；
3. LLM 只能基于 Evidence Packet 回答，证据不足时应部分回答或拒答。

## Target Audience

- **Knowledge Level**: 知道 LLM 基本概念、首次系统学习 RAG 的读者
- **Context**: 第 8 章开头的全局地图
- **Expectations**: 能顺着两条路径定位“知识没进来”“没召回”“证据不足”分别坏在哪里

## Content Type Analysis

- **Data Structure**: 上下双泳道，离线索引为在线召回提供派生结构，Catalog 同时约束两条路径
- **Key Relationships**: Source Chunk 是引用锚点；Index 是派生物；Evidence Packet 位于检索和 LLM 之间
- **Visual Opportunities**: 文档堆、切块、目录盾牌、关键词与向量双索引、漏斗、证据包、带引用回答与拒答分支

## Key Data Points (Verbatim)

- “RAG 位于外部知识进入 Context 的路径上，它不直接改写模型参数，也不自动成为长期 Memory。”
- “Catalog 管‘有没有资格’，Retriever 管‘与问题是否相关’，Evidence Gate 管‘能否支持声明’，Answer Policy 管‘此刻应该说多少’。”
- “这不是‘回答能力变差’，而是把不确定性变得诚实、可定位。”

## Layout × Style Signals

- Content type: 两条连续生命周期 → `linear-progression`
- Tone: 教学、工程、需要降低抽象感 → `hand-drawn-edu`
- Audience: 先看全局，再回正文理解组件 → 横向 16:9
- Complexity: complex → 每条泳道只保留 5–6 个节点，细节交给后续技术图

## Design Instructions (from user input)

- 画面需要比现有深色流程框更直观，有具体对象和隐喻，不只是一排矩形
- 沿用 LLM 主图的暖白背景、深蓝文字和柔和四色视觉语言
- 用明显边界表现 Catalog、Evidence Gate 和引用，不把相关性画成真实性
- 适合网页正文宽度和移动端缩放

## Recommended Combinations

1. **linear-progression + hand-drawn-edu** (Recommended): 双泳道流程最清楚，也能用文档、索引和证据包建立具体感
2. **dense-modules + pop-laboratory**: 工程密度高，但初学者第一眼负担较大
3. **structural-breakdown + technical-schematic**: 适合系统架构，但会延续现有技术框图观感
