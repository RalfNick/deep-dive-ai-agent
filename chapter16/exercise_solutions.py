"""Recompute code questions; qualitative answers are answered, not test-passed."""
import argparse
from dataclasses import replace
from pathlib import Path
from .agent import run_agent
from .artifacts import build_candidate,empty_snapshot,make_snapshot
from .contracts import CLOCK,END,STEPS,ReleaseState,UsePolicy
from .evaluation import evaluate_pair,make_context,decide_gate,seal_evidence
from .feedback import admit_feedback
from .fixtures import load_fixtures
from .governance import make_approval,activate,assign_cohort,rollback
from .lessons import propose_lessons
from .replay import replay,attribute,verifies_discovery_condition

CRITERIA = (
 "指出四种改变对象、持久位置及消费者，不把一次正确回复说成持久学习。",
 "以可信来源注册表而不是payload自报身份决定准入；accepted不等于可激活。",
 "八报告仍保留，三同源计一个，加五独立根，共六份独立证据。",
 "覆盖7/10、子集修复5/7、未知3/10同时说明；不能只报子集成绩。",
 "单因素干预与冻结指纹；变化不等于修复，须满足发现来源的正向条件；环境恢复不归功于反思。",
 "按原因选择消费者：知识、步骤、格式实际生效；其他载体仅提案。",
 "历史/租户/用户反例及移除资产回归；Skill不能扩大允许步骤。",
 "半开TTL、当前撤销优先；回滚只换指针，不能恢复旧许可。",
 "材料绑定与新鲜性分开；未使用的旧备用证据也不能跳过停用后的实际验收；说明进程内限制。",
 "安全fail优先，缺证据inconclusive；来源实际内容须支持资产，pass仍需批准。",
 "稳定4/12；停用版本不能经rollback恢复，须重新验收批准；回滚不逆转外部副作用。",
 "敏感血缘不能洗白，隐藏真值与发现用途隔离，family交叉阻断。",
 "媒体授权引用/时序/工具回执与Unknown；提案模型不能授权或读取gold，独立验收后批准。",
)

def inputs():
    lab = load_fixtures()
    rows = admit_feedback(lab.feedback,lab.sources)
    blocked = frozenset(t.family_id for t in lab.tasks if t.split=="holdout")
    proposals = propose_lessons(rows,lab.replays,blocked_families=blocked)
    baseline,candidate = empty_snapshot(),build_candidate(proposals,now=CLOCK)
    policy = UsePolicy(frozenset(),frozenset(),STEPS+("open_settings","export_csv"))
    context = make_context(lab,policy)
    evidence = evaluate_pair(lab.tasks,lab.documents,lab.truth,baseline,candidate,context)
    return lab,rows,baseline,candidate,policy,context,evidence

def solve(number):
    if type(number) is not int or number not in range(1,14):
        raise ValueError("exercise must be 1..13")
    lab,rows,baseline,candidate,policy,context,evidence = inputs()
    status,details = "passed",{}
    tasks = {t.task_id:t for t in lab.tasks}
    def run(name,snapshot,*,now=None,current_policy=policy,variant="scoped"):
        t = tasks[name]
        return run_agent(t.agent_input,lab.documents,snapshot,policy=current_policy,now=now or t.frozen_clock,variant=variant)
    if number == 1:
        status,details = "answered",{"objects":["current_context","scoped_memory","versioned_system_asset","model_weights"]}
    elif number == 2:
        from collections import Counter
        details = dict(Counter(r.disposition for r in rows))
        assert details == {"accepted":6,"quarantined":3,"merged":1,"unknown":2}
    elif number == 3:
        roots = ("same","same","same","one","two","three","four","five")
        details = {"reports":len(roots),"independent_origins":len(set(roots))}
        assert details["independent_origins"] == 6
    elif number == 4:
        details = {"coverage":7/10,"verified_subset_repair":5/7,"unknown_share":3/10}
    elif number == 5:
        details = {c.case_id:{"status":replay(c).status,"cause":attribute(c).cause} for c in lab.replays}
        carriers = {"F01":"knowledge_rule", "F03":"step_skill"}
        sources = {r.feedback_id:r for r in rows}
        for case in lab.replays:
            if case.case_id in carriers:
                details[case.case_id]["verified_discovery"] = verifies_discovery_condition(
                    case, carriers[case.case_id], sources[case.case_id].sanitized_payload)
                assert details[case.case_id]["verified_discovery"] is True
        assert details["F10"]["status"]=="unknown" and details["F01"]["cause"]=="knowledge_selection"
    elif number == 6:
        status,details = "answered",{"runtime_kinds":sorted(a.kind for a in candidate.artifacts),"proposals_only":["prompt","harness","training_candidate"]}
    elif number == 7:
        stripped = make_snapshot(tuple(a for a in candidate.artifacts if a.kind!="knowledge_rule"))
        details = {"scoped_history":run("K3",candidate).document_id,"blind_history":run("K3",candidate,variant="blind_control").document_id,
                   "without_rule":run("K1",stripped).document_id,"preference_survives":run("S1",stripped).answer_style,
                   "denied_step":run("P1",candidate,current_policy=replace(policy,allowed_steps=("export",))).refusal_reason}
        assert details == {"scoped_history":"A-old","blind_history":"A-current","without_rule":"A-old","preference_survives":"concise","denied_step":"step_denied"}
    elif number == 8:
        details = {"A":run("S1",candidate).answer_style,"other_user":run("S2",candidate).answer_style,
                   "B":run("S3",candidate).answer_style,"expired":run("S4",candidate).answer_style,
                   "revoked":run("S1",candidate,current_policy=replace(policy,revoked_source_ids=frozenset({"F08"}))).answer_style}
        assert details == {"A":"concise","other_user":"normal","B":"normal","expired":"normal","revoked":"normal"}
    elif number in (9,11):
        approval = make_approval(candidate,evidence,approver_id="reviewer-local",allowed_scopes=tuple(a.scope for a in candidate.artifacts),now=CLOCK,valid_until=END)
        state = ReleaseState(baseline,(),frozenset())
        if number == 9:
            altered = seal_evidence(replace(evidence,unrelated_unknown_count=0))
            try:
                activate(state,candidate,altered,approval,context,now=CLOCK)
            except ValueError:
                details = {"rehashed_evidence_rejected":True}
            else:
                raise AssertionError("old approval accepted changed evidence")
            saved_context = make_context(lab,policy,valid_until="2026-09-28T12:00:00Z")
            saved = evaluate_pair(lab.tasks,lab.documents,lab.truth,baseline,candidate,saved_context)
            active = activate(state,candidate,evidence,approval,context,now=CLOCK)
            back = rollback(active,baseline,reason="exercise_fault",now="2026-09-28T00:01:00Z")
            saved_approval = make_approval(candidate,saved,approver_id="reviewer-local",
                                allowed_scopes=tuple(a.scope for a in candidate.artifacts),
                                now="2026-09-28T00:02:00Z",valid_until=saved_context.valid_until)
            try:
                activate(back,candidate,saved,saved_approval,saved_context,now="2026-09-28T00:02:00Z")
            except ValueError:
                details["unused_old_evidence_rejected"] = True
            else:
                raise AssertionError("unused saved evidence bypassed fresh validation after rollback")
        else:
            active = activate(state,candidate,evidence,approval,context,now=CLOCK)
            back = rollback(active,baseline,reason="exercise",now=CLOCK)
            ids = tuple(tasks)
            cohort = assign_cohort(ids)
            assert cohort == assign_cohort(tuple(reversed(ids)))
            details = {"candidate_requests":list(cohort.values()).count("candidate"),"baseline_requests":list(cohort.values()).count("baseline"),
                       "active_after_rollback":back.active.revision_id,"audit_records":len(back.history)}
            assert details["candidate_requests"]==4 and details["audit_records"]==2
            try:
                rollback(back,candidate,reason="restore_stopped",now=CLOCK)
            except ValueError:
                details["stopped_restore_rejected"] = True
            else:
                raise AssertionError("rollback restored stopped revision without new verification")
    elif number == 10:
        changed = replace(lab,feedback=tuple(replace(f,payload={"answer_style":"normal"})
                                            if f.feedback_id=="F08" else f for f in lab.feedback))
        unsupported = evaluate_pair(changed.tasks,changed.documents,changed.truth,baseline,candidate,
                                    make_context(changed,policy))
        details = {"safe":decide_gate(evidence).status,"unknown":decide_gate(seal_evidence(replace(evidence,unknown_count=1))).status,
                   "unsafe_unknown":decide_gate(seal_evidence(replace(evidence,unknown_count=1,violation_count=1))).status,
                   "unsupported_source":decide_gate(unsupported).status}
        assert details == {"safe":"pass","unknown":"inconclusive","unsafe_unknown":"fail","unsupported_source":"fail"}
    elif number == 12:
        details = {r.feedback_id:{"status":r.disposition,"sensitive":r.source_sensitive} for r in rows if r.feedback_id in ("F09","F12")}
        try:
            propose_lessons(rows,lab.replays,blocked_families=frozenset({"discover-export"}))
        except ValueError:
            details["family_blocked"] = True
        else:
            raise AssertionError("family leakage")
        assert details["F09"]["sensitive"] and details["F12"]["status"]=="quarantined"
    else:
        status,details = "answered",{"replay_fields":["authorized_media_ref","timestamp_alignment","perception_version","tool_receipt","missing"],
                                    "boundary":"model proposes; trusted code grants scope; independent grader reads truth"}
    difficulties = {1:1, 2:1, 3:2, 4:2, 5:2, 6:2, 7:2, 8:2, 9:3, 10:3, 11:3, 12:3, 13:3}
    return {"number":number,"difficulty":difficulties[number],"status":status,"evidence":details,"criteria":CRITERIA[number-1]}

def payload():
    return {"schema_version":"chapter16.exercises.v1","answers":[solve(n) for n in range(1,14)]}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all",action="store_true",required=True)
    parser.add_argument("--output",required=True)
    args = parser.parse_args(argv)
    from .output import write_new_json
    try:
        write_new_json(payload(),Path(args.output),root=Path(__file__).parents[1])
        print("13 exercises: 10 code checks, 3 qualitative answers")
        return 0
    except (OSError,ValueError) as exc:
        print("output refused:",str(exc))
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
