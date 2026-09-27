# 第 11 章 v1.0 正式发布记录

发布日期：2026-09-27。正式标签：`book-chapter11-v1.0`。发布基线：v1.0-rc2；rc1 与 rc2 的正文、代码、报告和 Review 历史均保留。

## 发布内容

- 正文《Coding Agent：代码库就是它的环境》、7 幅在用原创图、5 组无 API Key 实验、14 道练习与参考答案；
- 配套工作台真实执行 Git、文件和测试子进程，覆盖目标红灯、过期补丁、零测试假绿、验收反例与旧证据失效；
- 产品观察指南把 Codex 与 Claude Code 映射到同一观察合同，但不把文档步骤冒充产品实测。

## 发布验证

- `python -B -m unittest discover -s chapter11/tests -v`：26 项通过；
- 规范 JSON 与 Markdown 两次生成逐字节一致；
- 仓库合同、发布安全检查、Node 排版合同与 MkDocs strict 构建通过。

规范 JSON SHA-256：`135ed5792a6577e567b7e826b7b710272c7a652d67ea71b39917317374f44422`。规范 Markdown SHA-256：`375d0b8d9a75266648c2c32594b53862861b549cf10c2c83c45ffb4cebd0bb50`。

## 证据边界

本版本没有运行真实 Codex 或 Claude Code 修复，没有安装 Skill、Hook 或子 Agent，也没有把可信教学仓库放入恶意代码沙箱。固定工作台验证的是仓库调查、修改与验收合同，不是模型或产品排名。
