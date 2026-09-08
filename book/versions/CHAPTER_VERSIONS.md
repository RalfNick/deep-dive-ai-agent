# 《深入浅出 AI Agent》章节版本记录

本书采用“稳定入口 + Git tag + 版本化预览”的方式保留历史。

- `book/chapterN.md`、`chapterN/` 与 `book/images/figN-*` 始终指向该章最新版本；
- 每个正式版本使用 annotated tag `book-chapterN-vMAJOR.MINOR` 保存完整源码；
- `output/pdf/chapterN-preview.pdf` 是最新预览，历史 PDF 保存到 `output/pdf/versions/chapterN/`；
- 结构重写或读者路径不兼容时增加主版本，修正、扩充和实验增强时增加次版本；
- 已发布 tag 和历史 PDF 不覆盖、不改写。若发现旧版错误，在新版本记录中说明。

## 恢复与比较

### 2026-09-07 第八章 v1.4：证据边界与读者路径复审

由 v1.4-rc2 通过发布门禁后转为正式版本，使用 annotated tag `book-chapter8-v1.4` 固定完整源码。完整前版基线为 `49d185efd2b5463cd6962d45ac1d13d8a7710d22`；此前 editorial-v1 候选记录和公开 tag 均保留。

- 修正 Chunk 继承整篇 fact_ids：显式人工引句标注，只让完整包含引句的片段支持事实；无标注不覆盖。
- 重排后再次验证资格与父摘要；新增重排期间撤回、原文更新配旧索引、SSO 段缺成员事实等失败先行测试。
- 正文 v0—v7 改为教学阶段，核心接口与实现一致；标准答案、冲突解析与自然语言验真的交付边界写明。
- 新增 inspect_request 入口，完整请求移至 v7 后；生产清单移至 chapter8/production-guide.md。有效中文约 2.28 万，字数门槛对齐写作指南的 1.8 万。
- 报告 schema_version=2，单查询 mrr 更名 reciprocal_rank；图 8-5、8-8 新增 v2 SVG，原图保留。

回归记录见[第八章本轮复审](../reviews/chapter8-review-v1.4-rc2.md)。比较命令：`git diff 49d185e -- book/chapter8.md chapter8/`。

### 2026-09-07 全书读者路径修订：editorial-v1

本轮以 annotated tag `book-editorial-v1` 发布到 GitHub 与网站。修改前完整基线为 `46be2bbca32dde80abadff65f20884407441859d`（已发布的 `book-chapter9-v1.0.3`）；该提交保存本轮修改前的全书、实验、来源与旧图。旧 tag 不移动。

| 章节 | 编辑候选版本 | 本轮变化 |
| --- | --- | --- |
| 1 | editorial-v1 | 新主图以候选表对应 Logit / Softmax；采样项与追加项一致；原 WebP 保留 |
| 2 | editorial-v1 | 沿用 float 验收，产品观察标为进阶；保留原事实核对日期 |
| 3 | editorial-v1 | 收束生产清单，以四个闭环问题衔接第四章 |
| 4 | editorial-v1 | 开场改为审批中断与恢复，突出本章区别于最小循环的职责 |
| 5 | editorial-v1 | 先装小输入，再读完整字段；后移实验合同；说明教学优先级的适用边界 |
| 6 | editorial-v1 | 任务卡先行，七类状态后移，Artifact 字段标为进阶 |
| 7 | 不变 | 本轮保留偏好生命周期主线，不为统一形式改写有效内容 |
| 8 | v1.4 | 实事求是说明 Embedding 适配器未交付，删重，补 BM25/RRF 完整答案与核对命令；随后由 rc2 修正证据边界并正式发布 |
| 9 | editorial-v1 | 22 个 FAQ 移到配套材料，下一章名与目录一致；字数下限对齐全书写作标准 |

候选阶段的验证记录见[本轮 Review](../reviews/editorial-review-2026-09-06.md)。原 RC 名称只标识发布前稿；正式发布由 `book-editorial-v1` 与 `book-chapter8-v1.4` 固定，未生成新版 PDF。

查询旧稿示例：`git show 46be2bbca32dde80abadff65f20884407441859d:book/chapter5.md`。比较时对同一路径运行 `git diff 46be2bbca32dde80abadff65f20884407441859d -- book/chapter5.md`。

### 已有版本的恢复方式

只查看某版正文：

```powershell
git show book-chapter1-v1.0:book/chapter1.md
```

临时查看该版完整工程：

```powershell
git switch --detach book-chapter1-v1.0
```

比较两个版本：

```powershell
git diff book-chapter1-v1.0 book-chapter1-v1.1 -- book/chapter1.md chapter1
```

查看结束后切回工作分支，不要在 detached HEAD 上直接提交。

## 第 1 章：大模型入门

| 版本 | 日期 | Git tag | 状态与主要变化 | 自动验证 | PDF |
| --- | --- | --- | --- | --- | --- |
| v1.0 | 2026-08-13 | `book-chapter1-v1.0` | Review 前基线；保留原正文、6 张图、5 个实验与参考答案 | 5 个脚本与编译检查通过；独立测试 `0 discovered` | `output/pdf/versions/chapter1/chapter1-v1.0.pdf`，42 页，SHA-256 `64778C17C2601EC6B15508EBCB9B9B633524943FDBDB866B210A1E18C0FE437A` |
| v1.1 | 2026-08-13 | `book-chapter1-v1.1` | 按 Codex Review 完成证据收口、技术纠错、实验报告、独立测试、引用与练习答案增强 | 9 项独立测试通过；5 个实验与报告生成通过；SVG、链接和脚注静态检查通过 | `output/pdf/versions/chapter1/chapter1-v1.1.pdf`，43 页，SHA-256 `CC2DA449EA45ABED88921E91E0A7B0E06658954C2BEC0218EBD73394B9252113` |
| v1.2 | 2026-08-30 | `book-chapter1-v1.2` | 新增中文原创“大模型如何工作”主信息图，用四阶段视觉主线解释 Token、Transformer、概率生成与自回归循环；原 6 张 SVG 技术图和正文机制说明全部保留 | 第 1 章 10 项测试、仓库 41 项合同测试、4 项渲染测试与 MkDocs strict 构建通过；WebP 主图约 224 KiB | 未生成独立 PDF；网站与 Git tag 为本次发布载体 |

## 第 3 章：从生成到闭环执行

| 版本 | 日期 | Git tag | 状态与主要变化 | 自动验证 | PDF |
| --- | --- | --- | --- | --- | --- |
| v1.0 | 2026-08-14 | `book-chapter3-v1.0` | Review 前基线；保留原正文、7 张图、5 个编号实验与 1 个 Trace 补充实验 | 6 项旧测试通过；Review 的 4 个反例可复现 | `output/pdf/versions/chapter3/chapter3-v1.0.pdf`，28 页，SHA-256 `D259D6B8207D334E209AD7B42432EE9953960F4E67F82DFF6F0C89C20F7400F6` |
| v1.1 | 2026-08-14 | `book-chapter3-v1.1` | 按 Codex Review 完成 Observation 驱动策略、结构化 Verifier、Trace 审计、超时与幂等失败注入、框架事实复核、答案与排版修订 | 19 项 Python 测试、6 个实验脚本、4 项渲染门禁测试通过；30 页 PDF 全页目检通过 | `output/pdf/versions/chapter3/chapter3-v1.1.pdf`，30 页，SHA-256 `3E2E6319B17B0A972FEEB4A8172E74D2EAD55FC2FCB70A91230EC882DFEEE54D` |

## 第 5 章：上下文工程

| 版本 | 日期 | Git tag | 状态与主要变化 | 自动验证 | PDF |
| --- | --- | --- | --- | --- | --- |
| v1.0 | 2026-08-16 | `book-chapter5-v1.0` | 首个复审发布版；包含 ContextItem、SourcePolicy、Context Builder、Context Packet、五组边界实验、7 张原创图、14 道分层练习与双视角 Review | 第 5 章 50 项及第 4 章 24 项 Python 测试、4 项渲染门禁通过；28 变体报告二次生成 SHA-256 一致；SVG、链接、敏感信息与 P1 静态检查通过；35 页 PDF 全页目检通过 | `output/pdf/versions/chapter5/chapter5-v1.0.pdf`，35 页，SHA-256 `1F63F6FF87F3AB4DCAD493DE49731C1CEFB1A55F82EBC80C2604E7DDEBEC9CD4` |
| v1.1 | 2026-08-16 | `book-chapter5-v1.1` | 按独立 Review 完成练习答案同步、真实 Grader 门禁、结构化缺 Key 报告、预算语义重构、冲突矩阵扩展及工具协议证据收口；v1.0 不改写 | 第 5 章 63 项及第 4 章 24 项 Python 测试、4 项渲染门禁通过；30 变体报告二次生成 SHA-256 一致；链接、15 脚注、7 SVG、凭据与旧 P1 静态检查通过；36 页 PDF 全页目检通过 | `output/pdf/versions/chapter5/chapter5-v1.1.pdf`，36 页，SHA-256 `2843EF79D820A4EC3B18FFDA1DD1EC73CD598160301FDEDE291AD37460C50874` |

## 第 6 章：长任务中的上下文架构

| 版本 | 日期 | Git tag | 状态与主要变化 | 自动验证 | PDF |
| --- | --- | --- | --- | --- | --- |
| v1.0 | 2026-08-17 | `book-chapter6-v1.0` | 首个正式发布版；包含 Event Log、Working Set、CompactionArtifact、RunCheckpoint、Context Rehydration、五组确定性实验、失败矩阵、7 张原创图、14 道分层练习与四视角 Review；保留 `chapter6-v1.0-draft`。后续复核发现第 23 页独立粗体段首、第 45 页小结孤行，以及 PDF 内 16 个作者本机文件链接，已由 v1.0.1 修复；本版标记为 superseded，历史文件与 tag 不改写 | 第 4/5/6 章分别 24/63/140 项 Python 测试及 5 项渲染门禁通过；15-case JSON、Markdown、JSONL Trace 两次生成 SHA-256 一致，分别为 `50CBBC74C8D938D619DAB131F8D37BBB8443162C1FEA74233C90FD6EB3686E5E`、`F05FBA8F7A4EF7177EA7FE1B1FA18F8CC7528BD9D806D0FEEB1AFF86F87CE107`、`CBCC12216DF02182D9E5B4F64A3A1B29EF9554140877E33CBC986FE69604EB96`；7 SVG 的 XML、安全、桌面与 390px 响应式门禁通过；47 页 PDF 全页目检通过 | `output/pdf/versions/chapter6/chapter6-v1.0.pdf`，47 页，SHA-256 `211B722B74715C0C139BE4E70266327348DCF2833C61648E055AB8B30D072C1E` |
| v1.0.1 | 2026-08-17 | `book-chapter6-v1.0.1` | 当前发布版；合并第 23 页独立粗体段首，收束小结以消除第 45 页孤行；发布 HTML 不再嵌入 `<base>`、作者本机样式或脚本路径，仓库内链接改为不可点击的可移植引用，图片使用相对路径；PDF 只保留 10 个外部 HTTPS URI，作者本机 URI 为 0 | 第 4/5/6 章分别 24/63/143 项 Python 测试及 5 项 Node 渲染门禁通过；新增 HTML 搬迁语义、PDF annotation URI 和历史 PDF 保留测试；15-case JSON、Markdown、JSONL Trace 两次生成及 canonical SHA-256 仍分别为 `50CBBC74C8D938D619DAB131F8D37BBB8443162C1FEA74233C90FD6EB3686E5E`、`F05FBA8F7A4EF7177EA7FE1B1FA18F8CC7528BD9D806D0FEEB1AFF86F87CE107`、`CBCC12216DF02182D9E5B4F64A3A1B29EF9554140877E33CBC986FE69604EB96`；47 页替代 PDF 全页目检通过，最终渲染与已目检页面逐页像素一致 | `output/pdf/versions/chapter6/chapter6-v1.0.1.pdf`，47 页，SHA-256 `15B08A2679710CE06E0115C46A9457648F782215448F8B03BC28FADF42C73000`；稳定预览与版本 PDF 字节一致 |

## 第 8 章：RAG 与知识库

| 版本 | 日期 | Git tag | 状态与主要变化 | 自动验证 | PDF |
| --- | --- | --- | --- | --- | --- |
| v1.0 | 2026-08-28 | `book-chapter8-v1.0` | 首个网站发布版；包含 v0—v7 主线、18 篇虚构文档、20 个确定性案例、8 张原创图、14 道练习与四视角 Review；后续复审发现状态预期与实际结果未分流、两条拒答夹具合同不完整、Precision@K 口径不一致，由 v1.1 修复 | 56 项第 8 章测试通过；三份规范报告可重复生成；CI 与 Pages 发布成功 | 未生成独立 PDF；历史正文、代码与网站源文件由 Git tag 固定 |
| v1.1 | 2026-08-28 | `book-chapter8-v1.1` | 当前优化版；补齐无答案 fact 合同和 Partial 事实集合，区分 10 个符合性案例与 3 个失败探针，新增状态分类与摘要，统一唯一文档/固定 K 指标口径，同步报告、Trace、图 8-8、正文、来源和 Review | 60 项第 8 章测试通过；JSON、Markdown、JSONL SHA-256 分别为 `FA711B9F6203D97602612C8A017B82FC6B275E5CF02083F4981837D2236317EB`、`2D53AE220A48466701D9DFA2B507E3D6339DB6AACEB8CDC588CE1927C099259A`、`A6C6BA9F668173A1C3A9DBFC4246A2402ACA127D261C6B2D1C80EB9B38F18C9C` | 未生成独立 PDF；网站为本章当前发布载体 |
| v1.2 | 2026-08-29 | `book-chapter8-v1.2` | 加入检索前知识加工、派生问答与 Source Chunk 的来源边界，补充二值量化适用条件，并据此优化主流程、实验边界与图 8-2 | 第 8 章 61 项测试与规范报告复现通过；GitHub CI、Pages 和 `wlxralf.com` 发布成功 | 未生成独立 PDF；历史正文、代码与网站源文件由 Git tag 固定 |
| v1.3 | 2026-08-30 | `book-chapter8-v1.3` | 新增中文原创“RAG 如何工作”主信息图，用离线知识加工、在线证据回答和四道责任边界建立第一遍阅读路线；原 8 张 SVG 技术图全部保留 | 第 8 章 61 项测试、仓库 41 项合同测试、4 项渲染测试与 MkDocs strict 构建通过；WebP 主图约 206 KiB | 未生成独立 PDF；网站与 Git tag 为本次发布载体 |
| v1.4 | 2026-09-07 | `book-chapter8-v1.4` | 修正 Chunk 事实继承边界和重排后的资格、父摘要回查；统一 reciprocal_rank 口径；新增真实请求检查入口并将生产扩展移到独立指南；同步全书读者路径编辑版 | 第 8 章 71 项、仓库 43 项合同测试及 4 项渲染测试通过；其他已发布章节 372 项回归通过；规范报告可重复生成，MkDocs strict 构建通过 | 未生成独立 PDF；网站与 Git tag 为本次发布载体 |

## 第 9 章：工具调用与 MCP

| 版本 | 日期 | Git tag | 状态与主要变化 | 自动验证 | PDF |
| --- | --- | --- | --- | --- | --- |
| v1.0 | 2026-09-01 | `book-chapter9-v1.0` | 首个正式发布版；包含 v0–v6 渐进主线、8 幅原创手绘图、5 组 20 个确定性案例、14 道练习、来源台账与双视角 Review | 第 9 章 46 项测试、仓库发布检查与 MkDocs strict 构建通过 | 未生成独立 PDF；网站与 Git tag 为本章发布载体 |
| v1.0.1 | 2026-09-01 | `book-chapter9-v1.0.1` | 发布扫描热修版；仓库级安全检查忽略本地 Worktree，避免把工程工作目录误判为待发布内容；正文和实验结论不变 | 新增 Worktree 扫描回归测试；标签与 v1.0 指向同一最终发布提交 | 未生成独立 PDF；历史由 Git tag 固定 |
| v1.0.2 | 2026-09-04 | `book-chapter9-v1.0.2` | 复审优化版；修正旧版 MCP 握手方向和 Function Calling / Runtime / MCP 架构关系；统一“三份调用合同 + 一份写操作回执”的语义；为三个 Tool 落实 Output Schema 及运行时验证；增加阅读路线、版本冻结点和一个输出合同失败实验；旧图、旧 Review 与旧 tag 均保留 | 第 9 章 47 项测试；规范报告 21 个 Case，其中 20 个 Runtime Observation、1 个 Specification Fixture；仓库发布检查与 MkDocs strict 构建通过 | 未生成独立 PDF；网站与 Git tag 为本章发布载体 |
| v1.0.3 | 2026-09-04 | `book-chapter9-v1.0.3` | 当前发布元数据热修版；正文、代码、报告和插图与 v1.0.2 相同；修正 `book/manifest.json` 中全书更新时间、第 9 章更新时间和仍写作“四份工具合同”的旧摘要，增加回归断言，确保独立博客同步后不会继续显示旧口径 | 第 9 章 47 项测试；仓库 42 项合同测试；发布安全检查与 MkDocs strict 构建通过 | 未生成独立 PDF；网站与 Git tag 为本章发布载体 |

## 第 10 章：大规模工具集与异步任务

| 版本 | 日期 | Git tag / 保存位置 | 状态与主要变化 | 自动验证 | PDF |
| --- | --- | --- | --- | --- | --- |
| v1.0-rc1 | 2026-09-07 | `codex/chapter10-tools-async-v1` 候选分支，候选提交 `b11240b`、交接提交 `a51511f` | 首个完整写作候选；约 2 万中文字符、6 幅原创手绘图、5 组标准库实验、14 道练习与答案、官方来源和自审；保留第 1–9 章全部正文、旧图和 tag，未覆盖公开版本 | 37 项章节检查（36 项运行/解答，1 项可选 HTML 预览）；双连接领取、事务失败回滚、规范报告复现；不含真实模型、外部 SDK 或分布式 exactly-once | 未生成或发布 PDF/EPUB |
| v1.0 | 2026-09-08 | `book-chapter10-v1.0` | 首个正式发布版；正文与候选主线不变，补齐发布清单、网站导航、实验状态、版本恢复入口和 CI 合同；v1.0-rc1 候选提交继续保留 | 第 10 章 37 项检查、仓库合同、已发布章节回归、4 项 Node 排版合同、规范报告复现、发布安全检查与 MkDocs strict 构建通过 | 未生成独立 PDF；网站与 Git tag 为本章发布载体 |

v1.0-rc1 是正式发布前的冻结候选，未单独创建 tag；其两个提交仍可从 Git 历史恢复。v1.0 只增加发布所需元数据、导航和门禁，不重写候选提交。第十章未生成或发布 PDF/EPUB。

## 后续章节发布规则

其他章节首次纳入版本管理时，先按当时状态建立 `v1.0` 基线并生成版本化 PDF，再开始 Review 修订。任何正文、配套代码、练习答案、资料台账或图示发生实质变化，都必须在本文件新增版本记录；不能先覆盖旧版、事后再猜测历史内容。
