# 全书读者路径优化：editorial-v2-local

日期：2026-10-03。修改前完整基线：`c8f2995343e90de0721c4236f880c88bbcb3d324`。本地分支：`codex/whole-book-reader-revision`。状态：本地编辑候选，未发布。

## 范围与历史保护

依据[全书读者审稿](../reviews/whole-book-reader-review-2026-10-03.md)，改善首次阅读时的学习台阶、首次动手路线和承诺边界，不普遍扩篇，不强制统一案例。

- 编辑前保存21份稿件的[字节快照与SHA-256](whole-book-reader-v2-before-2026-10-03/README.md)，其中包含完整18章旧稿；旧版本索引从冻结Git提交补存，另保存六份验收测试原件，共28份。
- 第1–17章定向修订；第18章正文、附录A正文、实验实现、规范报告和图片均保持原样。
- 第12章实验README同步最短入口与live边界；不补容器实现、不降低安全门禁、不调用模型。
- 两份阅读合同同步：第14章检查每张表均有滚动容器，不再锁死旧表格数量；第16章移除“不得链接尚未写出的第17章”这一过时限制。其余历史冻结与验收记录不改写。
- 历史验收采用测试专用适配器：迁移记录和RC哈希核对冻结旧稿，受保护路径的授权文字修订还须保留对应Git原始字节；只登记本轮明确范围，不允许实现、图片或规范报告通过快照豁免。第12章以实际manifest确认后续章未公开，不再要求把已有候选稿称为“仍是规划”。
- 新增[候选阅读导航](../READING_PATHS.md)，不修改公开manifest、构建allowlist或站点导航。
- 原审稿、旧版本记录及既有tag保留；本轮不推送、不发布、不翻译。

## 修改地图

| 章节 | 本轮编辑 |
| --- | --- |
| 1 | 数学跳读提示、子目录与根目录切换提醒 |
| 2 | 先讲示范/比较/奖励；优化器术语、算法矩阵与DPO目标分层，目标用等价四步表达避免渲染乱码 |
| 3–4 | Trace工具名称说明；显式区分验收拒绝后的继续纠错与终止策略 |
| 5 | Packet、双Digest、序列化和评分字段真实标为进阶 |
| 6 | 新旧配置小输入；失败构造后移；测试断言与报告观察分开 |
| 7 | 字段/Store细节后移；说明无语言关键词时偏好可能不召回 |
| 8 | 不同查询不作增益曲线；结果摘要与请求Trace口径统一 |
| 9–10 | 环境入口提前；quickstart、async/await与持久job的生命周期桥梁 |
| 11–12 | 工作台/产品双路线；Replay与live范围准确；首跑第一组及决策—观察表 |
| 13 | 组合数白话定义、无放回选法与一次展开计算 |
| 14 | 重试Span短对照；正确衔接后训练，而非预告安全章 |
| 15 | logit→概率→损失→更新手算表，DPO符号与已有答案链接 |
| 16 | 正常四步发布先行，停用后旁路放进进阶；链接当前第17章 |
| 17 | 五事件的逐步状态表，不补造生成/播放事件 |
| 18 | 正文不改，仅同步目录中的教学系统范围 |

第6章新增价格数值是人工手算的业务说明，不是规范30事件轨迹的输出；第14章Span表是固定夹具的局部摘录；第15章概率表对应既有单样本更新；第17章状态表对应既有归约器。新增解释不扩大原实验结论。

## 验证记录

环境：Python 3.11.15、pytest 9.0.2、Node.js 24.15.0。使用仓库既有本地环境，没有新安装框架；不将该环境称为第12章原发布锁定环境。Windows子进程验证继承 `PYTHONUTF8=1` 和 `PYTHONDONTWRITEBYTECODE=1`。

### 最终结果

| 范围 | 本轮结果 |
| --- | --- |
| 仓库合同 `python -B -m unittest discover -s tests -q` | 58项通过，含8项新历史保护回归 |
| 第2章标准库实验 | loss mask、偏好、采样、推理预算、结构输出、模型选择共6个入口退出码0；真实micro-SFT未重跑 |
| 第3–8章独立unittest | 分别20、24、63、143、65、71项通过 |
| 第10–11章独立unittest | 分别42、26项通过 |
| 第12章明确核心集合 | 162项通过，包含工具、运行、恢复、验收、Trace、上下文、预检、Provider合同及正文/交付/预览；不包括框架、全组实验与整套练习 |
| 第13–18章独立pytest | 分别38、69、128、85、85、107项通过 |
| 排版守卫 `node --test book/tests/render_checks.test.mjs` | 4项通过；第14章预览的7张表均有滚动容器 |
| 仓库安全与链接 `python -B -m scripts.check_repository --root .` | 退出码0 |
| 原稿归档 | 28份摘要全部匹配；独立复核确认各Git blob与冻结提交一致 |
| 本地站点 | allowlist组装218份来源，`python -B -m mkdocs build --strict`退出码0；未部署 |

第12章核心集合通过显式列举16个测试文件运行，不是把完整测试失败藏成全量通过。完整收集最初在 `test_agents_sdk.py`、`test_langgraph.py` 因缺少 `agents` / `langgraph` 依赖停止；第五组、框架练习也依赖它们。第1章的三个数值测试模块缺少NumPy，第9章的MCP实验、服务和报告复现模块缺少MCP SDK；这些不计作完整通过。第2章真实micro-SFT未执行，未更新旧训练结果。完整CI环境与所有平台组合没有在本轮重建。

### 文字与实际输出核对

- 导航首个命令 `python -X utf8 -B chapter3/agent_loop.py` 得到失败测试 → 补丁 → 测试通过 → Verifier接受，最终 `completed`、4次工具调用。
- 第6章报告查询得到 `sliding-window-8-events`、`unsafe_signature_change`、约束保留0.5、负约束保留0；单独的unittest不冒充打印指标。
- 第7章无语言关键词的查询与 `preferred_language` 无词项重叠，实际召回不包含该记录。
- 第10章quickstart显示 `queued → running → succeeded`，只有1份执行回执。
- 第12章第一组实际读写并运行测试：红灯已观察、2次写入、2条diff路径、3项候选测试、4项独立验收，最终 `completed`。
- 第14章固定 `recovery-01` 的局部Span顺序与正文一致；incident在重试后多出 `context.assemble` 与 `model.plan`，不是凭最终延迟倒推原因。
- 第15章实际单样本更新：`read` 概率从1/6变为0.2479756939，损失1.7917594692 → 1.3944245461。新增表中的分数与舍入说明一致。
- 第17章五个事件逐前缀归约，生成、播放、对话尾部和后台任务状态均与新增表一致。
- 第2章DPO改写为同一个目标的四步表达，HTML保留完整代码表达、不再把下划线解析成强调；第15章新增符号直接可读。没有修改网站数学配置，也没有声称全书所有旧公式已做跨浏览器视觉验收。

### 稳定报告摘要

以下三份报告分别生成到两个新目录，SHA-256完全相同；规范报告未覆盖。第12章目录名称含 `live-reports` 只是已有的忽略目录，本次明确是离线Replay，不是live实测。

| 报告 | 两次相同的SHA-256 |
| --- | --- |
| 第6章 `context-continuity.json` | `50CBBC74C8D938D619DAB131F8D37BBB8443162C1FEA74233C90FD6EB3686E5E` |
| 第12章第一组 `group-1.json` | `7EBB3859D34FB4D915EAF63568F749A8340184A1071B92ACA308F3473561D739` |
| 第15章第三组 `group-3.json` | `9DFFE418F2E7C40035674CA5901450BCFB7DB7BC9D76E6DF3D08ACF22E819E36` |

本地输出分别在 `chapter6/.runs/reader-v2-context`、`chapter12/live-reports/reader-v2-offline-first`、`chapter15/.runs/reader-v2-sft`；重复目录另存，不覆盖第一次输出。当前编辑源摘要见[新稿SHA-256清单](whole-book-reader-v2-hashes.json)。

### 初次发现的问题及处理

- `test_manuscript_meets_density_and_exercise_contract`：第15章超出28000字符上限42字符；压紧重复引导，未提高上限，完整128项重跑通过。
- `test_preview_contains_only_chapter14_assets_and_reader_guards`：新增表格令旧固定数量失效；改为核对每张实际渲染表都有滚动容器，未减少图与移动阅读保护。
- `test_manuscript_is_a_candidate_and_uses_only_observed_evidence`：第12章头部旧状态标记缺失；恢复发布基线与未执行声明，同时保留本地修订未发布说明。
- `test_release_record_and_agent_status_are_explicit`：旧断言要求把第15–18章称为“仍是规划”；改为核对实际公开manifest，已有本地候选不等于公开发布。
- `test_manuscript_structure_and_reader_entry`：第16章旧断言禁止链接尚未写出的第17章；如今正文已存在，移除过时禁令，链接由仓库扫描验证。
- `test_recorded_target_bytes_match_size_and_digest`、`test_final_record_contains_actual_hashes_and_review_disposition`、`test_old_chapters_and_rc_history_unchanged`、`test_old_chapter_content_code_images_and_reports_are_preserved`：旧迁移/RC记录描述冻结版本；验收转为核对被冻结原件及实际Git内容，没有把旧摘要改成新稿摘要。相关完整套件重新通过。
- `test_experiment_tree_has_no_private_or_generated_artifacts`：子进程生成字节码缓存；仅清理已验证的临时缓存，后续子进程继承禁写字节码设置，仓库58项重跑通过。
- 第4章首次Windows子进程输出解码失败：继承UTF-8设置后24项通过，未改实验实现。缺框架模块的收集/运行错误仍归环境限制，不计通过。

### 审稿与范围复核

完成读者路径与实现事实独立复核。未发现高优先级问题；第16章停止条件和第12章安装顺序两处小问题已修复，版本保护适配器追加复核通过。详见[本轮优化复核](../reviews/whole-book-reader-revision-v2-review-2026-10-03.md)。

第18章正文、附录A、图片、来源台账、Agent实现、规范报告、旧迁移台账、旧版本记录、公开manifest、构建器、网站配置和发布工作流均未改写。本轮只证明本地编辑与有限离线合同，不宣称真实模型能力或全书所有平台组合都通过。

## 仍然保留的边界

当前是真正的本地编辑候选，不等于已上线，也不是出版终稿验收。未重新核对全部产品资讯，不更新原来源核对日期；没有真实模型、Docker、GPU训练或生产部署证据。没有生成译文、PDF或EPUB。附录B–E及后记仍属规划。
