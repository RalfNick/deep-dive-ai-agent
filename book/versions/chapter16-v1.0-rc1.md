# 第 16 章 v1.0-rc1 本地候选记录

记录日期：2026-09-29。分支：`codex/chapter16-continuous-improvement`。状态：本地候选、未发布；正文与机制修订已冻结，实际验收及记录完整性检查通过。本轮不推送、不合并、不建 tag/PR、不部署，不修改公开导航或章节 allowlist。

## 内容与环境

正文为 29,832 个字符，其中 20,024 个汉字；剔除代码块、标题、表格、脚注定义及链接目标后，叙述汉字 18,795 个。统计口径不是把代码与表格算作中文讲解。包含 14 个主节、34 个二三级标题、7 幅原创矢量图、5 张比较表、5 组实验、6 个失败样本和 13 道分层练习。

实验包括 12 条反馈、6 份作者编写的文档、16 项任务；四个切片各有一项开发任务、三项按家族隔离的留出任务。实际消费载体为知识规则、步骤技能和有作用域的记忆；提示词、Harness 与训练变化只作为改进提案，不冒充已实施能力。

验证环境为 Windows、Python 3.11.15、pytest 9.0.2、jsonschema 4.26.0、Markdown 3.10.2、Node 24.15.0、Playwright 1.62.1、MkDocs 1.6.1 与已有 Edge。复用 `.venv-chapter15` 的匹配锁定测试依赖；章节运行时仅用 Python 标准库，预览为可选依赖。未安装模型、容器或新的浏览器软件；未读取 API Key、`.env`，未调用真实 Provider。

来源核对日为 2026-09-29，台账区分产品官方动态资料与固定版本论文。产品例子用于职责映射，不是 SDK 兼容性、价格或最新功能覆盖的承诺。

## 可恢复基线与历史

| 位置 | 固定点与用途 |
| --- | --- |
| 原 Chapter 15 RC2 基线 | `2bcfaf0250fdd8dbf8b1f051bc62d576bef52875`；第 1–15 章原稿、图、来源和历史版本不改写 |
| 原第 16 章稿图与预览 | `d2b82f9b21985aa492ea0708f1cc400db4f8bfd0`；[审稿前稿图快照](chapter16-draft-before-review/README.md)保存，正文归档只修相对链接，图为原字节 |
| 自审后、独立审查对象 | `76ce9c0d3436a4a5f0e6e1b366a910f5b49649f0`；唯一 reviewer 审查到该提交 |
| 修复后最后内容提交 | `6859054bdc6e10beb08bb3161e270ef5d6477457`；四项 Important、两项 Minor 的代码/正文/答案/报告修复 |

版本记录自身及最终记录测试的提交由 Git 历史确定，不写自引用的 HEAD。更早的[练习编排前草稿](chapter16-draft-before-exercise-alignment.md)来自 `594b84cd232b8ab5866cdb50f9299e24adb54d93`，原正文 SHA-256 为 `68c6d3622d687970a3fbe0f384829d4af465318714a65f9c550c39ed333e8805`；其后来可浏览的图/代码链接不表示那些交付已经存在于该早期提交。

审稿前原正文 SHA-256 为 `f31c2cc01cddfc3b3ac96428744d20d960722f6fc47e4d7023213168caa15535`。[审稿前报告目录](../../chapter16/report-history/draft-before-review/manifest.json)保留全部九个文件原字节，旧 manifest SHA-256 为 `047c8307a62a52b56b3cc0797bf72916b09f0a22a9364ec3f5b3cd8bb88eebf8`。新报告只由程序在全新目录生成，验证后同步；没有删除旧运行目录或手改成绩。

## 已证明与未证明

已证明：在作者编写的离线夹具中，三类资产确实改变下一次有限策略运行；相关回放、来源权威、资产作用域、有序步骤、安全反例、证据内容、审批和发布历史之间的边界可被测试。正常候选的 11/16→16/16、修复三项目标只说明本实验机制符合合同。盲目覆盖控制组失败，缺失回执为未决；Unknown/环境故障不转成虚假的成功。

未证明：真实模型学习收益、泛化与统计显著性、生产身份鉴权、持久审批、自然语言反馈自动理解、任意 PII/注入防护或线上灰度安全。回放冻结工具结果，不重执行外部动作；步骤解释器不构成外部执行回执。归因是受控干预下的条件性机制假设。哈希不证明事实或授权，进程内注册表不是签名/IAM，历史快照不能恢复被撤销权限，回滚不补偿外部副作用。不存在真实 Usage 时不报告 Token 或费用。

## 命令与实际结果

以下测试命令中的 `python` 指本轮 `.venv-chapter15/Scripts/python.exe`；安全/站点命令用已有 `.venv/Scripts/python.exe`。每个命令及比较均 exit 0，输出范围为本地工程生成目录。

| 检查 | 命令/判据与已运行结果 |
| --- | --- |
| 第 16 章与仓库合同 | `python -B -m pytest chapter16/tests tests -q --tb=short`：最终 114 项、93 项子测试通过，其中章节 65 项、仓库 49 项；未混合收集其他独立依赖环境 |
| 第 15 章回归 | `python -B -m pytest chapter15/tests -q --tb=short`：128 项通过；未混合收集其他独立依赖环境 |
| 规范复现 | `python -B -m chapter16.experiments --group all --output chapter16/.runs/rc1-verified-a` 及新目录 `rc1-verified-b`：两套各九个文件与 `reports/` 逐字节相同 |
| 练习复现 | `python -B -m chapter16.exercise_solutions --all --output chapter16/.runs/rc1-exercises-a.json` 及新文件 `rc1-exercises-b.json`：与规范答案字节相同；10 个代码检查、3 个定性答案 |
| Node | `npm test --prefix book`：4 项通过 |
| 预览 | `python -B -m chapter16.preview`、`node book/check_chapter16_preview.mjs`：1440×1000 / 390×844，两端各 7 图、5 表、零失效锚点与整页横向溢出；手机宽图最小 760px、局部滚动；关键图人工查看 |
| 安全与历史 | `python -B scripts/check_repository.py --root . --git-history`：通过；真实本机 URI 与秘密扫描仍启用，未扩大精确历史豁免 |
| 公开源与构建 | `python -B scripts/build_site.py --root . --output _web`：218 份源；`python -B -m mkdocs build --strict`：通过。已有补充页 nav INFO 和主题自带告示不是本章构建失败 |
| 发布边界与旧稿 | `book/manifest.json` 仍 `0.14.0`、14 章 published、15/16 planned；`_web` 无 15/16 内容；受保护旧文件与基线 diff 为空，公开导航和 Pages 工作流未修改 |

输出目录的唯一创建、拒绝已有目录/文件、父链链接检查、有限 JSON、无离线联网或读取凭据，以及错误步骤、来源错配、回放变化、审批复用、缺失嵌套证据均在章节回归中检查。输出防护不宣称能抵御同机恶意并发文件系统变更，也不是 OS 沙箱。

## SHA-256 与验证记录

下表是实际文件字节哈希，不与报告内部内容哈希混用。

| 文件 | bytes | SHA-256 |
| --- | ---: | --- |
| `book/chapter16.md` | 74398 | `a2c1be3fe2d4e6f16593b05d6a30c73659656d1c649936d6bf204bf5c8d2aef6` |
| `book/sources/chapter16-sources.md` | 3797 | `ba1e7178455ceb5fdcb62e972d284e75de452ac549acf3fedbf310ffe0d8f783` |
| `chapter16/reports/manifest.json` | 999 | `2490d7e27ef3e24176ff9895c330713c6c5a08db577799cfff38df76b1915be1` |
| `chapter16/reports/improvement-report.json` | 101236 | `f1d3f2a0752356e77fb148207a90950bf48f44cae6b705cdff80cbda98b87b12` |
| `chapter16/reports/exercise-results.json` | 3509 | `e336d326ce64d90795514de692046d73b57c2f7b1cf472b89926404554cd3e29` |
| `chapter16/schemas/improvement-report-v1.schema.json` | 28957 | `568c61b60709a3621b2a7563dab0d9e06618dc1a01970be6fb97764b33a78967` |

内部 `report_hash` 为 `1e69b9a2075c9e01f9dacad98f88d57d22d3de5c82da066ad8bd6e97e60d3304`，`evidence_hash` 为 `5ddf5bd610bffd195d1e01c72bd522273dfc056a1fb12bb01daca782fbb6ebfa`。文件 hash 覆盖完整序列化字节，内部 hash 按合同排除自身字段；二者不能互相替代。[规范 manifest](../../chapter16/reports/manifest.json)逐一列出八份数据/说明文件的字节与哈希，manifest 自身另外记录于上表。

## 审稿与实施裁定

详见[双视角审稿与逐项处置](../reviews/chapter16-review-codex-v1.0-rc1.md)。自审后只做一次新上下文整分支审查，不为每任务派发 Agent；4 项 Important、2 项 Minor 均在一次修复流程中解决。十五个新回归在修复前实际 14 失败、1 通过，修复后全通过；没有 Critical 或已知未处置的重要问题。未做第二次独立复审，最终绿色矩阵是实施方验证，不冒称独立认证。

- 按用户批准沿用 native 及当前干净分支，不新建工作树；所有稿件、图、报告、预览和截图均在本书工程内。旧第 15 章外部路径测试依赖正常系统临时目录，沿用既有环境并执行，不修改其代码来换取通过。
- 任务 1 提前忽略 `.runs`，避免把中间运行物纳入交付。可执行合同用测试约束；行文通俗性由读者/专家审稿判断，不以词语禁用检查代替阅读。
- `UsePolicy` 是当前可信策略，与历史资产快照分离。回滚必须复查当前权限；来源的合法范围缩小与提案文本编辑仍允许，不能用逐字比对掩盖授权设计。
- 修订前保存正文/图/报告；归档正文只修相对链接，登记原提交和原字节，JSON/SVG 保持原字节。题号调整前的早稿也保留。
- 七图逐一查看、布局修正后再生成；已有 Tldraw 6.0.2 成功导出一个可编辑源，未安装软件。图号按首次阅读顺序排列，源 basename 不改，截图按语义图号定位。
- URI 安全规则额外改动 `scripts/check_repository.py` 与 `tests/test_repository_safety.py`：裸 URI scheme 正则前缀不是机器地址；三类真实 URI、当前树和历史回归仍拦截，原历史精确豁免未扩大。
- 新增 `AssetEvidence`，把候选相关回放与来源权威纳入证据闭包；这是未公开 RC 的必要合同修复。旧 v1 报告保留，不宣称旧快照与新 Schema 的字节结构相同。
- 未安装 SDK/模型/容器，未做翻译、PDF/EPUB、推送或网站发布。严格构建只是验证已有公开章节不被污染；第 15/16 章后续发布需另行授权。
