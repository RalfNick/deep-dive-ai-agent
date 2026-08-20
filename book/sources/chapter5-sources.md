# 第 5 章资料台账：上下文工程

核对日期：2026-08-16。模型名称、API 字段、产品默认行为、上下文上限和自动压缩策略属于快速变化信息，出版前必须再次核验。

## 使用原则

- 本章只回答“本次模型调用看见什么、为什么看见、以什么权威与格式看见”；长任务压缩、长期记忆和 RAG 内部机制分别留给第 6、7、8 章；
- 产品行为只使用厂商官方文档、官方工程博客或官方开源仓库；研究结论优先使用原始论文；
- 作者先前文章和用户提供的 PDF 用于发现概念、术语与阅读路径，不作为快变事实的最终依据；
- 本章实验固定模型决策策略或使用可选真实模型探针，分别评估 Build、Decision 与 Safety，不把三层压成一个“成功率”；
- 离线实验只能证明确定性的上下文边界是否生效，不能证明某个真实模型更强；
- 不把内容中自称“系统指令”的文字升级为高权威指令；来源渠道与权威等级必须由 Harness 在内容之外赋予。

## 论点—来源映射

| 论点或快变事实 | 主要来源 | 证据类别 | 正文用途 | 出版前复核 |
| --- | --- | --- | --- | --- |
| Context 不只是 Prompt，还包括消息、工具、检索证据、运行状态与输出约束 | Anthropic, *Effective context engineering for AI agents*；LangChain Context Engineering 文档 | 官方工程实践 / 官方文档 | 概念边界、Context Packet | 是，术语会演进 |
| 长窗口是容量，不等于每个位置都能被同等利用 | Liu et al., *Lost in the Middle*；Hsieh et al., *RULER* | 同行评审论文 / 原始论文 | 信息位置实验、外推限制 | 否，论文结论稳定；模型外推需复测 |
| 工具名称、描述与参数会参与模型的工具选择 | DeepSeek Chat Completions API / Tool Calls；LangChain Context Engineering | 官方 API / 官方文档 | 说明原生工具协议背景；本章实验只验证文本化工具合同 | 是，API 字段会变化 |
| 外部数据可能携带间接提示注入 | Greshake et al., 2023；OpenAI Prompt Injection 安全说明 | 原始论文 / 官方安全说明 | 不可信内容与 Action Gateway | 是，缓解建议会变化 |
| `AGENTS.md` / `CLAUDE.md` 是产品装配的项目上下文，而不是 OS 级强制策略 | Codex `AGENTS.md` 文档；Claude Code Memory 文档 | 官方产品文档 | 产品映射与权威边界 | 是，发现与加载规则会变化 |
| 上下文应采用小入口、按需展开，而不是单个巨大说明文件 | OpenAI Harness Engineering；Anthropic Context Engineering | 官方工程案例 | 预加载与 Just-in-time、工程清单 | 是，不外推案例数字 |
| DeepSeek 教学适配器当前使用 `/chat/completions`、JSON Output，并校验 `message.content` 中的教学 JSON | DeepSeek Chat Completions API、Error Codes | 官方 API | 可选真实模型探针；明确未实现原生 `tools/tool_calls` | 是，模型名与字段为快变项 |

## OpenAI 与 Codex 官方资料

| 来源 | 本章核对的事实 | 使用边界 |
| --- | --- | --- |
| OpenAI, [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md/)（2026-08-16 访问） | Codex 从全局到项目当前目录发现并拼接指令文件；更接近工作目录的内容位于组合输入后部；组合大小受配置限制 | 发现顺序、默认字节限制和页面地址会变化；正文不把“后出现”写成绝对服从保证 |
| OpenAI, [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/), 2026-01-23 | Agent Loop 把模型输入、工具定义、工具结果和后续消息持续纳入模型可见历史，并需要管理窗口增长 | 只用于说明 Context 是运行时装配物；具体内部实现需复核 |
| OpenAI, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/), 2026-02-11 | 巨大单一 `AGENTS.md` 会挤占任务与相关资料；实践采用短入口、结构化仓库知识和渐进披露 | “约 100 行”等为特定团队案例，不作为普遍阈值；不引用速度和规模数字 |
| OpenAI, [How GPT-5.6 fuses frontier intelligence with frontier efficiency](https://openai.com/index/gpt-5-6-frontier-intelligence-efficiency/), 2026-07-29 | Agentic Harness 通过延迟发现控制工具与插件带来的上下文膨胀，并用确定性顺序与追加式历史改善前缀缓存复用 | 具体工具输出上限、产品默认值和缓存结果属于快变项；不把性能数据外推 |
| OpenAI, [Understanding prompt injections](https://openai.com/safety/prompt-injections/)（2026-08-16 访问） | 第三方内容可通过对话上下文误导 Agent，提示注入是跨行业仍在研究的安全问题 | 官方页面给出风险认知而非完备防御证明；本章用确定性网关作第二道边界 |

## Anthropic 与 Claude Code 官方资料

| 来源 | 本章核对的事实 | 使用边界 |
| --- | --- | --- |
| Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), 2025-09-29 | Context Engineering 是对推理时完整 Token 集合的选择和维护；建议高信号上下文、清晰工具、Just-in-time 检索与渐进披露 | 压缩、记笔记和多 Agent 的内部实现留到后续章；工程经验不是模型无关定律 |
| Claude Code Docs, [How Claude remembers your project](https://code.claude.com/docs/en/memory)（2026-08-16 访问） | `CLAUDE.md`、项目规则和自动记忆进入会话上下文；官方明确其属于上下文而非强制配置 | 路径、加载顺序、行数与字节阈值是快变项；不把产品当前默认写成永久契约 |
| Claude Code Docs, [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)（2026-08-16 访问） | 上下文可包含历史、文件、命令输出、`CLAUDE.md`、记忆、Skills 与系统指令 | 自动压缩细节只用于章节边界提示，详细讨论留给第 6 章 |
| Claude Code Docs, [Extend Claude Code](https://code.claude.com/docs/en/features-overview)（2026-08-16 访问） | 不同扩展以不同加载时机消耗上下文；过多扩展会增加噪声，工具 Schema 可按需加载 | 具体成本表和默认加载策略需出版前复核 |

## LangChain 与 LangGraph 官方资料

| 来源 | 本章核对的事实 | 使用边界 |
| --- | --- | --- |
| LangChain Docs, [Context engineering in agents](https://docs.langchain.com/oss/python/langchain/context-engineering)（2026-08-16 访问） | 单次模型上下文包括指令、消息、工具、模型与输出格式；工具名称、描述和参数会影响何时、怎样使用工具；Transient Context 与持久状态应区分 | 中间件、类名、示例模型和 API 会变化；本章只映射职责，不围绕框架 API 组织正文 |
| LangChain Docs, [Context overview](https://docs.langchain.com/oss/python/concepts/context)（2026-08-16 访问） | 可用可变性和生命周期描述 Context；运行配置不一定自动进入模型输入 | 用于术语对齐，不把框架术语当唯一标准 |
| LangGraph Docs, [Memory](https://docs.langchain.com/oss/python/langgraph/add-memory)（2026-08-16 访问） | 消息裁剪、删除、摘要和 Checkpoint 是不同操作 | 仅用于说明与第 6 章的边界；本章不实现长任务压缩 |
| LangGraph Docs, [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)（2026-08-16 访问） | Checkpoint 保存图状态并支持恢复，与单次模型 Context 不同 | 具体 Checkpointer / Store API 留到后续章 |

## DeepSeek 官方资料与真实模型探针

| 来源 | 本章核对的事实 | 使用边界 |
| --- | --- | --- |
| DeepSeek, [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/), 2026-08-16 访问 | 当前端点为 `POST /chat/completions`；消息支持 system/user/assistant/tool；工具描述用于模型选择；JSON Output 使用 `response_format={"type":"json_object"}` 且提示中需明确 JSON；当前页面列出 `deepseek-v4-pro` 与 `deepseek-v4-flash` | 所有模型名、默认 Thinking、枚举与限制出版前必查；正文不把当前模型当长期默认 |
| DeepSeek, [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls), 2026-08-16 访问 | 原生协议通过请求 `tools[].function` 提供 Schema，并从响应 `message.tool_calls` 读取提议 | 本章只用它界定“尚未实现什么”；原生工具协议留给第 9 章 |
| DeepSeek, [Error Codes](https://api-docs.deepseek.com/quick_start/error_codes/), 2026-08-16 访问 | 401、403、429、5xx 等需要映射为可诊断的失败状态 | 错误码和重试建议会变化；教学适配器不会静默回退到离线策略 |
| DeepSeek, [JSON Output](https://api-docs.deepseek.com/guides/json_mode/), 2026-08-16 访问 | 结构化实验请求需要同时配置 JSON Output 并在消息中要求 JSON | 页面偶有抓取超时，最终出版需重新打开核对 |

真实探针通过环境变量 `DEEPSEEK_API_KEY` 读取凭据，不在代码、命令、Trace、报告或正文中保存 Key。当前实现默认模型来自 2026-08-16 的官方 API 页面；缺少凭据时写出 `run_status=config_error`、`configuration_error=missing_credential` 的零尝试报告并以退出码 2 结束，已经发起请求后的认证、限流、超时或格式错误则记录为具体 Provider 状态。两类失败都不能伪装成真实模型结果。

## 原始论文

| 来源 | 本章使用内容 | 外推限制 |
| --- | --- | --- |
| Liu et al., [Lost in the Middle: How Language Models Use Long Contexts](https://aclanthology.org/2024.tacl-1.9/), TACL 2024 | 在多文档问答和键值检索中，相关信息位置变化可显著影响受测模型表现；提出位置敏感的长上下文评测思路 | 不能推断所有 2026 模型必然呈同样 U 形，也不能把本章确定性位置实验称为论文复现 |
| Hsieh et al., [RULER: What's the Real Context Size of Your Long-Context Language Models?](https://arxiv.org/abs/2404.06654), 2024 | 标称窗口、简单 Needle 测试与多任务有效上下文能力不是同一指标 | 受测模型与版本已过时；本章仅借鉴“按任务和长度评测”的方法 |
| Greshake et al., [Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173), 2023 | 外部检索数据中的自然语言可模糊数据与指令边界，并影响工具化应用 | 本章合成字符串只是最小攻击夹具，不代表覆盖真实攻击面或证明完整防御 |
| Vaswani et al., [Attention Is All You Need](https://papers.neurips.cc/paper/7181-attention-is-all-you-need), NeurIPS 2017 | 自注意力使 Token 表示依赖序列内其他位置，为读者连接第 1 章与“模型只处理输入投影”提供基础 | 不用该论文直接证明现代 Agent 的上下文策略或产品行为 |

## 作者既有文章与本地工程资料

| 来源 | 本章使用内容 | 处理方式 |
| --- | --- | --- |
| `docs/codex-tutorial/2026-07-29-context-architecture.md` | Prompt / Context / Session / Memory 边界、Context Packet、五道选择闸门、`missing_topics`、Write/Select/Compress/Isolate 和分层评估思路 | 作为作者先前研究线索；本章重新设计数据模型、实验合同与文字，不直接复制文章结论或图 |
| `docs/codex-tutorial/2026-07-31-harness-engineering.md` | Context Builder 与 Action Gateway 的责任边界 | 与第 4 章保持术语连续；不重复状态机、审批、幂等与 Verifier 细节 |
| `docs/codex-tutorial/2026-07-31-tool-engineering-agent-tools.md` | 工具名称、描述、参数与错误返回同时是模型接口和执行接口 | 本章只评估作为普通 Context Section 的文本化工具合同，完整原生工具协议留给第 9 章 |
| `docs/codex-tutorial/2026-08-04-memory-engineering.md` | Context、RunState、Session、长期 Memory 与事实源的生命周期边界 | 用来防止第五章提前写完记忆章节 |
| `book/chapter4.md` | Harness 全局地图、模型只看见环境投影、工具提议与真实执行分离 | 第五章实现上一章尚未实现的 Context Builder，并复用 Action Gateway 作为安全后置边界 |
| `book/OUTLINE.md` | 第 5 章范围、与第 6–8 章的分工 | 已纳入 v1.1 版本历史，发布 tag 可独立重建章节范围依据 |
| `chapter5/context/`、`chapter5/experiments/`、`chapter5/tests/` | 本章 ContextItem、Builder、Serializer、Probe、Gateway、五组实验与 63 项测试 | 正文工程结论的首要本地证据；发布前已从工作树根目录重跑 |
| `chapter5/reports/context-experiments.json` | 30 条确定性实验记录以及分层指标；SHA-256 `1F7B18137B1F3A44188DA3FCF5C682370CD47288DFD8114292FF593B759A396E` | 只报告各指标和失败类型，不计算跨层总分；两次生成字节一致 |

## 用户提供资料

| 文件 | 已检查范围 | 本章采用内容 | 限制 |
| --- | --- | --- | --- |
| 用户提供资料 `AI学习资料.pdf`，23 页 | 2026-08-15 逐页渲染检查；文档为图片型 PDF | 第 20 页 Token / 位置编码词条用于确认入门衔接；第 21 页注意力与 RAG 词条用于术语边界；第 22 页 Function Call 与向量检索、第 23 页 Agent / MCP / Skills / A2A 用于检查读者可能混淆的概念 | 属于作者整理的二手学习资料，不作为 API、产品默认行为或安全结论的一手证据；不复用原图和大段文字；作者本机路径不进入公开仓库 |
| 用户提供资料 `大模型入门.pdf` | 2026-08-15 在用户当时提供的位置未找到 | 暂未使用 | 文件重新提供后再做页码级增量核对；缺失不阻塞本章，因为第 1 章与官方资料已覆盖必要基础；作者本机路径不进入公开仓库 |

## 本章实验的证据合同

1. **固定项**：任务夹具、候选 ContextItem、SourcePolicy、预算单位、离线 Probe 规则和 Action Gateway；
2. **改变项**：组装策略、冲突内容、关键信息位置、文本化工具合同、噪声与注入内容；
3. **Build 指标**：必需信息召回、无关信息保留、缺失主题显式率、超预算量、来源与排除原因完整性；
4. **Decision 指标**：结构化输出有效性、目标值是否正确、是否在证据不足时请求上下文；
5. **Safety 指标**：秘密泄漏数、夹具相关的注入服从观察、策略违规数、Action Gateway 是否拦截危险提议；`passed` 只表示固定 Fixture 合同通过，不是系统安全认证；
6. **不证明的内容**：模型排名、通用提示模板、真实生产成功率、完整 RAG 质量、完整提示注入防御或供应商 SLA；
7. **真实模型运行**：属于可选 Probe，必须记录模型名、请求摘要、Provider 状态与时间；缺少 Key 时明确跳过。

## 出版前更新检查

1. 重新核对 Codex `AGENTS.md` 的发现顺序、默认大小上限和最终文档地址；
2. 重新核对 Claude Code `CLAUDE.md`、Memory、Skills、MCP Schema 与 compaction 的加载行为；
3. 重新核对 DeepSeek 模型名、端点、Thinking 默认值、JSON Output 和错误码；
4. 记录最终真实模型探针的日期、模型、脚本 commit 和原始报告摘要，不保存凭据；
5. 从干净环境重跑 Chapter 4/5 测试与五组实验，核对报告哈希；
6. 复核论文表述没有从“受测模型”外推为“所有模型”；
7. 检查 7 幅原创图没有复用用户 PDF 或厂商文章的图形资产；
8. 如果用户重新提供《大模型入门.pdf》，补做页码级台账，但仅吸收与本章范围直接相关的内容；
9. 检查所有外链可访问，并保存标题、作者、日期和必要的版本元数据；
10. 对正文中的产品名、模型名、命令、默认值和阈值逐项标注最终核对日期。

## v1.1 发布证据

- Chapter 4：24 / 24 项测试通过；Chapter 5：63 / 63 项测试通过；
- 离线报告：30 attempts / 30 valid decisions / 0 infrastructure failures，两次生成 SHA-256 均为 `1F7B18137B1F3A44188DA3FCF5C682370CD47288DFD8114292FF593B759A396E`；
- 渲染门禁：4 / 4 通过；本地链接、15 个脚注、7 个 SVG XML、29 个二三级标题与 14 道练习静态检查通过；
- 安全静态检查：Chapter 5 范围内未发现凭据形状明文，旧预算合同与旧实验数量表述未残留在当前实现；
- PDF：`output/pdf/versions/chapter5/chapter5-v1.1.pdf`，36 页 A4，SHA-256 `2843EF79D820A4EC3B18FFDA1DD1EC73CD598160301FDEDE291AD37460C50874`，全页目检通过；
- v1.0 PDF 保持 SHA-256 `1F63F6FF87F3AB4DCAD493DE49731C1CEFB1A55F82EBC80C2604E7DDEBEC9CD4`，未覆盖。
