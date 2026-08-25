# 第 7 章“记忆”实施计划

> 执行原则：严格按测试驱动推进；每个实现任务先写失败测试并确认失败原因，再添加最小实现。

## 任务 1：冻结公共合同

- 新建 `chapter7/memory_runtime/contracts.py`；
- 先写 `chapter7/tests/test_contracts.py`，覆盖枚举、namespace、不可变 ID、稳定时间与规范序列化；
- 实现 `MemoryCandidate`、`MemoryRecord`、`RecallQuery`、`RecallResult`、`Tombstone`、`DeletionReceipt` 和 `MemoryEvent`；
- 验证错误状态使用稳定 reason code，而不是自由文本判断。

## 任务 2：实现不可变 Store 与索引投影

- 先写并发冲突、幂等重复、版本链、namespace 隔离和 Tombstone 测试；
- 实现追加式 JSONL Event Store 与内存投影；
- 同 ID 同内容允许幂等，不同内容拒绝；
- 索引是可重建投影，不是事实主记录。

## 任务 3：实现 Write Gate

- 先写稳定偏好、显式规则、Secret、猜测、一次性授权、低价值闲聊、重复候选和冲突候选测试；
- 实现确定性候选提取夹具与 Write Policy；
- 输出 allow/reject/review 及稳定原因；
- 写入前执行 sensitivity、scope、lifetime、authority 和 conflict 检查。

## 任务 4：实现 Recall Pipeline

- 先写 namespace、权限、状态、TTL、类型、Top-K、稳定排序和噪声测试；
- 实现硬过滤与可手算评分；
- 分数拆成 task match、authority、recency、confidence，报告不只保留总分；
- 增加 Context projection，限制每条记忆进入模型的字段和长度。

## 任务 5：实现 Correct 与 Forget

- 先写 supersedes 链、并发版本冲突、过期、逻辑删除、删除后不可召回、索引陈旧和删除收据测试；
- 实现版本化修正和 Tombstone；
- 实现受控物理清理的教学接口；
- 证明旧索引不能越过主记录状态恢复已删除内容。

## 任务 6：实现五组实验与固定报告

- 构造 Coding Agent 跨任务 Fixture；
- 实现五组对照和至少四个故障注入；
- 冻结逐案例期望，不让报告生成器自证正确；
- 输出 `chapter7/reports/memory-engineering.json`、`.md` 与脱敏 `.jsonl`；
- 增加两次生成字节一致性、报告字段和 Non-claims 测试。

## 任务 7：建立来源台账与发布门禁

- 创建 `book/sources/chapter7-sources.md`；
- 收录论文、官方产品文档、作者既有文章和本地实现；
- 标记事实使用、明确不声称、核对日期与出版前复核项；
- 发布门禁检查章节长度、标题、图片、练习、答案、来源字段、本地路径、Secret、排名与 byte/Token 边界。

## 任务 8：绘制七幅原创 SVG

- 先写文件名、尺寸、XML、安全、文字可读性和来源标签测试；
- 使用统一 1200×675 画布并提供窄屏可读布局；
- 图表中的实验数字直接来自固定 JSON；
- 栅格化检查桌面与 390px 阅读效果。

## 任务 9：撰写正文与参考答案

- 按设计说明的七个递进版本写作；
- 先完成前半章最小实现，再完成治理、评估和产品映射；
- 正文逐图解释读图顺序，逐实验列出支持与不支持的结论；
- 14 题按解释、实验修改、系统设计和批判性思考分层；
- 每份答案包含预期推理、常见错误和可检查验收。

## 任务 10：接入书库

- 更新 `README.md`、`book/README.md`、`book/OUTLINE.md`、`mkdocs.yml` 和 `docs/EXPERIMENT_STATUS.md`；
- 把第 6 章末尾链接从规划改为第 7 章正文；
- 第 7 章末尾只链接第 8 章规划；
- 不生成英文或繁体正文。

## 任务 11：四视角 Review

- 读者视角：术语是否先有例子、节奏是否过密、代码能否跟上；
- AI 专家视角：边界、数据模型、评估与产品事实是否准确；
- 工程视角：并发、幂等、隔离、删除和报告复现是否可靠；
- 出版视角：图、链接、版式、练习答案与引用是否完整；
- 输出 `book/reviews/chapter7-review-codex.md`，修复 P1 和选定 P2 后复审。

## 任务 12：最终验证与发布

- 运行第 1–7 章测试和仓库级检查；
- 连续两次生成固定报告并比较 SHA-256；
- 执行 Secret、绝对路径、断链、占位符、产品排名和 byte-as-Token 扫描；
- 精确暂存文件、提交、推送；
- 等待 GitHub CI 与 Pages 成功后再宣称在线发布。
