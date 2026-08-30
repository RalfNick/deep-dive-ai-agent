# 来源：第 8 章“RAG 与知识库”

来源文件：`book/chapter8.md`。

## RAG 的边界

> RAG 位于外部知识进入 Context 的路径上，它不直接改写模型参数，也不自动成为长期 Memory。

> 长上下文回答的是“能否放下”，RAG 回答的是“哪些内容有资格进入、为什么进入、怎样引用”。

## 四个职责

> Catalog 管“有没有资格”，Retriever 管“与问题是否相关”，Evidence Gate 管“能否支持声明”，Answer Policy 管“此刻应该说多少”。

## 离线知识加工

原始文件先解析结构并建立 Source Chunk，再处理重复内容、版本关系和治理字段，最后生成稀疏或稠密索引。派生问答与事实卡只能帮助召回，引用和验收仍要回到当前有效的 Source Chunk。

## 在线证据回答

Actor、目标版本和查询时间先进入 Catalog 过滤；合法候选参加混合召回；融合和重排后再经过 Return Gate，最终形成 Evidence Packet。Answer Policy 只表达被证据覆盖的事实；证据不足时部分回答或拒答。

## 完整请求的原文步骤

1. 获得 Actor，并提取版本与必需事实；
2. Catalog 排除旧版本、未来预告、撤回草稿和越权文档；
3. BM25 与语义通道召回，RRF 融合，Reranker 精排；
4. Return Gate 回查 Catalog；
5. Evidence Builder 形成事实、冲突和引用；
6. Answer Policy 只表达被覆盖的事实；
7. Verifier 验证引用，Recorder 保存脱敏事件链。

## 核心判断

> 这不是“回答能力变差”，而是把不确定性变得诚实、可定位。
