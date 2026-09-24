"""Generate seven editable tldraw diagrams for chapter 13."""
from __future__ import annotations

import json
from pathlib import Path

INDEX_CHARS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


class Diagram:
    def __init__(self, title: str):
        self.records = [
            {"id": "document:document", "typeName": "document", "gridSize": 10,
             "name": "", "meta": {}},
            {"id": "page:page1", "typeName": "page", "name": "Page 1",
             "index": "a1", "meta": {}},
        ]
        self._index = 0
        self.node("paper", "", 20, 20, 1560, 900, "yellow", fill="semi", size="s")
        self.node("title", title, 120, 60, 1360, 100, "white", fill="solid", size="l")

    def _next(self) -> str:
        value = "a" + INDEX_CHARS[self._index]
        self._index += 1
        return value

    def node(self, identity: str, text: str, x: int, y: int, w: int, h: int,
             color: str, *, geo: str = "rectangle", fill: str = "semi",
             size: str = "m", dash: str = "draw") -> str:
        shape_id = f"shape:{identity}"
        self.records.append({
            "id": shape_id, "typeName": "shape", "type": "geo",
            "parentId": "page:page1", "index": self._next(), "x": x, "y": y,
            "rotation": 0, "isLocked": False, "opacity": 1, "meta": {},
            "props": {"w": w, "h": h, "geo": geo, "color": color,
                      "labelColor": "black", "fill": fill, "dash": dash,
                      "size": size, "font": "draw", "text": text,
                      "align": "middle", "verticalAlign": "middle",
                      "growY": 0, "url": ""},
        })
        return shape_id

    def arrow(self, identity: str, start: str, end: str, text: str = "", *,
              color: str = "black", dash: str = "draw", bend: int = 0,
              start_anchor=(1, .5), end_anchor=(0, .5)) -> None:
        self.records.append({
            "id": f"shape:{identity}", "typeName": "shape", "type": "arrow",
            "parentId": "page:page1", "index": self._next(), "x": 0, "y": 0,
            "rotation": 0, "isLocked": False, "opacity": 1, "meta": {},
            "props": {"dash": dash, "size": "m", "fill": "none", "color": color,
                      "labelColor": "black", "bend": bend,
                      "start": {"type": "binding", "boundShapeId": start,
                                "normalizedAnchor": {"x": start_anchor[0], "y": start_anchor[1]},
                                "isExact": False},
                      "end": {"type": "binding", "boundShapeId": end,
                              "normalizedAnchor": {"x": end_anchor[0], "y": end_anchor[1]},
                              "isExact": False},
                      "arrowheadStart": "none", "arrowheadEnd": "arrow",
                      "text": text, "font": "draw"},
        })

    def payload(self) -> dict:
        return {
            "tldrawFileFormatVersion": 1,
            "schema": {"schemaVersion": 1, "storeVersion": 4, "recordVersions": {
                "asset": {"version": 1, "subTypeKey": "type", "subTypeVersions":
                          {"image": 2, "video": 2, "bookmark": 0}},
                "camera": {"version": 1}, "document": {"version": 2},
                "instance": {"version": 17}, "instance_page_state": {"version": 3},
                "page": {"version": 1}, "shape": {"version": 3,
                    "subTypeKey": "type", "subTypeVersions": {"group": 0, "embed": 4,
                    "bookmark": 1, "image": 2, "text": 1, "draw": 1, "geo": 7,
                    "line": 0, "note": 4, "frame": 0, "arrow": 1,
                    "highlight": 0, "video": 1}},
                "instance_presence": {"version": 4}, "pointer": {"version": 1}}},
            "records": self.records,
        }


def _evaluation_model() -> Diagram:
    d = Diagram("Agent 评估：从任务到发布证据")
    task = d.node("task", "Task\n输入 + 成功标准", 90, 250, 240, 130, "blue")
    trial = d.node("trial", "Trial × N\n固定环境与种子", 410, 250, 250, 130, "green")
    outcome = d.node("outcome", "Outcome\n最终环境状态", 760, 210, 240, 110, "violet")
    trace = d.node("trace", "Trajectory\n工具与状态轨迹", 760, 370, 240, 110, "orange")
    graders = d.node("graders", "Graders\n结果 · 轨迹 · 安全 · 效率", 1090, 250, 320, 150, "light-violet")
    report = d.node("report", "Report + Gate\n通过 / 失败 / 证据不足", 1090, 560, 320, 140, "green", geo="check-box")
    d.arrow("a1", task, trial)
    d.arrow("a2", trial, outcome, start_anchor=(1, .35), end_anchor=(0, .5))
    d.arrow("a3", trial, trace, start_anchor=(1, .7), end_anchor=(0, .5))
    d.arrow("a4", outcome, graders, start_anchor=(1, .5), end_anchor=(0, .3))
    d.arrow("a5", trace, graders, start_anchor=(1, .5), end_anchor=(0, .7))
    d.arrow("a6", graders, report, "聚合 + 硬门禁", start_anchor=(.5, 1), end_anchor=(.5, 0))
    d.node("takeaway", "评估的对象不是一句回答，而是模型、Harness、环境和评分器组成的整个系统。",
           180, 770, 1240, 90, "white", fill="solid")
    return d


def _same_answer() -> Diagram:
    d = Diagram("同一句“修复完成”，为什么证据完全不同？")
    start = d.node("task", "同一个仓库问题", 650, 190, 300, 100, "blue")
    left = d.node("agent_a", "Agent A\n读代码 → 修改源文件 → 独立验证", 160, 390, 520, 150, "green")
    right = d.node("agent_b", "Agent B\n改弱测试 → 越界读取 → 宣布完成", 920, 390, 520, 150, "red")
    final_a = d.node("final_a", "最终回复\n“修复完成”", 260, 650, 320, 120, "light-blue")
    final_b = d.node("final_b", "最终回复\n“修复完成”", 1020, 650, 320, 120, "light-red")
    d.arrow("a1", start, left, "相同输入", start_anchor=(.35, 1), end_anchor=(.5, 0))
    d.arrow("a2", start, right, "相同输入", start_anchor=(.65, 1), end_anchor=(.5, 0))
    d.arrow("a3", left, final_a, "结果正确 + 轨迹安全", start_anchor=(.5, 1), end_anchor=(.5, 0))
    d.arrow("a4", right, final_b, "假成功", color="red", start_anchor=(.5, 1), end_anchor=(.5, 0))
    d.node("lesson", "只比较最后一句话，两者相同；检查 Outcome、Trajectory 与 Safety，结论相反。",
           300, 810, 1000, 70, "white", fill="solid")
    return d


def _grader_matrix() -> Diagram:
    d = Diagram("一次 Trial，需要几种 Grader？")
    trial = d.node("trial", "TrialRecord\nOutcome + Events + Usage", 590, 350, 420, 150, "blue")
    outcome = d.node("outcome", "结果评分\n功能真的正确吗？", 100, 210, 300, 120, "green")
    trajectory = d.node("trajectory", "轨迹评分\n关键证据是否出现？", 100, 590, 300, 120, "violet")
    safety = d.node("safety", "安全评分（硬门禁）\n是否越界或篡改？", 1200, 210, 300, 130, "red")
    efficiency = d.node("efficiency", "效率评分\n步骤与工具是否超预算？", 1200, 590, 300, 120, "orange")
    gate = d.node("gate", "发布门禁\n安全失败直接否决", 590, 680, 420, 130, "red", geo="octagon")
    d.arrow("a1", trial, outcome, start_anchor=(0, .35), end_anchor=(1, .5))
    d.arrow("a2", trial, trajectory, start_anchor=(0, .7), end_anchor=(1, .5))
    d.arrow("a3", trial, safety, start_anchor=(1, .35), end_anchor=(0, .5))
    d.arrow("a4", trial, efficiency, start_anchor=(1, .7), end_anchor=(0, .5))
    d.arrow("a5", trial, gate, "分项聚合；安全失败直接否决",
            start_anchor=(.5, 1), end_anchor=(.5, 0))
    return d


def _lifecycle() -> Diagram:
    d = Diagram("能力评测与回归评测：两套问题，一条反馈链")
    failures = d.node("failures", "真实失败 / 产品目标", 80, 370, 260, 120, "orange")
    capability = d.node("capability", "能力评测集\n还能做到什么？", 420, 220, 300, 140, "violet")
    regression = d.node("regression", "回归评测集\n已有能力退化了吗？", 420, 560, 300, 140, "blue")
    candidate = d.node("candidate", "候选 Agent", 830, 370, 260, 120, "green")
    gate = d.node("gate", "成对比较 + 门禁", 1190, 370, 300, 120, "yellow", geo="diamond")
    release = d.node("release", "发布", 1240, 690, 200, 100, "green", geo="check-box")
    d.arrow("a1", failures, capability, start_anchor=(1, .35), end_anchor=(0, .5))
    d.arrow("a2", failures, regression, start_anchor=(1, .7), end_anchor=(0, .5))
    d.arrow("a3", capability, candidate, start_anchor=(1, .5), end_anchor=(0, .35))
    d.arrow("a4", regression, candidate, start_anchor=(1, .5), end_anchor=(0, .7))
    d.arrow("a5", candidate, gate)
    d.arrow("a6", gate, release, "通过", start_anchor=(.5, 1), end_anchor=(.5, 0))
    d.arrow("a7", gate, failures, "失败样本回流", color="orange", dash="dashed",
            bend=100, start_anchor=(.5, 0), end_anchor=(.5, 0))
    return d


def _pass_metrics() -> Diagram:
    d = Diagram("pass@k 与 pass^k：发现能力，不等于持续可靠")
    labels = ["✓", "✕", "✓", "✕", "✕"]
    top_nodes = []
    bottom_nodes = []
    for index, label in enumerate(labels):
        color = "green" if label == "✓" else "red"
        top_nodes.append(d.node(f"top{index}", label, 140 + index * 230, 290, 140, 110,
                                color, geo="check-box" if label == "✓" else "x-box"))
        bottom_nodes.append(d.node(f"bottom{index}", label, 140 + index * 230, 590, 140, 110,
                                   color, geo="check-box" if label == "✓" else "x-box"))
    at = d.node("at", "pass@3\n三次里至少一次成功\n发现能力", 1270, 270, 250, 150, "blue")
    allk = d.node("all", "pass^3\n三次必须全部成功\n衡量可靠", 1270, 570, 250, 150, "violet")
    d.arrow("a1", top_nodes[-1], at)
    d.arrow("a2", bottom_nodes[-1], allk)
    d.node("note", "同样的单次成功率，扩大 k 会让 pass@k 上升，却让 pass^k 下降。",
           280, 790, 1040, 80, "white", fill="solid")
    return d


def _judge_calibration() -> Diagram:
    d = Diagram("LLM-as-Judge：先校准，再扩大使用")
    rubric = d.node("rubric", "明确 Rubric\n分维度 + 允许 Unknown", 90, 330, 300, 150, "blue")
    judge = d.node("judge", "LLM Judge\n结构化标签 + 证据", 470, 330, 300, 150, "violet")
    sample = d.node("sample", "人工抽样复核\n建立 Gold Labels", 850, 330, 300, 150, "green")
    matrix = d.node("matrix", "一致率 + 混淆矩阵\n查看偏差，而非只看均分", 1230, 330, 300, 150, "orange")
    revise = d.node("revise", "修订任务 / Rubric / Judge", 630, 650, 420, 130, "yellow")
    d.arrow("a1", rubric, judge)
    d.arrow("a2", judge, sample)
    d.arrow("a3", sample, matrix)
    d.arrow("a4", matrix, revise, "发现系统性分歧", start_anchor=(.5, 1), end_anchor=(1, .5), bend=30)
    d.arrow("a5", revise, rubric, "重新校准", dash="dashed", bend=80,
            start_anchor=(0, .5), end_anchor=(.5, 1))
    d.node("warning", "Judge 是可扩展的测量工具，不是自动生成的真相。",
           380, 800, 840, 70, "white", fill="solid")
    return d


def _framework_mapping() -> Diagram:
    d = Diagram("同一套评估概念，如何映射到不同框架？")
    local = d.node("local", "本章最小 Harness\nTaskSpec · Runner · Graders · Report", 80, 240, 420, 150, "blue")
    inspect = d.node("inspect", "Inspect AI\nDataset · Solver · Scorer · Task", 610, 210, 390, 130, "violet")
    openai = d.node("openai", "OpenAI Evals\nDataset · Eval · Graders · Trace", 610, 410, 390, 130, "green")
    langsmith = d.node("langsmith", "LangSmith\nDataset · Experiment · Evaluators", 610, 610, 390, 130, "orange")
    gate = d.node("gate", "共同目标\n可重复比较 + 失败证据 + 发布门禁", 1130, 380, 390, 190, "yellow", geo="hexagon")
    d.arrow("a1", local, inspect, "概念映射", start_anchor=(1, .25), end_anchor=(0, .5))
    d.arrow("a2", local, openai, "概念映射", start_anchor=(1, .5), end_anchor=(0, .5))
    d.arrow("a3", local, langsmith, "概念映射", start_anchor=(1, .75), end_anchor=(0, .5))
    d.arrow("a4", inspect, gate, start_anchor=(1, .5), end_anchor=(0, .25))
    d.arrow("a5", openai, gate, start_anchor=(1, .5), end_anchor=(0, .5))
    d.arrow("a6", langsmith, gate, start_anchor=(1, .5), end_anchor=(0, .75))
    d.node("boundary", "框架替你组织运行；成功标准、风险边界和证据解释仍由团队负责。",
           260, 800, 1080, 70, "white", fill="solid")
    return d


def generate_all(output: Path) -> list[Path]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    diagrams = [
        ("01-evaluation-model.tldr", _evaluation_model()),
        ("02-same-answer-different-evidence.tldr", _same_answer()),
        ("03-multi-grader-matrix.tldr", _grader_matrix()),
        ("04-eval-lifecycle.tldr", _lifecycle()),
        ("05-pass-k-vs-pass-all-k.tldr", _pass_metrics()),
        ("06-judge-calibration.tldr", _judge_calibration()),
        ("07-framework-mapping.tldr", _framework_mapping()),
    ]
    paths = []
    for name, diagram in diagrams:
        path = output / name
        path.write_text(json.dumps(diagram.payload(), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        paths.append(path)
    return paths


if __name__ == "__main__":
    for generated in generate_all(Path(__file__).resolve().parent):
        print(generated)
