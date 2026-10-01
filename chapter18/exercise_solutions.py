from pathlib import Path
from .cases import run_case
from .contracts import ExerciseReport


def solution_payload(*, root: Path, workdir: Path) -> ExerciseReport:
    ids = {8: "stale-patch", 10: "cancel-late-result", 11: "kb-permission-denied", 12: "repair-verified"}
    cases = {n: run_case(case, root=root, workdir=workdir / case) for n, case in ids.items()}
    texts = {
        1: "一个决策上下文配多个工具仍可是单 Agent；固定步骤是 Workflow；独立任务、观察与决策责任才构成协作边界。",
        2: "资料互不依赖且输出可独立核对时值得拆分；必须等前一步结果的任务先画依赖边，不按角色数量硬拆。",
        3: "串行为7+11+5=23；理想并行为max(7,11,5)+2+3=16。额外开销达到12时与串行打平，超过12则更慢。",
        4: "将“研究一下”改成明确目标版本、必要资料、身份、允许工具、预算、输出格式与验收证据的有限任务。",
        5: "缺必要输入应列 missing 并返回 unknown，不把猜测或更宽上下文当作自动补救。",
        6: "三次引用同一个来源只增加意见数，不增加来源数；不同来源也可能转述同一原始事实。",
        7: "两份都有效的矛盾资料应保留 conflict，并列来源与差异；需要优先级规则或澄清，不能自选多数。",
        8: "实际实验拒绝第二份旧补丁，保留第一次写入；重新读取、重新提出，不是关闭基线校验。",
        9: "总16中保留验证2，Worker和重试合用14；换一个执行者不重新领取总额度。",
        10: "取消后的正常结果不会复活运行；已发生写入仍在回执中。是否需要补偿是另一个受控动作。",
        11: "public 调用不得读取 staff 资料；换专家或摘要转述都不提升身份，最终报告也不包含受限引句。",
        12: "真实补丁、4/4冻结测试、独立行为核对共同构成 verified；执行者的 done 只是待验收结果。",
        13: "按业务风险选最小责任闭环，再补身份、治理、动作隔离、持久性、预算和回滚证据，而不是先堆完整平台。",
    }
    answers = []
    for n in range(1, 14):
        computation, refs = {}, []
        if n == 3:
            durations = (7, 11, 5)
            computation = {"serial_units": sum(durations), "parallel_units": max(durations) + 2 + 3,
                           "break_even_overhead": sum(durations) - max(durations)}
        elif n == 9:
            from .contracts import BudgetLimits
            limits = BudgetLimits()
            computation = {"total": limits.tool_calls, "workers": limits.tool_calls - limits.verifier_reserve, "verifier": limits.verifier_reserve}
        elif n in cases:
            result = cases[n]
            refs = ["case:" + result["case_id"]] + ["case:" + result["case_id"] + "/event:" + e["event_id"] for e in result["trajectory"]]
            if n == 8:
                computation = {"stale_patch_refusals": result["metrics"]["stale_patch_refusals"], "status": result["status"]}
            elif n == 10:
                computation = {"committed_actions": sum(r["executed"] for r in result["receipts"]), "status": result["status"]}
            elif n == 11:
                computation = {"policy_refusals": result["metrics"]["policy_refusals"], "status": result["status"]}
            else:
                receipt = next(r for r in result["receipts"] if r["executed"])
                computation = {"tests_passed": receipt["verification"]["tests_passed"], "tests_total": receipt["verification"]["tests_total"],
                               "behavior_passed": receipt["verification"]["behavior_passed"], "status": result["status"]}
        rubric = ["说明理由", "指出证据与未证明范围"]
        if n == 13:
            rubric = ["身份", "数据", "动作隔离", "持久性", "预算", "回滚"]
        answers.append({"exercise_id": n, "kind": "code" if n in cases else "calculation" if n in {3, 9} else "design",
                        "answer": texts[n], "computation": computation, "evidence_refs": refs, "rubric": rubric})
    return {"schema_version": "chapter18.exercises.v1", "answers": answers,
            "case_evidence": [{"case_id": result["case_id"], "status": result["status"], "metrics": result["metrics"],
                               "event_ids": [e["event_id"] for e in result["trajectory"]]} for result in cases.values()]}
