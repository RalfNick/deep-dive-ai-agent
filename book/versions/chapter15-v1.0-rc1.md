# 第 15 章 v1.0-rc1 本地候选记录

记录日期：2026-09-27。分支：`codex/chapter15-agent-post-training`。起点：`6b9a3c55602510e0a4d3a78981d2264c941e6e3e`。章节基线内容提交：`a6b9d65bfb9e527c508ccdbe47fb152b3e9e2490`。本记录与审稿修订所在的候选提交以 Git 历史为准；下方的报告哈希固定本次实验内容。状态：**本地 v1.0-rc1 候选，未推送、未发布**。

## 候选内容

- [正文](../chapter15.md) 23,624 个字符、35 个二三级标题，按失败归因、数据资格、SFT/DPO/RL、奖励投机和发布判断五幕展开。
- 7 幅原创矢量图、5 组离线实验、7 个明确失败样本、5 张比较表、13 道分层练习与[参考答案](../../chapter15/reference-answers.md)。
- 24 条带血缘与 split 的固定轨迹：12 条通过审计、12 条隔离，只有 5 条来自 train 且可作为 SFT 示例。
- 4 状态、6 动作的有限策略用于 SFT 概率更新；4 组成对偏好用于 DPO 手算；3 种奖励设计用于固定动作选择、200 次回放与发布门禁。
- [来源台账](../sources/chapter15-sources.md)以 2026-09-27 核对的一手论文和官方文档为准；[真实训练迁移指南](../../chapter15/real-training-guide.md)只有未执行的字段与流程映射。

## 环境与执行合同

- 本地验证：Python 3.11.15，pytest 9.0.2，jsonschema 4.26.0，Markdown 3.10.2；Node.js 24.15.0。Python 测试与预览在忽略的 `.venv-chapter15/` 中运行，依赖来源是 `chapter15/requirements-dev.txt` 与 `chapter15/requirements-preview.txt`。
- 核心运行时代码只用 Python 标准库；规范实验离线、不读取 API Key、不下载模型，也不启动 GPU。
- 统一种子 `1501`；每个奖励变体固定 200 个 episode、四个各 50 的教学切片。报告 Schema 为 `chapter15.post-training.v1`，manifest 为 `chapter15.artifact-manifest.v1`，练习为 `chapter15.exercises.v1`。
- 规范报告位于 [chapter15/reports/](../../chapter15/reports/)；两次独立运行 `repro-a` 和 `repro-b` 的 `manifest.json` SHA-256 均为 `701ddeabb3093f2faa5d466cb85b65c251ee8b2ec023f149f5d762750c243a38`，且与规范 manifest 字节一致。练习两次输出哈希均为 `08c562fb9fbd7f1245bdbcd585c290fca7cd18aec0b54e446337ac59dd798477`。

## 规范产物哈希

下列值取自 `chapter15/reports/manifest.json`，均为 SHA-256：

| 产物 | 哈希 |
| --- | --- |
| `group-1.json` | `f8174ca493e4c1df6d4e481ed421ff096b28810da0037da033e8e4abb7413d40` |
| `group-2.json` | `f1a599cfb8578f200551b938e31a8d79c91869b8fdf142925c3e30b365a20ee1` |
| `group-3.json` | `d7cb73a9b47571cf6f3aabefe9d0a2bd43570221d57d88b184d10ffc1e0bdbc5` |
| `group-4.json` | `0b512d30cacd0a1b476c61cce5d24c5fe64bf125ce00eebea79986714bd5a749` |
| `group-5.json` | `e538cda697c62cddcdda7b1db9aa1d257a43f7ceaeb38e96466a7b69913c94f3` |
| `post-training-report.json` | `11061e9929e3384f0ecedeff2f9b3d67777ea1668f47869246f1843dd91895f9` |
| `post-training-report.md` | `e5a3cca65178989378c0d643e891009235ca97db3ed58894de7e02d08a17da8d` |
| `manifest.json` | `701ddeabb3093f2faa5d466cb85b65c251ee8b2ec023f149f5d762750c243a38` |
| `exercise-results.json` | `08c562fb9fbd7f1245bdbcd585c290fca7cd18aec0b54e446337ac59dd798477` |

## 验证清单

| 命令或检查 | 结果 |
| --- | --- |
| `.venv-chapter15\Scripts\python.exe -B -m pytest chapter15/tests -q` | 98 项通过；另以 `python -B -m pytest chapter15/tests tests -q` 验证 145 项与 89 个子测试通过 |
| `python -B -m chapter15.experiments --group all --output chapter15/.runs/repro-a`、`repro-b` 与修订后的 `final-review-repro` | 三份 manifest 逐字节相同，且与规范报告一致 |
| `python -B -m chapter15.exercise_solutions --all --output chapter15/.runs/exercises.json` | 13 道答案与规范结果逐字节一致，覆盖计算与设计判据 |
| `.venv-chapter15\Scripts\python.exe -B -m chapter15.preview` 与 `node book/check_chapter15_preview.mjs` | 1440×1000 和 390×844：7/7 图、5/5 表，0 失效页内锚点和整页横向溢出；截图留在忽略目录 |
| `python -B -m pytest tests -q`、`npm test --prefix book` | 仓库 47 项、89 个子测试与 Node 排版 4 项通过 |
| `python -B scripts/check_repository.py --root . --git-history` | 当前树与可达 Git 历史检查退出码 0；仅对下文注明的历史计划行设精确路径例外 |
| `python -B scripts/build_site.py --root . --output _web`、`python -B -m mkdocs build --strict` | 218 个 allowlist 源文件，严格构建通过；第 14 章存在，第 15 章文件数为 0 |

## 已证明与未证明

本候选证明：给定固定夹具，失败干预可以按证据路由；成功但违规、泄漏、重复或缺血缘的轨迹会被隔离；SFT 与 DPO 的有限动作算式可复算；可抵消的安全惩罚可能保留违规动作；安全硬门禁、切片和环境有效性可以按固定顺序产生三态发布判断；规范报告可以逐字节重建。

本候选没有证明：真实模型后训练后的任务质量；GPU 训练、PPO/GRPO/RFT 运行；固定 24 条轨迹代表生产分布；200 次回放代表生产违规概率；预置 split 自动完成安全切分；本地奖励模拟执行了 RL 参数更新；本地教学合同符合任何 Provider 或训练平台的完整 API。

原设计规格还要求在有限状态环境中演示奖励驱动的策略更新、探索和预算约束。本候选的第 5 组实际是固定奖励排序与动作回放，未实现这一段更新过程；这是**明确的范围收缩**，不是已完成的 RL 训练实验。正式发布前需决定补做该教学实验，或接受当前只解释奖励投机与发布门禁的范围。

## 审稿与公开边界

[双视角审稿](../reviews/chapter15-review-codex-v1.0-rc1.md)记录了读者和 AI/后训练工程两轮检查及 P1/P2 处理。第 1–14 章发布内容与历史 tag 保留；`book/manifest.json` 继续为 `0.14.0`，第 15 章状态仍为 `planned`。候选正文、实验、图片和答案不进入 `_web` 或公开 MkDocs 站点。本轮不推送、不合并、不创建发布 tag、PR、PDF 或网站部署。

整分支只读复查又发现并已修复：单组实验拒绝覆盖时误删旧 JSON、轨迹四个布尔证据字段接受非布尔值、零样本或非有限切片差值可能通过发布门禁；同时加固了空白变换记录和带空格的 `unknown` 来源。修复均先由失败测试复现，再通过定向测试和全套回归。

早期实施计划的一个历史 blob 曾包含用户指定的本机仓库根路径。当前计划已改为相对表述；历史扫描对该 blob 的第 619 行路径告警作精确豁免，仍扫描全部历史 Secret 和其他机器路径。候选历史没有重写。
