---
references:
  - ref_id: 01
    filename: refs/01-ref-semantic-navigation.jpg
    usage: direct
  - ref_id: 02
    filename: refs/02-ref-visual-system.png
    usage: style
layout: binary-comparison
style: hand-drawn-edu
aspect_ratio: "16:9"
language: zh
backend: imagegen
---

Use case: infographic-diagram
Asset type: 第 11 章 Coding Agent 预备信息图
Primary request: 创作一张中文原创 A/B 对比信息图，解释 Coding Agent 使用文本搜索与语义代码图导航代码库的差异。Image 1 只作为左右对比和阅读动线参考，不能复制其品牌、文字、具体图标或绝对结论。Image 2 只用于统一全书暖白背景、卡片层级和柔和配色。
Input images: Image 1 is a composition reference; Image 2 is a style reference. Neither is an edit target.

Canvas and composition: 16:9 landscape. Large centered title and short subtitle at top. Split the main area vertically into two mirrored lanes. The same user task and Coding Agent appear at the top of both lanes. Left mint lane uses text search and branches into three visible failure risks. Right pale blue lane queries a code graph and follows explicit relationships to file and line locations. Both lanes merge into one lavender verification bar at the bottom.

Style: clean hand-drawn educational infographic, warm cream paper, deep navy typography, rounded cards, small developer-oriented icons, slightly imperfect lines but strong alignment. Friendly and professional, not cartoon marketing.

Required visual content:
Left lane: user task → Coding Agent → search by name → three branches: too many results, ambiguous same-name symbols, missed structural relationship → warning that the change may be incomplete.
Right lane: user task → Coding Agent → query code graph → a visible network with Class, Method and Interface nodes; edges labeled calls, implements and extends → exact file and line cards → inspect affected locations.
Bottom shared bar: both approaches still go through Diff, Build, Test and Verifier. Make this shared boundary visually prominent.

All visible text must be rendered verbatim in Simplified Chinese except the listed technical terms. Use only the following text; do not invent extra captions:
Title: “Coding Agent 如何找到真正该改的代码”
Subtitle: “文本搜索找名称；语义代码图找关系”
Shared labels: “用户任务”, “Coding Agent”
Left heading: “文本搜索：按名称找候选”
Left labels: “搜索名称”, “结果太多”, “同名异义”, “漏掉结构关系”, “修改可能不完整”
Right heading: “语义代码图：沿关系找位置”
Right labels: “查询代码图”, “Class”, “Method”, “Interface”, “calls”, “implements”, “extends”, “文件 + 行号”, “检查受影响位置”
Bottom heading: “导航之后仍要验证”
Bottom labels: “Diff”, “Build”, “Test”, “Verifier”
Bottom takeaway: “代码图提供导航，不替代测试与验证。”

Constraints: exact text; no misspellings; no garbled Chinese; no logos; no watermarks; no social handles; no brand names; no claim of perfect coverage; no “绝不遗漏”; no “一定正确”. Do not imply that code graphs replace text search entirely. Maintain balanced comparison and enough whitespace for web readability.
