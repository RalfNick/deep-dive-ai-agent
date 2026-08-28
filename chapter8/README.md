# 第 8 章实验：从零构建一条可治理 RAG 管道

本目录对应《深入浅出 AI Agent》第 8 章“RAG 与知识库：让 Agent 先查证，再回答”。公共实验只使用 Python 标准库，不需要网络、模型下载或 API Key。

## 你将构建什么

以 18 篇虚构“星舟工作台”产品与问答文档、20 个固定问题为语料，从 v0 到 v7 实现：

- 有版本、状态、时效、权限、信任与摘要的 Source Catalog；
- 固定字符、结构感知和上下文前缀三种切块；
- BM25 稀疏召回与固定概念向量语义召回；
- RRF 融合、确定性教学 Reranker 和 Catalog 返回前重查；
- Evidence Packet、稳定 Citation、Answer / Partial / Abstain；
- Retrieval、Citation、Answer 与 Governance 分层指标；
- JSON、Markdown 和脱敏 JSONL 三份可逐字节复现的报告。

固定语义编码器不是训练得到的 Embedding，教学 Reranker 也不是真实 Cross-Encoder。公共报告验证边界合同，不比较模型或产品能力。

## 目录

~~~text
chapter8/
├── knowledge_runtime/
│   ├── contracts.py       # Document、Chunk、Query、Hit、Citation 与 Evidence
│   ├── catalog.py         # 文档加载、Schema 校验与硬过滤
│   ├── chunking.py        # 三种切块策略
│   ├── sparse.py          # BM25 与中英混合教学分词
│   ├── dense.py           # 可替换协议与固定概念向量
│   ├── fusion.py          # RRF
│   ├── rerank.py          # 可解释教学精排
│   ├── retrieve.py        # 过滤、召回、融合、重排与 Catalog 重查
│   ├── evidence.py        # Evidence Packet、Citation 与拒答
│   └── evaluation.py      # 分层指标
├── fixtures/
│   ├── starboard_docs/    # 18 篇 Markdown 与 18 份元数据
│   └── questions.json     # 20 个固定问题
├── experiments/run_all.py # 五组实验
├── reports/               # 规范报告
├── live/                  # 可选真实模型探针
├── tests/                 # 合同、故障、报告与出版门禁
└── reference-answers.md   # 14 道练习答案
~~~

## 环境与运行

- Python 3.11–3.13；
- 公共路径无第三方运行依赖；
- 固定时钟是 Fixture，不读取当前时间；
- Live Probe 默认 dry-run，输出不进入规范报告。

运行测试：

~~~powershell
python -m unittest discover -s chapter8/tests -v
~~~

生成报告：

~~~powershell
python -m chapter8.experiments.run_all --output chapter8/reports
~~~

连续运行两次，以下文件应逐字节相同：

- `reports/rag-evidence.json`
- `reports/rag-evidence.md`
- `reports/rag-trace.jsonl`

## 五组实验

| 组 | 案例数 | 主要观察 |
| --- | ---: | --- |
| baseline | 3 | 无引用猜测、全量 Context 冲突、无答案边界 |
| chunking | 3 | 结构完整、标题路径、原文摘要不变 |
| retrieval | 4 | Precision、Recall、MRR、NDCG 与空结果 |
| governance | 5 | 版本、权限、未来、撤回、陈旧索引 |
| evidence | 5 | 缺失事实、错引、冲突、注入与拒答 |

每个案例 `sample_count=1`。报告不提供聚合“RAG 成功率”；未测 Provider Token、费用、延迟与真实模型质量保持 `null`。

## 建议阅读顺序

1. 先运行报告，找到贯穿问题与 `governance-compound-upgrade`；
2. 阅读 `contracts.py` 和 `catalog.py`，理解合法性为什么早于相关性；
3. 阅读 `chunking.py`、`sparse.py`、`dense.py` 与 `fusion.py`；
4. 沿 `retrieve.py` 跟踪一次 Query 的分项和 Return Gate；
5. 最后读 `evidence.py` 与 `evaluation.py`，区分命中、引用和支持。

正文见 `book/chapter8.md`，来源边界见 `book/sources/chapter8-sources.md`。
