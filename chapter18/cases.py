from dataclasses import replace
from pathlib import Path
from .contracts import BudgetLimits, CaseResult, Decision, ToolCall, WorkerResult
from .fixtures import load_case_specs
from .policy import ScriptedPolicy
from .system import Session, new_packet


def run_case(case_id: str, *, root: Path, workdir: Path, order: tuple[str, ...] = ()) -> CaseResult:
    spec = next((r for r in load_case_specs(root) if r["case_id"] == case_id), None)
    if spec is None:
        raise ValueError("unknown case")
    p = new_packet()
    extra = {}
    if case_id in {"parallel-separated", "one-worker-timeout"}:
        keys = ("sharing", "edition", "support_hours") if case_id == "parallel-separated" else ("sharing", "support_hours")
        p = replace(p, input_refs=keys, output_requirements=keys)
    elif case_id == "serial-dependency":
        p = replace(p, input_refs=("edition", "sharing"), output_requirements=("edition", "sharing"))
    elif case_id == "source-version-conflict":
        p = replace(p, input_refs=("retention",), output_requirements=("retention",))
    elif case_id == "same-source-three-votes":
        p = replace(p, input_refs=("sharing", "retention"), output_requirements=("sharing", "retention"))
    elif case_id == "kb-permission-denied":
        p = replace(p, allowed_sources=frozenset({"restricted-current"}), input_refs=("internal_quota",), output_requirements=("internal_quota",))
    elif case_id in {"repair-verified", "repair-needs-approval", "stale-patch", "disjoint-patches", "cancel-late-result"}:
        p = replace(p, goal="修复嵌套相对链接并保护旧行为", input_refs=("repair_correct",), output_requirements=("repair_correct",))
    elif case_id == "global-budget-exhausted":
        p = replace(p, limits=BudgetLimits(tool_calls=8))
    session = Session(root, workdir, p, timeout_worker="support" if case_id == "one-worker-timeout" else None)
    r = session.runtime
    if case_id in {"single-sufficient", "kb-verified-answer", "delegation-return", "handoff-transfer", "context-not-forwarded", "kb-permission-denied"}:
        source, key = ("restricted-current", "internal_quota") if case_id == "kb-permission-denied" else ("public-current", "sharing")
        if case_id == "single-sufficient":
            from .system import ObservedScriptedPolicy
            r._policies[p.task_id] = ObservedScriptedPolicy((ToolCall("single-read", "knowledge", (("source_id", source), ("key", key))),), "root-a1")
            session.run_workers((p.task_id,))
        else:
            worker = session.research("expert", source, key, missing_context=case_id == "context-not-forwarded")
            session.run_workers((worker,))
            if case_id == "handoff-transfer":
                r.handoff("expert", task_id=worker)
    elif case_id in {"parallel-separated", "one-worker-timeout"}:
        workers = [session.research("product", "parallel-product", "sharing")]
        if case_id == "parallel-separated":
            workers.append(session.research("edition", "parallel-product", "edition"))
        workers.append(session.research("support", "parallel-support", "support_hours"))
        completion = order or tuple(workers)
        if set(completion) != set(workers) or len(completion) != len(workers):
            raise ValueError("completion order must name each worker once")
        session.run_workers(completion)
        durations = (7, 11, 5)
        extra["logical_schedule"] = {"durations": list(durations), "delegation_units": 2, "integration_units": 3,
                                      "serial_units": sum(durations), "parallel_units": max(durations) + 2 + 3, "unit": "logical_not_seconds"}
    elif case_id == "serial-dependency":
        first = session.research("edition", "parallel-product", "edition")
        session.run_workers((first,))
        if any(c.key == "edition" and c.value == "团队版" for result in r.state.results for c in result.claims):
            r.record("dependency_ready", p.task_id, result_task=first)
            second = session.research("product", "parallel-product", "sharing")
            session.run_workers((second,))
        extra["dependency"] = {"before": "edition", "after": "product", "serial_units": 7 + 11}
    elif case_id in {"duplicate-research", "same-source-three-votes"}:
        count = 2 if case_id == "duplicate-research" else 3
        workers = [session.research(f"research-{n}", "public-current", "sharing") for n in range(count)]
        session.run_workers(workers)
    elif case_id == "source-version-conflict":
        workers = [session.research("policy-a", "conflict-a", "retention"), session.research("policy-b", "conflict-b", "retention")]
        session.run_workers(workers)
    elif case_id == "scope-escalation":
        child = replace(p, task_id="expert", parent_id=p.task_id, worker_id="expert", depth=1, allowed_sources=p.allowed_sources | {"restricted-current"})
        r._policies[p.task_id] = ScriptedPolicy((Decision("delegate", packet=child),))
        r.step(p.task_id)
    elif case_id == "global-budget-exhausted":
        workers = []
        for n in range(3):
            child = replace(p, task_id=f"research-{n}", parent_id=p.task_id, worker_id=f"research-{n}", depth=1)
            calls = tuple(Decision("tool", call=ToolCall(f"call-{n}-{i}", "knowledge", (("source_id", "public-current"), ("key", "sharing")))) for i in range(4))
            r.start(child, ScriptedPolicy(calls), attempt_id=f"a-{n}")
            workers.append(child.task_id)
        for _ in range(3):
            for worker in workers:
                r.step(worker)
    elif case_id == "handoff-cycle":
        r._policies[p.task_id] = ScriptedPolicy(tuple(Decision("handoff", next_controller="expert") for _ in range(3)))
        child = replace(p, task_id="expert", parent_id=p.task_id, worker_id="expert", depth=1)
        r.start(child, ScriptedPolicy(tuple(Decision("handoff", next_controller="manager") for _ in range(2))), attempt_id="expert-a1")
        for task in (p.task_id, child.task_id, p.task_id, child.task_id, p.task_id):
            r.step(task)
    else:
        session.prepare_code()
        workers = [session.coder("coder-a", "src/linkcheck.py")]
        if case_id in {"stale-patch", "disjoint-patches"}:
            workers.append(session.coder("coder-b", "src/policy.py" if case_id == "disjoint-patches" else "src/linkcheck.py", late=case_id == "stale-patch"))
        session.run_workers(workers)
        gateway = session.gateway()
        for proposal in session.proposals.values():
            gateway.apply(proposal, approved=case_id != "repair-needs-approval")
        if case_id == "cancel-late-result":
            r.cancel("cancelled_after_commit")
            result = r.state.results[0]
            r.accept_result(result)
        elif case_id != "repair-needs-approval":
            gateway.finish()
        if case_id == "stale-patch":
            proposals = list(session.proposals.values())
            naive = {"source": proposals[0].replacement}
            naive["source"] = proposals[1].replacement
            extra["in_memory_control"] = {"late_proposal_would_replace_first": naive["source"] == proposals[1].replacement,
                                          "real_gateway_refuses_stale_baseline": True}
    return session.result(case_id, spec["group"], **extra)


def run_group(group: int, *, root: Path, workdir: Path) -> tuple[CaseResult, ...]:
    if group not in range(1, 6):
        raise ValueError("group must be 1..5")
    return tuple(run_case(row["case_id"], root=root, workdir=workdir / row["case_id"])
                 for row in load_case_specs(root) if row["group"] == group)
