# Coding Agent 如何找到真正该改的代码

## Overview

同一个任务、同一个 Coding Agent，只改变代码导航方式：左侧按名称搜索，右侧沿程序结构关系导航，最后都必须进入验证。

## Learning Objectives

读者将理解：

1. 文本搜索的三类典型失效；
2. 语义代码图怎样回答结构问题；
3. 导航结果为什么仍需测试和 Verifier。

---

## Section 1: 文本搜索

**Key Concept**: 名称匹配能找到候选，但需要 Agent 自己从文本结果中重建程序关系。

**Content**:

- 同名结果很多，需要逐个判断；
- 同名符号可能含义不同；
- 没有共享查询词时，结构连接可能被漏掉。

**Visual Element**:

- 用户任务 → Coding Agent → 搜索框 → 三个分叉漏斗
- 分叉分别表示：结果太多、符号歧义、漏掉结构连接
- 汇合到“修改不完整？”警告卡

**Text Labels**:

- Headline: “文本搜索：按名称找候选”
- Labels: “搜索名称”, “结果太多”, “同名异义”, “漏掉结构关系”, “修改可能不完整”

---

## Section 2: 语义代码图

**Key Concept**: 类、方法和接口成为节点，调用、实现和继承成为显式的边，并保留源码位置。

**Content**:

- 节点：Classes、methods、interfaces；
- 边：calls、implements、extends；
- 节点和边保留 exact file and line。

**Visual Element**:

- 用户任务 → Coding Agent → 查询代码图
- 中央网络包含 Class、Method、Interface 节点和 calls、implements、extends 边
- 网络输出一组文件与行号卡片，再进入“检查所有受影响位置”

**Text Labels**:

- Headline: “语义代码图：沿关系找位置”
- Labels: “查询代码图”, “Class”, “Method”, “Interface”, “calls”, “implements”, “extends”, “文件 + 行号”, “检查受影响位置”

---

## Section 3: 共同的完成边界

**Key Concept**: 导航解决“去哪里看”，验证解决“修改是否真的完成”。

**Content**:

- 找到连接位置不等于修改正确；
- 修改仍需差异检查、构建、测试和 Verifier。

**Visual Element**:

- 左右两路在底部汇合到一个验证台
- 验证台有 diff、build、test、Verifier 四个检查章

**Text Labels**:

- Headline: “导航之后仍要验证”
- Labels: “Diff”, “Build”, “Test”, “Verifier”
- Takeaway: “代码图提供导航，不替代测试与验证。”

---

## Design Instructions

### Style Preferences

- 暖白背景、深蓝标题；左侧薄荷绿，右侧浅蓝，底部验证区使用淡紫
- 轻手绘教育风，图标具体、连线清楚

### Layout Preferences

- 16:9 左右镜像对比，中间竖向分隔
- 两侧起点一致，突出只改变导航方式
- 底部汇合到共同 Verifier

### Other Requirements

- 中文准确；英文字段仅保留 Class、Method、Interface、calls、implements、extends、Diff、Build、Test、Verifier
- 不出现原作者品牌、网站、水印或社交账号
- 不使用“绝不遗漏”“一定正确”等绝对结论
