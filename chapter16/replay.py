"""Fixed tool-result tape, not re-execution of external side effects."""
from .contracts import AttributionResult, ReplayCase, ReplayResult, RunResult, utc
from .serialization import digest

def replay(case: ReplayCase, *, selection="baseline", procedure="baseline") -> ReplayResult:
    if selection not in ("baseline", "scoped_current") or procedure not in ("baseline", "complete"):
        raise ValueError("unsupported intervention")
    required = set(case.missing) | ({"tool_receipt"} if not case.tool_tape else set())
    if f"tenant-{case.input.tenant_id}" not in case.permissions:
        required.add("document_permission")
    if case.agent_version != "deterministic-agent-v1":
        required.add("unsupported_agent_version")
    request = case.input
    docs = [d for d in case.documents if d.tenant_id == request.tenant_id and d.domain == request.domain
            and f"tenant-{request.tenant_id}" in case.permissions
            and utc(d.valid_from) <= utc(case.frozen_clock) < utc(d.valid_until)]
    if request.requested_version == "historical" or selection == "scoped_current":
        docs = [d for d in docs if d.version == request.requested_version]
    doc = docs[0] if docs else None
    if doc is None:
        required.add("no_authorized_document")
    missing = tuple(sorted(required))
    status = "unknown" if missing else ("environment_error" if "timeout" in case.tool_tape else "replayed")
    steps = () if request.operation != "export" or not doc else doc.steps
    if procedure == "baseline" and request.operation == "export" and request.requested_version == "current":
        steps = tuple(s for s in steps if s not in ("choose_destination", "verify_receipt"))
    outcome = RunResult(doc.document_id if doc else None, steps, "normal", None, (), (),
                        "timeout" if status == "environment_error" else None,
                        missing if status == "unknown" else (), len(steps) + 1, len(case.tool_tape))
    return ReplayResult(status, outcome, missing, ("replay-" + case.case_id,))

def attribute(case: ReplayCase) -> AttributionResult:
    variants = (("baseline", "baseline"), ("scoped_current", "baseline"), ("baseline", "complete"))
    results = tuple(replay(case, selection=s, procedure=p) for s,p in variants)
    baseline, selected, complete = results
    frozen = digest({"input":case.input, "documents":case.documents, "tape":case.tool_tape,
                     "permissions":case.permissions, "clock":case.frozen_clock, "agent":case.agent_version})
    interventions = tuple({"selection":s, "procedure":p, "frozen_hash":frozen,
                           "result":result.to_dict()} for (s,p),result in zip(variants,results))
    unknown = ()
    if baseline.status != "replayed":
        cause = "environment" if baseline.status == "environment_error" else "unknown"
        unknown = baseline.missing if cause == "unknown" else ()
    elif selected.status != "replayed":
        cause, unknown = "unknown", selected.missing or ("unverified_selection_intervention",)
    elif selected.outcome.document_id != baseline.outcome.document_id:
        cause = "knowledge_selection"
    elif complete.status != "replayed":
        cause, unknown = "unknown", complete.missing or ("unverified_procedure_intervention",)
    elif complete.outcome.steps != baseline.outcome.steps:
        cause = "procedure_incomplete"
    else:
        cause, unknown = "unknown", ("no_discriminating_intervention",)
    return AttributionResult(cause, interventions, unknown)


def verifies_discovery_condition(case, carrier, condition):
    """Positive, finite source condition; never read holdout truth or a task ID.

    A changed result is only a mechanism hypothesis. Knowledge repair must
    select the source-required document; procedure repair must reproduce the
    source-required ordered steps, under the same frozen replay conditions.
    """
    if carrier == "knowledge_rule":
        result = replay(case, selection="scoped_current")
        return (condition.get("selection") == "scoped_current"
                and isinstance(condition.get("document_id"), str)
                and result.status == "replayed"
                and result.outcome.document_id == condition["document_id"])
    if carrier == "step_skill":
        steps = condition.get("steps")
        result = replay(case, procedure="complete")
        return (isinstance(steps, (tuple, list)) and bool(steps)
                and result.status == "replayed" and result.outcome.steps == tuple(steps))
    return False
