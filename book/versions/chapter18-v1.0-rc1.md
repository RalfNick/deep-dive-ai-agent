# 第18章 v1.0-rc1 本地候选记录

日期：2026-10-01（Asia/Shanghai）。分支：`codex/chapter18-multi-agent-final-system`。本章为《Multi-Agent 与最终系统：不是 Agent 越多越好》。本轮只形成完整本地候选，不推送、不合并、不创建tag/PR、不部署，不生成翻译、PDF或EPUB。

## 冻结与历史保护

- 书籍基线：`c2cd958912a5a2c0f750ef31617927c694903979`，Chapter17 RC3及第1–17章内容不改写。
- 首个完整审稿候选：`14493f92873e7e80024cfc4713641cd2aa8531e3`；包含书稿、代码、七图与预览实现，可由该提交恢复，不重写历史。
- 审稿修复内容点：`e95b211936615dd2e62028e4e52f8e731ef981f2`。最终冻结点是本记录所在的本地提交；不创建公开tag。
- [审稿前九文件](../../chapter18/reports/reference-rc1/manifest.json)原字节保留。它是旧候选的证据，不作为当前强化语义门禁的通过包。[当前冻结九文件](../../chapter18/reports/reference-rc1-reviewed/manifest.json)另存新目录，正文链接以此为准。
- `book/manifest.json` 保持 `0.14.0`，第18章为planned，不加入公开导航或站点allowlist。只追加版本账、修正AGENTS本地状态与对应迁移账派生值，不回填旧章记录。

## 交付规模与内容

正文24,021个叙述汉字、37,777个Markdown字符、33个二/三级标题、七幅原创SVG、五张比较表、五组实验与13道分层练习。叙述口径排除代码块及标题、表格、图引用、脚注定义行，不把代码和资料列表凑成正文长度。

四幕依次解释任务是否值得拆、上下文与控制权、失败后的协作边界、知识/修复两条最小路径。实验包自包含、运行时使用Python标准库；固定策略产生决策，结果从实际资料/文件/可信测试观察构造。20个案例是机制合同验证，不能推断模型能力或SDK排名。

默认总额度16内含验证保留2，所有Worker共享14；子任务可以进一步限制自身和后代的行动额度。真实修复有读取、提案、批准、单写者提交、4项可信测试和独立行为探针。取消保留已执行回执，旧补丁明确拒绝，缺项、冲突、权限拒绝和预算耗尽分别记录。

本地包：`chapter18/`；正文：`book/chapter18.md`；图：`book/images/chapter18/`；可编辑源：`infographic/chapter18/`；来源：`book/sources/chapter18-sources.md`；[十三题答案](../../chapter18/reference-answers.md)；[双视角与独立审稿处理](../reviews/chapter18-review-codex-v1.0-rc1.md)。

## 环境与实际验证

复用已有Windows环境：Python3.11.15、pytest9.0.2、jsonschema4.26.0、Markdown3.10.2、Node24.15.0、Playwright1.62.1、MkDocs1.6.1、tldraw6.0.2和既有Edge。没有安装模型、SDK、容器或新依赖；没有读取模型密钥、调用Provider或执行Docker。只在资料核对阶段访问官方文档及论文，实验离线。

| 检查 | 实际方法与结果 |
| --- | --- |
| 一次独立审稿 | 全正文与主要代码只读审稿；独立席实际运行40项合同/上下文/证据/预算/Runtime测试，无Critical，5项Important和1项Minor。随后作者一次修复，不声称第二次独立复审 |
| 失败先行 | 五项核心发现的12个回归修复前全部失败；修复后完整100项通过。额外嵌套预览路径1项RED→GREEN；新增夹具收集问题也单独RED→GREEN |
| 本章 | `.venv-chapter15/Scripts/python.exe -B -m pytest chapter18/tests -q`：101通过，一次完整运行14.70秒；包括真实可信文件与子进程验证，不是仅检测文本 |
| 相关矩阵 | 同解释器 `pytest chapter15/tests chapter16/tests chapter17/tests tests -q`：348通过、93子测试通过。范围明确，不称全书全部测试 |
| 报告 | `python -B -m chapter18.experiments --group all --output chapter18/.runs/final-c` 与新目录final-d；九文件各自与当前冻结包逐字节一致；旧final-a/b不覆盖 |
| 独立答案 | `python -B -m chapter18.exercise_solutions --all --output chapter18/.runs/answers-final-c.json` 与final-d；两份与冻结exercise-results.json字节一致，共13题 |
| Schema/语义 | Draft2020-12结构校验；报告校验同时要求接纳、唯一提交、生产者身份、前后摘要、最终验证事件/调用数/证据关联。删除事件、全部轨迹或错配摘要/身份均拒绝 |
| 插图 | 七份tldraw源由现有6.0.2导出；七SVG实际浏览器渲染，文本包围盒都在1600×960画布内；作者逐幅查看，无生成式图片文字 |
| 桌面/手机 | `python -B -m chapter18.preview`、`node book/check_chapter18_preview.mjs`；1440×1000和390×844均七图/五表，图片本地加载；失效锚点、页面错误、远程请求与整页横向溢出均0。手机图内滚动，标题行无单字孤行 |
| Node合同 | `npm --prefix book test`：4通过、0失败 |
| 公开清单构建 | `python -B scripts/build_site.py --root . --output chapter18/.runs/site-sources-rc1`：218份源。以忽略目录内临时继承配置运行 `python -B -m mkdocs build --strict --config-file chapter18/.runs/mkdocs-rc1.yml`：exit0，最终复验1.23秒；没有第18章公开源，不覆盖原_web/site |
| 安全与历史 | `python -B scripts/check_repository.py --root . --git-history`：exit0；迁移账合同通过，精确旧文件差异为空，`git diff --check`无错误。在清理本次临时构建物后用原规则复验，不新增扫描豁免 |

### 未通过的整库检查，不能省略

实际运行根目录 `.venv-chapter15/Scripts/python.exe -B -m pytest -q`，**15项收集错误、exit2**：

- 第1章 `test_experiment_report.py`、`test_sampling_bigram.py`、`test_token_attention.py` 缺NumPy。
- 第9章 `test_experiments.py`、`test_mcp_app.py`、`test_report_reproducibility.py` 缺MCP。
- 第12章 `test_agents_sdk.py`、`test_langgraph.py` 缺Agents SDK；`fixtures/link-checker/tests/test_existing.py` 缺根目录下src导入环境。
- 同名模块冲突：第11章 `test_exercise_solutions.py`、`test_experiments.py`，第12章 `test_experiments.py`、`test_preview.py`，第13章 `test_experiments.py`，第4章 `test_runtime.py`。

这些与Chapter17 RC3基线一致，未在本轮额外安装或修改旧章。作者修复的是本章新增夹具被误收集的问题，限定排除本章夹具，不豁免普通章节测试；当前没有新增第16项。

临时公开构建HTML与本地绝对路径配置被仓库源码扫描器读到时，产生作者路径与站点基址链接报告；这是本轮新生成验证数据，不是要提交的源码。严格构建完成后仅清理本次两个确切构建目录与临时配置，保留读者预览、规范报告、实验复现结果和历史内容，再运行原检查，不放宽规则。

## 当前九文件 SHA-256

Schema：`chapter18.team.v1`；答案：`chapter18.exercises.v1`。所有数值从实际事件/回执派生。20案状态为answer7、blocked2、conflict2、needs_approval1、stopped3、unknown3、verified2；工具调用合计49、验证调用4、旧补丁拒绝1、重复写入0、安全违规0。不是把这些状态压成一个“成功率”。

| 文件（均在 `chapter18/reports/reference-rc1-reviewed/`） | SHA-256 |
| --- | --- |
| exercise-results.json | `fd13e2993687b93c7823191923baaf358d5db13d24c85cdee8f329aa1f69c415` |
| group-1.json | `64028cd78301cccbfbff0caafebf209d2353339220d023f6d7333648e8889b4c` |
| group-2.json | `6af1edc75827d6aa8f3433a30f9aaee98ab055dcfd27c801c569c0b3bf5d7853` |
| group-3.json | `89a78798247b77575d8a32145755969032e452e22df10ddc0ca20629f7cccf33` |
| group-4.json | `47d8ac413adaec7d97f2af267444f6bea6d8319389374c2e5f43f8d40d25019b` |
| group-5.json | `4fd074758069650675fd62fbf4074e19be4cc0ecaf5843917c5fc5d3f75668fd` |
| manifest.json | `7f48a42f78c1110bdfd3b9df346825779c7e7c699d1f637f0226921043df545e` |
| summary.md | `519966458059e4f64c7d4093364ad13928f13b165a35bc40ea3085ee9530dd57` |
| team-report.json | `21b5e3229e53ac1dd2cecfb04d6ac1bcc24f018c1f96108966b454359d9da29a` |

正文文件字节摘要：`8d613f783c688a724a9218522f1c7440545ddf22b3d7b89df86fb89f636b1aaa`。manifest中的八份payload摘要实际复核，规范包及两次fresh run一致。

## 已证明、未证明与延后项

已证明：所列确定性任务中，身份/来源/上下文、冲突与缺项、预算与停止、控制交接、授权提交与最终验收有对应边界；知识业务入口保留合格矛盾；实际修复从3/4到4/4并通过行为探针；报告缺失关键关联会拒绝；九文件与答案可复现。

未证明：真实模型更好、更便宜或更快；真实并发收益；任意自然语言蕴含；生产RAG；跨进程恢复与持久幂等；宿主/容器安全；恶意并发文件替换；验收后外部变化持续审计；真实SDK互操作与企业部署。具体全部执行裁决及代价见审稿报告。

延后小项：知识quickstart终端尚不显示逐条结论、引句和missing。完整结果在规范JSON中可见，不影响验收状态，但首次终端体验还可改善。
