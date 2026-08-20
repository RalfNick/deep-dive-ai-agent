# 《深入浅出 AI Agent》章节版本记录

本书采用“稳定入口 + Git tag + 版本化预览”的方式保留历史。

- `book/chapterN.md`、`chapterN/` 与 `book/images/figN-*` 始终指向该章最新版本；
- 每个正式版本使用 annotated tag `book-chapterN-vMAJOR.MINOR` 保存完整源码；
- `output/pdf/chapterN-preview.pdf` 是最新预览，历史 PDF 保存到 `output/pdf/versions/chapterN/`；
- 结构重写或读者路径不兼容时增加主版本，修正、扩充和实验增强时增加次版本；
- 已发布 tag 和历史 PDF 不覆盖、不改写。若发现旧版错误，在新版本记录中说明。

## 恢复与比较

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

## 后续章节发布规则

其他章节首次纳入版本管理时，先按当时状态建立 `v1.0` 基线并生成版本化 PDF，再开始 Review 修订。任何正文、配套代码、练习答案、资料台账或图示发生实质变化，都必须在本文件新增版本记录；不能先覆盖旧版、事后再猜测历史内容。
