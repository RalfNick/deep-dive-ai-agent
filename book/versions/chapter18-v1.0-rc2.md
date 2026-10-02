# 第18章 v1.0-rc2 本地优化记录

日期：2026-10-02（Asia/Shanghai）。分支：`codex/chapter18-multi-agent-final-system`。本轮响应“review一下并优化”，只更新第18章本地候选；不推送、不合并、不创建tag/PR、不部署，不生成译文或PDF。

## 版本保护与变更

RC1完整冻结点：`c1c2586d0dc982dbed08aa665590112c37705a35`。在修改前保存[63份阅读材料快照](chapter18-v1.0-rc1/README.md)：旧稿、七图、来源、代码、答案、设计源和两套规范报告，Git blob逐个校验。快照不复制测试/运行夹具；conftest.py的原字节以.txt后缀保留，避免自动加载。复现完整旧工程应检出冻结提交。原RC1版本记录、Review及两套九文件原包均不改写。

正文仍为《Multi-Agent与最终系统：不是Agent越多越好》；四幕主线、7SVG、5比较表、5组20案及13题不变。当前24,870叙述汉字、39,986个Markdown字符、33个二/三级标题。新增七状态阅读提示、Worker结果的人话例子、Group4关键输出、带引用的知识终端摘录和可运行冲突查询；哈希/事件关联细节改为进阶阅读，第4题参考答案与两句要求一致。

代码增加知识输出evidence_verdict，并补强四项检查：引句中出现明确夹具事实值；Worker来源范围绑定；引用进入该Worker实际发送上下文；answer验收引用逐项对应合格证据。来源台账仅更新本地证据与日期说明，外部资料核对日仍是2026-10-01，没有伪称重新核对产品。

当前[RC2规范包](../../chapter18/reports/reference-rc2/manifest.json)另存新目录，不覆盖RC1。包内九文件与RC1-reviewed合法案例字节相同，原因是修订收紧错误记录的接受条件、改善解释与呈现，不改变正常固定策略结果。七图字节未变。第1–17章稿图、代码、报告和历史记录不改；公开manifest仍0.14.0，第18章planned，导航/allowlist不变。

## 实际验证

复用已有Python3.11.15/pytest9.0.2/jsonschema4.26.0/Markdown3.10.2测试环境；Node24.15.0、Playwright1.62.1与既有Edge检查预览；严格构建改用已有系统Python发布环境的MkDocs1.6.1。没有安装工具、访问模型Provider、读取Key或运行Docker。

| 验证 | 实际结果 |
| --- | --- |
| 五项RED→GREEN | 四项知识证据问题与知识输出缺失先各自复现，再修复；新增归档保护合同。中途正文测试仍期待RC1链接，更新为RC2冻结入口后复验 |
| 本章 | `.venv-chapter15/Scripts/python.exe -B -m pytest chapter18/tests -q`：107通过，约15秒 |
| 相关矩阵 | 同解释器 `pytest chapter15/tests chapter16/tests chapter17/tests tests -q`：348通过、93子测试通过 |
| 两次全实验 | `chapter18.experiments --group all --output chapter18/.runs/rc2-final-a` 与rc2-final-b：各20案9文件；逐字节匹配RC2规范包 |
| 两次独立答案 | `chapter18.exercise_solutions --all --output chapter18/.runs/rc2-answers-a.json` 与rc2-answers-b.json：13题，均与规范exercise-results.json相同 |
| 读者示例 | UTF-8知识入口显示“支持”、两份真实引句、missing=[]；正文冲突查询输出conflict、30天/conflict-a、90天/conflict-b |
| 预览 | `chapter18.preview`、`node book/check_chapter18_preview.mjs`；1440×1000/390×844的7图5表均正常，失效锚点/整页横向溢出/页面错误/远程请求均0 |
| Node | `npm --prefix book test`：4通过 |
| 严格公开构建 | `scripts/build_site.py --root . --output chapter18/.runs/site-sources-rc2`：218源；已有发布环境 `python -B -m mkdocs build --strict --config-file chapter18/.runs/mkdocs-rc2.yml`通过，约2.50秒；临时源/HTML/配置随后清理，不覆盖正式构建目录 |

原规则仓库扫描与Git历史检查均exit0；版本账对应的LF规范化迁移值已复核，最终仓库合同50项与93子测试通过。与RC1比较，第1–17章、七图、两套RC1报告、原版本/审稿记录、公开manifest、导航和allowlist差异为空；`git diff --check`通过。本章最终复验107项通过（16.55秒）。最终冻结点为包含本记录的本地提交，不建立公开tag。[本轮审稿与已修复问题](../reviews/chapter18-review-codex-v1.0-rc2.md)另存，不冒称第二次独立审稿。

### 整库未通过的检查

根目录pytest仍有15项既有收集错误，类别与RC1一致，不是全书全部通过。快照最初导致一项额外conftest导入冲突，已通过非执行后缀归档修复，复验回到15项；没有修改旧章或豁免普通测试。第一次使用测试环境运行MkDocs因模块缺失未启动，切换已有发布环境后才确认严格构建成功。

## 摘要与哈希

20案：answer7、blocked2、conflict2、needs_approval1、stopped3、unknown3、verified2；工具调用49、验证调用4、旧补丁拒绝1、重复写入0、安全违规0。它们是固定任务的机制结论，不转换为模型成功率。

- 正文SHA-256：`bf04dd3181e3d712c25a2ed95567fb7549b3c7bf40af1e9dead47d8562b7dde6`。
- RC2 team-report.json：`21b5e3229e53ac1dd2cecfb04d6ac1bcc24f018c1f96108966b454359d9da29a`。
- RC2 manifest.json：`7f48a42f78c1110bdfd3b9df346825779c7e7c699d1f637f0226921043df545e`。
- RC2 exercise-results.json：`fd13e2993687b93c7823191923baaf358d5db13d24c85cdee8f329aa1f69c415`。

其他payload摘要由manifest列出，全部实测核对；没有用抄写哈希替代fresh run。

## 证据边界

本轮证明固定任务中错误引用、Worker范围/上下文错配与错误验收摘要被拒绝，正常报告继续可复现，读者能直接查看知识结论。没有证明通用语义蕴含、真实模型协作收益、实测并发加速、生产身份/审批、操作系统隔离、跨进程恢复或分布式幂等；记录关联不能抵御恶意宿主伪造全部记录。公开站点没有新增第18章。
