"""Fixed tool-result tape, not re-execution of external side effects."""
from .contracts import AttributionResult, ReplayCase, ReplayResult, RunResult
from .serialization import digest

def replay(case: ReplayCase, *, selection="baseline", procedure="baseline") -> ReplayResult:
    if selection not in ("baseline", "scoped_current") or procedure not in ("baseline", "complete"):
        raise ValueError("unsupported intervention")
    missing = tuple(sorted(set(case.missing) | ({"tool_receipt"} if not case.tool_tape else set())))
    status = "unknown" if missing else ("environment_error" if "timeout" in case.tool_tape else "replayed")
    request = case.input
    docs = [d for d in case.documents if d.tenant_id == request.tenant_id and d.domain == request.domain]
    if request.requested_version == "historical" or selection == "scoped_current":
        docs = [d for d in docs if d.version == request.requested_version]
    doc = docs[0] if docs else None
    steps = () if request.operation != "export" or not doc else doc.steps
    if procedure == "baseline" and request.operation == "export" and request.requested_version == "current":
        steps = tuple(s for s in steps if s not in ("choose_destination", "verify_receipt"))
    outcome = RunResult(doc.document_id if doc else None, steps, "normal", None, (), (),
                        "timeout" if status == "environment_error" else None,
                        missing if status == "unknown" else (), len(steps) + 1, len(case.tool_tape))
    return ReplayResult(status, outcome, missing, ("replay-" + case.case_id,))

def attribute(case: ReplayCase) -> AttributionResult:
    baseline = replay(case)
    variants = (("baseline", "baseline"), ("scoped_current", "baseline"), ("baseline", "complete"))
    frozen = digest({"input":case.input, "documents":case.documents, "tape":case.tool_tape,
                     "permissions":case.permissions, "clock":case.frozen_clock, "agent":case.agent_version})
    interventions = tuple({"selection":s, "procedure":p, "frozen_hash":frozen,
                           "result":replay(case, selection=s, procedure=p).to_dict()} for s,p in variants)
    if baseline.status != "replayed":
        cause = "environment" if baseline.status == "environment_error" else "unknown"
    elif replay(case, selection="scoped_current").outcome.document_id != baseline.outcome.document_id:
        cause = "knowledge_selection"
    elif replay(case, procedure="complete").outcome.steps != baseline.outcome.steps:
        cause = "procedure_incomplete"
    else:
        cause = "unknown"
    return AttributionResult(cause, interventions, baseline.missing if cause == "unknown" else ())
