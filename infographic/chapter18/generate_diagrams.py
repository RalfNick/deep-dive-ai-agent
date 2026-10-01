"""Seven scenes, paired editable tldraw sources and controlled Chinese SVGs."""
from __future__ import annotations
import json
from pathlib import Path
from infographic.chapter14.generate_diagrams import Scene, Node, Edge, _svg, _tldraw


def n(key, label, x, y, color, w=300, h=120):
    return Node(key, label, x, y, w, h, color)


def build_scenes() -> tuple[Scene, ...]:
    return (
        Scene("01-boundaries", "多角色，不一定是多 Agent",
              "看独立决策状态和控制边界，不看提示词里写了几个职位。",
              (n("single", "单 Agent", 80, 220, "blue"),
               n("singletools", "同一控制器\n调用 Tools / Skills", 580, 220, "blue", 430),
               n("singleend", "独立任务\n优先保持简单", 1190, 220, "green"),
               n("workflow", "Workflow", 80, 430, "green"),
               n("graph", "预先设计步骤\n条件分支与汇合", 580, 430, "green", 430),
               n("workflowend", "程序决定路线\n模型可用于某一步", 1190, 430, "green"),
               n("team", "Multi-Agent", 80, 640, "violet"),
               n("workers", "独立上下文与状态\n有界委派或控制交接", 580, 640, "violet", 430),
               n("teamend", "多控制单元\n仍需最终验收", 1190, 640, "orange")),
              (Edge("e1", "single", "singletools"), Edge("e2", "singletools", "singleend"),
               Edge("e3", "workflow", "graph", color="green"), Edge("e4", "graph", "workflowend", color="green"),
               Edge("e5", "team", "workers", color="violet"), Edge("e6", "workers", "teamend", color="violet")),
              "同一提示词换角色 ≠ 独立 Agent；是否拆分，先看任务边界。"),
        Scene("02-dependencies", "先画依赖，再讨论并行",
              "固定逻辑单位：串行 7 + 11 + 5 = 23；并行 max(7,11,5) + 2 + 3 = 16。",
              (n("start", "委派\n成本 2", 80, 410, "blue", 250),
               n("a", "产品查询\n7 逻辑单位", 550, 200, "blue", 330),
               n("b", "版本查询\n11 逻辑单位", 550, 410, "green", 330),
               n("c", "支持查询\n5 逻辑单位", 550, 620, "violet", 330),
               n("join", "汇合与核验\n成本 3", 1190, 410, "orange", 320)),
              (Edge("e1", "start", "a"), Edge("e2", "start", "b"), Edge("e3", "start", "c"),
               Edge("e4", "a", "join"), Edge("e5", "b", "join", "最长分支", "green"), Edge("e6", "c", "join")),
              "三项查询必须独立；23 / 16 是教学排程，不是实测加速比。"),
        Scene("03-delegation-handoff", "委派返回；交接接管",
              "上行仍由 Manager 验收；下行由 Expert 成为当前控制器。",
              (n("manager", "Manager\n保留主任务控制权", 70, 270, "blue", 360),
               n("worker", "Worker\n完成有界子任务", 630, 270, "green", 330),
               n("return", "Manager\n接纳或拒绝结果", 1190, 270, "blue", 340),
               n("before", "Manager\n交接前的控制器", 70, 600, "blue", 360),
               n("expert", "Expert\n交接后的控制器", 630, 600, "violet", 330),
               n("continue", "Expert 继续\n状态与预算不重置", 1190, 600, "orange", 340)),
              (Edge("e1", "manager", "worker", "委派"), Edge("e2", "worker", "return", "返回结果", "green"),
               Edge("e3", "before", "expert", "接管控制权", "violet"), Edge("e4", "expert", "continue", "继续运行", "violet")),
              "结果流向与控制权流向不同；handoff 不是给子任务改个名字。"),
        Scene("04-task-context", "任务说明，先让人读懂",
              "父任务的身份、版本、范围和预算，只能继承或收窄。",
              (n("parent", "父任务\n身份 · 目标 · 上限", 70, 380, "blue", 340, 160),
               n("goal", "两句说明\n查什么 · 交什么", 600, 200, "green", 370),
               n("scope", "TaskPacket\n版本 · 来源 · 写入范围", 600, 420, "violet", 370),
               n("budget", "共享账本\n子任务没有新额度", 600, 640, "orange", 370),
               n("context", "实际发送的上下文\n原文片段 + 来源哈希", 1170, 290, "blue", 360, 150),
               n("result", "WorkerResult\n结论 · 缺项 · 提案", 1170, 590, "green", 360, 150)),
              (Edge("e1", "parent", "goal"), Edge("e2", "parent", "scope"), Edge("e3", "parent", "budget"),
               Edge("e4", "goal", "context"), Edge("e5", "scope", "context"), Edge("e6", "context", "result", "证据随结果返回", "green")),
              "保留文件与发送内容是两回事；Worker 不会自动看见主对话。"),
        Scene("05-integration", "并行提案，单写者集成",
              "两个 Worker 各读独立快照；只有受控 Gateway 能修改集成工作区。",
              (n("wa", "Worker A\n独立快照", 70, 230, "blue", 300),
               n("pa", "提案 A\n基线哈希 + 替换", 490, 230, "blue", 320),
               n("wb", "Worker B\n独立快照", 70, 580, "violet", 300),
               n("pb", "提案 B\n基线哈希 + 替换", 490, 580, "violet", 320),
               n("gate", "单写者 Gateway\n范围 · 审批 · 当前哈希", 910, 380, "orange", 360, 170),
               n("verify", "最终集成验证\n测试 + 行为探针", 1300, 600, "green", 250, 160),
               n("stale", "基线已变化\n拒绝旧补丁", 900, 660, "red", 300, 100)),
              (Edge("e1", "wa", "pa"), Edge("e2", "wb", "pb", color="violet"),
               Edge("e3", "pa", "gate"), Edge("e4", "pb", "gate", color="violet"),
               Edge("e5", "gate", "verify", "提交后验收", "green"), Edge("e6", "gate", "stale", "哈希不符", "red")),
              "Worker 说 done 只代表提案返回；写入、集成正确与验收是另外三件事。"),
        Scene("06-lifecycle", "额度与取消，都不能抹账",
              "总额度 16 已包含验证保留 2；Worker 最多用 14，不是 16 + 2。",
              (n("workerbudget", "Worker 池\n最多 14 次", 90, 220, "blue", 350),
               n("verifierbudget", "Verifier 保留\n2 次只用于验收", 620, 220, "green", 370),
               n("global", "共享总账本\n重试和写入也扣费", 1160, 220, "orange", 350),
               n("running", "运行中", 70, 530, "blue", 240),
               n("cancel", "取消确认\nstopped", 440, 530, "orange", 280),
               n("late", "迟到结果\n拒绝接纳", 850, 530, "red", 280),
               n("receipt", "已提交回执\n仍然保留", 1240, 530, "violet", 280)),
              (Edge("e1", "workerbudget", "verifierbudget", "总额内分池"), Edge("e2", "verifierbudget", "global", "不重置", "orange"),
               Edge("e3", "running", "cancel"), Edge("e4", "cancel", "late", "身份与状态检查", "red"),
               Edge("e5", "late", "receipt", "取消不是回滚", "violet")),
              "超时要留缺项；取消要留副作用；换控制器也不获得新预算。"),
        Scene("07-final-system", "最终系统：两条业务路，一套边界",
              "知识回答要合格来源；代码修改要审批、执行回执与最终验证。",
              (n("user", "用户目标\n身份 + 成功条件", 60, 420, "blue", 300),
               n("context", "上下文装配\n版本与最小可见域", 460, 210, "blue", 330),
               n("runtime", "有界 Runtime\n任务与全局账本", 460, 430, "violet", 330),
               n("policy", "权限与状态检查\n拒绝扩权 / 迟到结果", 460, 650, "orange", 330),
               n("knowledge", "知识证据\n来源 + 覆盖 + 冲突", 900, 210, "green", 330),
               n("answer", "answer\n缺证据则 unknown", 1290, 210, "green", 260),
               n("proposal", "补丁提案 + 审批\n无批准则暂停", 900, 550, "orange", 330),
               n("execute", "execute\n受控写入 + 回执", 1290, 510, "blue", 260),
               n("verify", "verify\n测试 + 行为探针", 1290, 690, "green", 260, 100)),
              (Edge("e1", "user", "runtime"), Edge("e2", "context", "runtime"), Edge("e3", "policy", "runtime", color="orange"),
               Edge("e4", "runtime", "knowledge"), Edge("e5", "knowledge", "answer", "验收", "green"),
               Edge("e6", "runtime", "proposal"), Edge("e7", "proposal", "execute", "批准", "orange"), Edge("e8", "execute", "verify", "最终验收", "green")),
              "最小系统不是全书组件的堆叠；让每项结论都找得到边界和证据。"),
    )


def generate(root: Path) -> tuple[Path, ...]:
    outputs = []
    for scene in build_scenes():
        for directory, suffix, payload in (
            ("infographic/chapter18", ".tldr", json.dumps(_tldraw(scene), ensure_ascii=False, indent=2) + "\n"),
            ("book/images/chapter18", ".svg", _svg(scene))):
            path = root / directory / (scene.stem + suffix)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8", newline="\n")
            outputs.append(path)
    return tuple(outputs)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    for path in generate(root):
        print(path.relative_to(root))
