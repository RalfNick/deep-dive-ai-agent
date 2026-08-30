---
title: "Coding Agent 如何找到真正该改的代码"
topic: "technical comparison"
data_type: "binary comparison"
complexity: "moderate"
point_count: 8
source_language: "en"
user_language: "zh"
---

## Main Topic

对比 Coding Agent 依赖文本名称搜索与沿语义代码图导航两种方式，解释代码图怎样显式提供 calls、implements、extends 等结构关系，同时保留测试与验证边界。

## Learning Objectives

读者看完后应该理解：

1. 文本搜索为什么容易产生噪声、符号歧义与结构遗漏；
2. 语义代码图的节点、边和源码位置怎样支持结构化导航；
3. 更好的导航不等于修改正确，最终仍要构建、测试和验证。

## Target Audience

- **Knowledge Level**: 使用过 Claude Code、Codex 或其他 Coding Agent 的开发者
- **Context**: 第 11 章 Coding Agent 的代码库导航部分
- **Expectations**: 能区分文本相关性与程序结构关系，并理解二者可以组合

## Content Type Analysis

- **Data Structure**: 左右 A/B 对照，输入和 Agent 相同，只改变导航工具
- **Key Relationships**: 文本名称 → 候选匹配；代码图 → 节点和边 → 受影响位置；两边最终都进入验证
- **Visual Opportunities**: 左侧分叉的失败类型，右侧节点—边网络与精确源码位置，底部共享 Verifier

## Key Data Points (Verbatim)

- 节点：“Classes, methods, and interfaces”
- 边：“calls, implements, extends”
- 每个节点和边保留：“the exact file and line”

## Layout × Style Signals

- Content type: 两种导航方式对照 → `binary-comparison`
- Tone: 代码教学、需要亲和但不能夸大 → `hand-drawn-edu`
- Audience: 开发者 → 图标可以具体到符号、关系边、文件和行号
- Complexity: moderate → 16:9 横向，左右镜像，底部共享验证边界

## Design Instructions (from user input)

- 参考推文图的直观 A/B 结构，但制作中文原创版本
- 沿用全书暖白、深蓝和柔和彩色卡片视觉系统
- 右侧不能写“绝不遗漏”或暗示代码图替代测试
- 暂作为第 11 章素材，不插入概念不匹配的已发布章节

## Recommended Combinations

1. **binary-comparison + hand-drawn-edu** (Recommended): 与用户参考的阅读体验一致，适合解释三个失败和结构关系
2. **binary-comparison + bold-graphic**: 对比更强，但容易变成营销海报
3. **comparison-matrix + corporate-memphis**: 信息更规范，但过程感与直观性较弱
