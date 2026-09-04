# 第 9 章工具调用与 MCP 实验证据

> 这是固定决策与固定 Fixture 的边界一致性实验，不是模型或产品能力比较。

- 固定时钟：`2026-09-01T00:00:00Z`
- MCP 协议基线：`2026-07-28`
- 教学 SDK：`mcp==2.1.1`
- 样本：21 个确定性单样本案例
- 证据构成：20 个运行观察 + 1 个规范 Fixture

## contract

| 案例 | 版本 | 观察结果 | 证据类型 |
| --- | --- | --- | --- |
| `contract-free-text` | v0 | completion_claim_without_action_evidence | runtime_observation |
| `contract-malformed-json` | v1 | json_parse_rejected | runtime_observation |
| `contract-schema-violation` | v1, v2 | schema_rejected:/window_minutes | runtime_observation |
| `contract-output-schema-violation` | v2 | invalid_tool_output:/error_rate | runtime_observation |
| `contract-valid-call` | v2 | result:succeeded | runtime_observation |

## loop

| 案例 | 版本 | 观察结果 | 证据类型 |
| --- | --- | --- | --- |
| `loop-result-correlation` | v2, v3 | matched:True | runtime_observation |
| `loop-three-calls` | v3 | completed:1_side_effect | runtime_observation |
| `loop-mismatched-call-id` | v3 | mismatch_detected:True | runtime_observation |
| `loop-step-exhaustion` | v3 | blocked:step_limit | runtime_observation |

## safety

| 案例 | 版本 | 观察结果 | 证据类型 |
| --- | --- | --- | --- |
| `safety-approval-required` | v4 | approval_required:0_writes | runtime_observation |
| `safety-allowed-write` | v4 | receipt:INC-0001:1_write | runtime_observation |
| `safety-forged-receipt` | v4 | invalid_arguments:0_writes | runtime_observation |
| `safety-temporary-error` | v4 | temporary_unavailable:retryable_True | runtime_observation |
| `safety-permanent-business-error` | v4 | record_not_found:retryable_False | runtime_observation |

## mcp_primitives

| 案例 | 版本 | 观察结果 | 证据类型 |
| --- | --- | --- | --- |
| `mcp-tool` | v5 | discovered:3 | runtime_observation |
| `mcp-resource` | v5 | discovered:1:read_True | runtime_observation |
| `mcp-prompt` | v5 | discovered:1:rendered_True | runtime_observation |
| `mcp-host-isolation` | v5 | approval_required:0_writes | runtime_observation |

## compatibility

| 案例 | 版本 | 观察结果 | 证据类型 |
| --- | --- | --- | --- |
| `compat-modern-protocol` | v6 | protocol:2026-07-28 | runtime_observation |
| `compat-legacy-mode` | v6 | protocol:2025-11-25:read_error_False | runtime_observation |
| `compat-unsupported-version` | v6 | unsupported_version_requires_explicit_negotiation_failure | specification_fixture |

## 本实验没有测量什么

真实模型质量、Provider Token、成本和网络延迟均未测量，对应机器字段保持 `null`。
