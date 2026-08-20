"""Audit call/result linkage and replay the state-changing trace events."""

from __future__ import annotations

from agent_loop import AgentLoop, PriceRepo, RepairPolicy, ToolCall
from trace_audit import audit_trace


def main() -> None:
    with PriceRepo() as repo:
        first = AgentLoop(
            repo, completion_verifier=repo.verify_completion
        ).run(RepairPolicy())
        audit = audit_trace(first)
        calls = [event for event in first.events if event.kind == "tool_call"]
        results = [event for event in first.events if event.kind == "tool_result"]
        calls_by_id = {event.data["call_id"]: event for event in calls}
        changing_calls = [
            calls_by_id[event.data["call_id"]]
            for event in results
            if event.data["state_changed"]
        ]
        final_digest = repo.state_digest()

    with PriceRepo() as replay_repo:
        initial_digest = replay_repo.state_digest()
        for event in changing_calls:
            replay_repo.execute(
                ToolCall(
                    event.data["call_id"],
                    event.data["name"],
                    event.data["arguments"],
                )
            )
        replay_digest = replay_repo.state_digest()

    print(f"calls={len(calls)} results={len(results)}")
    print(f"duplicate_call_ids={list(audit.duplicate_call_ids)}")
    print(f"duplicate_result_ids={list(audit.duplicate_result_ids)}")
    print(f"missing_result_ids={list(audit.missing_result_ids)}")
    print(f"orphan_result_ids={list(audit.orphan_result_ids)}")
    print(f"result_before_call_ids={list(audit.result_before_call_ids)}")
    print(f"completion_contract_ok={audit.completion_contract_ok}")
    print(f"audit_ok={audit.ok}")
    print(f"state_changing_events={len(changing_calls)}")
    print(f"initial_digest={initial_digest}")
    print(f"final_digest={final_digest}")
    print(f"replay_digest={replay_digest}")
    print(f"replay_matches={replay_digest == final_digest}")
    assert audit.ok
    assert replay_digest == final_digest


if __name__ == "__main__":
    main()
