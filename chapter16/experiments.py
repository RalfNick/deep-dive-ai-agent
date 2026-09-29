"""Five deterministic evidence experiments; no provider/environment discovery."""
import argparse
from collections import Counter
from dataclasses import replace
from pathlib import Path
from .agent import run_agent
from .artifacts import build_candidate, empty_snapshot
from .contracts import CLOCK, END, STEPS, ImprovementReport, ReleaseRecord, ReleaseState, UsePolicy
from .evaluation import decide_gate, evaluate_pair, grade, make_context, seal_evidence
from .feedback import admit_feedback
from .fixtures import load_fixtures
from .governance import activate, assign_cohort, make_approval, rollback
from .lessons import export_training_candidates, propose_lessons
from .replay import attribute, replay
from .serialization import body_hash, digest

def prepare(lab):
    admissions = admit_feedback(lab.feedback,lab.sources)
    blocked = frozenset(t.family_id for t in lab.tasks if t.split == "holdout")
    proposals = propose_lessons(admissions,lab.replays,blocked_families=blocked)
    baseline, candidate = empty_snapshot(), build_candidate(proposals,now=CLOCK)
    policy = UsePolicy(frozenset(),frozenset(),STEPS+("open_settings","export_csv"))
    context = make_context(lab,policy)
    evidence = evaluate_pair(lab.tasks,lab.documents,lab.truth,baseline,candidate,context)
    return admissions,proposals,baseline,candidate,policy,context,evidence

def blind_rows(lab,candidate,policy,evidence):
    gold = {g.success_ref:g for g in lab.truth}
    rows = []
    for task, old in zip(lab.tasks,evidence.paired_trials):
        current_policy = replace(policy,revoked_source_ids=policy.revoked_source_ids|frozenset(task.revoked_source_ids))
        result = run_agent(task.agent_input,lab.documents,candidate,policy=current_policy,now=task.frozen_clock,variant="blind_control")
        rows.append({**old,"candidate":result.to_dict(),"candidate_grade":grade(task,result,gold[task.success_ref]).to_dict()})
    return tuple(rows)

def run_group(group,lab):
    if type(group) is not int or group not in range(1,6):
        raise ValueError("group must be 1..5")
    admissions,proposals,baseline,candidate,policy,context,evidence = prepare(lab)
    titles = ("反馈先准入", "固定回放与条件性归因", "真实消费与过度泛化", "独立验收与三态门禁", "审批、离线灰度与回滚")
    result = {"group":group,"title":titles[group-1]}
    if group == 1:
        result.update(counts=dict(Counter(a.disposition for a in admissions)),admissions=[a.to_dict() for a in admissions])
    elif group == 2:
        counts = Counter(replay(c).status for c in lab.replays)
        result.update(coverage={"total":4,**{s:counts[s] for s in ("replayed","environment_error","unknown")}},
                      cases=[{"case_id":c.case_id,"replay":replay(c).to_dict(),"attribution":attribute(c).to_dict()} for c in lab.replays],
                      proposals=[p.to_dict() for p in proposals],training_candidates=list(export_training_candidates(proposals,blocked_families=frozenset())))
    elif group == 3:
        blind = blind_rows(lab,candidate,policy,evidence)
        result.update(snapshot=candidate.to_dict(),paired_trials=[dict(r) for r in evidence.paired_trials],
                      blind_control=[dict(r) for r in blind],blind_failures=[r["task_id"] for r in blind if r["candidate_grade"]["status"] != "pass"],
                      success_counts={"baseline":sum(r["baseline_grade"]["status"]=="pass" for r in evidence.paired_trials),
                                      "scoped_candidate":sum(r["candidate_grade"]["status"]=="pass" for r in evidence.paired_trials),
                                      "blind_control":sum(r["candidate_grade"]["status"]=="pass" for r in blind)})
    elif group == 4:
        blind = blind_rows(lab,candidate,policy,evidence)
        unsafe = seal_evidence(replace(evidence,paired_trials=blind,
                              violation_count=sum(bool(r["candidate"]["violations"]) for r in blind)))
        task = replace(lab.tasks[4],agent_input=replace(lab.tasks[4].agent_input,tool_receipts=("missing_receipt",)))
        injected_lab = replace(lab,tasks=(*lab.tasks[:4],task,*lab.tasks[5:]))
        injected = evaluate_pair(injected_lab.tasks,lab.documents,lab.truth,baseline,candidate,make_context(injected_lab,policy))
        result.update(gates={"scoped":decide_gate(evidence).status,"blind_control":decide_gate(unsafe).status,
                            "missing_receipt":decide_gate(injected).status}, evidence=evidence.to_dict(),
                      injection={"task_id":task.task_id,"variant":"missing_receipt","context_hash":digest(injected.context),
                                 "unknown_count":injected.unknown_count,"reason_codes":list(decide_gate(injected).reason_codes)},
                      unsafe_reason_codes=list(decide_gate(unsafe).reason_codes))
    else:
        approval = make_approval(candidate,evidence,approver_id="reviewer-local",allowed_scopes=tuple(a.scope for a in candidate.artifacts),now=CLOCK,valid_until=END)
        state = activate(ReleaseState(baseline,(),frozenset()),candidate,evidence,approval,context,now=CLOCK)
        cohort = assign_cohort(tuple(t.task_id for t in lab.tasks))
        gold = {g.success_ref:g for g in lab.truth}
        canary_rows=[]
        for task in lab.tasks:
            selected = candidate if cohort[task.task_id] == "candidate" else baseline
            task_policy = replace(policy,revoked_source_ids=policy.revoked_source_ids|frozenset(task.revoked_source_ids))
            run = run_agent(task.agent_input,lab.documents,selected,policy=task_policy,now=task.frozen_clock)
            canary_rows.append({"task_id":task.task_id,"cohort":cohort[task.task_id],"grade":grade(task,run,gold[task.success_ref]).to_dict()})
        probe = next(t for t in lab.tasks if t.task_id == "S1")
        expired_clock = "2026-10-28T00:00:00Z"
        fault = run_agent(probe.agent_input,lab.documents,candidate,policy=policy,now=expired_clock)
        stop = ReleaseRecord("pending","stop",candidate,candidate,approval.approval_id,evidence.evidence_hash,cohort,"expired_memory_probe",expired_clock)
        stop = replace(stop,record_id=body_hash(stop,"record_id"))
        state = replace(state,history=state.history+(stop,))
        back = rollback(state,baseline,reason="canary_expired_memory",now=expired_clock)
        result.update(approval=approval.to_dict(),cohort=cohort,cohort_counts=dict(Counter(cohort.values())),
                      canary_trials=canary_rows,changed_condition={"clock":expired_clock,"probe":"S1","result":fault.to_dict(),
                      "grade":grade(probe,fault,gold[probe.success_ref]).to_dict()},stopped=True,
                      history=[r.to_dict() for r in back.history],active_revision=back.active.revision_id)
    return result

def run_all(lab):
    groups = tuple(run_group(g,lab) for g in range(1,6))
    rows = groups[3]["evidence"]["paired_trials"]
    report = ImprovementReport("chapter16.improvement.v1",groups,
             {"tasks":len(rows),"development":sum(r["split"]=="development" for r in rows),
              "holdout":sum(r["split"]=="holdout" for r in rows),
              "baseline_pass":sum(r["baseline_grade"]["status"]=="pass" for r in rows),
              "candidate_pass":sum(r["candidate_grade"]["status"]=="pass" for r in rows),
              "targets_repaired":sum(r["target"] and r["baseline_grade"]["status"]=="fail" and r["candidate_grade"]["status"]=="pass" for r in rows),
              "gate":groups[3]["gates"]["scoped"]},
             {"fixture_hash":digest(lab),"seed":1601,"clock":CLOCK,"policy":"authored deterministic finite rules"},
             ("Offline mechanism conformance, not model ability or autonomous training.",
              "Author-known holdout; no blind generalization or causal production A/B claim.",
              "In-process approval registry is a trusted rehearsal, not signatures/IAM.",
              "Rollback changes future pointer, never reverses external side effects.",
              "Path guards assume no concurrent malicious filesystem mutation."),"pending")
    report = replace(report,report_hash=body_hash(report,"report_hash"))
    validate_report(report)
    return report

def validate_report(report):
    if (report.schema_version != "chapter16.improvement.v1" or len(report.groups) != 5
        or [g["group"] for g in report.groups] != list(range(1,6))
        or report.report_hash != body_hash(report,"report_hash") or not report.source_proof or not report.limits):
        raise ValueError("invalid improvement report contract/hash")
    from .output import safe_data
    safe_data(report)
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group",choices=["all","1","2","3","4","5"],default="all")
    parser.add_argument("--output",required=True)
    args = parser.parse_args(argv)
    from .output import write_new_json,write_report_bundle
    root = Path(__file__).parents[1]
    try:
        lab = load_fixtures()
        if args.group == "all":
            from .exercise_solutions import payload
            paths = write_report_bundle(run_all(lab),Path(args.output),root=root,exercises=payload())
        else:
            paths = (write_new_json(run_group(int(args.group),lab),Path(args.output),root=root),)
        print("created",len(paths),"stable local artifacts")
        return 0
    except (OSError,ValueError) as exc:
        print("output refused:",str(exc))
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
