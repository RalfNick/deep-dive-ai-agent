# Chapter 8 evidence repair Implementation Plan

> 在用户已批准的 Review 范围内，于当前任务顺序执行，沿用隔离编辑副本。不另建任务、不发布。

**Goal:** 修正片段证据与最终回查，确保正文只承诺已验证能力，并减少后半章重复。

**Architecture:** 文档提供人工审核的 fact_id → 原文引句标注；Chunk 仅获得其完整包含的引句所支持的事实。最终返回在重排后回查资格与父摘要。固定答案策略保留为教学桩，不充当自然语言验证器。

**Tech Stack:** Python 标准库、Markdown、现有 MkDocs 与 SVG。

**Spec:** 用户确认的第八章 Review 六项意见。冻结基线 49d185efd2b5463cd6962d45ac1d13d8a7710d22。

## Constraints

- 旧提交、旧图和已发布 tag 保留；新稿为 v1.4-rc2 本地候选。
- 不接付费模型，不添加新的框架或真实 Embedding 实验。
- v0—v7 仅代表教学阶段，不声称对应消融组；实际实验仍是五组固定案例。

## Tasks

- [x] 在 tests/test_evidence.py 断言：只传迁移 SSO 段时 missing 为 members-preserved-32；只传执行示例时 abstain；SSO 和成员段齐全时 answer。先运行 unittest 看失败。
- [x] 在 tests/test_retrieve.py 注入重排期间撤回和旧索引配新原文，断言最终无无效命中、回查拒绝计数增加。先运行测试看失败。
- [x] contracts.py 增加 FactAnnotation(fact_id, quote) 与 KnowledgeDocument.fact_annotations；校验引句属于原文和已声明事实。catalog.py 读取显式标注；Chunk.from_document 只携带完整命中的引句事实。无标注不继承。为标注失配与切断引句增加失败先行的测试。
- [x] retrieve.py 保留重排前资格检查，并在重排后、截取 top_k 前校验当前资格与 document_digest。先过滤再截断，避免失效结果占位。
- [x] 逐篇人工标注 18 篇教学语料；运行 chapter8 全部测试。不得通过改期望状态掩盖证据减少；必要时分析真实候选与已验证事实分布。
- [x] 正文核心代码替换为实际接口，设计草图明确标注；说明标准答案、fact_id 与引句由人工提供。先回放完整请求，再给命令，生产清单移至 chapter8/production-guide.md 并从站点复制。
- [x] RR 与 MRR 分开解释，运行报告使用 reciprocal_rank 字段；同步图、答案、来源、版本台账与站点元数据。重建报告两次核对摘要。
- [x] 运行章节测试、仓库测试、渲染测试、安全检查和严格构建；记录实测结果。提交独立修订分支后同步 D 盘工程，不合并主分支、不推送。

## Verification

使用 python -B -m unittest discover -s chapter8/tests -v，并设 PYTHONDONTWRITEBYTECODE=1 与 PYTHONUTF8=1。正文不绑定措辞测试，代码示例用实际入口验证。产物由 run_all 生成，不手改统计值。
