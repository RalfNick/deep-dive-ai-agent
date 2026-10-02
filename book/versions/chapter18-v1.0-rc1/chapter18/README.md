# 第18章：有界协作与最小最终系统

固定决策策略、真实资料读取、真实可信夹具修改和验证。无需 API Key，运行时只用 Python 标准库；不是模型能力或 SDK 排名。

从仓库根目录运行。建议 Python 3.11；测试依赖和哈希锁在 `requirements-dev.txt`，预览依赖在 `requirements-preview.txt`。本轮验证环境为 Python 3.11.15 / pytest 9.0.2 / jsonschema 4.26.0 / Markdown 3.10.2。已有兼容环境可直接用；本章不自动安装工具，不联网读取模型。

```powershell
python -m pip install --require-hashes -r chapter18/requirements-dev.txt
python -m pip install --require-hashes -r chapter18/requirements-preview.txt
python -B -m pytest chapter18/tests -q
python -B -m chapter18.experiments --group all --output chapter18/.runs/reader-first
python -B -m chapter18.exercise_solutions --all --output chapter18/.runs/answers-reader.json
python -B -m chapter18.preview
```

安装只用于读者自备环境，不是实验的运行时网络请求。输出必须使用新名称，已存在空目录也拒绝覆盖。全实验输出9文件；`--group 1`至`--group 5`输出2文件，明确标为 partial，不能冒充完整Suite。真实工作区在同级 `.runs/<输出名>-workspaces/`。

两条最小业务路径：

```powershell
python -B -m chapter18.quickstart --mode knowledge --workdir chapter18/.runs/knowledge-reader
python -B -m chapter18.quickstart --mode repair --workdir chapter18/.runs/repair-pending-reader
python -B -m chapter18.quickstart --mode repair --approve --workdir chapter18/.runs/repair-approved-reader
```

预期分别为 answer、needs_approval、verified。默认知识路径读取两份当前合格资料，覆盖1/1、工具调用2；冲突资料不会被首项选择掩盖，超过在途限额时分批。批准修复：真实写入一次，可信测试4/4，独立行为探针通过；工具调用5，其中最终验证2。未批准不写入。

材料入口：

- [书稿](../book/chapter18.md)与[来源台账](../book/sources/chapter18-sources.md)。
- [审稿后规范摘要](reports/reference-rc1-reviewed/summary.md)、[总报告](reports/reference-rc1-reviewed/team-report.json)、[manifest](reports/reference-rc1-reviewed/manifest.json)。
- [十三题参考答案](reference-answers.md)、[实现/未实现边界](IMPLEMENTATION.md)。
- [七幅图的可编辑源与生成记录](../infographic/chapter18/README.md)。

默认总工具额度16内含验证保留2；所有Worker共享14，不因委派或handoff重置。教学耗尽案明确使用8/2。场景使用虚构星舟问答和可信小仓库，不执行任意不可信代码，不提供操作系统沙箱、容器部署、跨进程恢复或生产审批服务。逻辑排程23/16不是实测延迟。公开站点未加入第18章。

子任务收紧额度约束自身及后代的工具尝试和提交，仍扣共享账本；不创建新的验证池。旧 `reports/reference-rc1/` 是审稿前候选证据，原字节保留，不作为当前语义门禁的通过报告。正文与可运行代码的审稿前完整状态可从提交 `14493f9` 恢复；本次首次 RC1 冻结以 reviewed 包为准。
