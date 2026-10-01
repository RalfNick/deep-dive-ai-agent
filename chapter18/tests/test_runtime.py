from dataclasses import replace
import pytest
from chapter18.contracts import BudgetLimits, Decision, RunState, ToolCall, ToolOutcome, WorkerResult
from chapter18.tests.helpers import packet


def make_runtime(executor=None, limits=None):
    from chapter18.budget import BudgetLedger
    from chapter18.runtime import TeamRuntime
    from chapter18.policy import ScriptedPolicy
    p = packet(limits=limits or BudgetLimits())
    runtime = TeamRuntime(RunState("manager", "public"), BudgetLedger(p.limits), executor or (lambda p, c: ToolOutcome(c.call_id, "ok")))
    runtime.start(p, ScriptedPolicy(()), attempt_id="root-1")
    return runtime, p


def child_of(p, n):
    return replace(p, task_id=f"child-{n}", parent_id=p.task_id, worker_id=f"expert-{n}", depth=1)


def test_delegation_returns_but_handoff_transfers_controller():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime()
    child = child_of(p, 1)
    result = WorkerResult(child.task_id, "attempt-1", child.worker_id, "done")
    runtime.start(child, ScriptedPolicy((Decision("result", result=result),)), attempt_id="attempt-1")
    runtime.step(child.task_id)
    assert runtime.state.controller == "manager"
    assert runtime.handoff(child.worker_id, task_id=child.task_id)
    assert runtime.state.controller == "expert-1" and runtime.state.principal == "public"


def test_workers_observe_only_their_own_tool_outcomes():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime(lambda p, c: ToolOutcome(c.call_id, "ok", (("owner", p.worker_id),)))
    for n in (1, 2):
        child = child_of(p, n)
        runtime.start(child, ScriptedPolicy((Decision("tool", call=ToolCall(f"call-{n}", "knowledge")),)), attempt_id=f"a-{n}")
        runtime.step(child.task_id)
    assert dict(runtime.observations["child-1"].outcomes[0].data)["owner"] == "expert-1"
    assert dict(runtime.observations["child-2"].outcomes[0].data)["owner"] == "expert-2"
    assert len(runtime.observations["child-1"].outcomes) == 1


def test_transient_retry_counts_globally_and_stops_after_one_extra_attempt():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime(lambda p, c: ToolOutcome(c.call_id, "transient_error"), BudgetLimits(tool_calls=8))
    child = child_of(p, 1)
    runtime.start(child, ScriptedPolicy((Decision("tool", call=ToolCall("call-1", "knowledge")),)), attempt_id="a-1")
    runtime.step(child.task_id)
    assert runtime.ledger.used == 2 and runtime.state.tool_calls == 2
    assert len(runtime.observations[child.task_id].outcomes) == 2


@pytest.mark.parametrize("change", [{"task_id":"wrong"}, {"attempt_id":"wrong"}, {"worker_id":"wrong"}])
def test_misattributed_result_is_rejected(change):
    runtime, p = make_runtime()
    result = WorkerResult(p.task_id, "root-1", p.worker_id, "done")
    assert not runtime.accept_result(replace(result, **change))
    assert runtime.state.results == ()


def test_duplicate_result_and_late_result_do_not_change_acceptance():
    runtime, p = make_runtime()
    result = WorkerResult(p.task_id, "root-1", p.worker_id, "done", decisions=999, tool_calls=999)
    assert runtime.accept_result(result)
    assert runtime.state.results[0].tool_calls == 0
    assert not runtime.accept_result(result)
    assert len(runtime.state.results) == 1
    runtime.cancel("user_cancel")
    assert not runtime.accept_result(result)
    assert runtime.state.status == "stopped"


def test_fifth_handoff_stops_without_resetting_counter():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime()
    runtime.start(child_of(p, 1), ScriptedPolicy(()), attempt_id="expert-a1")
    for target in ("expert-1", "manager", "expert-1", "manager"):
        assert runtime.handoff(target, task_id=p.task_id)
    assert not runtime.handoff("manager", task_id=p.task_id)
    assert runtime.state.handoffs == 4 and runtime.state.status == "stopped"


def test_three_children_and_four_decisions_are_hard_bounds():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime()
    for n in range(3):
        child = child_of(p, n)
        script = tuple(Decision("tool", call=ToolCall(f"c-{n}-{i}", "knowledge")) for i in range(5))
        runtime.start(child, ScriptedPolicy(script), attempt_id=f"a-{n}")
    with pytest.raises(ValueError):
        runtime.start(child_of(p, 3), ScriptedPolicy(()), attempt_id="a-3")
    for _ in range(5):
        runtime.step("child-0")
    assert len(runtime.observations["child-0"].outcomes) == 4
    assert runtime.state.reason_code == "worker_decision_limit"


def test_denied_tool_does_not_invoke_executor_or_consume_quota():
    from chapter18.policy import ScriptedPolicy
    def forbidden(p, c):
        raise AssertionError("not allowed to execute")
    runtime, p = make_runtime(forbidden)
    runtime.start(child_of(p, 1), ScriptedPolicy((Decision("tool", call=ToolCall("shell-1", "shell")),)), attempt_id="a-1")
    runtime.step("child-1")
    assert runtime.ledger.used == 0
    assert runtime.observations["child-1"].outcomes[0].status == "denied"


def test_third_delegation_level_is_rejected_without_new_task():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime()
    child = child_of(p, 1)
    runtime.start(child, ScriptedPolicy(()), attempt_id="a-1")
    grandchild = replace(child, task_id="grandchild", parent_id=child.task_id, depth=2)
    runtime.start(grandchild, ScriptedPolicy(()), attempt_id="a-2")
    with pytest.raises(ValueError):
        runtime.start(replace(grandchild, task_id="too-deep", parent_id=grandchild.task_id, depth=3), ScriptedPolicy(()), attempt_id="a-3")
    assert "too-deep" not in runtime.state.tasks


def test_restarting_attempt_cannot_reset_existing_task_quota():
    from chapter18.policy import ScriptedPolicy
    runtime, p = make_runtime()
    with pytest.raises(ValueError):
        runtime.start(p, ScriptedPolicy(()), attempt_id="root-2")
    assert runtime.state.attempts[p.task_id] == "root-1"
