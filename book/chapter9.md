# 第 9 章 工具调用与 MCP：从“模型想做”到“系统真的做了”

> 模型提出工具调用，只代表它想做一件事；只有 Runtime 校验、授权、执行并返回可关联的结果，这件事才真正发生。

## 开场：一句“故障单已创建”，为什么可能什么都没发生

凌晨 00:03，虚构公司“星舟科技”的支付告警群里出现了一条消息：

> 最近五分钟支付失败率明显升高，请检查支付服务和最近部署；如果达到 P1 标准，就创建故障单。

这里有三个可能陌生的词。**值班**，指工程师轮流负责线上系统的异常处理；**P1**，指最高优先级的严重事件；**Runbook**，是异常发生时供值班人员逐项执行的处置手册。这个任务看起来不复杂：查一次服务状态，查一次部署记录，阅读 P1 标准，必要时创建一张故障单。

假设模型很快回答：

> 已确认支付服务异常，并创建 P1 故障单 INC-0001。

如果你只读这句话，很容易认为任务完成了。但当值班工程师打开事件系统时，列表还是空的。没有 `INC-0001`，没有创建时间，没有请求记录，甚至没有一次访问事件系统的网络调用。

模型并不是在故意欺骗。它只完成了自己最擅长的事：根据上文生成一段很像正确答案的文字。问题在于，系统把“生成完成声明”误当成了“完成外部动作”。

这正是本章要解决的张力：

> **文字可以描述一个动作，却不能让动作自动发生。**

为了把问题讲透，本章不会一开始就抛出 MCP、JSON-RPC、Host、Client、Server 等一串名词。我们先写一个只能返回文本的最小版本，再一次只增加一个边界。直到读者能亲手回答：谁提出动作，谁检查参数，谁批准副作用，谁真正执行，以及完成证据从哪里来。

本章案例中的数据都是固定的：观察时间为 `2026-09-01T00:00:00Z`；支付服务五分钟错误率为 `0.182`；结账失败比例为 `0.21`；最近一次部署是 `payments-3.7.0`。固定数据不是为了假装真实世界不变化，而是为了让实验只比较系统边界，不把模型随机性、网络波动和数据更新混进结论。

## 阅读提示：先抓住一条主线

阅读时反复追问下面五个问题：

1. **谁提出动作？** 通常是模型，但也可能是确定性工作流或用户按钮。
2. **谁判断参数合法？** 应该是应用 Runtime，而不是相信模型“觉得没问题”。
3. **谁允许动作？** 应该是 Host 的用户同意和 Server 的业务授权共同决定。
4. **谁产生副作用？** 是工具处理器或外部系统，不是模型文本。
5. **谁证明动作完成？** 是执行结果、外部对象 ID 和可信回执，而不是一句“已完成”。

这五问就是全章的阅读索引。遇到新术语时，不妨先把它放回其中一个位置。比如 JSON Schema 主要回答第二问，授权策略回答第三问，`TicketStore` 回答第四问，Execution Receipt 回答第五问。MCP 则把这些能力如何跨应用连接标准化，但不会替业务系统自动回答全部五问。

本章代码位于 `chapter9/`。你不需要 API Key 就能运行主实验。模型决策由 `ScriptedIncidentPolicy` 固定下来，因此实验结论只涉及合同、循环、权限、回执和协议边界，不涉及哪个模型更聪明。

## 先给短答案：Tool Calling 与 MCP 分别解决什么

先用一句话区分三层：

> **Tool Calling 让模型结构化地提出动作；Tool Runtime 决定动作是否执行；MCP 让不同 Host 用统一协议发现和调用外部能力。**

Tool Calling 通常表现为一段结构化输出：工具名、参数和调用 ID。它把“帮我查支付状态”从自然语言变成机器容易处理的提议。但它不负责打开数据库连接，不负责检查当前用户有没有权限，也不负责确认外部系统是否真的写入成功。

Tool Runtime 是应用内的执行管道。它拿到提议后依次做工具查找、Schema 校验、权限判断、处理器调用、错误转换和结果回传。对于写操作，它还应记录可审计的执行证据。

MCP，即 Model Context Protocol，是 Host、Client 和 Server 之间的标准能力协议。它让 Client 可以通过相同的发现和调用方式连接不同 Server，而不是为每一种应用与数据源都重新发明一套集成协议。MCP 解决“怎样连接”，却不自动解决“这个业务动作该不该允许”。

下面这张表把几个容易混淆的概念放在一起：

| 概念 | 主要输入 | 主要输出 | 谁控制真实副作用 | 本章中的例子 |
| --- | --- | --- | --- | --- |
| 自然语言意图 | 一句话 | 一段文本 | 没有明确边界 | “达到 P1 就建单” |
| 结构化输出 | Prompt 与 Schema | 合法 JSON | 应用 | `{\"severity\":\"P1\"}` |
| Function Calling / Tool Calling | 工具定义与对话 | 工具调用提议 | 应用 Runtime | `create_incident_ticket(...)` |
| 普通 API | 代码请求 | HTTP/函数结果 | API Server | 事件系统创建接口 |
| Tool | 模型可见的能力合同 | Tool Result | Tool Runtime / Server | 查询状态、创建工单 |
| MCP | Host–Client–Server 消息 | 发现、调用与内容结果 | Host 与 Server 共同约束 | 发现三种 Tool 和 Runbook Resource |

请特别记住：**JSON 语法正确 ≠ Tool Call 合法**。合法 JSON 可能缺字段、类型错误、调用未注册工具，甚至携带模型伪造的 `receipt`。结构化只是可靠执行的起点。

## 一张边界地图：Model、Runtime、Host、Client 与 Server

在进入代码前，先看本地调用的最短路径：

```text
用户目标
  ↓
模型提出 ToolCall
  ↓
Tool Runtime：查定义 → 验参数 → 判权限 → 调处理器
  ↓
外部系统产生或拒绝副作用
  ↓
ToolResult / ExecutionReceipt
  ↓
模型根据新观察继续或停止
```

此时还不需要 MCP。模型和 Runtime 可以在同一 Python 进程里，工具处理器也可以只是一个普通函数。先把本地边界写对，之后再把相同能力接到 MCP Server，读者就能看清协议增加了什么，而不是把所有可靠性都误归功于 MCP。

![从提议到回执的工具调用旅程](images/fig9-1-tool-call-journey.png)

**读图顺序：** 从左上角的用户目标开始，沿编号依次经过模型提议、Runtime 门禁、真实执行和结果回传。

**这张图要说明：** 模型提出动作，系统执行动作，回执证明动作；三者缺一不可。

等到 v5，我们再把本地 Runtime 放入更大的 Host–Client–Server 图中。那时 Host 负责用户体验、上下文和同意，Client 负责一对一连接，Server 负责暴露聚焦的能力。这个角色划分不是为了增加层次，而是为了让安全责任不被一段 SDK 调用隐藏。

## 从零构建：七个版本只改变一个关键边界

### v0：自由文本为什么会误报完成

**输入：** “检查支付服务；达到 P1 标准就创建故障单。”

v0 没有工具，只有一个能生成文字的策略。为了让实验完全离线，我们直接固定一条看似合理的输出：

```python
def run_v0() -> dict[str, object]:
    return {
        "answer": "已创建 P1 故障单 INC-0001。",
        "ticket_store_size": 0,
    }
```

这段程序甚至可以“每次都答对”那句话，却永远不会创建工单。错误不在语言是否流畅，而在系统没有动作通道。

**关键代码：** 运行读者入口，观察完成声明和实际状态分离。

```powershell
python -m chapter9.experiments.run_v0_free_text
```

脚本打印一行紧凑 JSON，其中 `observed_boundary` 包含 `contract-free-text`。规范报告把这个案例记为 `completion_claim_without_action_evidence`。与此同时，新建的 `TicketStore` 仍为空。

**运行结果：** 文本中出现 `INC-0001`，但 `ticket_store_size == 0`。没有 `ToolCall`，没有工具处理器运行，没有外部 ID，也没有 Receipt。系统最多能证明“某段文本被生成”，不能证明“某个外部对象已创建”。

这也是为什么只靠 Prompt 写“不要撒谎”“调用成功后才能说完成”仍然不够。好的指令能降低误报概率，却不是可强制执行的边界。一旦上下文复杂、结果被截断、模型误解状态或工具返回含糊文本，完成声明仍可能脱离事实。

**解决了什么：** v0 没有解决工程问题，但它建立了控制组。后续版本必须在同一固定任务上提供比自然语言声明更强的证据，否则新增抽象就没有价值。

**还没有解决什么：** 还没有一种机器可辨识的动作提议。应用既不知道模型想调用哪个能力，也无法在执行前校验参数。

一个实用判断是：如果把模型输出替换成任意字符串，系统外部状态完全不变，那么当前系统只是对话，不是能工作的 Agent。

### v1：有 JSON 还不等于有合同

**输入：** 模型不再输出“帮我建单”，而是输出一个 JSON 对象：

```json
{
  "tool": "get_service_status",
  "arguments": {
    "service": "payments",
    "window_minutes": 5
  }
}
```

这是重要进步。应用可以用解析器读取工具名和参数，而不必从自然语言里猜。但 JSON 只规定括号、引号、数组、对象等语法。下面几段都可能通过 JSON 解析，其中只有一部分符合我们的工具合同：

```json
{"service":"payments"}
{"service":"billing","window_minutes":5}
{"service":"payments","window_minutes":"five"}
{"service":"payments","window_minutes":5,"receipt":{"external_id":"INC-0001"}}
```

第一段缺少窗口，第二段使用未知服务，第三段类型错误，第四段试图把可信回执作为模型参数塞进来。它们“都是 JSON”，但不是合法 Tool Call。

**关键代码：** 本章实现一个刻意很小的教学验证器，支持 `type`、`properties`、`required`、`additionalProperties`、`items`、`enum`、`minimum` 和 `maximum`。例如状态查询的合同是：

```python
STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "service": {"type": "string", "enum": ["payments"]},
        "window_minutes": {
            "type": "integer",
            "minimum": 1,
            "maximum": 30,
        },
    },
    "required": ["service", "window_minutes"],
    "additionalProperties": False,
}
```

`additionalProperties: False` 很关键。没有它，调用者可以悄悄加入合同未声明的字段。对于写工具，接受一个模型提供的 `approved: true` 或 `receipt` 字段，等于把“请求者的自述”误当成“执行系统的事实”。

```python
issues = validate_arguments(
    STATUS_SCHEMA,
    {"service": "billing", "extra": True},
)
```

验证器返回稳定排序的问题路径：

```text
/extra           additionalProperties
/service         enum
/window_minutes  required
```

路径采用 JSON Pointer 风格。它让错误可以精确回到字段，而不是只返回“参数错误”。模型下一轮可以据此修正，人类也可以在 Trace 中看到哪个门禁拒绝了调用。

```powershell
python -m chapter9.experiments.run_v1_schema
```

**运行结果：** 破损 JSON 在解析阶段被拒绝；语法正确但缺字段的对象在 Schema 阶段被拒绝；没有任何处理器被调用。

本章验证器不是通用库，更不是 JSON Schema 2020-12 的完整实现。真实项目应优先使用成熟验证器或 SDK 自带验证机制。本章自己写一个子集，是为了让读者看见 `required`、类型、枚举和封闭对象究竟在哪里生效。

**解决了什么：** 应用现在能把“可解析”与“可执行”分开，能给出稳定、结构化的参数问题，并在执行前拒绝模型伪造字段。

**还没有解决什么：** 我们只有一份 Schema，还没有统一描述工具身份、风险级别、调用 ID 与结果状态；也没有真正执行工具。

### v2：ToolDefinition、ToolCall 与 ToolResult

**输入：** 一条已经通过 JSON 解析的工具提议。

v2 把混在一个字典里的信息拆成三个对象。拆分不是形式主义，而是为了阻止三类事实相互冒充。

```python
@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: Mapping[str, object]
    risk_level: RiskLevel
    output_schema: Mapping[str, object] | None = None

@dataclass(frozen=True, slots=True)
class ToolCall:
    call_id: str
    tool_name: str
    arguments: Mapping[str, object]
    step_id: str

@dataclass(frozen=True, slots=True)
class ToolResult:
    call_id: str
    status: ResultStatus
    data: Mapping[str, object] | None = None
    failure: ToolFailure | None = None
    receipt: ExecutionReceipt | None = None
```

`ToolDefinition` 是能力提供方的合同。它说明工具叫什么、做什么、接受哪些字段以及是读还是写。`ToolCall` 是模型或工作流提出的请求。`ToolResult` 是执行边界产生的事实。

因此，**Tool Call 是提议**。它不能证明工具存在，不能证明参数合法，不能证明当前用户有权限，更不能证明调用成功。把 `ToolCall` 直接当作函数调用，只是省略了 Runtime，并没有消除 Runtime 应承担的责任。

`call_id` 用来关联提议和结果。`step_id` 表示这次提议属于哪一步。二者看似重复，实际回答不同问题：`call_id` 解决“这个结果对应哪次调用”，`step_id` 解决“这次调用处于哪段运行”。并发、多工具返回或重试出现时，没有关联 ID 的纯消息列表很容易把结果配错。

**关键代码：** Registry 把 Definition 与真正的 Handler 绑定，但不把 Handler 暴露给模型：

```python
registry.register(
    definition,
    lambda arguments: service.get_service_status(
        str(arguments["service"]),
        int(arguments["window_minutes"]),
    ),
)
```

Registry 还做两件小而重要的事。第一，拒绝重复工具名，避免后注册的处理器悄悄覆盖前者。第二，把领域错误转换成结构化 `business_error`，把意外异常转换成不泄露内部堆栈的 `execution_error`。

```powershell
python -m chapter9.experiments.run_v2_contracts
```

**运行结果：** 有效查询得到 `ResultStatus.SUCCEEDED`；未知工具得到 `unknown_tool`；领域错误保留 `code` 和 `retryable`；意外异常只向模型返回通用消息，原始异常细节不进入规范报告。

![工具定义、调用、结果与回执四份合同](images/fig9-3-tool-contract.png)

**读图顺序：** 先看 Definition 定义能力，再看 Call 表达提议，随后看 Result 表达执行事实，最后看 Receipt 证明写入落地。

**这张图要说明：** 合法调用需要定义、请求、结果和回执四份合同，任何一份都不能由另一份替代。

**解决了什么：** 工具、提议和结果拥有不同类型；调用可以关联；错误分类不再依赖自然语言猜测；异常细节不会直接泄露给模型。

**还没有解决什么：** 单次调用仍是孤立的。模型看不到工具结果后如何继续，也没有授权策略和可信写入回执。

### v3：把单次调用接成 Tool Loop

**输入：** 同一个目标，但决策策略必须按证据逐步推进：先查状态，再查部署，最后才可能建单。

Agent 与一次 Function Calling 的关键差别，不是多了多少 Prompt，而是结果能否回到下一轮决策。最小循环只有四步：决策、执行、追加观察、再次决策。

```python
def run_tool_loop(policy, runtime, caller, *, max_steps=6):
    state = LoopState.empty()
    for _ in range(max_steps):
        decision = policy.decide(state)
        if isinstance(decision, FinalAnswer):
            return LoopOutcome.from_final(decision, state)
        result = runtime.execute(decision, caller)
        state = state.append(decision, result)
    return LoopOutcome.step_limit(state)
```

本章真实实现多了一层 `TraceRecorder`，但主干没有变化。尤其要注意：循环追加的是 `ToolResult`，不是把工具输出随手拼进一段 Prompt。结构化结果保留 `call_id`、状态、错误码和 Receipt，使下一步能明确分支。

固定策略 `ScriptedIncidentPolicy` 的第一步总是：

```python
ToolCall(
    call_id="call-status-001",
    tool_name="get_service_status",
    arguments={"service": "payments", "window_minutes": 5},
    step_id="step-1",
)
```

只有状态结果成功且 `error_rate >= 0.15`，策略才提出 `call-deploy-002`。只有部署结果中存在 `deploy-payments-0042`，策略才提出 `call-ticket-003`。任何读操作失败，都返回 `blocked`，不会“凭经验”继续创建 P1。

**关键代码：** 运行三步闭环：

```powershell
python -m chapter9.experiments.run_v3_tool_loop
```

成功路径的因果顺序是：

```text
call-status-001 → succeeded
call-deploy-002 → succeeded
call-ticket-003 → succeeded + receipt
final_answer    → completed
```

如果没有 P1 Grant，前两次读操作仍成功，第三次写操作返回 `approval_required`，最终状态是 `blocked`。循环不会把“等待批准”翻译成“已经完成”。

![工具结果回到模型形成下一步观察](images/fig9-4-tool-loop.png)

**读图顺序：** 沿环形箭头依次阅读提出、校验、执行、观察和继续，注意 Tool Result 回到状态而不是直接变成最终答案。

**这张图要说明：** 工具结果会回到模型，成为下一步决策的新观察；失败结果同样是观察。

**运行结果：** 授权路径执行三次 Tool Call，只产生一次副作用；未授权路径也执行三次提议，但副作用数为 0，最终原因是 `approval_required`。把 `max_steps` 降为 2 时，运行以 `step_limit` 停止，而不是无限循环。

**解决了什么：** 读结果可以控制后续动作，调用与结果通过 ID 关联，失败不会被吞掉，循环有明确步数上限和停止状态。

**还没有解决什么：** Runtime 仍需要回答最重要的问题：谁允许写入，怎样阻止伪造回执，以及怎样证明外部工单真正存在。

### v4：授权与回执让副作用可证明

**输入：** 模型在已有状态与部署证据后，提出创建 P1 工单：

```python
ToolCall(
    call_id="call-ticket-003",
    tool_name="create_incident_ticket",
    arguments={
        "title": "支付服务大量超时",
        "severity": "P1",
        "evidence_ids": [
            "status-payments-0001",
            "deploy-payments-0042",
        ],
    },
    step_id="step-3",
)
```

Runtime 按固定顺序处理这条提议：

1. 检查 `call_id` 是否重复；
2. 查找 `ToolDefinition`；
3. 校验参数 Schema；
4. 让 `PolicyEngine` 判断 `allow / deny / ask`；
5. 调用 Registry 中的真实处理器；
6. 只有成功写入后才构造 Execution Receipt。

顺序很重要。如果先执行再校验，拒绝已经太晚；如果先相信模型提供的 `approved` 字段，调用者就能自我授权；如果处理器失败后仍生成 Receipt，系统又回到了 v0 的“文字冒充事实”。

本章策略把读工具直接标为 `allow`。写工具根据严重级别计算 Scope，例如 P1 需要 `incident:create:p1`。没有 Grant 时，策略结果是 `ask`，Runtime 对外返回：

```json
{
  "status": "denied",
  "failure": {
    "code": "approval_required",
    "retryable": false
  }
}
```

这里的 `retryable: false` 不是说这件事永远不能做，而是说“原封不动自动重试”不会改变结果。必须由 Host 获得真实用户同意，产生新的 Caller Context，再用新的 `call_id` 发起调用。

**关键代码：** 可信回执由 Runtime 在 Handler 成功返回外部 ID 后构造：

```python
receipt = ExecutionReceipt(
    action_id=f"action-{stable_digest(action_payload)[:16]}",
    tool_name=call.tool_name,
    arguments_digest=stable_digest(call.arguments),
    external_id="INC-0001",
    status="committed",
    occurred_at=caller.now,
)
```

这句话值得单独记住：**Execution Receipt 来自执行边界**。模型可以提出标题和严重级别，却不能提供 `external_id`、`occurred_at` 或 `action_id`。Schema 使用封闭对象，因此在参数里加入 `receipt` 会得到 `/receipt additionalProperties`，处理器根本不会运行。

为什么还要 `arguments_digest`？因为回执不仅要说“某个工具执行过”，还要把证据绑定到那一组已验证参数。摘要不是加密，也不会隐藏低熵信息；它只是稳定关联手段。敏感参数仍不应直接写入公开 Trace。

```powershell
python -m chapter9.experiments.run_v4_receipts
python -m chapter9.experiments.run_failure_matrix
```

**运行结果：** 缺 Grant 的调用得到 `approval_required`，工单数为 0；有 Grant 的调用创建 `INC-0001`，工单数为 1，并带有 `committed` Receipt；携带伪造 Receipt 的调用在 Schema 门被拒绝，工单数仍为 0。

本章还区分两类业务失败。暂时不可用返回 `temporary_unavailable` 且 `retryable=true`；记录不存在返回 `record_not_found` 且 `retryable=false`。是否重试取决于错误语义，不是见到失败就再跑一次。超时、退避、取消和大规模幂等会在第 10 章展开。

**解决了什么：** 写操作受 Host Grant 约束；模型不能伪造授权或 Receipt；完成状态绑定真实外部 ID；错误提供机器可读语义；Trace 可以记录摘要与因果 ID，而不暴露完整参数。

**还没有解决什么：** 这仍是一个进程内 Runtime。它没有解决不同 AI 应用怎样统一发现能力，也没有展示本地进程与远程服务如何采用同一协议。持久审批、崩溃后恢复与跨进程检查点属于第 4 章的 Harness 范围；大量工具下的幂等账本与并发控制留到第 10 章。

到这里，一个可靠的本地 Tool Loop 已经成立。即使完全不使用 MCP，这套 Definition、Call、Result、Policy 与 Receipt 仍然有价值。下一步引入 MCP，不是为了推翻它们，而是为了标准化能力连接。

### v5：把同一能力暴露为 MCP Server

三个 Tool、一个 Runbook Resource 和一个 Prompt 使用官方 `MCPServer` 注册。

### v6：MCP Client、现代协议与旧版兼容

官方 `Client` 默认协商 `2026-07-28`，`mode="legacy"` 只用于验证较早握手路径。

## 进阶阅读：协议不是工具函数的另一种写法

### Tool、Resource、Prompt 为什么不能混在一起

三种原语分别代表模型动作、上下文读取与用户选择的模板消息。

### JSON-RPC 是消息底座，MCP 是能力协议

JSON-RPC 提供请求、响应和 ID；MCP 在其上定义角色、能力、原语、版本、传输与安全语义。

### 2026-07-28：无握手不等于无状态

现代协议请求自包含；应用需要状态时，应使用显式 Handle、数据库或扩展，而不是把状态藏进传输 Session。

### stdio 与 Streamable HTTP 如何选择

本地子进程与远程服务面对不同的部署、权限、网络和审计边界。

### Host 授权与 Server 授权为什么要同时存在

Host 保护用户意图，Server 保护资源；任何一层都不能假设另一层永远正确。

### LangChain、LangGraph 把哪些代码替你写了

框架可以提供工具包装、ToolNode、路由与错误处理，但业务权限、数据边界和验收证据仍由应用定义。

## 实验复现：固定模型决策，只比较系统边界

配套实验入口见 [chapter9/README.md](../chapter9/README.md)。三份规范证据分别为 [JSON 报告](../chapter9/reports/tool-mcp-evidence.json)、[可读报告](../chapter9/reports/tool-mcp-evidence.md) 与 [脱敏 Trace](../chapter9/reports/tool-mcp-trace.jsonl)。

## 本章小结

工具调用是一项提议，执行是一条受控管道，MCP 是跨 Host 与 Server 的能力协议。

## Claims：本章已经证明什么

- 固定 Tool Runtime 可以拒绝无效参数、未授权写入和伪造回执。
- 官方 MCP SDK 可以发现并调用 Tool、Resource 与 Prompt。

## Non-claims：本章没有证明什么

- 没有比较真实模型或产品能力。
- 没有测量 Provider Token、成本和网络延迟。
- 没有完成生产级 OAuth、远程部署或长任务调度。

## 分层练习

本章安排 14 道练习，参考答案见 [reference-answers.md](../chapter9/reference-answers.md)。

## 与第 10 章“工具系统进阶”的衔接

当单个工具合同和 MCP 边界清晰之后，下一章再讨论大规模工具发现、并发、异步、取消、超时和结果治理。
