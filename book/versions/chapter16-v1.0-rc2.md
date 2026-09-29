# 第 16 章 v1.0-rc2 本地修订记录

日期：2026-09-29。分支：`codex/chapter16-continuous-improvement`。本地候选，未发布。沿用户批准的 native 方式在原分支修订，不推送、不合并、不建 tag/PR、不部署，不改变公开清单与导航。

## 内容与历史保护

正文32,345字符、21,388汉字；剔除代码、表格、标题、脚注及链接目标后20,114个叙述汉字。14个主节、34个二三级标题、7幅图、5张比较表、5组实验、6个失败样本、13题及参考答案。增加关键输出摘录与候选卡，序列化细节移入进阶说明；七图和来源不改。

RC1固定提交为 `c693d3aa94c1753c071994c4f769e9bd3097f2db`。[RC1正文/七图](chapter16-v1.0-rc1/README.md)与[九份报告](../../chapter16/report-history/v1.0-rc1/manifest.json)在任何修订前保存，原 Review 与版本记录不变。归档正文只调整相对链接，SVG/JSON保持原字节，源码从固定提交恢复。第1–15章、旧RC快照和公开导航不改写。

## 修复范围

- 回滚区分“历史已知”和“允许恢复”；停用版本须新验收/批准再激活，不能经 rollback 绕回。stop 后尚未回滚时，旧 activate 也不再是正常幂等重试；回滚时钟不可倒退。
- 来源不只核验身份、权限、范围与键名，还核对实际行为字段。权威偏好已改 normal 时，旧 concise 即使原隐藏题16/16仍不能批准；不把附加解释文字做逐字匹配。
- 回放区分复现、变化与满足修复条件。目标文档缺失为 unknown，知识/步骤干预须满足发现来源的正向条件；提案不读取留出真值，未决材料由工厂拒绝。
- 练习5/10/11补充正向发现条件、相反来源内容与停用恢复检查，规范答案从程序重新生成。

Schema仍为 `chapter16.improvement.v1`，不新增字段。正常五组轨迹与报告字节不变，因为修复针对失败边界；练习和manifest改变，不将字节相同误说成实现没有变化。对应行为由新回归和代码历史区分。

## 环境及实际验证

复用既有Python3.11.15、pytest9.0.2、jsonschema4.26.0、Markdown3.10.2、Node24.15.0、Playwright1.62.1、MkDocs1.6.1与Edge。测试解释器为 `.venv-chapter15/Scripts/python.exe`，安全与站点构建复用 `.venv/Scripts/python.exe`。未安装依赖、模型或容器，未读取API Key/.env，未调用真实Provider。

| 检查 | 实际命令与结果 |
| --- | --- |
| 第16章/仓库完整矩阵 | `python -B -m pytest chapter16/tests tests -q --tb=short`：129通过、93子测试通过；含80项章节测试、49项仓库合同，没有取消收集 |
| 上一章 | `python -B -m pytest chapter15/tests -q --tb=short`：128通过 |
| 规范报告 | `python -B -m chapter16.experiments --group all --output chapter16/.runs/rc2-verified-a`，另用新目录`rc2-verified-b`：两套各九文件逐字节一致，验证后同步规范目录 |
| 独立练习 | `python -B -m chapter16.exercise_solutions --all --output chapter16/.runs/rc2-exercises-a.json`及`rc2-exercises-b.json`：与规范答案字节一致，10项代码判据、3项定性答案 |
| Node | `npm test --prefix book`：4通过 |
| 本地预览 | `python -B -m chapter16.preview`及`node book/check_chapter16_preview.mjs`：1440×1000 / 390×844，各七图五表，零失效锚点/整页溢出；16.8–16.10局部截图实际查看 |
| 安全与历史 | `python -B scripts/check_repository.py --root . --git-history`：exit0，不扩大秘密或路径扫描豁免 |
| 公开构建 | `python -B scripts/build_site.py --root . --output _web`：218份源；`python -B -m mkdocs build --strict`：exit0；15/16不进入公开树 |

最终新上下文只读审查尚未执行。以上绿色矩阵是实施方结果，不是独立认证；交付前补充审查结论。未混合收集所有独立章节环境，不能写成全书每个实验都重跑。

## SHA-256

| 文件 | bytes | SHA-256 |
| --- | ---: | --- |
| `book/chapter16.md` | 80013 | `12f187f22aa5ebf8731bdbc33989620e37a80150037a936745a34087e75475da` |
| `book/sources/chapter16-sources.md` | 3797 | `ba1e7178455ceb5fdcb62e972d284e75de452ac549acf3fedbf310ffe0d8f783` |
| `chapter16/reports/manifest.json` | 999 | `a6da62a79eec256c4ab6dcc830f4e1f487e51cabe54b789cb1307eabe13ef616` |
| `chapter16/reports/improvement-report.json` | 101236 | `f1d3f2a0752356e77fb148207a90950bf48f44cae6b705cdff80cbda98b87b12` |
| `chapter16/reports/exercise-results.json` | 3716 | `290bfe093e0903a99593c35efef1da0458bad03dbc622388bff442984f953408` |
| `chapter16/schemas/improvement-report-v1.schema.json` | 28957 | `568c61b60709a3621b2a7563dab0d9e06618dc1a01970be6fb97764b33a78967` |

内部report_hash仍为`1e69b9a2075c9e01f9dacad98f88d57d22d3de5c82da066ad8bd6e97e60d3304`，evidence_hash仍为`5ddf5bd610bffd195d1e01c72bd522273dfc056a1fb12bb01daca782fbb6ebfa`；两者与完整文件字节哈希不是同一口径。完整九文件校验见[manifest](../../chapter16/reports/manifest.json)。

## 已证明与未证明

已证明：在固定Atlas夹具中，三个机制问题及相关停用入口被正常API回归覆盖；合法来源补充说明、缩小范围及新验证再发布不被一并禁止。实际资产消费与独立门禁仍给出11/16→16/16、三项目标修复、盲目消费fail、缺回执inconclusive。数字只说明确定性边界符合性。

未证明：真实模型能力提升、盲测泛化、自然语言因果解释、生产授权/持久审批、任意PII或注入防护、线上A/B收益或外部副作用补偿。结构化来源也可能错误，因此发现支持不能代替独立真值。保留当前政策/时间复查，哈希不证明事实，进程内注册表不是IAM或签名服务。

详见[RC2读者/专家审稿](../reviews/chapter16-review-codex-v1.0-rc2.md)。所有新稿件、归档、报告、预览及截图位于本书工程；公开manifest仍为`0.14.0`，14章published、15/16planned。未生成翻译、PDF/EPUB，也未执行发布。
