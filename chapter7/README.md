# 第 7 章实验：从零构建一个 Memory Runtime

本目录对应《深入浅出 AI Agent》第 7 章“记忆：不是把聊天记录全部塞回去”。实验只使用 Python 标准库，不需要 API Key、向量数据库或远程模型。

## 你将构建什么

`memory_runtime/` 实现四个跨任务操作：

- Write：候选信息经过策略闸门后才能提交；
- Recall：先做作用域、状态、有效期和敏感级别硬过滤，再做可解释排序；
- Correct：新值形成连续版本，并通过 `supersedes` 指向旧值；
- Forget：Tombstone 阻止旧版本继续召回，并生成不含正文的删除收据。

它是确定性的教学实现，不包含真实 LLM、Embedding、向量库、分布式事务和合规删除后端；Fixture 直接提供结构化来源与 Authority，不等于生产环境已经认证这些身份。

## 目录

~~~text
chapter7/
├── memory_runtime/
│   ├── contracts.py       # Candidate、Record、Query、Tombstone 等公共合同
│   ├── policy.py          # Write Gate
│   ├── store.py           # 追加版本链与当前投影
│   ├── recall.py          # 硬过滤与可分解排序
│   ├── runtime.py         # Write / Recall / Correct / Forget 编排
│   └── persistence.py     # UTF-8 JSONL Event Log 往返
├── fixtures/              # Coding Agent 跨任务固定夹具
├── experiments/run_all.py # 五组、15 个确定性案例
├── reports/               # JSON、Markdown、脱敏 JSONL
├── tests/                 # 合同、并发、报告和出版门禁
└── reference-answers.md   # 14 道练习答案
~~~

## 环境

- Python 3.11–3.13；
- 无第三方运行依赖；
- 公共实验不读取任何 Provider 凭据；
- 固定时钟为报告夹具的一部分，不使用当前系统时间。

## 运行测试

~~~powershell
python -m unittest discover -s chapter7/tests -v
~~~

## 重新生成报告

~~~powershell
python -m chapter7.experiments.run_all --output chapter7/reports
~~~

规范文件为：

- `reports/memory-engineering.json`：五组案例、独立指标与 Claims；
- `reports/memory-engineering.md`：便于阅读的结果表；
- `reports/memory-engineering-trace.jsonl`：逐案例脱敏证据码。

连续执行两次生成命令时，三份文件应逐字节一致。报告只记录 UTF-8 序列化结果；任何字节数都不是 Token 数。

## 五组实验

| 组 | 改变什么 | 主要观察 |
| --- | --- | --- |
| baseline | 无记忆、完整历史、结构化 Memory | 任务验收与一次性规则误用 |
| write | 全写、策略闸门、闸门加人工复核 | 写入精确率、写入召回率、Secret 写入 |
| recall | 全局扫描、只做作用域、作用域加排序 | 召回精确率、跨作用域泄漏 |
| correct | 原地覆盖、版本化修正、陈旧写者 | 审计链、修正收敛、并发冲突 |
| forget | 陈旧索引、回主 Store 解析、跨租户探针 | 删除后泄漏与隔离 |

每个变体只有一个固定案例，`sample_count_per_case=1`。它支持边界符合性判断，不支持真实模型平均表现、生产成功率或产品排名。

## 建议阅读顺序

1. 先运行测试和报告，不急着读全部实现；
2. 阅读 `contracts.py`，理解每条记录为什么不只是字符串；
3. 阅读 `policy.py` 与 `recall.py`，比较 Write 和 Recall 的不同责任；
4. 阅读 `store.py`，手动追踪 v1、v2 与 Tombstone；
5. 最后阅读 `experiments/run_all.py`，核对报告指标怎样由实际执行产生。

正文见 [`book/chapter7.md`](../book/chapter7.md)，练习答案见 [`reference-answers.md`](./reference-answers.md)。
