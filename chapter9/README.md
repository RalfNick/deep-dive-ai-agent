# 第 9 章实验：工具调用与 MCP

本目录对应《深入浅出 AI Agent》第 9 章。实验从“模型用自然语言声称已创建故障单”开始，逐步加入 JSON、Schema、Tool Contract、Tool Loop、授权、Execution Receipt 和 MCP。所有默认实验都离线运行，不需要 API Key。

- [返回第 9 章正文](../book/chapter9.md)
- [查看分层练习参考答案](./reference-answers.md)

第一次运行前只需记住：Definition 是能力目录，Call 是申请，Result 是办理结果，Receipt 是写操作成功后由执行边界记录的关联回执。Receipt 不是模型生成的文字，也不是外部系统的密码学签名；生产环境仍可能需要按外部 ID 回查。

> 证据边界：这里固定模型决策、Fixture 与时钟，只比较外围系统是否守住合同。它不是模型质量测试，也不构成 OpenAI、Anthropic、DeepSeek 或任何 Agent 产品的能力排名。

## 环境

- Python 3.11–3.13
- 教学依赖：`mcp==2.1.1`
- 协议基线：MCP `2026-07-28`
- 旧版兼容路径：MCP `2025-11-25`
- 固定时钟：`2026-09-01T00:00:00Z`

在仓库根目录执行：

```powershell
python -m pip install -r chapter9/requirements.txt
python -m unittest discover -s chapter9/tests -v
```

## 七步版本

每个命令只突出一个新增边界：

```powershell
python -m chapter9.experiments.run_v0_free_text
python -m chapter9.experiments.run_v1_schema
python -m chapter9.experiments.run_v2_contracts
python -m chapter9.experiments.run_v3_tool_loop
python -m chapter9.experiments.run_v4_receipts
python -m chapter9.experiments.run_v5_mcp_server
python -m chapter9.experiments.run_v6_mcp_client
```

| 版本 | 新增边界 | 读者应观察什么 |
| --- | --- | --- |
| v0 | 无 | 完成声明没有动作证据 |
| v1 | JSON 与输入 Schema | 语法合法和调用合法是两件事 |
| v2 | Definition / Call / Result | `call_id` 把请求与结果关联起来 |
| v3 | Tool Loop | Result 回到模型，成为下一步观察 |
| v4 | Host Policy / Server Policy / Receipt | 同意、授权与执行证据各自独立 |
| v5 | MCP Server | 同一领域能力暴露为 Tool、Resource、Prompt |
| v6 | MCP Client 与版本模式 | 现代请求自描述，旧版显式走 legacy 路径 |

## 生成规范报告

```powershell
python -m chapter9.experiments.run_all --output chapter9/reports
python -m chapter9.experiments.run_failure_matrix
```

规范输出有三份：

- `reports/tool-mcp-evidence.json`：机器可读的 5 组 20 个案例；
- `reports/tool-mcp-evidence.md`：供读者阅读的表格；
- `reports/tool-mcp-trace.jsonl`：脱敏事件流。

重复运行 `run_all` 后，三份文件应保持字节一致。实现通过固定时钟、稳定 ID、排序后的 JSON Key 与 LF 换行消除非业务噪声。报告不写作者机器路径、随机 UUID、真实凭据或 Provider 响应 ID。

| 实验组 | 案例数 | 主要问题 |
| --- | ---: | --- |
| contract | 4 | 自由文本、JSON、Schema 与合法调用的边界 |
| loop | 4 | 结果关联、三步循环、错配与步数耗尽 |
| safety | 5 | 同意、授权、伪造回执、暂时与永久错误 |
| mcp_primitives | 4 | Tool、Resource、Prompt 与 Host 隔离 |
| compatibility | 3 | 现代协议、legacy 模式与不支持版本 |

## 可选真实 Provider 探针

探针默认只做 Dry Run，不联网，也不读取凭据：

```powershell
python -m chapter9.live.live_probe --provider deepseek
python -m chapter9.live.live_probe --provider openai
python -m chapter9.live.live_probe --provider anthropic
```

只有读者显式增加 `--execute`，并在当前进程环境中配置对应凭据，探针才会请求 Provider。实时结果写到未纳入版本控制的 `chapter9/live-reports/`，只保留规范化调用信息，不保存凭据。详细限制见 `live/README.md`。

真实探针只能回答“这个 Provider 当前是否产生了可适配的工具提议”，不能替代 20 个确定性边界案例，也不能把一次响应推广成模型成功率、稳定性、成本或延迟结论。

## 代码阅读顺序

1. `tool_runtime/contracts.py`：四份核心合同和错误状态。
2. `tool_runtime/schema.py`：教学用 JSON Schema 子集与稳定问题路径。
3. `tool_runtime/registry.py`：Definition 与 Handler 的注册关系。
4. `tool_runtime/policy.py`、`runtime.py`：校验、策略、执行与回执边界。
5. `tool_runtime/loop.py`：固定策略怎样消费 Tool Result。
6. `incident_domain/`：只读查询和唯一写入动作。
7. `mcp_app/server.py`、`client.py`、`adapter.py`：官方 SDK 的 Server、Client 与 Host 适配层。
8. `experiments/run_all.py`：五组案例怎样汇总为可重复证据。
9. `tests/`：每条主张实际穿过了哪一个边界。

## 已证明与未证明

本目录证明：固定输入下，非法参数在 Handler 前被拒绝；未获授权的写入不产生副作用；成功写入产生由执行边界构造的 Receipt；`call_id` 能关联结果；三种 MCP 原语保持不同控制权；官方 SDK 的现代与 legacy 教学路径按锁定版本工作；规范报告可重复生成。

本目录没有证明：某个真实模型更强；任意第三方 MCP 实现都兼容；进程内测试等价于公网部署；内存 TicketStore 提供生产级幂等和灾难恢复；单次实时探针能代表长期质量；字符数或 JSON 长度可以代替 Provider Token 计量。

教学版 `ResultStatus` 也是有意缩小的应用内分类。不要把它直接当作 MCP 线上错误码：Unknown Tool 和畸形 MCP 请求属于协议错误，已经进入具体 Tool 后的可行动失败才属于 Tool Execution Error。

继续扩展时，请先新增失败案例，再修改 Runtime；不要通过放宽 Schema、把授权字段塞进模型 Arguments，或让 Handler 伪造成功结果来“修复”测试。
