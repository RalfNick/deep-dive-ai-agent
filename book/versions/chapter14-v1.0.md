# 第 14 章 v1.0 正式发布记录

发布日期：2026-09-27。正式标签：`book-chapter14-v1.0`。发布基线：[v1.0-rc2](chapter14-v1.0-rc2.md)；rc1 与 rc2 记录不改写。

## 发布内容

- 正文《Benchmark、Tracing 与生产诊断》、24 个场景、72 条教学 Trace、7 幅图、5 组实验、14 道练习与答案；
- 用 Benchmark Card、分位数、依赖图、关键路径、用量覆盖和重试放大率建立可比测量合同；
- 用隐私转换、Head/Tail 采样、切片、支持证据、反证与消融形成可回归诊断闭环。

## 发布验证

- `python -B -m pytest chapter14/tests -q`：69 项通过；
- 两个独立输出目录的报告与练习结果逐字节一致；
- Draft 2020-12 JSON Schema、Trace/图形合同、仓库合同、发布安全检查、Node 排版合同与 MkDocs strict 构建通过。

## 证据边界

72 条 Trace、教学成本单位和固定消融不代表生产分布或真实价格。本版本没有证明任何模型、Coding Agent 或观测平台的能力高低，也没有宣称本地采样器具备生产 Collector 的容量、背压与合规能力。
