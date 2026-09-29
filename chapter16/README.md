# 第16章：从失败中学习

本地候选，未发布。Python3.11+标准库运行时；不联网，不读取环境密钥，不调用模型/外部工具。固定seed1601、时钟2026-09-28T00:00:00Z；TTL实验显式推进时钟。夹具是虚构Atlas帮助中心，不是客户数据。

在仓库根运行；若需要独立环境：

```powershell
python -m venv .venv-chapter16
.venv-chapter16/Scripts/python.exe -m pip install --require-hashes -r chapter16/requirements-dev.txt
.venv-chapter16/Scripts/python.exe -m pip install -r chapter16/requirements-preview.txt
```

将下面的python换成该环境解释器即可；纯实验不用安装开发/预览依赖。

```powershell
python -B -m chapter16.experiments --group all --output chapter16/.runs/reader-first
python -B -m pytest chapter16/tests -q
python -B -m chapter16.exercise_solutions --all --output chapter16/.runs/answers-first.json
python -B -m chapter16.preview
```

每次用全新路径。已有空目录/文件也拒绝，exit3；参数错误exit2，成功exit0。报告仅允许chapter16/.runs或首次创建的chapter16/reports，越界/链接/Windows reparse父链拒绝。部分磁盘失败保留说明，不自动清理或覆盖。路径检查假设没有恶意进程在检查后并发改文件系统，不是操作系统级沙箱。

逐组运行：`--group 1`、`2`、`3`、`4`、`5` 都需 `--output chapter16/.runs/group-N-first.json`，只输出对应组。全组产生5组JSON、总JSON、摘要Markdown、13题结果与manifest，共9文件。

先读group1的准入状态；再读group2的回放/未知分母；group3看document_id、steps、answer_style与实际资产哈希；group4看三态门禁；group5看批准绑定、4/12离线分配和显式时钟变化后的stop/rollback。失败与未决是实验的一部分，不手改JSON“修分数”。

知识规则、步骤Skill与范围记忆实际改变有限策略行为；Prompt/Harness/训练候选只是提案。这里证明机制合同，不证明模型能力、自动归因、盲测泛化或生产A/B收益。批准注册表是进程内受信任演练，不是签名/IAM服务；回滚不会撤销外部副作用。

入口：[正文](../book/chapter16.md)、[参考答案](reference-answers.md)、[规范报告](reports/improvement-report.json)、[来源](../book/sources/chapter16-sources.md)。可选预览使用Markdown==3.10.2；HTML与截图只在忽略目录，不写公开站点。
