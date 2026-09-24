# 第 12 章 v1.0-rc2 本地候选记录

记录日期：2026-09-24。状态：**本地候选，未发布**。上一版本记录为 [v1.0-rc1](chapter12-v1.0-rc1.md)。

本版本只做出版表达和读者运行路径修订，不改变 Agent Runtime、工具、恢复、Verifier、框架适配器或规范实验报告。

## 相对 rc1 的变化

1. 在正文第一次运行实验之前补充 Python 3.11、虚拟环境和锁定依赖说明，并链接实验 README。
2. 正文不再并列展示中间开发阶段的测试数量；具体结果进入本版本记录，避免权限差异和后续增补让正文快速过期。
3. 删除“用户决定暂不安装”等协作过程措辞，改成可长期阅读的实验环境说明。
4. 将容器章节明确定位为生产隔离的理论合同和参考配置：当前没有完整探针编排，也不提供 Docker 实测结论或生产沙箱承诺。
5. 同步修改总目录，将“可在沙箱中完成任务”收束为“说明生产沙箱应满足的理论合同”。

## 证据边界

- 离线 Replay、真实文件读写、测试进程、SQLite、Verifier、LangGraph 与 OpenAI Agents SDK 的 rc1 证据保持不变。
- 真实模型运行仍未执行。
- 容器隔离仍为 `unverified`；本章不把完整 Docker 验证作为教学目标。
- `trusted_local` 只适用于仓库内可信 fixture 与经过审阅的 Replay，不适用于不可信代码。

## 本轮验证

- `.venv\Scripts\python.exe -B -m pytest chapter12/tests -q`：`210 passed`。本次在允许创建系统临时目录和符号链接的 Windows 环境中运行，因此 rc1 中因权限跳过的符号链接用例本轮通过。
- `.venv\Scripts\python.exe -B -m unittest discover -s tests -q`：43 项通过。
- `python -B -m scripts.check_repository`：通过。
- `python -B -m chapter12.preview` 与 `node book/check_chapter12_preview.mjs`：桌面端和 390px 移动端均加载七幅图片，正文新增链接无失效锚点；宽表格继续使用横向滚动容器。
- `.venv\Scripts\python.exe -B -m scripts.build_site`：生成 `site_sources=163`，第 12 章仍未进入公开 allowlist。
- `python -B -m mkdocs build --strict`：通过。站点构建使用已经安装 MkDocs 的系统 Python；章节测试虚拟环境不额外安装预览依赖。

## 历史保留

rc1 版本记录、审稿报告、提交历史、报告哈希和图片均不覆盖。本文件只记录 rc2 的小幅修订，公开 manifest 仍保持第 12 章为 `planned`，不代表已经发布。
