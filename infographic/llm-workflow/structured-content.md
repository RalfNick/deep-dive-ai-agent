# 大模型如何工作

## Overview

从一段文本开始，沿着 Tokenization、Embedding、Transformer 和概率生成四个阶段，看到模型怎样逐个生成 Token。

## Learning Objectives

读者将理解：

1. 文本怎样变成模型可计算的表示；
2. Transformer Block 怎样读取和变换上下文；
3. 为什么输出一个 Token 后还要重新循环。

---

## Section 1: 文本变成数字

**Key Concept**: 自然语言必须先经过 Tokenizer，再由 Embedding 转为连续向量。

**Content**:

- “神经网络处理数字。自然语言进入模型前，必须先经过 Tokenizer。”
- “Token ID 只是词表里的编号。”
- “模型会通过 Embedding 表，把每个离散 ID 映射为一个高维向量。”

**Visual Element**:

- 输入句子卡片：“Agent 会使用工具”
- Token 卡片：“Agent”“会”“使用”“工具”
- Token ID 小方块与二维向量网格

**Text Labels**:

- Headline: “1 文本 → Token”
- Labels: “输入文本”, “Tokenizer”, “Token ID”, “Embedding + 位置”

---

## Section 2: Transformer 反复处理上下文

**Key Concept**: Attention 在位置之间读取信息，FFN 在每个位置内部变换信息。

**Content**:

- “注意力决定‘从其他位置读什么’，前馈网络决定‘读到之后怎样变换’。”
- “残差连接让新信息与原表示相加，归一化帮助深层网络稳定训练。”
- “数十层 Block 反复执行，浅层局部模式逐渐组合成更适合当前预测的表示。”

**Visual Element**:

- 堆叠的 Transformer Block × N
- Block 内部四块：因果自注意力、残差 + 归一化、前馈网络、残差 + 归一化
- 少量位置连线表示只能读取可见前文

**Text Labels**:

- Headline: “2 Transformer Block × N”
- Labels: “因果自注意力”, “从前文读取信息”, “前馈网络”, “逐位置变换”, “残差 + 归一化”

---

## Section 3: 从表示到概率

**Key Concept**: 最后一个位置的隐藏表示被映射为词表 Logits，再变成概率分布。

**Content**:

- “最后一层得到当前位置的隐藏向量后，模型把它投影到词表大小的 Logits。”
- “Softmax 将 Logits 转成概率。”

**Visual Element**:

- 立体表示层 → Linear → Logits → Softmax
- 三根概率柱：“读取”“调用”“删除”
- 高亮被选择的候选

**Text Labels**:

- Headline: “3 预测下一个 Token”
- Labels: “隐藏表示”, “Linear”, “Logits”, “Softmax”, “概率分布”, “选择 / 采样”

---

## Section 4: 自回归循环

**Key Concept**: 选出的 Token 被追加到上下文，然后模型再预测一步。

**Content**:

- “模型选出一个 Token 后，整个过程重新开始。这就是自回归生成。”
- “模型每次只前进一步；连贯文本来自同一计算被自回归地重复执行。”

**Visual Element**:

- 橙色 Token 卡片被追加到输入序列
- 粗回环箭头返回第一阶段
- 小型停止标志：结束 Token / 长度 / 工具调用

**Text Labels**:

- Headline: “4 追加并重复”
- Labels: “追加到上下文”, “再次预测”, “停止条件”

---

## Data Points (Verbatim)

### Key Terms

- “Decoder-only”
- “Token ID”
- “Embedding + 位置”
- “Transformer Block × N”
- “词表 Logits”
- “概率分布”
- “下一个 Token”

---

## Design Instructions

### Style Preferences

- 暖白纸张背景，深蓝主标题
- 蓝、绿、紫、橙四阶段色；圆角卡片、轻手绘线条与干净图标
- 标题清晰，正文标签短，不使用小段落

### Layout Preferences

- 3:4 纵向构图
- 四个编号阶段从上到下推进，中间对 Transformer Block 做一次放大
- 用明显回环箭头把第 4 阶段连回第 1 阶段

### Other Requirements

- 中文标签必须逐字准确
- 不出现品牌 Logo、水印、账号和英文宣传语
- 不把 Attention 画成读取未来 Token
