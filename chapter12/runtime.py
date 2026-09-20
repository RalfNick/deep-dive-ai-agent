"""A deliberately explicit Agent loop: decide, propose, execute, observe, verify."""
from __future__ import annotations

from .contracts import Record
from .services import Services


def run(state: Record, services: Services) -> Record:
    services.store.save(state)
    transient_failures = 0
    while not services.stopped(state):
        if state["status"] == "verifying":
            state = services.finish(state)
            continue
        try:
            decision = services.decide(state)
            transient_failures = 0
        except TimeoutError as error:
            transient_failures += 1
            if transient_failures <= 2 and not services.stopped(state):
                services.store.save_with_event(state, "model_retry", {
                    "attempt": transient_failures, "error": str(error)})
                continue
            return services.fail(state, str(error) or type(error).__name__)
        except (RuntimeError, ValueError) as error:
            return services.fail(state, str(error) or type(error).__name__)
        if decision["kind"] == "final":
            state["messages"].append({"role": "assistant", "content": decision["text"]})
            state = services.finish(state)
        elif decision["kind"] == "plan":
            state["plan"] = decision["text"]
            state["messages"].append({"role": "assistant", "content": decision["text"]})
            services.store.save_with_event(state, "plan_updated", {"plan": decision["text"]})
        else:
            state = services.propose(state, decision["call"])
            if state["status"] == "awaiting_approval":
                return state
            if state["pending"] is not None and not services.stopped(state):
                state = services.observe(state, services.execute(state))
    return state
