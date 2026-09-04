# 第 9 章 v1.0.2 复审：工具调用与 MCP

- 复审日期：2026-09-04
- 复审对象：`book/chapter9.md`、`chapter9/`、8 幅当前插图、来源台账、实验报告与发布检查
- 复审视角：初学读者；AI Agent / MCP 工程实现者；实验与证据审计；视觉语义
- 历史基线：v1.0 Review 保留在 `chapter9-review-codex.md`，本文件不改写旧结论
- 最终结论：v1.0.2 通过；没有未处理的 P0 或 P1

## 总体判断

本章仍保持 v0–v6 的渐进主线，但 v1.0.2 把几处容易“看懂了却形成错误心智模型”的细节收紧。最重要的变化不是增加篇幅，而是让文字、图片、代码和报告对同一件事使用同一套边界：每次调用需要 Definition、Call、Result 三份合同；只有产生副作用的写操作才需要 Receipt；Function Calling 产生提议，Runtime 负责控制，本地 Handler 与 MCP Server 是两条可选执行路径。

综合评价为 9.3/10。对于首次接触 Tool Calling 与 MCP 的读者，章节已经能先建立直觉，再逐步进入合同、循环、授权和协议；对于工程读者，新增 Output Schema 运行时门禁和失败案例补上了先前“Definition 有字段、执行却未校验”的证据缺口。

## 本轮发现与处理

| ID | 级别 | 发现 | v1.0.2 处理 | 状态 |
| --- | --- | --- | --- | --- |
| R9V2-01 | P1 | 旧版 MCP 握手图把 `notifications/initialized` 方向画反，可能让读者形成错误时序 | 重绘图 9-7，明确 Client → Server 的 `initialize`、Server → Client 的结果、Client → Server 的 `notifications/initialized` | 已关闭 |
| R9V2-02 | P1 | `ToolDefinition.output_schema` 存在，但三个领域 Tool 未声明输出合同，Runtime 也没有校验结果 | 为三个 Tool 声明封闭 Output Schema；在 Result 进入 Loop 前验证；新增 `invalid_tool_output` 失败语义与回归测试 | 已关闭 |
| R9V2-03 | P1 | 旧边界图容易被读成 Function Calling → Runtime → MCP 的固定流水线 | 重绘图 9-2：Runtime 分别连接本地 Handler 与 MCP Client / Server，两条路径的 Result 都回到 Runtime | 已关闭 |
| R9V2-04 | P2 | “三张单据”“四份合同”和“Receipt 证明动作”三种说法相互冲突 | 全章统一为“三份调用合同 + 一份写操作回执”，把“证明”收紧为“提供可核对证据” | 已关闭 |
| R9V2-05 | P2 | 报告把 19 个运行观察与 1 个规范 Fixture 合称“20 个实验”，证据种类不够透明 | 增加 Output Schema 运行案例；报告改为 21 个 Case，并显式拆成 20 个 Runtime Observation + 1 个 Specification Fixture | 已关闭 |
| R9V2-06 | P2 | 长章缺少按读者目标选择的路线，协议版本信息分散 | 增加初学、Runtime 实现、生产落地三条阅读路线；章首增加版本冻结点 | 已关闭 |

## 读者视角

开场仍以“模型声称已经建单，但系统里没有工单”的冲突切入，能把抽象协议问题落到可检查的事实。v0–v6 每次只增加一个关键边界，适合从零阅读。新增的三条阅读路线允许读者跳过暂时不需要的生产细节，而不会破坏主线。

术语类比现在更严谨：Definition 是服务目录，Call 是申请，Result 是办理结果；Receipt 仅在写操作成功时出现。这个修正很关键，因为只读查询同样是合法 Tool Call，却不应为了凑齐“四份合同”伪造回执。

图片承担的是关系解释而不是装饰。当前图 9-2 展示两条执行路径，图 9-3 展示三份基础合同与条件式回执，图 9-7 展示现代协议和旧生命周期的不同。读者可以先读图底部结论，再回正文找字段与失败案例。

## AI 工程视角

**输入与输出是两道门。** Input Schema 在 Handler 前保护执行边界；Output Schema 在 Handler 成功后保护 Loop 与调用者。`contract-output-schema-violation` 固定返回字符串形式的 `error_rate`，Runtime 必须以 `execution_error / invalid_tool_output` 拒绝，错误路径稳定为 `/error_rate`。这支持“输出合同确实执行”的主张，但不支持“输出值一定真实”。

**Receipt 是条件式证据。** Runtime 只为写 Tool 构造 Receipt，并要求 Handler 返回外部对象 ID。当前教学实现证明同一信任域内的执行关联，不是外部系统的密码学签名；跨服务系统仍需回查、签名或独立 Verifier。

**MCP 是连接路径，不是安全替身。** Host / Agent Runtime 仍负责本地意图、上下文和策略；MCP Client / Server 标准化能力发现与调用；Server 仍需按受信身份执行业务授权。新的架构图不再把 MCP 画成所有本地执行之后必经的一站。

**协议历史被显式冻结。** 本章以 MCP `2026-07-28` 和 `mcp==2.1.1` 为测试组合，并保留 `2025-11-25` 的旧版教学路径。2026-09-04 复核时，官方规范入口仍指向 `2026-07-28`，官方 Python SDK Releases 页面仍将 `v2.1.1` 标为 Latest。这个事实只说明当前复核状态，不承诺未来不变。

## 实验与证据

- 规范报告：5 组 21 个 Case，其中 20 个来自实际 Runtime / SDK 运行，1 个是版本不兼容 Specification Fixture。
- 合同组：5 个案例，新增输出合同漂移；其余四组分别覆盖 Loop、Safety、MCP Primitives 与 Compatibility。
- 证据限制：固定策略不是模型采样；进程内 SDK 测试不是公网互操作；Fixture 不是运行观察；未测量字段继续保持 `null`。
- 报告输出：JSON、Markdown 与脱敏 JSONL Trace 可由同一命令重建。
- 自动验证：第 9 章 47 项测试、仓库发布检查和 MkDocs strict 构建通过。

## 视觉复审

当前正文仍引用 8 幅图：1 幅 1024×1536 竖版主图，7 幅 1536×864 横版图。v1.0.2 新增四个带 `-v2` 的文件名，旧图不覆盖，便于审计历史。

- 图 9-1：把“回执证明动作”改为“回执提供可核对的执行证据”。
- 图 9-2：本地与 MCP 两条路径并列，不再形成错误的串行暗示。
- 图 9-3：明确前三份合同适用于每次调用，Receipt 只属于写操作。
- 图 9-7：修正旧版 `notifications/initialized` 的发送方向。

图片文字仍需要人工目检；尺寸、文件引用、唯一替代文本和读图合同由自动测试覆盖。生成式图片不能替代协议来源，图中时序必须继续由官方规范核对。

## 保留的限制

- 教学 JSON Schema 仍只是明确拒绝未知关键字的子集，不等价于完整 Draft 2020-12 实现。
- TicketStore、Grant 与重复 Call ID 检查仍是进程内机制，不提供跨进程持久幂等。
- MCP 测试没有覆盖真实 stdio 子进程、Streamable HTTP、OAuth、网络分区与第三方兼容矩阵。
- 可选 Provider Probe 不进入规范报告，也不能给出模型质量、成本或稳定性排名。
- Output Schema 只验证结果形状；领域真实性、时效性与业务完整性仍需额外验证。

这些限制均已在正文、README 或 Non-claims 中公开，不构成未处理的 P0/P1，但决定了示例不能原样当作生产平台。
