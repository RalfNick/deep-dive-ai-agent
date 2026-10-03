# 附录 A v1.0-rc1 本地候选记录

日期：2026-10-03，Asia/Shanghai。基线：第18章RC2冻结点fffa620。分支：codex/appendix-a-environment-setup。本轮只生成本地候选，不推送、不合并、不建tag/PR、不发布网站。

## 交付与保护

完整正文、4幅原创SVG及配对tldraw源、3组离线操作实验、9道分层练习与具体参考答案、官方来源台账、读者/技术两轮作者自审、独立只读审查及本地预览。正文25,266个Markdown字符；排除围栏代码后12,028个汉字（含标题、练习、脚注，不称纯叙述字数）；40个二/三级标题。附录是快速准备，不照搬核心章3万字标准，也不创建第19章。既有18章正文、代码、图及版本记录不改写；首次附录版本由本次本地Git提交冻结，后续另立RC2。

所有交付均在本书独立仓库内：正文book/appendix-a.md；实验appendix_a/；最终图book/images/appendix-a/；编辑源infographic/appendix_a/；资料与审稿在book/sources/和book/reviews/；预览appendix_a/preview-pages/index.html。临时严格构建目录已在核对边界后移除，未删除既有章节。预览及截图忽略Git但保留本地，源码可重新生成。

## 实际环境

复用已有.venv-chapter15的Python3.11.15、pytest9.0.2、jsonschema4.26.0、Markdown3.10.2；Node24.15.0、book内Playwright1.62.1及本机Edge；已有tldraw6.0.2 CLI；严格站点构建使用系统Python中的MkDocs1.6.1。本轮未安装包、浏览器或模型SDK，不执行Docker或tsc，不读取API Key、不请求模型。

## 最终验证

以下命令均从仓库根目录执行。表中python指已有.venv-chapter15/Scripts/python.exe；严格MkDocs项使用系统Python。具体路径与读取范围均为本书项目；不把本机结果扩大为任意操作系统或Provider验收。

| 检查 | 实际命令/动作 | 结果与边界 |
| --- | --- | --- |
| 最短标准库路径 | python -B -S -m unittest appendix_a.tests.test_preparation -v | 14项通过；-S关闭第三方site路径，证明该入口不需要Markdown或SDK |
| 完整附录交付 | python -B -m unittest discover -s appendix_a/tests -q | 22项通过；包含预览依赖、图源、Node与公开构建边界 |
| 第3章实际离线起步 | python -X utf8 -B chapter3/agent_loop.py；python -B -m unittest discover -s chapter3/tests -q | completed，4次工具调用，accepted=true；任务内2项测试、本章20项测试通过 |
| 相关回归 | python -B -m pytest appendix_a/tests chapter18/tests chapter15/tests chapter16/tests chapter17/tests tests -q | 477项与107项子测试通过；不是整库全章测试 |
| 既有Node回归 | node --test book/tests/*.test.mjs | 4项通过 |
| TS教学反例 | node appendix_a/examples/task.ts；node appendix_a/examples/unchecked.ts | 分别输出“检查链接，最多 3 步”及31；未进行静态类型检查 |
| 九题具体答案 | python -X utf8 -B -m appendix_a.exercise_solutions --all | 九题结果与解释可打印，不只是占位成功标记 |
| 原图与编辑源 | python -B -m infographic.appendix_a.generate_diagrams | 4幅SVG及4份.tldr；解析/绑定/箭头检查通过，四幅PNG实际审读；已有CLI导出一幅.tldr成功 |
| 双宽度预览 | python -B -m appendix_a.preview；node book/check_appendix_a_preview.mjs | 1440与390宽度各4幅图、4张表、4图加载；失效锚点0、页面错误0、远程请求0、整页横向溢出0；手机图内可滚动 |
| 公开来源保护 | python -B scripts/build_site.py --root . --output appendix_a/.runs/site-sources-rc1 | 218份原公开来源，附录正文/图和第15–18章候选未进入 |
| 严格站点构建 | 系统python -B -m mkdocs build --strict --config-file appendix_a/.runs/mkdocs-rc1.yml | 实际通过；临时配置仅调整项目内docs_dir/site_dir路径，输出检查后清理 |
| 仓库检查 | python -B scripts/check_repository.py --root .；另加--git-history；git diff --check | 当前树、既有历史扫描及空白检查通过 |
| 旧版保护 | git diff --name-only fffa620，限定既有chapter正文/代码/图/历史及book/manifest.json、mkdocs.yml | 无变化；现有18章原版本保留，公开manifest仍0.14.0、14章已发布 |

## 稳定报告与哈希

规范报告只使用固定夹具：schema_version=appendix-a/1、network_access=false，无机器绝对路径、当前时间、凭据值或虚构费用。真实主机--inspect观察只打印，不进入规范哈希。规范包与appendix_a/.runs/reproduce-first、reproduce-second的四个文件逐字节一致，三个载荷哈希与清单一致；重用输出目录会拒绝覆盖。

| 文件 | SHA-256 |
| --- | --- |
| book/appendix-a.md | 31f86d860f571d8bafbdf27e9af19b82c76e7f4e1c2fae84beb1bd434ddef8fd |
| appendix_a/reports/reference-rc1/api.json | a654601b083fe56ed866e835f46c932e77cece7f078956856f24b5efc7b54428 |
| appendix_a/reports/reference-rc1/environment.json | 2bf8116444ba7175210f495513f8ddc6ecee475d42283c5fd5c89b1b174c8d43 |
| appendix_a/reports/reference-rc1/python.json | 7502bfe06e4d3b491584ffb5a65e833fa5de4dfefe25ebacbc4df799f5575d73 |
| appendix_a/reports/reference-rc1/manifest.json | 5d4b11b022bb0efa0ba203886acb7068646d218caf344181ddfd17a2209cc83f |

## 发现、修复与未通过项目

- 独立审查发现标准库路线误用完整discover：关闭第三方site路径时，22项中预览检查因缺Markdown失败。正文改为14项核心模块入口，-S复验通过；22项完整交付保留依赖前置。
- OpenAI配置示意显式固定官方base_url，防止旧OPENAI_BASE_URL指向其他服务；README补Node>=22.18前置。该修复不是一次真实API验收。
- 图1短标签被遮挡，去掉重复标签；图3入边重叠，先失败复现再修改SVG及可编辑锚点，最终四图审读通过。
- 中途相关回归曾因资料/审稿/版本链接尚未创建出现1项失败；补齐后最终477项和107项子测试通过。不把中途失败隐藏成一路全绿。
- 首次tldraw导出因输出目录未创建失败；显式创建项目内目标后导出成功，没有安装新工具。未进行编辑器回读。
- 原公开图片收集器会把附录SVG一并纳入。失败测试复现后，仅在scripts/build_site.py增加appendix-a图片排除保护；公开manifest、导航及218份已发布源不扩充。构建脚本并非完全未改。
- 最终元数据扫描发现版本记录曾含作者机器绝对路径，改为仓库相对位置说明后重新扫描；文稿不依赖作者本地目录。
- 整库根pytest在基线和候选均出现相同15项既有收集错误，涉及Chapter1缺NumPy、Chapter9缺MCP、Chapter12缺AgentsSDK/夹具导入及部分同名测试模块冲突。未安装补依赖或改旧章；不宣称全书全部测试通过。

## 已证明与未证明

已证明：本机标准库读者路径、输入与预算验证、错误分类、请求草图、异步夹具、报告复现/拒绝覆盖、四图及预览、相关章节回归与候选发布边界符合本地约定。核心包无发送功能，观察结果明确区分not_run与unknown。

未证明：真实Provider可用性、当前账户权限/余额/区域、模型或工具能力、真实Token/费用、第三方SDK实测、TypeScript静态检查、跨平台全量复现，以及生产级权限隔离。离线报告不能证明这些结论。

## 冻结与后续

本轮在上述本地分支创建候选提交；提交自身即RC1完整冻结点，可由git log读取，不在提交内填写自身哈希。没有push、merge、tag、PR或部署。后续有实质修改时新建RC2记录及规范包，保留本次正文、图源、报告、来源日期和Git冻结点；不覆盖reference-rc1。
