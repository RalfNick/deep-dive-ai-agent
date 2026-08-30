---
title: "大模型如何工作"
topic: "scientific-educational"
data_type: "process and structural breakdown"
complexity: "complex"
point_count: 5
source_language: "zh"
user_language: "zh"
---

## Main Topic

用一张纵向信息图解释 decoder-only 生成式大模型怎样把文本变成 Token 和向量，怎样通过重复的 Transformer Block 得到词表概率，并通过自回归循环逐个生成 Token。

## Learning Objectives

读者看完后应该理解：

1. 文本、Token ID、Embedding 和上下文化表示不是同一种东西；
2. Attention、FFN、残差与归一化在 Transformer Block 中承担不同职责；
3. 模型输出的是下一个 Token 的概率分布，连贯文本来自循环生成。

## Target Audience

- **Knowledge Level**: 大模型初学者
- **Context**: 阅读第 1 章时建立全局心智模型
- **Expectations**: 不先背公式，也能顺着数据流讲出一次生成过程

## Content Type Analysis

- **Data Structure**: 四阶段主流程，Transformer Block 是中间的局部结构展开，自回归形成回环
- **Key Relationships**: 文本依次转为离散 ID、连续表示、上下文化表示和词表概率；选出的 Token 回到输入
- **Visual Opportunities**: Token 卡片、向量网格、Attention 连线、堆叠 Block、概率柱形图与回环箭头

## Key Data Points (Verbatim)

- “文本 → Token ID → Embedding + 位置 → N 个 Transformer Block → 词表 Logits → 概率分布 → 下一个 Token”
- “注意力决定‘从其他位置读什么’，前馈网络决定‘读到之后怎样变换’。”
- “模型选出一个 Token 后，整个过程重新开始。这就是自回归生成。”
- “模型每次只前进一步；连贯文本来自同一计算被自回归地重复执行。”

## Layout × Style Signals

- Content type: 高密度流程与局部结构 → `dense-modules`
- Tone: 面向初学者、技术但不冰冷 → `hand-drawn-edu`
- Audience: 需要一眼看到全局，再按编号细读 → 纵向 3:4
- Complexity: complex → 只保留四大阶段和一个局部放大，不塞入训练、KV Cache 与架构变体

## Design Instructions (from user input)

- 参考用户提供的 “How LLMs work” 图的清晰分区、编号流程和层次感，但必须中文原创，不复制原图构图、文字或品牌元素
- 暖白底、深蓝文字，蓝、绿、紫、橙分别编码四个阶段
- 让图承担解释任务，不把正文段落搬进图片
- 网站与移动端都要可读，不出现水印、账号、Logo 或宣传语

## Recommended Combinations

1. **dense-modules + hand-drawn-edu** (Recommended): 最接近用户期望的“分区大图”，同时保留初学者友好感
2. **structural-breakdown + technical-schematic**: 技术精度更高，但容易回到现有工程图气质
3. **linear-progression + corporate-memphis**: 更简洁活泼，但 Transformer 内部结构表达会变弱
