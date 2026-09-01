# Chapter 9 Tool Calling and MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish Chapter 9 as a beginner-friendly, code-backed explanation of tool calling and modern MCP, with deterministic experiments, an official SDK server/client, eight hand-drawn educational figures, review evidence, and both GitHub Pages and `wlxralf.com` delivery.

**Architecture:** Build a provider-neutral tool runtime first, then attach the same incident-domain capabilities to the official MCP Python SDK. Keep all public claims reproducible through fixed fixtures and a scripted decision policy; isolate provider live probes from canonical reports. Treat prose, visual prompts, reports, exercises, source ledger, repository navigation, CI, and website synchronization as one versioned chapter release.

**Tech Stack:** Python 3.11–3.13 standard library, `mcp==2.1.1`, `unittest`, Markdown, PNG infographics generated through Codex `imagegen`, Node.js 22 book render checks, MkDocs Material, GitHub Actions, Next.js/Cloudflare main site.

**Spec:** `docs/superpowers/specs/2026-08-31-chapter9-tool-calling-mcp-design.md`

## Global Constraints

- Work from the standalone book repository root; never write secrets, `.env` files, provider receipts, host names, user profile paths, or absolute author-machine paths.
- Treat MCP protocol revision `2026-07-28` as the modern baseline and `mcp==2.1.1` as the pinned teaching SDK; mark older `initialize` behavior as compatibility material.
- Keep the canonical Tool Runtime provider-neutral and Python-standard-library-only; only `chapter9/mcp_app/` and its tests may require the MCP SDK.
- Use `unittest`, fixed clock `2026-09-01T00:00:00Z`, stable IDs, UTF-8/LF, sorted JSON keys, and deterministic Fixture order.
- Canonical reports must contain five groups and keep real-model quality, provider Token counts, cost, and latency as `null`.
- Do not call serialized bytes, characters, or JSON length “Token”; do not publish Provider or product rankings.
- The chapter must contain ordered `v0` through `v6`, 2.5–3.0 万 effective Chinese characters, exactly eight figures, fourteen numbered exercises, Claims, Non-claims, and links to experiments and answers.
- Use the user-confirmed visual system: Chinese `hand-drawn-edu`, cream paper, deep navy outlines, muted blue/green/purple/orange sections; main poster 1024×1536, seven supporting figures 1536×864.
- Save every infographic’s source brief, analysis, structured content, and final prompt before generation; do not repair image text with programmatic overlays.
- Keep English translation `status: planned`; do not create Traditional Chinese content.
- Stage exact paths only. Preserve public history and create a new immutable tag `book-chapter9-v1.0` only after all release gates pass.

---

## File Structure

The completed implementation adds these focused units:

```text
chapter9/
├── __init__.py
├── README.md
├── requirements.txt
├── reference-answers.md
├── publication_checks.py
├── fixtures/
│   ├── service-status.json
│   ├── recent-deployments.json
│   └── runbooks/payments-current.md
├── tool_runtime/
│   ├── __init__.py
│   ├── contracts.py
│   ├── schema.py
│   ├── registry.py
│   ├── policy.py
│   ├── runtime.py
│   ├── loop.py
│   ├── trace.py
│   └── persistence.py
├── incident_domain/
│   ├── __init__.py
│   ├── queries.py
│   ├── tickets.py
│   └── factory.py
├── mcp_app/
│   ├── __init__.py
│   ├── server.py
│   ├── client.py
│   └── adapter.py
├── experiments/
│   ├── __init__.py
│   ├── run_v0_free_text.py
│   ├── run_v1_schema.py
│   ├── run_v2_contracts.py
│   ├── run_v3_tool_loop.py
│   ├── run_v4_receipts.py
│   ├── run_v5_mcp_server.py
│   ├── run_v6_mcp_client.py
│   ├── run_failure_matrix.py
│   └── run_all.py
├── live/
│   ├── README.md
│   ├── provider_adapters.py
│   ├── live_probe.py
│   └── live-probe.example.json
├── reports/
│   ├── tool-mcp-evidence.json
│   ├── tool-mcp-evidence.md
│   └── tool-mcp-trace.jsonl
└── tests/
    ├── test_contracts.py
    ├── test_schema_registry.py
    ├── test_incident_domain.py
    ├── test_policy_runtime.py
    ├── test_tool_loop.py
    ├── test_mcp_app.py
    ├── test_experiments.py
    ├── test_report_reproducibility.py
    ├── test_live_probe.py
    ├── test_chapter_mainline.py
    ├── test_figures.py
    └── test_publication_checks.py
```

The book side adds `book/chapter9.md`, eight `book/images/fig9-*.png` files, `book/sources/chapter9-sources.md`, and `book/reviews/chapter9-review-codex.md`. Infographic reproducibility records live under eight `infographic/chapter9-*/` directories; reference images stay ignored by Git under each `refs/` directory.

---

### Task 1: Freeze incident fixtures and core contracts

**Files:**
- Create: `chapter9/__init__.py`
- Create: `chapter9/requirements.txt`
- Create: `chapter9/fixtures/service-status.json`
- Create: `chapter9/fixtures/recent-deployments.json`
- Create: `chapter9/fixtures/runbooks/payments-current.md`
- Create: `chapter9/tool_runtime/__init__.py`
- Create: `chapter9/tool_runtime/contracts.py`
- Test: `chapter9/tests/__init__.py`
- Test: `chapter9/tests/test_contracts.py`

**Interfaces:**
- Produces: `RiskLevel`, `ResultStatus`, `ToolDefinition`, `ToolCall`, `ValidationIssue`, `ToolFailure`, `ExecutionReceipt`, `ToolResult`, `CallerContext`, and `stable_digest(payload)`.
- Consumes: no application code; only fixed JSON/Markdown fixtures and Python standard library.

- [ ] **Step 1: Write the failing contract tests**

```python
from dataclasses import FrozenInstanceError
from pathlib import Path
import json
import unittest

from chapter9.tool_runtime.contracts import (
    RiskLevel,
    ToolCall,
    ToolDefinition,
    stable_digest,
)

ROOT = Path(__file__).resolve().parents[2]


class ContractTests(unittest.TestCase):
    def test_fixed_fixtures_describe_payment_status_deployment_and_runbook(self):
        status = json.loads((ROOT / "chapter9/fixtures/service-status.json").read_text(encoding="utf-8"))
        deployments = json.loads((ROOT / "chapter9/fixtures/recent-deployments.json").read_text(encoding="utf-8"))
        runbook = (ROOT / "chapter9/fixtures/runbooks/payments-current.md").read_text(encoding="utf-8")
        self.assertEqual("2026-09-01T00:00:00Z", status["observed_at"])
        self.assertEqual(0.182, status["services"]["payments"]["error_rate"])
        self.assertEqual("deploy-payments-0042", deployments[0]["deployment_id"])
        self.assertIn("error_rate >= 0.15", runbook)

    def test_tool_contracts_reject_blank_identity_and_are_frozen(self):
        with self.assertRaises(ValueError):
            ToolCall(call_id="", tool_name="get_service_status", arguments={}, step_id="step-1")
        definition = ToolDefinition(
            name="get_service_status",
            description="Read the fixed service snapshot.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            risk_level=RiskLevel.READ,
        )
        with self.assertRaises(FrozenInstanceError):
            definition.name = "changed"
        self.assertEqual(stable_digest({"b": 2, "a": 1}), stable_digest({"a": 1, "b": 2}))
```

- [ ] **Step 2: Run the tests and confirm the missing-module failure**

Run: `python -m unittest chapter9.tests.test_contracts -v`

Expected: FAIL because `chapter9.tool_runtime.contracts` does not exist.

- [ ] **Step 3: Add exact fixed Fixture values**

`service-status.json` must store `payments` with `error_rate: 0.182`, `p95_latency_ms: 4200`, `failed_checkout_ratio: 0.21`, `window_minutes: 5`, and `observed_at: 2026-09-01T00:00:00Z`. `recent-deployments.json` must contain two sorted entries, with `deploy-payments-0042`, version `payments-3.7.0`, deployed at `2026-08-31T23:42:00Z` first. The Runbook must state that P1 requires `error_rate >= 0.15` for five minutes plus material checkout failure, and must never contain instructions aimed at the model.

- [ ] **Step 4: Implement immutable contracts and canonical hashing**

```python
class RiskLevel(str, Enum):
    READ = "read"
    WRITE = "write"


class ResultStatus(str, Enum):
    SUCCEEDED = "succeeded"
    INVALID_ARGUMENTS = "invalid_arguments"
    DENIED = "denied"
    BUSINESS_ERROR = "business_error"
    EXECUTION_ERROR = "execution_error"


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

    def __post_init__(self) -> None:
        if not self.call_id.strip() or not self.tool_name.strip() or not self.step_id.strip():
            raise ValueError("tool call identity fields must be non-blank")


def stable_digest(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
```

Define every produced dataclass with `frozen=True, slots=True`; use the `ToolDefinition` field order shown above and copy mapping inputs to plain sorted dictionaries before hashing. `ToolResult.succeeded(call_id, data, receipt=None)` and `ToolResult.failed(call_id, status, code, message, retryable=False, issues=())` must be the only constructors used outside this file.

- [ ] **Step 5: Run the contract tests**

Run: `python -m unittest chapter9.tests.test_contracts -v`

Expected: PASS.

- [ ] **Step 6: Commit the fixed domain contract**

```bash
git add chapter9/__init__.py chapter9/requirements.txt chapter9/fixtures chapter9/tool_runtime/__init__.py chapter9/tool_runtime/contracts.py chapter9/tests/__init__.py chapter9/tests/test_contracts.py
git commit -m "feat: add chapter 9 tool contracts and fixtures"
```

---

### Task 2: Implement the teaching JSON Schema subset and registry

**Files:**
- Create: `chapter9/tool_runtime/schema.py`
- Create: `chapter9/tool_runtime/registry.py`
- Test: `chapter9/tests/test_schema_registry.py`

**Interfaces:**
- Consumes: `ToolDefinition`, `ToolCall`, `ToolResult`, `ValidationIssue` from Task 1.
- Produces: `validate_arguments(schema, arguments) -> tuple[ValidationIssue, ...]`, `ToolRegistry.register(definition, handler)`, `ToolRegistry.definition(name)`, and `ToolRegistry.invoke(call)`.

- [ ] **Step 1: Write failing tests for validation paths and registration**

```python
class SchemaRegistryTests(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "type": "object",
            "properties": {
                "service": {"type": "string", "enum": ["payments"]},
                "window_minutes": {"type": "integer", "minimum": 1, "maximum": 30},
            },
            "required": ["service", "window_minutes"],
            "additionalProperties": False,
        }

    def test_validator_reports_stable_json_pointer_paths(self):
        issues = validate_arguments(self.schema, {"service": "billing", "extra": True})
        self.assertEqual(
            [("/extra", "additionalProperties"), ("/service", "enum"), ("/window_minutes", "required")],
            [(issue.path, issue.keyword) for issue in issues],
        )

    def test_registry_rejects_duplicate_and_unknown_tools(self):
        registry = ToolRegistry()
        definition = ToolDefinition("status", "Read status", self.schema, RiskLevel.READ)
        registry.register(definition, lambda arguments: {"service": arguments["service"]})
        with self.assertRaises(ValueError):
            registry.register(definition, lambda arguments: {})
        result = registry.invoke(ToolCall("call-1", "missing", {}, "step-1"))
        self.assertEqual(ResultStatus.BUSINESS_ERROR, result.status)
        self.assertEqual("unknown_tool", result.failure.code)
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m unittest chapter9.tests.test_schema_registry -v`

Expected: FAIL because `schema.py` and `registry.py` do not exist.

- [ ] **Step 3: Implement the documented JSON Schema subset**

Support only `type`, `properties`, `required`, `additionalProperties`, `enum`, `minimum`, `maximum`, and nested object/array values. Sort issues by `(path, keyword)`. Reject a Schema keyword outside that set with `ValueError("unsupported teaching schema keyword: <name>")`; this prevents the chapter from implying that the small validator implements all of JSON Schema 2020-12.

```python
def validate_arguments(schema: Mapping[str, object], arguments: Mapping[str, object]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    _validate(schema, arguments, path="", issues=issues)
    return tuple(sorted(issues, key=lambda item: (item.path, item.keyword)))
```

- [ ] **Step 4: Implement registry identity and exception conversion**

```python
ToolHandler = Callable[[Mapping[str, object]], Mapping[str, object]]


class ToolRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, tuple[ToolDefinition, ToolHandler]] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        if definition.name in self._entries:
            raise ValueError(f"duplicate tool: {definition.name}")
        self._entries[definition.name] = (definition, handler)

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._entries[name][0] for name in sorted(self._entries))
```

`invoke` must return `unknown_tool` for an absent name, `business_error` for a `DomainError`, and `execution_error` with the generic message `工具执行失败，详细信息仅保留在受保护日志中。` for unexpected exceptions. Never place exception representations or tracebacks in canonical results.

- [ ] **Step 5: Run the schema and registry tests**

Run: `python -m unittest chapter9.tests.test_schema_registry -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add chapter9/tool_runtime/schema.py chapter9/tool_runtime/registry.py chapter9/tests/test_schema_registry.py
git commit -m "feat: validate and register chapter 9 tools"
```

---

### Task 3: Build the deterministic incident-domain tools

**Files:**
- Create: `chapter9/incident_domain/__init__.py`
- Create: `chapter9/incident_domain/queries.py`
- Create: `chapter9/incident_domain/tickets.py`
- Create: `chapter9/incident_domain/factory.py`
- Test: `chapter9/tests/test_incident_domain.py`

**Interfaces:**
- Consumes: Task 1 fixtures and `ToolRegistry` from Task 2.
- Produces: `FixtureRepository.load(root)`, `TicketStore`, `IncidentService.get_service_status`, `IncidentService.list_recent_deployments`, `IncidentService.current_runbook`, `IncidentService.create_incident_ticket`, and `build_incident_registry(repository, service) -> ToolRegistry`.

- [ ] **Step 1: Write failing domain tests**

```python
class IncidentDomainTests(unittest.TestCase):
    def setUp(self):
        self.repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
        self.tickets = TicketStore(clock=lambda: "2026-09-01T00:00:00Z")
        self.service = IncidentService(self.repository, self.tickets)

    def test_queries_return_fixed_status_and_sorted_deployments(self):
        status = self.service.get_service_status("payments", 5)
        deployments = self.service.list_recent_deployments("payments", "2026-08-31T23:00:00Z")
        self.assertEqual(0.182, status["error_rate"])
        self.assertEqual(["deploy-payments-0042"], [item["deployment_id"] for item in deployments])

    def test_ticket_store_changes_only_after_real_creation(self):
        self.assertEqual((), self.tickets.all())
        ticket = self.service.create_incident_ticket(
            title="支付服务大量超时",
            severity="P1",
            evidence_ids=("status-payments-0001", "deploy-payments-0042"),
        )
        self.assertEqual("INC-0001", ticket["ticket_id"])
        self.assertEqual(1, len(self.tickets.all()))
```

- [ ] **Step 2: Run the tests and confirm missing implementations**

Run: `python -m unittest chapter9.tests.test_incident_domain -v`

Expected: FAIL on missing `FixtureRepository` and `IncidentService`.

- [ ] **Step 3: Implement strict Fixture loading and read tools**

`FixtureRepository.load` must reject unknown top-level fields, timestamps without `Z`, unsorted deployments, unknown services, and Runbook paths outside the Fixture root. `get_service_status` must reject any window other than the fixture’s five-minute window with `DomainError("unsupported_window", ...)` rather than interpolating nonexistent data.

- [ ] **Step 4: Implement the in-memory ticket boundary**

```python
class TicketStore:
    def create(self, *, title: str, severity: str, evidence_ids: tuple[str, ...]) -> dict[str, object]:
        if severity not in {"P1", "P2", "P3"}:
            raise DomainError("invalid_severity", f"unsupported severity: {severity}")
        ticket_id = f"INC-{len(self._tickets) + 1:04d}"
        record = {
            "ticket_id": ticket_id,
            "title": title,
            "severity": severity,
            "evidence_ids": list(evidence_ids),
            "created_at": self._clock(),
        }
        self._tickets.append(record)
        return dict(record)
```

`build_incident_registry` must register exactly `create_incident_ticket`, `get_service_status`, and `list_recent_deployments`, with closed object Schemas (`additionalProperties: false`) and `RiskLevel.WRITE` only on ticket creation.

`IncidentService.current_runbook()` must return the exact UTF-8 Fixture text loaded inside `FixtureRepository`; it must not read an arbitrary URI or caller-provided path.

- [ ] **Step 5: Run domain and registry tests**

Run: `python -m unittest chapter9.tests.test_incident_domain chapter9.tests.test_schema_registry -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add chapter9/incident_domain chapter9/tests/test_incident_domain.py
git commit -m "feat: add deterministic incident tools"
```

---

### Task 4: Add policy gates, side-effect receipts, and one-call execution

**Files:**
- Create: `chapter9/tool_runtime/policy.py`
- Create: `chapter9/tool_runtime/runtime.py`
- Test: `chapter9/tests/test_policy_runtime.py`

**Interfaces:**
- Consumes: Task 1 contracts, `validate_arguments`, `ToolRegistry`, and the incident registry.
- Produces: `PolicyDecision`, `PolicyEngine.evaluate(definition, call, caller)`, and `ToolRuntime.execute(call, caller) -> ToolResult`.

- [ ] **Step 1: Write failing tests for three execution gates**

```python
class PolicyRuntimeTests(unittest.TestCase):
    def setUp(self):
        repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
        self.tickets = TicketStore(clock=lambda: "2026-09-01T00:00:00Z")
        registry = build_incident_registry(repository, IncidentService(repository, self.tickets))
        self.runtime = ToolRuntime(registry, PolicyEngine())

    def test_invalid_arguments_never_reach_handler(self):
        result = self.runtime.execute(
            ToolCall("call-1", "get_service_status", {"service": "payments"}, "step-1"),
            CallerContext("reader", frozenset(), "2026-09-01T00:00:00Z"),
        )
        self.assertEqual(ResultStatus.INVALID_ARGUMENTS, result.status)
        self.assertEqual((), self.tickets.all())

    def test_p1_write_requires_host_grant(self):
        call = ToolCall("call-2", "create_incident_ticket", {
            "title": "支付服务大量超时", "severity": "P1",
            "evidence_ids": ["status-payments-0001", "deploy-payments-0042"],
        }, "step-3")
        denied = self.runtime.execute(call, CallerContext("oncall", frozenset(), "2026-09-01T00:00:00Z"))
        approved_call = ToolCall("call-3", call.tool_name, call.arguments, call.step_id)
        allowed = self.runtime.execute(approved_call, CallerContext("oncall", frozenset({"incident:create:p1"}), "2026-09-01T00:00:00Z"))
        self.assertEqual(ResultStatus.DENIED, denied.status)
        self.assertEqual(ResultStatus.SUCCEEDED, allowed.status)
        self.assertEqual("INC-0001", allowed.receipt.external_id)
        self.assertEqual(1, len(self.tickets.all()))
```

- [ ] **Step 2: Run the tests and verify the missing policy/runtime failure**

Run: `python -m unittest chapter9.tests.test_policy_runtime -v`

Expected: FAIL because `PolicyEngine` and `ToolRuntime` do not exist.

- [ ] **Step 3: Implement allow/deny/ask without durable workflow state**

```python
class PolicyOutcome(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class PolicyEngine:
    def evaluate(self, definition: ToolDefinition, call: ToolCall, caller: CallerContext) -> PolicyDecision:
        if definition.risk_level is RiskLevel.READ:
            return PolicyDecision(PolicyOutcome.ALLOW, "read_only")
        severity = str(call.arguments.get("severity", ""))
        scope = f"incident:create:{severity.casefold()}"
        if scope in caller.grants:
            return PolicyDecision(PolicyOutcome.ALLOW, "explicit_grant")
        return PolicyDecision(PolicyOutcome.ASK, f"missing_grant:{scope}")
```

Map `ASK` to a `ToolResult` with status `DENIED`, code `approval_required`, and `retryable=False`; do not pause or checkpoint in this chapter.

- [ ] **Step 4: Implement execution order and trusted receipt creation**

`ToolRuntime.execute` must enforce this exact order: duplicate `call_id` check, tool lookup, Schema validation, policy evaluation, registry invocation, receipt construction. Only a successful write tool gets a receipt. Construct `action_id` as `action-` plus the first 16 characters of a digest over tool name, validated arguments, and external ID. Never accept a `receipt` field in model arguments.

- [ ] **Step 5: Run all Task 1–4 tests**

Run: `python -m unittest chapter9.tests.test_contracts chapter9.tests.test_schema_registry chapter9.tests.test_incident_domain chapter9.tests.test_policy_runtime -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add chapter9/tool_runtime/policy.py chapter9/tool_runtime/runtime.py chapter9/tests/test_policy_runtime.py
git commit -m "feat: enforce chapter 9 tool execution gates"
```

---

### Task 5: Build the scripted Tool Loop and redacted trace

**Files:**
- Create: `chapter9/tool_runtime/loop.py`
- Create: `chapter9/tool_runtime/trace.py`
- Test: `chapter9/tests/test_tool_loop.py`

**Interfaces:**
- Consumes: `ToolRuntime.execute`, fixed incident tools, and core contracts.
- Produces: `FinalAnswer`, `LoopState`, `LoopOutcome`, `DecisionPolicy` protocol, `ScriptedIncidentPolicy`, `run_tool_loop(policy, runtime, caller, max_steps=6)`, `build_demo_loop(grants) -> LoopOutcome`, and `TraceRecorder`.

- [ ] **Step 1: Write the failing happy-path and failure-path tests**

```python
class ToolLoopTests(unittest.TestCase):
    def test_scripted_loop_reads_twice_then_creates_one_ticket(self):
        outcome = build_demo_loop(grants=frozenset({"incident:create:p1"}))
        self.assertEqual(
            ["get_service_status", "list_recent_deployments", "create_incident_ticket"],
            [event.tool_name for event in outcome.trace if event.event_type == "tool_call"],
        )
        self.assertEqual("completed", outcome.status)
        self.assertIn("INC-0001", outcome.final_answer.text)
        self.assertEqual(1, outcome.side_effect_count)

    def test_loop_does_not_turn_approval_required_into_success(self):
        outcome = build_demo_loop(grants=frozenset())
        self.assertEqual("blocked", outcome.status)
        self.assertEqual("approval_required", outcome.final_answer.reason)
        self.assertEqual(0, outcome.side_effect_count)
```

- [ ] **Step 2: Run and confirm failure**

Run: `python -m unittest chapter9.tests.test_tool_loop -v`

Expected: FAIL because `loop.py` and `trace.py` are missing.

- [ ] **Step 3: Implement a deterministic policy that reacts to results**

`ScriptedIncidentPolicy.decide(state)` must emit stable calls `call-status-001`, `call-deploy-002`, and `call-ticket-003`. It may propose P1 only after a successful status result proves `error_rate >= 0.15` and a successful deployment result identifies `deploy-payments-0042`. If either read fails, it returns a blocked `FinalAnswer` instead of creating a ticket.

`build_demo_loop(grants)` must construct fresh Fixture, TicketStore, registry, runtime, caller, and scripted policy instances on every call, call `run_tool_loop`, and return its `LoopOutcome` so tests never share side effects.

```python
class DecisionPolicy(Protocol):
    def decide(self, state: LoopState) -> ToolCall | FinalAnswer: ...


def run_tool_loop(policy: DecisionPolicy, runtime: ToolRuntime, caller: CallerContext, *, max_steps: int = 6) -> LoopOutcome:
    state = LoopState.empty()
    for step in range(max_steps):
        decision = policy.decide(state)
        if isinstance(decision, FinalAnswer):
            return LoopOutcome.from_final(decision, state)
        result = runtime.execute(decision, caller)
        state = state.append(decision, result)
    return LoopOutcome.step_limit(state)
```

- [ ] **Step 4: Record causal IDs without arguments or document bodies**

Trace events may contain event ID, step ID, call ID, tool name, result status, error code, argument digest, receipt action ID, and reason. They must not contain raw titles, Runbook text, caller subject, grants, exception text, or full tool results.

- [ ] **Step 5: Run the Tool Loop suite**

Run: `python -m unittest chapter9.tests.test_tool_loop chapter9.tests.test_policy_runtime -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add chapter9/tool_runtime/loop.py chapter9/tool_runtime/trace.py chapter9/tests/test_tool_loop.py
git commit -m "feat: add deterministic chapter 9 tool loop"
```

---

### Task 6: Implement the official MCP v2 server, client, and Host adapter

**Files:**
- Modify: `chapter9/requirements.txt`
- Create: `chapter9/mcp_app/__init__.py`
- Create: `chapter9/mcp_app/server.py`
- Create: `chapter9/mcp_app/client.py`
- Create: `chapter9/mcp_app/adapter.py`
- Test: `chapter9/tests/test_mcp_app.py`

**Interfaces:**
- Consumes: `FixtureRepository`, `IncidentService`, `TicketStore`, `CallerContext`, and the official `MCPServer`/`Client` API.
- Produces: `create_server(service, authorized_scopes) -> MCPServer`, `build_default_server(authorized_scopes=frozenset()) -> MCPServer`, `inspect_server(server) -> MCPInventory`, and `HostMCPAdapter.call_tool(name, arguments, caller)`.

- [ ] **Step 1: Pin the SDK and install it**

Set `chapter9/requirements.txt` to exactly:

```text
mcp==2.1.1
```

Run: `python -m pip install -r chapter9/requirements.txt`

Expected: `mcp 2.1.1` installs successfully under Python 3.11–3.13.

- [ ] **Step 2: Write failing in-memory MCP tests**

```python
from mcp import Client


class MCPAppTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        repository = FixtureRepository.load(ROOT / "chapter9/fixtures")
        self.tickets = TicketStore(clock=lambda: "2026-09-01T00:00:00Z")
        service = IncidentService(repository, self.tickets)
        self.server = create_server(service, authorized_scopes=frozenset({"incident:create:p1"}))

    async def test_modern_client_discovers_three_primitives(self):
        async with Client(self.server, raise_exceptions=True) as client:
            self.assertEqual("2026-07-28", client.protocol_version)
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()
            self.assertEqual(
                ["create_incident_ticket", "get_service_status", "list_recent_deployments"],
                sorted(tool.name for tool in tools.tools),
            )
            self.assertEqual(["runbook://payments/current"], [str(item.uri) for item in resources.resources])
            self.assertEqual(["triage_incident"], [item.name for item in prompts.prompts])

    async def test_tool_error_is_a_result_and_resource_is_not_a_tool(self):
        async with Client(self.server, raise_exceptions=True) as client:
            unknown = await client.call_tool("runbook://payments/current", {})
            resource = await client.read_resource("runbook://payments/current")
            self.assertTrue(unknown.is_error)
            self.assertIn("error_rate >= 0.15", resource.contents[0].text)
```

- [ ] **Step 3: Run the tests and confirm the missing server failure**

Run: `python -m unittest chapter9.tests.test_mcp_app -v`

Expected: FAIL because `create_server` is absent.

- [ ] **Step 4: Implement the official SDK server**

```python
from mcp.server import MCPServer


def create_server(incident_service: IncidentService, authorized_scopes: frozenset[str]) -> MCPServer:
    mcp = MCPServer("Starboard Incident")

    @mcp.tool()
    def get_service_status(service: str, window_minutes: int = 5) -> dict[str, object]:
        """Read one fixed service-health snapshot."""
        return incident_service.get_service_status(service, window_minutes)

    @mcp.resource("runbook://payments/current")
    def payments_runbook() -> str:
        """Return the current payment incident runbook."""
        return incident_service.current_runbook()

    @mcp.prompt()
    def triage_incident(service: str = "payments") -> str:
        """Create a user-selected incident triage request."""
        return f"请先查询 {service} 状态和最近部署；证据不足时不要创建故障单。"

    return mcp
```

Add the other two tools with typed arguments. The Server must enforce `authorized_scopes` inside `create_incident_ticket`; approval is constructor state invisible to the model, never a Tool argument.

`build_default_server` must load only `chapter9/fixtures`, create a fresh TicketStore with the fixed clock, and call `create_server`. Add `main() -> int` that runs `build_default_server().run()` over the SDK default `stdio` transport, and guard it with `if __name__ == "__main__": raise SystemExit(main())`. The README command is `python -m chapter9.mcp_app.server`.

- [ ] **Step 5: Implement client inventory and Host-side consent**

`inspect_server` must enter `Client(server, raise_exceptions=True)`, record `protocol_version`, capability presence, sorted tool/resource/prompt names, and leave without calling a write tool. `HostMCPAdapter` must run its own read/write policy before `client.call_tool`; Server authorization remains active even if a Host adapter is bypassed.

- [ ] **Step 6: Test modern and legacy modes without hand-writing JSON-RPC**

Add a test that opens `Client(server, mode="legacy")`, asserts its protocol version is not `2026-07-28`, and confirms the same read tool remains callable. Add a test that an unauthorized Server returns `is_error=True` for P1 creation. Do not assert SDK-private message fields.

- [ ] **Step 7: Run MCP and prior chapter tests**

Run: `python -m unittest discover -s chapter9/tests -v`

Expected: all current Chapter 9 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add chapter9/requirements.txt chapter9/mcp_app chapter9/tests/test_mcp_app.py
git commit -m "feat: add official MCP v2 incident server"
```

---

### Task 7: Generate five deterministic experiment groups and canonical reports

**Files:**
- Create: `chapter9/tool_runtime/persistence.py`
- Create: `chapter9/experiments/__init__.py`
- Create: `chapter9/experiments/run_v0_free_text.py`
- Create: `chapter9/experiments/run_v1_schema.py`
- Create: `chapter9/experiments/run_v2_contracts.py`
- Create: `chapter9/experiments/run_v3_tool_loop.py`
- Create: `chapter9/experiments/run_v4_receipts.py`
- Create: `chapter9/experiments/run_v5_mcp_server.py`
- Create: `chapter9/experiments/run_v6_mcp_client.py`
- Create: `chapter9/experiments/run_failure_matrix.py`
- Create: `chapter9/experiments/run_all.py`
- Create: `chapter9/reports/tool-mcp-evidence.json`
- Create: `chapter9/reports/tool-mcp-evidence.md`
- Create: `chapter9/reports/tool-mcp-trace.jsonl`
- Test: `chapter9/tests/test_experiments.py`
- Test: `chapter9/tests/test_report_reproducibility.py`

**Interfaces:**
- Consumes: complete Tool Runtime and MCP app.
- Produces: `build_report() -> dict[str, object]`, `generate_to(output: Path) -> tuple[Path, ...]`, and seven small reader-facing version runners.

- [ ] **Step 1: Write failing report-contract tests**

```python
class ExperimentTests(unittest.TestCase):
    def test_report_has_five_groups_twenty_cases_and_v0_through_v6(self):
        report = build_report()
        self.assertEqual(
            ["compatibility", "contract", "loop", "mcp_primitives", "safety"],
            sorted(report["groups"]),
        )
        cases = [case for group in report["groups"].values() for case in group["cases"]]
        self.assertEqual(20, len(cases))
        self.assertEqual(set(range(7)), {version for case in cases for version in case["versions"]})
        self.assertTrue(all(case["sample_count"] == 1 for case in cases))

    def test_unmeasured_fields_are_null_and_no_vendor_ranking_exists(self):
        report = build_report()
        self.assertEqual(
            {"provider_cost": None, "provider_latency_ms": None, "provider_tokens": None, "real_model_quality": None},
            report["unmeasured"],
        )
        self.assertNotIn("ranking", json.dumps(report, ensure_ascii=False).casefold())
```

- [ ] **Step 2: Run and confirm missing report builder**

Run: `python -m unittest chapter9.tests.test_experiments -v`

Expected: FAIL because `run_all.py` does not exist.

- [ ] **Step 3: Implement exact group sizes and failure probes**

Use these group contracts:

| Group | Case count | Required cases |
| --- | ---: | --- |
| contract | 4 | free text, malformed JSON, Schema violation, valid call |
| loop | 4 | read result correlation, successful three-call loop, mismatched call ID, step exhaustion |
| safety | 5 | approval required, allowed write, forged receipt, temporary error, permanent business error |
| mcp_primitives | 4 | Tool, Resource, Prompt, Host isolation |
| compatibility | 3 | modern protocol, legacy mode, unsupported-version explanation fixture |

The unsupported-version case is a deterministic specification fixture, not a hand-written transport implementation. Mark it `evidence_kind: "specification_fixture"`.

Each `run_vN_*.py` module must expose `main() -> int`, print one compact JSON object containing its version, input, observed boundary, and non-claim, and exit 0. `run_failure_matrix.py` prints the five safety cases in stable ID order; none of these scripts writes canonical reports.

- [ ] **Step 4: Implement stable writers**

```python
def write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
```

Implement matching Markdown and JSONL writers. The trace must sort by numeric event ID and include only IDs, digests, status, protocol version, primitive type, and reason.

- [ ] **Step 5: Add byte-reproducibility tests**

Generate to two temporary directories, compare each file byte-for-byte, compare the first output with the committed reports, reject CRLF, and assert that trace rows contain none of `title`, `runbook`, `arguments`, `caller`, `grants`, `exception`, or `content`.

- [ ] **Step 6: Generate and inspect canonical reports**

Run: `python -m chapter9.experiments.run_all --output chapter9/reports`

Run: `python -m chapter9.experiments.run_all --output chapter9/reports`

Expected: both runs leave identical Git content; report summary says 20 single-sample cases and explicitly states what the experiment cannot prove.

- [ ] **Step 7: Run all Chapter 9 tests**

Run: `python -m unittest discover -s chapter9/tests -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add chapter9/tool_runtime/persistence.py chapter9/experiments chapter9/reports chapter9/tests/test_experiments.py chapter9/tests/test_report_reproducibility.py
git commit -m "feat: add reproducible tool and MCP experiments"
```

---

### Task 8: Add optional Provider adapters and a dry-run Live Probe

**Files:**
- Create: `chapter9/live/README.md`
- Create: `chapter9/live/provider_adapters.py`
- Create: `chapter9/live/live_probe.py`
- Create: `chapter9/live/live-probe.example.json`
- Modify: `.gitignore`
- Test: `chapter9/tests/test_live_probe.py`

**Interfaces:**
- Consumes: provider response fixtures and unified `ToolCall`/`ToolResult`.
- Produces: `OpenAIResponsesAdapter`, `AnthropicMessagesAdapter`, and `run_probe(provider, execute=False)`.

- [ ] **Step 1: Write failing adapter tests with redacted fixtures**

```python
class LiveProbeTests(unittest.TestCase):
    def test_openai_and_anthropic_shapes_map_to_the_same_tool_call(self):
        openai_item = {"type": "function_call", "call_id": "call-1", "name": "get_service_status", "arguments": "{\"service\":\"payments\",\"window_minutes\":5}"}
        anthropic_block = {"type": "tool_use", "id": "call-1", "name": "get_service_status", "input": {"service": "payments", "window_minutes": 5}}
        self.assertEqual(
            OpenAIResponsesAdapter().to_tool_call(openai_item, "step-1"),
            AnthropicMessagesAdapter().to_tool_call(anthropic_block, "step-1"),
        )

    def test_default_probe_is_offline_and_does_not_require_a_key(self):
        result = run_probe("deepseek", execute=False)
        self.assertEqual("dry_run", result["status"])
        self.assertFalse(result["network_access"])
```

- [ ] **Step 2: Run and confirm missing adapters**

Run: `python -m unittest chapter9.tests.test_live_probe -v`

Expected: FAIL because the Live Probe modules do not exist.

- [ ] **Step 3: Implement shape adapters without provider SDK dependencies**

OpenAI/DeepSeek arguments arrive as a JSON string; Anthropic input arrives as an object. Both adapters must reject missing call IDs, unknown block types, non-object arguments, and malformed JSON. Result rendering must preserve the call ID and expose structured errors without including receipt internals in model-readable text.

- [ ] **Step 4: Implement explicit live execution gates**

`live_probe.py` accepts `--provider deepseek|openai|anthropic` and `--execute`. Without `--execute`, it performs no network access. With `--execute`, it reads only the matching environment key, writes only under `chapter9/live-reports/`, and redacts request headers and response IDs. Missing keys return exit code 2 and the message `live probe skipped: missing provider credential`.

- [ ] **Step 5: Protect live output and document exact commands**

Add `chapter9/live-reports/` to `.gitignore`. README commands must use placeholders and environment-variable names only; never include a key value.

- [ ] **Step 6: Run the dry-run and tests**

Run: `python chapter9/live/live_probe.py --provider deepseek`

Run: `python -m unittest chapter9.tests.test_live_probe -v`

Expected: dry-run succeeds without credentials and tests PASS.

- [ ] **Step 7: Commit**

```bash
git add .gitignore chapter9/live chapter9/tests/test_live_probe.py
git commit -m "feat: add optional chapter 9 provider adapters"
```

---

### Task 9: Build the source ledger and chapter evidence skeleton

**Files:**
- Create: `book/sources/chapter9-sources.md`
- Create: `book/chapter9.md`
- Test: `chapter9/tests/test_chapter_mainline.py`

**Interfaces:**
- Consumes: official sources verified on publication day and canonical local report paths.
- Produces: at least 20 source records and an ordered chapter shell whose headings become the prose contract.

- [ ] **Step 1: Write a failing source and heading contract**

```python
class ChapterMainlineTests(unittest.TestCase):
    def test_source_ledger_has_current_official_protocol_and_sdk_records(self):
        sources = SOURCES.read_text(encoding="utf-8")
        self.assertGreaterEqual(len(re.findall(r"^### \[S\d{2}\]", sources, re.MULTILINE)), 20)
        for value in ("2026-07-28", "mcp==2.1.1", "2026-09-01", "JSON Schema 2020-12", "JSON-RPC 2.0"):
            self.assertIn(value, sources)

    def test_chapter_shell_orders_mainline_before_advanced_material(self):
        chapter = CHAPTER.read_text(encoding="utf-8")
        positions = [chapter.index(f"### v{version}：") for version in range(7)]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(chapter.index("### v6："), chapter.index("## 进阶阅读："))
```

- [ ] **Step 2: Run and verify files are missing**

Run: `python -m unittest chapter9.tests.test_chapter_mainline -v`

Expected: FAIL because the chapter and source ledger do not exist.

- [ ] **Step 3: Create the source ledger with concrete records**

Include separate records for MCP latest specification, architecture, versioning, discovery, Tools, Resources, Prompts, stdio, Streamable HTTP, authorization, security guidance, Python SDK `v2.1.1`, SDK client guide, SDK testing guide, JSON Schema 2020-12, JSON-RPC 2.0, OpenAI Function Calling, OpenAI MCP/Connectors, Anthropic Tool Use, Anthropic MCP, LangChain Tools, LangGraph ToolNode, and the official `LLMs-from-scratch` repository. Every record must contain type, URL/local path, fact use, explicit non-claim, last checked `2026-09-01`, and pre-publication review `是`.

- [ ] **Step 4: Create the exact prose skeleton**

The file must start with the chapter title and include, in order, the opening failure, reading hint, short answer, boundary map, `v0`–`v6`, advanced protocol/framework/security material, experiment reproduction, summary, Claims, Non-claims, exercises, and Chapter 10 transition. Link the three canonical reports, `../chapter9/README.md`, and `../chapter9/reference-answers.md`.

- [ ] **Step 5: Run source and heading tests**

Run: `python -m unittest chapter9.tests.test_chapter_mainline -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add book/chapter9.md book/sources/chapter9-sources.md chapter9/tests/test_chapter_mainline.py
git commit -m "docs: establish chapter 9 evidence and reader path"
```

---

### Task 10: Write the opening and from-scratch Tool Runtime narrative

**Files:**
- Modify: `book/chapter9.md`
- Modify: `chapter9/tests/test_chapter_mainline.py`

**Interfaces:**
- Consumes: v0–v4 code, fixed reports, and Figures 9-1 through 9-4 references.
- Produces: the beginner path from the false completion claim through trusted execution receipts.

- [ ] **Step 1: Extend the failing reader-path test**

Require every `v0`–`v4` section to contain `**输入：**`, `**关键代码：**`, `**运行结果：**`, `**解决了什么：**`, and `**还没有解决什么：**`. Require the exact distinctions `JSON 语法正确 ≠ Tool Call 合法`, `Tool Call 是提议`, and `Execution Receipt 来自执行边界`.

- [ ] **Step 2: Run and confirm the skeleton fails the density contract**

Run: `python -m unittest chapter9.tests.test_chapter_mainline -v`

Expected: FAIL because the section evidence markers are absent.

- [ ] **Step 3: Write the opening failure and boundary explanation**

Use the concrete missing-ticket scene before definitions. Explain 值班、P1、Runbook and deployment at first use. Compare natural-language intent, structured output, Function Calling, ordinary API, Tool, and MCP in one table. Do not introduce Host/Client/Server before the reader understands one local Tool Call.

- [ ] **Step 4: Write v0–v2 with one-screen code excerpts**

Quote exact commands:

```powershell
python -m chapter9.experiments.run_v0_free_text
python -m chapter9.experiments.run_v1_schema
python -m chapter9.experiments.run_v2_contracts
```

Show the empty ticket store, stable Schema issue paths, and the unified `ToolDefinition`/`ToolCall`/`ToolResult` contracts. State that the teaching validator implements a subset, not all of JSON Schema.

- [ ] **Step 5: Write v3–v4 and the complete local loop**

Walk through propose → validate → authorize → invoke → receipt → continue. Show one allowed P1 call and one missing-grant failure. Explain why a model-generated string containing `INC-0001` cannot replace a receipt. Explicitly defer durable approval/resume to Chapter 4 and large-scale idempotency to Chapter 10.

- [ ] **Step 6: Run reader-path and runtime tests**

Run: `python -m unittest chapter9.tests.test_chapter_mainline chapter9.tests.test_tool_loop chapter9.tests.test_policy_runtime -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add book/chapter9.md chapter9/tests/test_chapter_mainline.py
git commit -m "docs: explain tool calling from first principles"
```

---

### Task 11: Write MCP, framework mapping, security, and scope boundaries

**Files:**
- Modify: `book/chapter9.md`
- Modify: `chapter9/tests/test_chapter_mainline.py`

**Interfaces:**
- Consumes: official MCP v2 implementation, source ledger, and canonical MCP cases.
- Produces: v5–v6 plus advanced sections that do not pre-empt Chapters 10 and 11.

- [ ] **Step 1: Add failing MCP accuracy assertions**

```python
def test_mcp_sections_preserve_modern_and_legacy_boundaries(self):
    chapter = CHAPTER.read_text(encoding="utf-8")
    for text in (
        "2026-07-28", "server/discover", "每个请求", "2025-11-25",
        "Host", "Client", "Server", "Tools", "Resources", "Prompts",
        "stdio", "Streamable HTTP",
    ):
        self.assertIn(text, chapter)
    self.assertNotIn("MCP 会自动保证工具安全", chapter)
```

- [ ] **Step 2: Run and verify the prose test fails**

Run: `python -m unittest chapter9.tests.test_chapter_mainline -v`

Expected: FAIL until the MCP sections are written.

- [ ] **Step 3: Write v5 as an SDK-backed Server walkthrough**

Introduce MCP through the N×M connection problem, then Host/Client/Server using the “接线员” analogy. Show the actual `MCPServer` decorators and the discovered Schema. Explain Tools as model-proposed capabilities, Resources as addressable application-selected context, and Prompts as user-selected templates. State that the Server receives only request data supplied to it, not automatic full-conversation access.

- [ ] **Step 4: Write v6 as a Client and compatibility walkthrough**

Show `async with Client(server)` plus `list_tools`, `read_resource`, `get_prompt`, and `call_tool`. Explain that the SDK’s in-memory Client is transport-free testing, `stdio` is the local process path, and Streamable HTTP is the deployment path. Contrast modern per-request metadata with the legacy `initialize` handshake without presenting SDK-private internals as protocol requirements.

- [ ] **Step 5: Write comparison and framework sections**

Provide explicit responsibility tables for Function Calling vs API vs MCP vs Skills vs plugins, and for OpenAI vs Anthropic vs LangChain vs LangGraph. Compare protocol shape and ownership only; do not rank quality. Put tool search, programmatic calls, Tasks, concurrency, cancellation, Registry, Skills over MCP, and MCP Apps in a “next map,” with Chapters 10–11 links.

- [ ] **Step 6: Write the threat model and “do not use MCP” section**

Cover untrusted descriptions/annotations, malicious Resources, prompt injection in Tool Results, local process privileges, remote data exfiltration, Host consent, Server business authorization, error sanitization, and logs. Give three cases where a direct typed function or one internal API is the clearer solution.

- [ ] **Step 7: Run prose, MCP, and source tests**

Run: `python -m unittest chapter9.tests.test_chapter_mainline chapter9.tests.test_mcp_app -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add book/chapter9.md chapter9/tests/test_chapter_mainline.py
git commit -m "docs: explain modern MCP architecture and tradeoffs"
```

---

### Task 12: Complete experiments guide, exercises, answers, and publication contract

**Files:**
- Create: `chapter9/README.md`
- Create: `chapter9/reference-answers.md`
- Create: `chapter9/publication_checks.py`
- Modify: `book/chapter9.md`
- Test: `chapter9/tests/test_publication_checks.py`

**Interfaces:**
- Consumes: full prose, canonical reports, source ledger, and experiment commands.
- Produces: exact chapter density/count gates and a complete reader exercise loop.

- [ ] **Step 1: Write failing publication checks**

The test must call `publication_errors` on the real bundle and initially fail for missing README/answers/exercises. It must also use a small synthetic bundle to prove that the checker catches: fewer than 25,000 or more than 30,000 effective CJK characters, missing `v0`–`v6`, non-exact figure set, duplicate exercise numbers, missing answer sections, fewer than 20 source records, secret-like strings, author paths, unsupported rankings, and offline-byte-as-Token claims.

- [ ] **Step 2: Implement the checker with code-fence exclusion**

```python
@dataclass(frozen=True, slots=True)
class PublicationContract:
    min_cjk: int = 25_000
    max_cjk: int = 30_000
    min_headings: int = 20
    max_headings: int = 40
    figure_count: int = 8
    exercise_count: int = 14
    source_count: int = 20
```

Count prose after removing fenced code, URLs, and Markdown link targets. Count exercises only when a line begins `1.` through `14.` and contains a star difficulty marker. Accept figure extensions `.png` only for Chapter 9.

- [ ] **Step 3: Write fourteen exact exercises and answers**

Exercises must cover tool boundaries, Schema modification, issue paths, call/result correlation, error taxonomy, P1 consent, receipts, Tool/Resource/Prompt classification, Host/Client/Server responsibility, modern/legacy compatibility, transport choice, malicious Server threat modeling, Function Calling/MCP/Skills/plugin selection, and a Chapter 10 tool-discovery design. Each answer section must include `**推理：**`, `**常见错误：**`, and `**验收：**`.

- [ ] **Step 4: Write the experiment README**

Document Python 3.11–3.13, `pip install -r chapter9/requirements.txt`, full test command, report generation command, seven version commands, dry-run Live Probe, exact canonical files, the 20-case group table, supported claims, and non-claims. Link back to `../book/chapter9.md`, sources, and answers.

- [ ] **Step 5: Finish summary, Claims, Non-claims, and Chapter 10 transition**

The transition must say that Chapter 9 used three tools with direct responses, while Chapter 10 addresses large Tool sets, description budget, discovery, background work, concurrency, cancellation, and idempotency at scale.

- [ ] **Step 6: Run publication checks except the still-missing image gate**

Run the synthetic checker tests and all non-figure real-bundle checks. The only allowed remaining real-bundle errors are the eight named `missing_figure:fig9-*` records.

- [ ] **Step 7: Commit**

```bash
git add book/chapter9.md chapter9/README.md chapter9/reference-answers.md chapter9/publication_checks.py chapter9/tests/test_publication_checks.py
git commit -m "docs: complete chapter 9 reader exercises and gates"
```

---

### Task 13: Generate and verify eight hand-drawn educational figures

**Files:**
- Create: `infographic/chapter9-01-tool-call-flow/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-01-tool-call-flow/analysis.md`
- Create: `infographic/chapter9-01-tool-call-flow/structured-content.md`
- Create: `infographic/chapter9-01-tool-call-flow/prompts/01-process-tool-call.md`
- Create: `infographic/chapter9-02-boundaries/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-02-boundaries/analysis.md`
- Create: `infographic/chapter9-02-boundaries/structured-content.md`
- Create: `infographic/chapter9-02-boundaries/prompts/02-comparison-boundaries.md`
- Create: `infographic/chapter9-03-contract/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-03-contract/analysis.md`
- Create: `infographic/chapter9-03-contract/structured-content.md`
- Create: `infographic/chapter9-03-contract/prompts/03-structure-tool-contract.md`
- Create: `infographic/chapter9-04-loop/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-04-loop/analysis.md`
- Create: `infographic/chapter9-04-loop/structured-content.md`
- Create: `infographic/chapter9-04-loop/prompts/04-process-tool-loop.md`
- Create: `infographic/chapter9-05-mcp-architecture/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-05-mcp-architecture/analysis.md`
- Create: `infographic/chapter9-05-mcp-architecture/structured-content.md`
- Create: `infographic/chapter9-05-mcp-architecture/prompts/05-structure-mcp-architecture.md`
- Create: `infographic/chapter9-06-primitives/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-06-primitives/analysis.md`
- Create: `infographic/chapter9-06-primitives/structured-content.md`
- Create: `infographic/chapter9-06-primitives/prompts/06-modules-mcp-primitives.md`
- Create: `infographic/chapter9-07-protocol-eras/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-07-protocol-eras/analysis.md`
- Create: `infographic/chapter9-07-protocol-eras/structured-content.md`
- Create: `infographic/chapter9-07-protocol-eras/prompts/07-comparison-protocol-eras.md`
- Create: `infographic/chapter9-08-failures/source-chapter9-visual-brief.md`
- Create: `infographic/chapter9-08-failures/analysis.md`
- Create: `infographic/chapter9-08-failures/structured-content.md`
- Create: `infographic/chapter9-08-failures/prompts/08-modules-failure-map.md`
- Create: `book/images/fig9-1-tool-call-journey.png`
- Create: `book/images/fig9-2-boundary-map.png`
- Create: `book/images/fig9-3-tool-contract.png`
- Create: `book/images/fig9-4-tool-loop.png`
- Create: `book/images/fig9-5-mcp-architecture.png`
- Create: `book/images/fig9-6-mcp-primitives.png`
- Create: `book/images/fig9-7-protocol-eras.png`
- Create: `book/images/fig9-8-failure-map.png`
- Modify: `book/chapter9.md`
- Modify: `chapter9/tests/test_publication_checks.py`
- Test: `chapter9/tests/test_figures.py`

**Interfaces:**
- Consumes: confirmed user reference style, chapter facts, and canonical report values.
- Produces: one 2:3 main poster and seven 16:9 supporting figures, each with a nearby prose caption that states its reading order and conclusion.

- [ ] **Step 1: Read the required image skills and copy the reference locally**

Read `baoyu-infographic` and `imagegen` completely. Copy the user-supplied style reference into each topic’s ignored `refs/01-ref-hand-drawn-education.png`; record `usage: direct` in the prompt frontmatter. Confirm backend `imagegen`, language `zh`, main aspect `2:3`, support aspect `16:9`, and style `hand-drawn-edu` from the approved design.

- [ ] **Step 2: Write failing raster figure tests**

Use Python standard-library PNG parsing: verify the eight-byte PNG signature and unpack the IHDR width/height with `struct.unpack(">II", payload[16:24])`. Require exactly eight `fig9-*.png`; require 1024×1536 for Figure 1 and 1536×864 for Figures 2–8; require each filename exactly once in `book/chapter9.md` with non-empty Chinese alt text.

- [ ] **Step 3: Save all eight reproducibility briefs before generation**

Each folder must contain faithful chapter content, the one learning objective, exact labels, visual elements, style/palette description, and the final backend prompt. Strip credentials and avoid long sentences inside images. The exact bottom conclusions are:

1. `模型提出动作，系统执行动作，回执证明动作。`
2. `Function Calling 描述一次调用，MCP 标准化能力连接。`
3. `合法调用需要定义、请求、结果和回执四份合同。`
4. `工具结果会回到模型，成为下一步决策的新观察。`
5. `Host 管安全与上下文，Client 管连接，Server 管能力。`
6. `Tool、Resource、Prompt 的关键差异是控制权。`
7. `现代 MCP 每次请求自描述，旧版靠初始化握手。`
8. `格式正确只是起点，安全执行需要多道边界。`

- [ ] **Step 4: Generate Figure 9-1 and inspect at original resolution**

Use `linear-progression + hand-drawn-edu`, four numbered sections, cream paper, navy ink, and blue/green/purple/orange blocks. Generate through `imagegen`, save the returned PNG, view with original detail, and regenerate from a corrected prompt if any title, arrow, or bottom conclusion is unreadable.

- [ ] **Step 5: Generate Figures 9-2 through 9-8**

Use `binary-comparison` for Figures 2 and 7, `structural-breakdown` for Figures 3 and 5, `linear-progression` for Figure 4, `dense-modules` for Figures 6 and 8, all with `hand-drawn-edu`. Crop/resize only when it does not remove labels or alter text; never paint over generated text.

- [ ] **Step 6: Add captions and accessible nearby explanations**

Each Markdown image must be followed by a paragraph beginning `**读图顺序：**` and another sentence beginning `**这张图要说明：**`. Precise version numbers, JSON keys, and error codes remain in code blocks, not solely in raster pixels.

- [ ] **Step 7: Run image and full publication gates**

Run: `python -m unittest chapter9.tests.test_figures chapter9.tests.test_publication_checks -v`

Expected: PASS with exact dimensions, names, links, prose density, exercise count, and source count.

Change the real-bundle assertion in `test_publication_checks.py` from the exact eight `missing_figure` records used in Task 12 to an empty error tuple.

- [ ] **Step 8: Commit prompts and final figures**

```bash
git add infographic/chapter9-01-tool-call-flow infographic/chapter9-02-boundaries infographic/chapter9-03-contract infographic/chapter9-04-loop infographic/chapter9-05-mcp-architecture infographic/chapter9-06-primitives infographic/chapter9-07-protocol-eras infographic/chapter9-08-failures book/images/fig9-1-tool-call-journey.png book/images/fig9-2-boundary-map.png book/images/fig9-3-tool-contract.png book/images/fig9-4-tool-loop.png book/images/fig9-5-mcp-architecture.png book/images/fig9-6-mcp-primitives.png book/images/fig9-7-protocol-eras.png book/images/fig9-8-failure-map.png book/chapter9.md chapter9/tests/test_figures.py
git commit -m "docs: add chapter 9 hand-drawn visual system"
```

---

### Task 14: Perform reader and AI-engineering review, then revise

**Files:**
- Create: `book/reviews/chapter9-review-codex.md`
- Modify: `book/chapter9.md`
- Modify: `chapter9/README.md`
- Modify: `chapter9/reference-answers.md`
- Modify: `book/sources/chapter9-sources.md`
- Modify: `chapter9/tests/test_chapter_mainline.py`
- Modify: `chapter9/tests/test_publication_checks.py`
- Modify: `chapter9/tests/test_figures.py`

**Interfaces:**
- Consumes: complete unpublished chapter bundle.
- Produces: severity-ranked review findings, disposition for every finding, and verified revisions.

- [ ] **Step 1: Run a reader-perspective review**

Check whether a reader unfamiliar with SRE can explain the incident, Tool Call, Tool Result, receipt, Host, Client, Server, Tool, Resource, and Prompt after first use. Record every jargon-before-example, code jump, unexplained output, long paragraph, and figure that repeats rather than teaches.

- [ ] **Step 2: Run an AI-engineering review**

Check protocol revision, SDK APIs, Schema subset wording, error taxonomy, consent vs Server authorization, receipt trust, modern vs legacy lifecycle, transport claims, provider mappings, MCP security, reproducibility, and Chapter 10/11 boundaries. Compare factual statements with the source ledger rather than memory.

- [ ] **Step 3: Write the review report**

Use sections: overall verdict, P0/P1/P2 findings, reader review, expert review, code/report evidence, visual review, source freshness, accepted changes, rejected suggestions with reasons, and final residual risks. Do not call the chapter “complete” before revisions and tests pass.

- [ ] **Step 4: Apply every accepted revision with a regression check**

For a factual correction, add or tighten a prose/source assertion. For a code correction, add a failing test before implementation. For readability, preserve the underlying claim and split the explanation around one concrete example.

- [ ] **Step 5: Run the Chapter 9 suite and safety scan**

Run: `python -m unittest discover -s chapter9/tests -v`

Run: `python scripts/check_repository.py --root .`

Expected: PASS; review report contains no open P0/P1 finding.

- [ ] **Step 6: Commit review and revisions**

```bash
git add book/reviews/chapter9-review-codex.md book/chapter9.md book/sources/chapter9-sources.md chapter9/README.md chapter9/reference-answers.md chapter9/tests/test_chapter_mainline.py chapter9/tests/test_publication_checks.py chapter9/tests/test_figures.py
git commit -m "docs: review and refine chapter 9"
```

---

### Task 15: Publish Chapter 9 through repository contracts and CI

**Files:**
- Modify: `README.md`
- Modify: `book/README.md`
- Modify: `book/manifest.json`
- Modify: `docs/EXPERIMENT_STATUS.md`
- Modify: `mkdocs.yml`
- Modify: `scripts/build_site.py`
- Modify: `tests/test_book_manifest.py`
- Modify: `tests/test_repository_contract.py`
- Modify: `tests/test_experiment_inventory.py`
- Modify: `tests/test_report_portability.py`
- Modify: `tests/test_workflow_contract.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: clean, reviewed Chapter 9 bundle and deterministic report hashes.
- Produces: manifest version `0.9.0`, nine published chapters, nine planned chapters, Chapter 9 MkDocs pages, CI coverage, commit, tag, and GitHub push.

- [ ] **Step 1: Change repository tests first**

Update all published ranges from `range(1, 9)` to `range(1, 10)`. Rename the manifest test to `test_manifest_exposes_nine_published_and_nine_unpublished_chapters`; assert Chapter 9 is published and Chapters 10–18 are planned. Require Chapter 9 test/report commands and `chapter9/requirements.txt` in CI.

- [ ] **Step 2: Run root tests and confirm publication wiring fails**

Run: `python -m unittest discover -s tests -v`

Expected: FAIL because the manifest, build allowlist, navigation, status ledger, and workflow still stop at Chapter 8.

- [ ] **Step 3: Update the manifest and navigation truthfully**

Set version `0.9.0`, updated date `2026-09-01`, Chapter 9 status `published`, summary, source `chapter9.md`, experiment `../chapter9/README.md`, answers `../chapter9/reference-answers.md`, and updated date. Add Chapter 9 to root/book reading tables, MkDocs prose and experiment nav, and change Chapter 8’s next link from `OUTLINE.md` to `chapter9.md` without altering its substantive content.

- [ ] **Step 4: Extend site and CI allowlists**

Change `scripts/build_site.py` chapter patterns/ranges to 1–9. In CI, cache and install `chapter9/requirements.txt`, run `python -m unittest discover -s chapter9/tests -v`, and regenerate `python -m chapter9.experiments.run_all --output chapter9/reports`. Add the three report paths to LF/portability checks.

- [ ] **Step 5: Record exact report hashes and status boundaries**

Update `docs/EXPERIMENT_STATUS.md` with the actual Chapter 9 test count, 20 deterministic cases, five groups, SDK version, the statement that in-memory MCP tests exercise protocol/SDK contracts rather than model quality, and SHA-256 for all three reports. Change the ledger check date to `2026-09-01`.

- [ ] **Step 6: Run all local release gates**

```powershell
python scripts/check_repository.py --root . --git-history
python -m unittest discover -s tests -v
python -m unittest discover -s chapter9/tests -v
python -m chapter9.experiments.run_all --output chapter9/reports
npm test --prefix book
python scripts/build_site.py --root . --output _web
python -m mkdocs build --strict
```

Expected: every command exits 0; a second report generation produces no Git diff.

- [ ] **Step 7: Commit the source release**

```bash
git add README.md book/README.md book/manifest.json book/chapter8.md docs/EXPERIMENT_STATUS.md mkdocs.yml scripts/build_site.py tests/test_book_manifest.py tests/test_repository_contract.py tests/test_experiment_inventory.py tests/test_report_portability.py tests/test_workflow_contract.py .github/workflows/ci.yml chapter9/reports
git commit -m "build: publish chapter 9"
```

- [ ] **Step 8: Tag and push only the verified commit**

Run: `git tag -a book-chapter9-v1.0 -m "Chapter 9: Tool Calling and MCP"`

Run: `git push origin main`

Run: `git push origin book-chapter9-v1.0`

Expected: both pushes succeed; GitHub CI and Pages complete for the tagged commit.

---

### Task 16: Synchronize and deploy `wlxralf.com`

**Files in sibling main-site project:**
- Modify by sync: `../ralf-blog/content/books/deep-dive-ai-agent/manifest.json`
- Create by sync: `../ralf-blog/content/books/deep-dive-ai-agent/chapter-9.md`
- Create by sync: `../ralf-blog/content/books/deep-dive-ai-agent/images/fig9-*.png`
- Modify by sync: `../ralf-blog/generated/book-sources.json`
- Modify by sync: `../ralf-blog/generated/book-search.json`
- Create/modify by sync: `../ralf-blog/public/book-assets/deep-dive-ai-agent/fig9-*.png`
- Modify test: `../ralf-blog/app/books/[book]/[chapter]/page.test.tsx`
- Modify test: `../ralf-blog/app/sitemap.test.ts`

**Interfaces:**
- Consumes: clean committed source repository at the same commit pushed in Task 15.
- Produces: Chapter 9 route, search entries, sitemap entry, synchronized assets, Cloudflare deployment, and public verification.

- [ ] **Step 1: Change main-site route tests first**

Require static params and sitemap to include `chapter-9` and no longer assert its absence. Add a rendering assertion that the Chapter 9 page contains `工具调用与 MCP` and an image URL under `/book-assets/deep-dive-ai-agent/fig9-1-tool-call-journey.png`.

- [ ] **Step 2: Run targeted tests and confirm stale snapshot failure**

From `../ralf-blog`, run:

```powershell
npx vitest run "app/books/[book]/[chapter]/page.test.tsx" app/sitemap.test.ts
```

Expected: FAIL because the local book snapshot still contains only Chapters 1–8.

- [ ] **Step 3: Synchronize from the clean source commit**

Run: `npm run book:sync`

Expected: output reports 10 readable entries (introduction plus nine chapters), Chapter 9 Markdown, eight new PNG assets, regenerated search, and the exact source commit from Task 15.

- [ ] **Step 4: Run main-site verification**

```powershell
npm run book:source-check
npm run book:check
npm test
npx tsc --noEmit
npm run lint
```

Expected: every command exits 0; the snapshot freshness check matches the source commit.

- [ ] **Step 5: Deploy through the existing Cloudflare workflow**

Run: `npm run deploy:app`

Expected: Cloudflare returns a successful deployment version and no build/test failure.

- [ ] **Step 6: Verify public pages and assets**

Open and verify:

- `https://wlxralf.com/books/deep-dive-ai-agent`
- `https://wlxralf.com/books/deep-dive-ai-agent/chapter-9`
- `https://wlxralf.com/book-assets/deep-dive-ai-agent/fig9-1-tool-call-journey.png`

The book home must show `9 / 18`; Chapter 9 must render all headings, code blocks, tables, and eight figures on desktop and mobile; Chapter 8 next navigation must reach Chapter 9.

- [ ] **Step 7: Record release evidence in the final handoff**

Report the source commit, immutable tag, GitHub CI result, GitHub Pages result, Cloudflare deployment version, canonical chapter URL, local repository path, exact test counts, and residual Non-claims. Do not describe the chapter as published until both GitHub and `wlxralf.com` checks succeed.

---

## Complete Verification Matrix

Before declaring the chapter complete, run and record all of the following from the book repository root:

```powershell
python scripts/check_repository.py --root . --git-history
python -m unittest discover -s tests -v
python -m unittest discover -s chapter1/tests -v
python -m unittest discover -s chapter3/tests -v
python -m unittest discover -s chapter4/tests -v
python -m unittest discover -s chapter5/tests -v
python -m unittest discover -s chapter6/tests -v
python -m unittest discover -s chapter7/tests -v
python -m unittest discover -s chapter8/tests -v
python -m unittest discover -s chapter9/tests -v
python chapter2/sft_mask_demo.py
python chapter2/real_sft_evidence.py
python chapter2/preference_demo.py
python chapter2/sampling_demo.py
python chapter2/reasoning_budget_demo.py
python chapter2/structured_output_demo.py
python chapter2/model_selection_demo.py
python -m chapter9.experiments.run_all --output chapter9/reports
npm test --prefix book
python scripts/build_site.py --root . --output _web
python -m mkdocs build --strict
git status --short
```

Expected final state: every command exits 0, report regeneration changes no tracked bytes, `git status --short` is empty, no secret/history finding exists, nine chapters are published, nine remain planned, and both public reading surfaces resolve Chapter 9.
