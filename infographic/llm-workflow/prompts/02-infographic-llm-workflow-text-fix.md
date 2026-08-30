---
references:
  - ref_id: 01
    filename: refs/01-ref-how-llms-work.png
    usage: style
layout: dense-modules
style: hand-drawn-edu
aspect_ratio: "3:4"
language: zh
backend: imagegen
---

Use case: scientific-educational
Asset type: 第 1 章网页与电子书主信息图
Primary request: 创作一张中文原创教育信息图《大模型如何工作》，解释 decoder-only 生成式大模型从输入文本到逐个生成 Token 的完整数据流。参考图只用于学习清晰分区、编号阶段、柔和配色和视觉层级，不复制其具体构图、文字、品牌或装饰。
Input images: Image 1 is a style and information-hierarchy reference only, not an edit target.

Canvas and composition: 3:4 portrait. Warm cream paper background. Large title at top, subtitle below. Four numbered stages flow vertically from top to bottom. Each stage is a large rounded pastel card with ample spacing. A thick orange loop arrow from stage 4 returns to stage 1. Maintain strong reading order and mobile readability.

Style: hand-drawn educational infographic, clean rather than childish. Deep navy typography and outlines. Stage colors: blue, mint green, lavender, warm orange. Slight hand-drawn texture, tidy icon illustrations, soft shadows, precise alignment. No photorealism.

Required visual content:
1. Stage 1 visually shows an input sentence becoming Token cards, Token IDs, then an embedding grid with position information.
2. Stage 2 shows stacked “Transformer Block × N”. One enlarged block contains causal self-attention, residual plus normalization, feed-forward network, residual plus normalization. Attention connections only point to visible previous positions.
3. Stage 3 shows hidden representation flowing through Linear, Logits and Softmax into a small probability bar chart. Highlight one selected next Token.
4. Stage 4 shows the selected Token appended to the context and the cycle repeating. Add three tiny stopping markers for end Token, length limit, and tool call.

All visible text must be rendered verbatim in Simplified Chinese. Use only the following text; do not invent extra captions:
Title: “大模型如何工作”
Subtitle: “从输入文本到下一个 Token”
Stage 1: “1 文本 → Token”, “输入文本”, “Agent 会使用工具”, “Tokenizer”, “Token ID”, “Embedding + 位置”
Stage 2: “2 Transformer Block × N”, “因果自注意力”, “从前文读取信息”, “残差 + 归一化”, “前馈网络”, “逐位置变换”
Stage 3: “3 预测下一个 Token”, “隐藏表示”, “Linear”, “Logits”, “Softmax”, “概率分布”, “读取”, “调用”, “删除”, “选择 / 采样”
Stage 4: “4 追加并重复”, “追加到上下文”, “再次预测”, “停止条件”
Bottom takeaway: “逐个生成 · 自回归循环”

Constraints: exact Chinese typography; especially render “自回归” exactly as three Chinese characters and never insert “白” or any other character; no misspellings; no garbled characters; exactly four numbered stages; no duplicated stages; no extra English prose; no equations; no logos; no watermarks; no social media handles; no brand names. Avoid dense paragraphs and tiny unreadable text. Keep the model mechanism accurate and do not depict the LLM as directly executing tools.
