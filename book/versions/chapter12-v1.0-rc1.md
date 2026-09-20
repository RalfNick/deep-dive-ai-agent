# 第 12 章 v1.0-rc1 本地候选记录

记录日期：2026-09-20。状态：**本地候选，未发布**。分支：`codex/chapter12-mini-agent`。

本记录保存第 12 章第一份完整候选的事实边界。它包含正文、实验代码、两套真实框架适配、五组离线实验、14 道练习、七幅原创图、本地预览与双视角审稿。公开 `book/manifest.json` 仍为 0.10.1，第 12 章仍是 `planned`，没有进入站点 allowlist，没有 push 或 deploy。

证据边界：真实模型运行：未执行。容器隔离：未验证。当前候选全套测试：`209 passed, 1 skipped`。

## 候选内容

- 正文：`book/chapter12.md`
- 实验说明：`chapter12/README.md`
- 参考答案：`chapter12/reference-answers.md`
- 来源台账：`book/sources/chapter12-sources.md`
- Pi 源码研究：`chapter12/pi-source-study.md`
- 审稿报告：`book/reviews/chapter12-review-codex-v1.0-rc1.md`
- 图片与生成记录：`book/images/chapter12/`、`infographic/chapter12/`
- 本地预览：`python -B -m chapter12.preview`；生成的 HTML 和截图被忽略，不是发布产物。

## 锁定环境与证据

| 项目 | 值 |
| --- | --- |
| Python | 3.11.15 |
| LangGraph | 1.2.11，真实 StateGraph / interrupt / SqliteSaver 路径已测试 |
| OpenAI Agents SDK | 0.20.0，真实 Model / Runner / function tool / RunState 路径已测试 |
| OpenAI Python | 2.54.0；没有真实模型请求 |
| Pi | 仅源码阅读，固定提交 `19451accdeec671c1f4da9eafac8fc270f510ef4`；未安装、未运行 |
| 真实模型运行 | **未执行**；请求数、工具数与 usage 均为 0 |
| 容器隔离 | **未验证**；用户决定暂不安装运行时，预检为 `runtime_unavailable` |

离线规范报告 SHA-256：

- `offline-canonical.json`：`AFC9AB8544C6123D9FBB087238CA5C983B6FE0AC4C11D2AAAD90B1D8A672F5DB`
- `framework-comparison.json`：`0FF34EBDA6150297DEB4B24E14DAA62441A8CFA79026E4B33A59917EFFB69057`
- `exercise-results.json`：`B445B75D8FB4612AAEFBDEF3E8558F7A90D96442E986DB183685A798BB86E9C6`

两次新目录离线重跑的 combined report 与已提交规范报告字节一致。它们证明固定 Replay 决策下的协议、状态、恢复、Verifier 与框架适配行为，不证明模型能力、实时性能或敌对环境安全。

## 验收结果

| 命令 | 候选结果 |
| --- | --- |
| `python -B -m pytest chapter12/tests -q` | `209 passed, 1 skipped`；唯一 skip 为 Windows 符号链接权限 |
| 两次 `chapter12.experiments --group all` | 均退出 0；combined SHA-256 相同 |
| `python -B -m chapter12.exercise_solutions --all` | 输出 14 题；第 11 题 unverified，按合同退出 2 |
| `python -B -m chapter12.preview` | 生成本地候选 HTML |
| `node book/check_chapter12_preview.mjs` | 1440×1000 与 390×844 均为 7 图、无整页横向溢出、无资源失败 |
| `python -B -m unittest discover -s tests -q` | 43 项通过 |
| `python -B -m scripts.check_repository` | 通过 |
| `python -B -m scripts.build_site` | `site_sources=163`；不含第 12 章正文或实验入口 |
| `python -B -m mkdocs build --strict` | 通过；第 12 章未进入生成站点 |
| `git diff --check` | 通过 |

## 文件校验值

以下 SHA-256 在独立 review 的全部修订完成后计算。目录集合按仓库相对路径排序，对每个文件生成 `path<TAB>SHA256<LF>`，再对 UTF-8 清单求哈希；版本记录本身不纳入集合，避免自引用。

| 对象 | 文件数 | SHA-256 |
| --- | ---: | --- |
| `book/chapter12.md` | 1 | `C550B0300725019A01DB53CC2806299B7D1B52ABEEFE5FBBE2E4E2AF85C37CB1` |
| `book/reviews/chapter12-review-codex-v1.0-rc1.md` | 1 | `A1015E6F2F92C4FE51B1F8666E5ADC4C75823381D4EEB62333D9A77273021C7E` |
| `book/sources/chapter12-sources.md` | 1 | `84B41C4C32459155AC2A53DF4F382FEA3AABD8C5A9E2FB3A70B1D0AFF741C55B` |
| `chapter12/` 非忽略文件集合 | 77 | `30ADE6D89030F1AEBC630C7110401AC7BEFA04DE1AAE1F65EFA9B358A3D59179` |
| `book/images/chapter12/` | 7 | `643A6D772140B541EA8B838F4E3F146938C9F81F6C0B4FACC67BDF4BCB2CF6B9` |
| `chapter12/requirements.txt` | 1 | `A78E345A9CDE948EAD2CE10429E3C08DE75BFB959EF5D8E1891637DE46630C89` |
| `chapter12/requirements-frameworks.txt` | 1 | `5CF3E359EBAA0AE80B47CE706DFB9387EE2CBFCD7158ABE2E1118BC5ED26E881` |
| `chapter12/requirements-dev.txt` | 1 | `D5BDC1C977B9F68ABD525D56EDDB1E664795AAA2FA461EEFCA1603FF3C94949B` |

## 已知限制

1. 容器的非 root、只读根、禁网、凭据隔离、资源限制和取消清理没有真实探针证据。
2. 真实模型入口因隔离预检失败而在读取 API Key 前停止；没有模型能力、费用或延迟数据。
3. Windows 符号链接边界因当前权限跳过；Linux 只完成标准库路径探针，不等于容器合同。
4. trusted-local 会执行候选测试，只适合可信 fixture 与可信 Replay；自定义 Replay 需要显式信任断言，但该断言不是强制隔离。
5. 单任务、小仓库和固定 Replay 的结果不能外推成通用框架排名或生产指标。

## 历史保留

- 正文与首次 review 已在提交 `b8c324a` 保存。
- 七幅图与本地预览已在提交 `dac3f2a` 保存。
- 旧章节正文、已有 tag 和公开 manifest 未重写。
- 本记录是候选历史，不是发布说明；后续若形成 rc2，应追加新版本文件和提交，而不是覆盖 rc1 历史。
