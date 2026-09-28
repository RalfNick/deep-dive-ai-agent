# 第 15 章 v1.0-rc2 本地候选记录

记录日期：2026-09-28。分支：`codex/chapter15-agent-post-training`。RC1 修订基线：`65ff413d0dce65f5f5942fad405a59ad52e544b3`；主体优化：`fc3ba4af9d462760511e5c6bbb3c3568d4ca18d6`；复审安全修复：`56aa08a9d985ad9981dc027bc039b2915c988b66`。状态：**仅本地候选，未推送、未发布**。版本记录自身提交以 Git 历史为准。

## 交付与历史保护

- [正文](../chapter15.md)共 26,585 个字符（含英文、代码与 Markdown），其中 13,695 个汉字；35 个二三级标题、7 幅图、6 张比较表、5 组实验、13 道练习及答案。
- 新增有限策略真实奖励更新、预算与探索；打通审计→SFT；验证偏好来源及两侧敏感检测；补充 Token 级 SFT、LoRA/QLoRA 和未执行迁移 smoke test；详见 [RC2 审稿](../reviews/chapter15-review-codex-v1.0-rc2.md)。
- [RC1 正文与 7 图归档](chapter15-v1.0-rc1/README.md)、[RC1 报告归档](../../chapter15/report-history/v1.0-rc1/post-training-report.md)与 v1 Schema 保留；原 [RC1 记录](chapter15-v1.0-rc1.md)和审稿不改写。
- 归档正文只调整相对链接以便阅读；原文件精确字节仍在 `65ff413`，原稿 SHA-256 为 `598be7754539600bf0ab9ebc43fc68f58cb539630c36c623b343b03e00680d3b`。旧 manifest 保持 `701ddeabb3093f2faa5d466cb85b65c251ee8b2ec023f149f5d762750c243a38`。
- 第 1–14 章原稿和历史 tag 不变。第 14 章仅新增 [待发布转场勘误](../errata/chapter14-next-chapter.md)，尚未应用于原稿或网站。

## 环境与数据合同

Python 3.11.15；pytest 9.0.2；jsonschema 4.26.0；Markdown 3.10.2；Node.js 24.15.0。使用忽略的 `.venv-chapter15/`，核心实验仍为标准库、离线、不读取 API Key、不下载模型。

报告为 `chapter15.post-training.v2`，manifest 仍为 `chapter15.artifact-manifest.v1`，练习为 `chapter15.exercises.v1`。24 条 SFT 轨迹的原始 split 为 12 train / 4 validation / 8 eval；12 条 eligible、12 条 quarantine，5 条合格 train 示例实际进入批量 SFT。偏好夹具额外派生 4 条人工受控 rejected 分支，不扩充 SFT 原始条数；反例工具均不执行。

奖励更新为单状态分类策略、固定种子 `1501`、学习率 `0.05`、最多 200 次更新、800 步总预算。安全变体先屏蔽 `modify_tests`，初始可选空间由三动作 `1/3` 变为两动作 `1/2`，所以不得把初始概率差异归因于学习。12 步预算演示运行 3 次更新、9 步后因无法预留下一动作最大 4 步而停止。

## 规范产物 SHA-256

| 产物 | 哈希 |
| --- | --- |
| `group-1.json` | `f8174ca493e4c1df6d4e481ed421ff096b28810da0037da033e8e4abb7413d40` |
| `group-2.json` | `6cbfed71c187c9602d7aa56a1a6191ce3379fbd83193115390c8bec442c44acc` |
| `group-3.json` | `9dffe418f2e7c40035674ca5901450bcfb7db7bc9d76e6df3d08acf22e819e36` |
| `group-4.json` | `085647c76b5b41e2a38eb0ce8b23b60a8ce2558b28d6dc03a9fee77863737ef9` |
| `group-5.json` | `fbd9c5cc6f6e57447b2ba54aa876363c7e0da03df2569432ada4ee1eb0e0400e` |
| `post-training-report.json` | `bcbe5cec952c8e5e11de5481d68cd1165ef64db62c457743ffb05ae2b5c1e62e` |
| `post-training-report.md` | `4c3cc1220259a7b4279a067fd4b9f61000f44ffcf33ae9a552dde076280128e1` |
| `manifest.json` | `0be675124324869d6f985b03bea9bd419159bbe2c5edd96e0db54e5597a49dc3` |
| `exercise-results.json` | `f8863d5caa48e53989f7a050fa7c0e6e5478e38af670d22185d7e21548c0ef70` |

## 验证记录

| 命令/检查 | 本轮结果 |
| --- | --- |
| `.venv-chapter15/Scripts/python.exe -B -m pytest chapter15/tests tests -q` | 175 项、89 个子测试通过；6 个 DPO 敏感回归先失败后通过 |
| `npm test --prefix book` | 4 项 Node 排版合同通过 |
| `python -B -m chapter15.experiments --group all --output chapter15/.runs/rc2-verified-a`，另运行 `rc2-verified-b` | 两份 manifest 与规范报告逐字节相同；固定哈希如上；输出均留在工程内忽略目录 |
| `python -B -m chapter15.exercise_solutions --all --output chapter15/.runs/rc2-verified-exercises-a.json`，另运行 `rc2-verified-exercises-b.json` | 安全修复后的两份练习结果与规范文件哈希相同 |
| `python -B -m chapter15.preview`、`node book/check_chapter15_preview.mjs` | 桌面 1440×1000 / 手机 390×844；7 图加载、6 表局部滚动、0 失效片段及整页横向溢出 |
| `tldraw export infographic/chapter15/04-sft-probability-shift.tldr -f png --scale 1 -o chapter15/.runs/rc2-tldraw` | 图源实际成功导出；本地检查字标与箭头，正文使用 SVG |
| `python -B scripts/check_repository.py --root . --git-history` | 当前树与可达历史检查通过；原有精确历史路径豁免不扩大 |
| `python -B scripts/build_site.py --root . --output _web`、`python -B -m mkdocs build --strict` | 218 个公开源文件，严格构建通过；第 15 章公开文件数为 0 |

根目录直接全量 `pytest -q` 收集时有 15 个既有错误，涉及独立章节依赖、同名测试模块与夹具路径；两个现有环境不具备 numpy/mcp/agents/langgraph 等依赖。本轮只承诺上表范围，没有以修改旧章、安装整书依赖或省略错误换取“全书测试通过”。

## 已证明与未证明

已证明：固定夹具中的来源敏感隔离、显式家族与词面指纹传递泄漏检查、实际审计数据进入有限 SFT、同上下文偏好来源核验、可复算 SFT/DPO、奖励驱动有限策略参数更新、受控探索前的安全屏蔽、预算预留、静态三态门禁以及报告可复现。

未证明：大模型权重或 GPU 训练收益、多步信用分配、参考策略 KL/PPO/GRPO 的实现、真实任务泛化、任意敏感数据识别、完整生产偏好前缀等价、四个静态标签桶代表真实任务切片、训练后策略通过独立冻结评测、供应商接口兼容或线上灰度安全。门禁 `pass` 的证据类型是 `static_gate_conformance_not_trained_policy_eval`，不是更新后策略发布许可。

资料以各项核对日期（2026-09-27/28）为界；main 文档只用于概念，实际训练必须另行冻结依赖、模型、数据和模板版本。新上下文复审的唯一 Important 已以一次 RED→GREEN 修复闭环；未再次独立复审修复提交。第 15 章保持 `planned`，公开 manifest 仍为 `0.14.0`。本轮不推送、不合并、不创建 tag/PR、不部署、不生成 PDF 或英文翻译。
