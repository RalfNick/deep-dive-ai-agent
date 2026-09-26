"""Generate seven Chapter 14 diagrams from one shared scene model."""
from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
from typing import Iterable


WIDTH = 1600
HEIGHT = 960
INDEX_CHARS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
APPROVED_DIAGRAMS = (
    ("01-evidence-gap", "离线绿色，线上红色：证据断层"),
    ("02-benchmark-comparability", "Benchmark 可比性：先对齐测量合同"),
    ("03-observability-signals", "五类观测信号：各自回答什么"),
    ("04-session-trace-span", "Session → Trace → Span：结构树与依赖边"),
    ("05-critical-path", "关键路径：延迟不是 Span 时长相加"),
    ("06-sampling-privacy", "采样与隐私：Head 提前判定，载荷先脱敏"),
    ("07-diagnosis-loop", "生产诊断闭环：从告警到回归"),
)

PALETTE = {
    "blue": ("#dceeff", "#155b9a"),
    "green": ("#dff3e4", "#287a4b"),
    "violet": ("#ece3fa", "#6846a5"),
    "orange": ("#fff0d8", "#c46b18"),
    "red": ("#fde3df", "#b8443b"),
    "yellow": ("#fff7c9", "#9d7510"),
    "grey": ("#edf0f2", "#59636e"),
    "white": ("#fffdf7", "#17365d"),
}


@dataclass(frozen=True)
class Node:
    identity: str
    label: str
    x: int
    y: int
    w: int
    h: int
    color: str
    geo: str = "rectangle"
    dash: str = "draw"


@dataclass(frozen=True)
class Edge:
    identity: str
    start: str
    end: str
    label: str = ""
    color: str = "blue"
    dash: str = "draw"
    bend: int = 0


@dataclass(frozen=True)
class Scene:
    stem: str
    title: str
    subtitle: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    takeaway: str


def _scene_evidence_gap() -> Scene:
    nodes = (
        Node("eval", "内部 Eval\n固定任务通过", 90, 320, 270, 140, "green"),
        Node("benchmark", "公共 Benchmark\n提供外部参照", 440, 320, 280, 140, "blue"),
        Node("gate", "发布门禁\n分数仍是绿色", 800, 320, 260, 140, "green", "check-box"),
        Node("prod", "生产现场\np95、成本、重试变红", 1180, 300, 330, 180, "red", "x-box"),
        Node("trace", "Tracing + Metrics\n补上运行证据", 650, 610, 330, 140, "violet"),
    )
    edges = (
        Edge("e1", "eval", "benchmark", "用途不同"),
        Edge("e2", "benchmark", "gate", "审合同"),
        Edge("e3", "gate", "prod", "证据断层", "red", "dashed"),
        Edge("e4", "prod", "trace", "现场回放", "orange"),
        Edge("e5", "trace", "gate", "回归任务", "violet", "dashed"),
    )
    return Scene(APPROVED_DIAGRAMS[0][0], APPROVED_DIAGRAMS[0][1], "分数说明受控条件下发生了什么，Trace 解释线上到底怎样发生。", nodes, edges, "离线评估不是生产观测的替代品；二者必须用同一条证据链连接。")


def _scene_benchmark() -> Scene:
    nodes = (
        Node("card_a", "Submission A\nResolved = 72%", 80, 330, 260, 130, "blue"),
        Node("dataset", "Dataset\n版本 · 子集 · 时段", 440, 190, 260, 120, "green"),
        Node("harness", "Harness\n工具 · 重试 · 沙箱", 440, 350, 260, 120, "violet"),
        Node("budget", "Budget\n步骤 · Token · 超时", 440, 510, 260, 120, "orange"),
        Node("environment", "Environment\n依赖 · 资源 · 隔离", 790, 270, 280, 120, "yellow"),
        Node("metric", "Metric\n口径 · 尝试次数", 790, 470, 280, 120, "green"),
        Node("verdict", "Comparability\n可比 / 部分可比 / 不可比", 1190, 330, 330, 150, "red", "diamond"),
    )
    edges = tuple(Edge(f"e{i}", "card_a", target) for i, target in enumerate(("dataset", "harness", "budget"), 1)) + (
        Edge("e4", "dataset", "environment"),
        Edge("e5", "harness", "environment"),
        Edge("e6", "budget", "metric"),
        Edge("e7", "environment", "verdict"),
        Edge("e8", "metric", "verdict"),
    )
    return Scene(APPROVED_DIAGRAMS[1][0], APPROVED_DIAGRAMS[1][1], "两个总分相同，也可能测量的是不同系统。", nodes, edges, "Benchmark Card 先回答“能否比较”，然后才轮到分数高低。")


def _scene_signals() -> Scene:
    nodes = (
        Node("metrics", "Metrics\n有多严重？", 120, 220, 270, 120, "blue"),
        Node("logs", "Logs\n发生了什么事件？", 120, 560, 270, 120, "grey"),
        Node("traces", "Traces\n一条请求如何流动？", 620, 350, 360, 150, "violet"),
        Node("evals", "Evals\n结果满足标准吗？", 1210, 220, 270, 120, "green"),
        Node("feedback", "Feedback\n用户感受如何？", 1210, 560, 270, 120, "orange"),
        Node("question", "生产问题\n慢、贵、卡住，但成功率没降", 590, 650, 420, 130, "red"),
    )
    edges = (
        Edge("e1", "metrics", "traces", "告警 → 定位"),
        Edge("e2", "logs", "traces", "事件 → 因果链"),
        Edge("e3", "traces", "evals", "轨迹 + 结果"),
        Edge("e4", "traces", "feedback", "关联体验"),
        Edge("e5", "question", "traces", "从一个 Trace 开始", "red"),
    )
    return Scene(APPROVED_DIAGRAMS[2][0], APPROVED_DIAGRAMS[2][1], "五类信号互补，没有一种单独等于“真相”。", nodes, edges, "Metric 找症状，Trace 找路径，Eval 判结果，Feedback 补体验，Log 留事件细节。")


def _scene_hierarchy() -> Scene:
    nodes = (
        Node("session", "Session\n一次连续工作", 650, 170, 300, 110, "blue"),
        Node("trace_a", "Trace A\n一次用户请求", 310, 370, 300, 120, "green"),
        Node("trace_b", "Trace B\n一次恢复请求", 990, 370, 300, 120, "orange"),
        Node("model", "Span\nModel", 90, 650, 230, 100, "violet"),
        Node("retrieve", "Span\nRetrieval", 380, 650, 230, 100, "blue"),
        Node("tool", "Span\nTool", 960, 650, 230, 100, "orange"),
        Node("verify", "Span\nVerifier", 1250, 650, 230, 100, "green"),
    )
    edges = (
        Edge("e1", "session", "trace_a", "归属树"),
        Edge("e2", "session", "trace_b", "归属树"),
        Edge("e3", "trace_a", "model", "parent"),
        Edge("e4", "trace_a", "retrieve", "parent"),
        Edge("e5", "trace_b", "tool", "parent"),
        Edge("e6", "trace_b", "verify", "parent"),
        Edge("e7", "model", "retrieve", "依赖", "violet", "dashed"),
        Edge("e8", "tool", "verify", "依赖", "violet", "dashed"),
    )
    return Scene(APPROVED_DIAGRAMS[3][0], APPROVED_DIAGRAMS[3][1], "Parent 表示结构归属；depends_on 表示执行依赖。", nodes, edges, "树让人读懂结构，DAG 才能计算关键路径；两种边不能混用。")


def _scene_critical_path() -> Scene:
    nodes = (
        Node("plan", "Model Plan\n70 ms", 80, 370, 230, 110, "violet"),
        Node("ret_a", "Retrieval A\n86 ms", 400, 270, 240, 110, "blue"),
        Node("ret_b", "Retrieval B\n64 ms", 400, 520, 240, 110, "blue"),
        Node("answer", "Model Answer\n100 ms", 760, 370, 260, 110, "violet"),
        Node("verify", "Verifier\n40 ms", 1130, 370, 230, 110, "green"),
        Node("endpoint", "Endpoint\n331 ms", 1410, 370, 150, 110, "orange", "ellipse"),
    )
    edges = (
        Edge("e1", "plan", "ret_a", "关键", "red"),
        Edge("e2", "plan", "ret_b", "并行", "grey"),
        Edge("e3", "ret_a", "answer", "关键", "red"),
        Edge("e4", "ret_b", "answer", "汇合", "grey"),
        Edge("e5", "answer", "verify", "关键", "red"),
        Edge("e6", "verify", "endpoint", "完成", "red"),
    )
    return Scene(APPROVED_DIAGRAMS[4][0], APPROVED_DIAGRAMS[4][1], "Span 总和 360 ms，大于端到端 331 ms；关键路径为 296 ms。", nodes, edges, "并行 Span 会重叠，嵌套 Span 会重复计数；关键路径只沿依赖 DAG 求最长工作链。")


def _scene_sampling() -> Scene:
    nodes = (
        Node("record", "Record\n最小必要字段", 70, 390, 220, 120, "blue"),
        Node("head", "Head Decision\n只读取 Trace ID", 400, 220, 270, 120, "orange"),
        Node("redact", "Redact\n凭据删 · 身份哈希", 400, 510, 270, 140, "violet"),
        Node("tail", "Tail Decision\n读取安全 Trace", 760, 520, 240, 120, "orange"),
        Node("export", "Export\n安全门禁", 1080, 520, 230, 120, "green"),
        Node("store", "Store\n受控 Trace", 1370, 390, 180, 120, "blue"),
        Node("metrics", "Population Metrics\n请求数 · 失败数", 70, 680, 250, 110, "green"),
    )
    edges = (
        Edge("e1", "record", "head", "仅 Trace ID", "orange"),
        Edge("e2", "head", "store", "是否保留", "orange", "dashed", -70),
        Edge("e3", "record", "redact", "载荷先脱敏"),
        Edge("e4", "redact", "tail", "安全 Trace"),
        Edge("e5", "tail", "export", "Tail 保留"),
        Edge("e6", "export", "store", "安全载荷"),
        Edge("e7", "record", "metrics", "总体计数", "green", "dashed"),
    )
    return Scene(APPROVED_DIAGRAMS[5][0], APPROVED_DIAGRAMS[5][1], "Head 只看标识；Tail 读取的完整载荷必须已经脱敏。", nodes, edges, "Head 可提前决定；任何被缓冲、保存或导出的完整载荷都必须先脱敏。")


def _scene_diagnosis() -> Scene:
    nodes = (
        Node("detect", "Detect\n确认症状", 110, 350, 210, 110, "red"),
        Node("locate", "Locate\n按版本和切片定位", 390, 190, 270, 130, "blue"),
        Node("replay", "Replay\n重放代表性 Trace", 740, 150, 260, 130, "violet"),
        Node("ablate", "Ablate\n逐项移除假设", 1080, 190, 250, 130, "orange"),
        Node("verify", "Verify\n保留反证与未知", 1240, 520, 260, 130, "green"),
        Node("release", "Release\n修复 + 回归门禁", 770, 650, 280, 130, "green", "check-box"),
        Node("regress", "Regression Tasks\n把线上失败带回离线", 300, 650, 300, 130, "yellow"),
    )
    edges = (
        Edge("e1", "detect", "locate"),
        Edge("e2", "locate", "replay"),
        Edge("e3", "replay", "ablate"),
        Edge("e4", "ablate", "verify"),
        Edge("e5", "verify", "release"),
        Edge("e6", "release", "regress"),
        Edge("e7", "regress", "detect", "新故障继续进入", "violet", "dashed", 100),
    )
    return Scene(APPROVED_DIAGRAMS[6][0], APPROVED_DIAGRAMS[6][1], "只有一个消融同时消除全部症状，才形成较强的根因证据。", nodes, edges, "诊断不是看一张图猜原因，而是症状、切片、反证、消融和回归组成的闭环。")


SCENES = (
    _scene_evidence_gap(),
    _scene_benchmark(),
    _scene_signals(),
    _scene_hierarchy(),
    _scene_critical_path(),
    _scene_sampling(),
    _scene_diagnosis(),
)


def _schema() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "storeVersion": 4,
        "recordVersions": {
            "asset": {"version": 1, "subTypeKey": "type", "subTypeVersions": {"image": 2, "video": 2, "bookmark": 0}},
            "camera": {"version": 1},
            "document": {"version": 2},
            "instance": {"version": 17},
            "instance_page_state": {"version": 3},
            "page": {"version": 1},
            "shape": {"version": 3, "subTypeKey": "type", "subTypeVersions": {
                "group": 0, "embed": 4, "bookmark": 1, "image": 2, "text": 1,
                "draw": 1, "geo": 7, "line": 0, "note": 4, "frame": 0,
                "arrow": 1, "highlight": 0, "video": 1,
            }},
            "instance_presence": {"version": 4},
            "pointer": {"version": 1},
        },
    }


def _anchors(start: Node, end: Node) -> tuple[tuple[float, float], tuple[float, float]]:
    sx, sy = start.x + start.w / 2, start.y + start.h / 2
    ex, ey = end.x + end.w / 2, end.y + end.h / 2
    if abs(ex - sx) >= abs(ey - sy):
        return ((1, 0.5), (0, 0.5)) if ex >= sx else ((0, 0.5), (1, 0.5))
    return ((0.5, 1), (0.5, 0)) if ey >= sy else ((0.5, 0), (0.5, 1))


def _tldraw(scene: Scene) -> dict[str, object]:
    records: list[dict[str, object]] = [
        {"id": "document:document", "typeName": "document", "gridSize": 10, "name": "", "meta": {}},
        {"id": "page:page1", "typeName": "page", "name": "Page 1", "index": "a1", "meta": {}},
    ]
    shapes = (
        Node("paper", "", 20, 20, 1560, 900, "yellow"),
        Node("title", scene.title, 100, 55, 1400, 85, "white"),
        *scene.nodes,
        Node("takeaway", scene.takeaway, 150, 825, 1300, 70, "white"),
    )
    index = 0
    for node in shapes:
        records.append({
            "id": f"shape:{node.identity}", "typeName": "shape", "type": "geo",
            "parentId": "page:page1", "index": "a" + INDEX_CHARS[index],
            "x": node.x, "y": node.y, "rotation": 0, "isLocked": False, "opacity": 1, "meta": {},
            "props": {"w": node.w, "h": node.h, "geo": node.geo, "color": node.color,
                      "labelColor": "black", "fill": "semi" if node.identity != "title" else "solid",
                      "dash": node.dash, "size": "l" if node.identity == "title" else "m",
                      "font": "draw", "text": node.label, "align": "middle",
                      "verticalAlign": "middle", "growY": 0, "url": ""},
        })
        index += 1
    by_id = {node.identity: node for node in scene.nodes}
    for edge in scene.edges:
        start_anchor, end_anchor = _anchors(by_id[edge.start], by_id[edge.end])
        records.append({
            "id": f"shape:{edge.identity}", "typeName": "shape", "type": "arrow",
            "parentId": "page:page1", "index": "a" + INDEX_CHARS[index],
            "x": 0, "y": 0, "rotation": 0, "isLocked": False, "opacity": 1, "meta": {},
            "props": {"dash": edge.dash, "size": "m", "fill": "none", "color": edge.color,
                      "labelColor": "black", "bend": edge.bend,
                      "start": {"type": "binding", "boundShapeId": f"shape:{edge.start}",
                                "normalizedAnchor": {"x": start_anchor[0], "y": start_anchor[1]}, "isExact": False},
                      "end": {"type": "binding", "boundShapeId": f"shape:{edge.end}",
                              "normalizedAnchor": {"x": end_anchor[0], "y": end_anchor[1]}, "isExact": False},
                      "arrowheadStart": "none", "arrowheadEnd": "arrow", "text": edge.label,
                      "font": "draw"},
        })
        index += 1
    return {"tldrawFileFormatVersion": 1, "schema": _schema(), "records": records}


def _point(node: Node, other: Node) -> tuple[float, float]:
    cx, cy = node.x + node.w / 2, node.y + node.h / 2
    ox, oy = other.x + other.w / 2, other.y + other.h / 2
    if abs(ox - cx) >= abs(oy - cy):
        return (node.x + node.w if ox >= cx else node.x, cy)
    return (cx, node.y + node.h if oy >= cy else node.y)


def _multiline(label: str, x: float, y: float, *, size: int = 26, weight: int = 600) -> str:
    lines = label.split("\n")
    start_y = y - (len(lines) - 1) * size * 0.6
    tspans = "".join(
        f'<tspan x="{x:.1f}" y="{start_y + i * size * 1.25:.1f}">{html.escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    return f'<text class="label" text-anchor="middle" font-size="{size}" font-weight="{weight}">{tspans}</text>'


def _svg(scene: Scene) -> str:
    by_id = {node.identity: node for node in scene.nodes}
    arrow_parts: list[str] = []
    for edge in scene.edges:
        start, end = by_id[edge.start], by_id[edge.end]
        sx, sy = _point(start, end)
        ex, ey = _point(end, start)
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        if edge.bend:
            dx, dy = ex - sx, ey - sy
            length = max((dx * dx + dy * dy) ** 0.5, 1)
            cx, cy = mx - dy / length * edge.bend, my + dx / length * edge.bend
            path = f"M {sx:.1f} {sy:.1f} Q {cx:.1f} {cy:.1f} {ex:.1f} {ey:.1f}"
            label_x, label_y = cx, cy - 12
        else:
            path = f"M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}"
            label_x, label_y = mx, my - 12
        _, stroke = PALETTE[edge.color]
        dash = ' stroke-dasharray="10 9"' if edge.dash != "draw" else ""
        arrow_parts.append(f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="4" stroke-linecap="round" marker-end="url(#arrow)"{dash}/>' )
        if edge.label:
            width = max(90, len(edge.label) * 18)
            arrow_parts.append(f'<rect x="{label_x - width/2:.1f}" y="{label_y - 23:.1f}" width="{width}" height="32" rx="12" fill="#fffdf7" opacity="0.94"/>')
            arrow_parts.append(_multiline(edge.label, label_x, label_y, size=18, weight=500))

    node_parts: list[str] = []
    for node in scene.nodes:
        fill, stroke = PALETTE[node.color]
        if node.geo == "ellipse":
            node_parts.append(f'<ellipse cx="{node.x + node.w/2}" cy="{node.y + node.h/2}" rx="{node.w/2}" ry="{node.h/2}" fill="{fill}" stroke="{stroke}" stroke-width="4"/>')
        elif node.geo == "diamond":
            points = f"{node.x + node.w/2},{node.y} {node.x + node.w},{node.y + node.h/2} {node.x + node.w/2},{node.y + node.h} {node.x},{node.y + node.h/2}"
            node_parts.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="4" stroke-linejoin="round"/>')
        else:
            node_parts.append(f'<rect x="{node.x}" y="{node.y}" width="{node.w}" height="{node.h}" rx="24" fill="{fill}" stroke="{stroke}" stroke-width="4"/>')
        node_parts.append(_multiline(node.label, node.x + node.w/2, node.y + node.h/2, size=25))

    return "\n".join((
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(scene.title)}</title>',
        f'<desc id="desc">{html.escape(scene.subtitle)}</desc>',
        '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M 0 1 L 10 6 L 0 11 z" fill="#17365d"/></marker></defs>',
        '<style>.label{font-family:"KaiTi","STKaiti","Microsoft YaHei",sans-serif;fill:#17365d}.small{font-family:"Microsoft YaHei",sans-serif;fill:#46617f}</style>',
        '<rect width="1600" height="960" fill="#fbf5e8"/>',
        '<rect x="24" y="24" width="1552" height="912" rx="34" fill="#fffdf7" stroke="#17365d" stroke-width="3"/>',
        _multiline(scene.title, 800, 92, size=42, weight=700),
        _multiline(scene.subtitle, 800, 150, size=21, weight=400),
        *arrow_parts,
        *node_parts,
        '<rect x="150" y="825" width="1300" height="70" rx="20" fill="#fff7c9" stroke="#9d7510" stroke-width="3"/>',
        _multiline(scene.takeaway, 800, 862, size=22, weight=600),
        '</svg>',
    )) + "\n"


def generate_all(source_dir: Path, image_dir: Path) -> tuple[tuple[Path, Path], ...]:
    source_dir = Path(source_dir)
    image_dir = Path(image_dir)
    source_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[tuple[Path, Path]] = []
    for scene in SCENES:
        source = source_dir / f"{scene.stem}.tldr"
        image = image_dir / f"{scene.stem}.svg"
        source.write_text(json.dumps(_tldraw(scene), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        image.write_text(_svg(scene), encoding="utf-8", newline="\n")
        outputs.append((source, image))
    return tuple(outputs)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    for source, image in generate_all(Path(__file__).resolve().parent, root / "book" / "images" / "chapter14"):
        print(f"{source.relative_to(root)} -> {image.relative_to(root)}")
