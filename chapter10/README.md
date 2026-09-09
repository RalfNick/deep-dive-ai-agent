# 第 10 章实验：大规模工具集与异步任务

状态：v1.1，已发布；v1.0 由历史标签完整保留。先读[正文](../book/chapter10.md)，练习对应[参考答案](reference-answers.md)。

## 十分钟开始

需要 Python 3.11+。在仓库根目录运行；五组实验只用标准库，不调用任何模型或外部业务接口，不需要 API Key。

```powershell
python -m chapter10.quickstart
python -m chapter10.experiments --group catalog
python -m chapter10.experiments --group boundaries
python -m chapter10.experiments --group concurrency
python -m chapter10.experiments --group lifecycle
python -m chapter10.experiments --group failures
python -m unittest discover -s chapter10/tests -v
```

| 组 | 看什么 | 关键输出 |
| --- | --- | --- |
| catalog | 目录、发现、加载与实际描述体积 | 300 / 299 / 2；全量 93,644 字节，按需载荷 1,412 字节 |
| boundaries | 空结果、歧义、预算、撤权、版本变更 | `[]`、两个平分项、`definition_budget_exceeded`、`denied`、`stale_definition` |
| concurrency | 固定 worker 数与结果归属 | 峰值在途 2；A、B 成功，C 明确失败 |
| lifecycle | 重新连接、进度、唯一结果、事件补读 | 3 条八月记录，共 6,000 分；游标 5 后只有成功事件 |
| failures | 提交冲突、迟到执行、取消、期限、重试 | 同键复用；旧代次拒绝；取消前后不同终态；重试有上限 |

命令每次在临时目录中建立独立 SQLite 数据库，结束时自动清理，不连接用户数据库。`--group` 筛选展示输出；当前小规模实现会先运行全部五组，因此每组都是同一套证据的一个视图。

`quickstart` 先完整展示提交、领取、计算、进度、结果提交与查询，再进入五组实验。它输出 `queued → running → succeeded`、三条八月记录和 6,000 分结果，使用临时数据库并自动清理；不包含后台调度器。`finish()` 验证提交资格，业务结果正确性由报表层负责，固定夹具由测试独立核验。

## 文件与阅读顺序

先运行并阅读 [quickstart.py](quickstart.py)，把接口连接顺序走通，然后按下面顺序看实现。

1. [catalog.py](catalog.py)：权限过滤 → 关键词打分 → 完整定义加载 → 再检查。
2. [concurrency.py](concurrency.py)：用固定数量 worker 消费有限输入列表。
3. [jobs.py](jobs.py)：SQLite 事务、作业状态、领取代次、取消与结果回执。
4. [experiments.py](experiments.py)：组装五组实验，安排逻辑时间与故障。
5. [tests](tests)：行为测试和参考解答；不是 Agent 真实任务成功率评测。

目录中 296 个归档工具只是合成定义，不是实际可调用连接器；目录的统一 `record_id` Schema 与报表作业的 `month` 参数是两个独立实验接口。没有一个隐含的真实模型在替你完成适配。

## 固定报告

```powershell
python -m chapter10.experiments --write
```

重建 [JSON](reports/tool-jobs-evidence.json)、[可读报告](reports/tool-jobs-evidence.md) 和 [事件流](reports/job-events.jsonl)。生成器显式使用 UTF-8/LF，无当前时间、随机 UUID、主机路径。重复运行应得到相同字节。

## 可选本地排版预览

预览不是实验依赖，不影响无第三方包的运行方式。

```powershell
python -m pip install -r chapter10/requirements-preview.txt
python -m chapter10.preview
```

生成 `chapter10/preview-pages/index.html`，用浏览器打开即可。该目录被 Git 忽略；网页引用仓库内相对资源，搬迁整个工程后仍可打开。可选预览测试在未安装 Markdown 时会明确跳过；运行时测试不会跳过。

## 边界

- 字节不等于 Token；没有测真实模型、网络延迟或外部吞吐。
- 作业库没有身份认证、HTTP 服务、后台调度守护进程、自动续租或文件下载接口。
- `now`、`owner`、`grants` 必须由可信运行时提供；内部 worker 方法不能直接公开。
- 恢复是重新领取可重复计算，不是恢复 Python 栈；所有写效果局限于同一 SQLite 结果事务。
- 唯一回执不保证邮件、付款等外部操作 exactly-once；需要外部幂等、查询或人工对账。
- 报告只证明列出的边界，本地重新连接不等于断电或磁盘故障测试。

资料核对与复审见[来源台账](../book/sources/chapter10-sources.md)、[自审记录](../book/reviews/chapter10-review-codex.md)。
