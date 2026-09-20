"""LangGraph owns node routing and durable interruption for the same lab."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import threading
from typing import TypedDict

from ..contracts import Record, TERMINAL
from ..providers.replay import ReplayModel
from ..recovery import resolve_approval
from ..services import Services
from ..state import Store


class GraphState(TypedDict):
    run: Record
    decision: Record | None
    result: Record | None
    approval_decision: bool | None


def _require_framework() -> None:
    if importlib.util.find_spec("langgraph") is None:
        raise RuntimeError("langgraph_unavailable")


def _compile(services: Services, checkpointer):
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import interrupt

    graph = StateGraph(GraphState)

    def decide_node(value: GraphState) -> Record:
        run = value["run"]
        try:
            decision = services.decide(run)
        except (RuntimeError, TimeoutError, ValueError) as error:
            return {"run": services.fail(run, str(error) or type(error).__name__),
                    "decision": None, "result": None, "approval_decision": None}
        if decision["kind"] == "plan":
            run["plan"] = decision["text"]
            run["messages"].append({"role": "assistant", "content": decision["text"]})
            services.store.save_with_event(run, "plan_updated", {"plan": decision["text"]})
        return {"run": run, "decision": decision, "result": None,
                "approval_decision": None}

    def propose_node(value: GraphState) -> Record:
        run = services.propose(value["run"], value["decision"]["call"])
        return {"run": run, "decision": value["decision"], "result": None,
                "approval_decision": None}

    def approval_node(value: GraphState) -> Record:
        pending = value["run"]["pending"]
        request = {key: pending[key] for key in
                   ("action_id", "arguments_hash", "workspace_hash", "path")}
        decision = bool(interrupt(request))
        run = resolve_approval(value["run"], services.store, decision)
        return {"run": run, "decision": value["decision"], "result": None,
                "approval_decision": decision}

    def execute_node(value: GraphState) -> Record:
        return {"run": value["run"], "decision": value["decision"],
                "result": services.execute(value["run"]),
                "approval_decision": value.get("approval_decision")}

    def observe_node(value: GraphState) -> Record:
        run = services.observe(value["run"], value["result"])
        return {"run": run, "decision": None, "result": None,
                "approval_decision": None}

    def verify_node(value: GraphState) -> Record:
        run = value["run"]
        run["messages"].append({"role": "assistant",
                                "content": value["decision"]["text"]})
        run = services.finish(run)
        return {"run": run, "decision": None, "result": None,
                "approval_decision": None}

    def after_decide(value: GraphState) -> str:
        if value["run"]["status"] in TERMINAL:
            return "end"
        kind = value["decision"]["kind"]
        return {"tool": "propose", "final": "verify", "plan": "decide"}[kind]

    def after_propose(value: GraphState) -> str:
        run = value["run"]
        if run["status"] == "awaiting_approval":
            return "approval"
        if run["status"] in TERMINAL:
            return "end"
        return "execute" if run["pending"] is not None else "decide"

    def after_approval(value: GraphState) -> str:
        run = value["run"]
        if run["status"] in TERMINAL:
            return "end"
        return "execute" if run["pending"] is not None else "decide"

    def after_verify(value: GraphState) -> str:
        return "end" if value["run"]["status"] in TERMINAL else "decide"

    for name, node in (("decide", decide_node), ("propose", propose_node),
                       ("approval", approval_node), ("execute", execute_node),
                       ("observe", observe_node), ("verify", verify_node)):
        graph.add_node(name, node)
    graph.add_edge(START, "decide")
    graph.add_conditional_edges("decide", after_decide,
        {"propose": "propose", "verify": "verify", "decide": "decide", "end": END})
    graph.add_conditional_edges("propose", after_propose,
        {"approval": "approval", "execute": "execute", "decide": "decide", "end": END})
    graph.add_conditional_edges("approval", after_approval,
        {"execute": "execute", "decide": "decide", "end": END})
    graph.add_edge("execute", "observe")
    graph.add_edge("observe", "decide")
    graph.add_conditional_edges("verify", after_verify, {"decide": "decide", "end": END})
    return graph.compile(checkpointer=checkpointer)


def run_graph(state: Record, services: Services, checkpoint: Path,
              approval: bool | None = None) -> Record:
    _require_framework()
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.types import Command

    checkpoint = Path(checkpoint).absolute()
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": state["run_id"]},
              "recursion_limit": 80}
    with SqliteSaver.from_conn_string(str(checkpoint)) as saver:
        graph = _compile(services, saver)
        if approval is None:
            snapshot = graph.get_state(config)
            if snapshot.values:
                output = graph.invoke(None, config=config)
            else:
                output = graph.invoke({"run": state, "decision": None,
                                       "result": None, "approval_decision": None},
                                      config=config)
        else:
            output = graph.invoke(Command(resume=approval), config=config)
    return output["run"]


def _stage(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--approval", choices=("true", "false"))
    args = parser.parse_args(argv)
    store = Store(args.state)
    state = store.load(args.run_id)
    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
    model = ReplayModel(decisions, state.get("provider_state") or None)
    services = Services(args.workspace, store, model, state["backend"], threading.Event())
    approval = None if args.approval is None else args.approval == "true"
    result = run_graph(state, services, args.checkpoint, approval)
    print(json.dumps({"pid": os.getpid(), "status": result["status"],
                      "reason": result["reason"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_stage())
