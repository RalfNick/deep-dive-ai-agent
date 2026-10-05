# 全书 0.18.0 网页与源码版

日期：2026-10-05。发布标签：`book-v0.18.0`。

## 交付范围

简体中文第1–18章、附录A、引言、配套实验、参考答案及原创图示。公开manifest采用`0.18.0`；附录有独立列表，不计入18章。第15/16/18章实验沿用RC2，第17章沿用RC3，附录A沿用RC1。

全书编辑冻结提交为`363b05a`；发布时另补第15/17章的实验、答案与下一章短链接。v2、v3修改前快照、旧稿、旧图、版本记录、规范报告及所有既有tag原样保留。各次历史记录中的测试数和“未发布”描述不回写。[发布正文哈希](book-v0.18.0-hashes.json)与旧编辑哈希分开保存。

## 发布门禁

仓库合同、分章测试、Node排版合同、安全检查及MkDocs严格构建分别运行。GitHub Pages继续以主分支CI成功为部署前提；个人站点从干净源提交同步，并检查正文、图示、搜索与导航。

默认根级pytest存在已记录的依赖/同名测试/夹具收集限制；公共CI按章与锁定环境隔离运行，不把局部通过描述为默认整库pytest已修复。

## 未证明与未交付

没有重新核验全部供应商功能，不扩大各章官方资料的冻结日期。没有调用真实模型、进行GPU训练、验证生产容器/设备隔离，或用确定性夹具比较产品能力。附录A真实API和tsc未运行。没有翻译，没有PDF/EPUB。

## 本地验收

Windows原生环境：Python 3.11.15。第12章单独安装完整哈希锁并使用pytest 9.1.1、Markdown 3.10.3；第13–18章使用已有pytest 9.0.2及各章预览依赖。基础发布环境安装NumPy 2.2.6、tiktoken 0.13.0和MCP 2.1.1；第12章框架环境独立使用MCP 2.2.0，避免依赖冲突。

| 入口 | 本轮结果 |
| --- | --- |
| 仓库unittest（含16项发布专项） | 79项通过 |
| 第1章unittest | 10项通过 |
| 第2章README七个离线脚本 | 7/7退出0 |
| 第3–11章逐章unittest | 20、24、63、143、65、71、47、42、26项通过 |
| 第12章锁定环境pytest | 210项通过，未跳过SDK相关测试 |
| 第13–18章独立pytest | 38、69、128、85、85、107项通过 |
| 附录A独立unittest | 22项通过 |
| Node书籍排版合同 | 4项通过 |
| 发布白名单构建 | 306源，含18章与附录A；无Review、版本归档或旧RC包 |
| `mkdocs build --strict` | 退出0 |
| 当前树与可达Git历史安全扫描 | 退出0 |

上述命令在仓库根执行；Python解释器分别指向隔离环境。常用入口为 `python -B -m unittest discover -s tests -q`、`python -B -m pytest chapterN/tests -q -p no:cacheprovider`、`python -B -m unittest discover -s appendix_a/tests -q`、`node --test book/tests/*.test.mjs`、`python -B scripts/check_repository.py --root . --git-history`、`python -B -m scripts.build_site --root .` 及 `python -B -m mkdocs build --strict`。第1–11章沿用独立unittest入口，第2章七个具体脚本见实验README。

发布审查修正了无哈希预览依赖误用hash模式、Windows历史JSON文本解码和中文站点锚点；不修改原依赖锁、实验实现或规范报告。个人网站另补附录目录、上下篇、进度、SEO与搜索支持，验证不把附录计为第19章。

首次远端CI在两项锚点测试失败：干净checkout尚未生成`_web`，测试加载MkDocs配置误依赖本地构建目录。新增只含实际配置与book的干净fixture复现RED，再使测试显式从book加载扩展配置；专项16项、仓库79项GREEN。没有前移站点构建来掩盖测试依赖，也没有跳过断言。个人站点同步后原搜索测试引用旧ContextPacket标题，现从真实章节heading核对搜索title/anchor；37文件147项、TypeScript和lint通过。

GitHub CI、Pages及Cloudflare线上状态以本次源提交对应的实际部署回执为准；本记录的本地通过不能代替线上成功。
