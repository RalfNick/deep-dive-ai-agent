from dataclasses import replace
import pytest
from chapter18.tests.helpers import packet


def test_default_limits_define_one_shared_budget():
    from chapter18.contracts import BudgetLimits
    limits = BudgetLimits()
    assert (limits.tool_calls, limits.verifier_reserve) == (16, 2)
    assert (limits.inflight, limits.depth, limits.handoffs) == (3, 2, 4)
    assert (limits.worker_decisions, limits.extra_retries) == (4, 1)


@pytest.mark.parametrize("field,value", [("tool_calls", -1), ("verifier_reserve", 17), ("depth", -1), ("tool_calls", True)])
def test_invalid_budget_is_rejected(field, value):
    from chapter18.contracts import BudgetLimits
    with pytest.raises(ValueError):
        BudgetLimits(**{field: value})


@pytest.mark.parametrize("field,value", [
    ("allowed_sources", frozenset({"restricted-current"})), ("allowed_tools", frozenset({"shell"})),
    ("allowed_writes", frozenset({"tests/test_existing.py"})), ("principal", "staff"),
])
def test_child_cannot_expand_scope_or_change_principal(field, value):
    from chapter18.contracts import validate_packet
    parent = packet()
    child = replace(parent, task_id="child", parent_id=parent.task_id, worker_id="expert", depth=1)
    validate_packet(child, parent)
    with pytest.raises(ValueError):
        validate_packet(replace(child, **{field: value}), parent)


@pytest.mark.parametrize("path", ["../answer.py", "/answer.py", "C:/answer.py", "src/../test.py", "src\\answer.py"])
def test_invalid_write_paths_are_rejected(path):
    from chapter18.contracts import validate_packet
    with pytest.raises(ValueError):
        validate_packet(packet(allowed_writes=frozenset({path})))


def test_non_hex_digest_and_wrong_parent_depth_are_rejected():
    from chapter18.contracts import validate_packet
    with pytest.raises(ValueError):
        validate_packet(packet(base_hashes=(("src/linkcheck.py", "z" * 64),)))
    parent = packet()
    with pytest.raises(ValueError):
        validate_packet(replace(parent, task_id="child", parent_id=parent.task_id, depth=2), parent)
