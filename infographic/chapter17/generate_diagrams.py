"""Seven deterministic figures; authored chart is the first figure's truth source."""

from __future__ import annotations

import json
from pathlib import Path

from infographic.chapter14.generate_diagrams import Scene, Node, Edge, _svg, _tldraw


def n(key: str, label: str, x: int, y: int, color: str,
      w: int = 260, h: int = 120) -> Node:
    return Node(key, label, x, y, w, h, color)


def build_scenes() -> tuple[Scene, ...]:
    return (
        Scene("02-five-inputs-evidence", "五类输入，统一证据链",
              "每类媒体都有来源、时间和可见范围；转成文字不会自动提高可信度。",
              (n("image", "图像\n区域 + 像素来源", 70, 210, "blue", 310),
               n("document", "文档页\n页码 + 版本", 70, 350, "green", 310),
               n("screen", "屏幕\n帧 ID + 截取时刻", 70, 490, "violet", 310),
               n("audio", "音频\n片段 + 时间戳", 70, 630, "orange", 310),
               n("text", "文本\n原文 + 权限域", 490, 210, "grey", 320),
               n("contract", "MediaRef + Observation\n来源 / 方法 / 不确定性", 550, 450, "blue", 440, 160),
               n("decision", "Decision\n回答 / Unknown / 阻断 / 刷新", 1100, 450, "green", 410, 160)),
              tuple(Edge(f"e{i}", key, "contract", color=color) for i,(key,color) in enumerate(
                  (("image","blue"),("document","green"),("screen","violet"),("audio","orange"),("text","grey")),1))+
              (Edge("e6", "contract", "decision", "证据仍须核验", "violet"),),
              "模型看到的内容是观察；能否回答还要看来源、冲突与边界。"),
        Scene("03-chart-verification", "图表观察 → 算术验证 → 决策",
              "柱形高度只是候选；CSV 是独立核验，不是隐藏答案属性。",
              (n("svg", "受控 SVG\n刻度 · 单位 · 月份", 70, 330, "blue", 280),
               n("geometry", "几何取数\nJan 80 / Feb 100", 430, 330, "violet", 300),
               n("csv", "独立 CSV\nmonth,unit,count", 430, 560, "green", 300),
               n("compare", "同单位同月份\n数值逐项一致？", 830, 350, "orange", 300, 160),
               n("answer", "Answer\n(100−80)/80=25%", 1220, 250, "green", 300),
               n("unknown", "Unknown\n缺项 / 冲突 / 零分母", 1220, 560, "red", 300)),
              (Edge("e1","svg","geometry"),Edge("e2","geometry","compare"),
               Edge("e3","csv","compare","独立核验","green"),
               Edge("e4","compare","answer","一致","green"),
               Edge("e5","compare","unknown","冲突","red")),
              "读图是观察；算数可手算；任一必要证据不成立就明确弃答。"),
        Scene("04-computer-use-gate", "Computer Use：行动须经五道门",
              "本图是模拟回执，不表示真的控制了桌面。",
              (n("observe","观察帧\nf1 @ 1000ms",60,370,"blue",250),
               n("map","坐标映射\nx/y 分别缩放",370,370,"violet",250),
               n("policy","权限 + 审批\nallow / deny",680,370,"orange",250),
               n("act","模拟行动\n记录执行回执",990,370,"blue",250),
               n("verify","新帧复核\n状态真的改变？",1290,370,"green",250),
               n("refresh","过期 → Refresh\n不再沿用旧坐标",220,640,"red",350)),
              (Edge("e1","observe","map"),Edge("e2","map","policy"),
               Edge("e3","policy","act"),Edge("e4","act","verify"),
               Edge("e5","observe","refresh","超过 2 秒","red","dashed")),
              "提议不是执行；执行不是验证；旧画面必须先刷新。"),
        Scene("05-stale-vs-current-frame", "同一坐标，不一定是同一控件",
              "屏幕坐标只有在指定帧、尺寸和目标框之内才有意义。",
              (n("old","旧帧 f1\n(400,225) = 提交",100,310,"blue",390,170),
               n("new","新帧 f-new\n(400,225) = 删除",650,310,"red",390,170),
               n("proposal","提议引用 f1\n动作 click submit",100,600,"violet",390,130),
               n("check","当前帧 ID 不同\n返回 Refresh，不点击",1110,430,"orange",390,170)),
              (Edge("e1","old","new","界面变化","red"),
               Edge("e2","old","proposal","绑定","violet"),
               Edge("e3","new","check","重新观察","orange"),
               Edge("e4","proposal","check","帧不匹配","red","dashed")),
              "坐标不是授权；画面文字也不能改变 allowlist 或审批决定。"),
        Scene("06-voice-double-timeline", "实时语音：两条时间线不能合并",
              "用户开始说话，播报可以停；后台任务要看独立事件。",
              (n("speech","用户 speech_started",60,240,"blue",340),
               n("cancel","response_cancelled\n停止生成请求",490,240,"violet",340),
               n("playback","playback_stopped\n扬声器不再播",1010,240,"orange",430),
               n("task","task_started\n后台仍 running",60,560,"green",340),
               n("commit","action_committed\n副作用已发生",490,560,"orange",340),
               n("complete","task_completed\n迟来的 cancel 不撤销",1010,560,"green",430)),
              (Edge("e1","speech","cancel"),Edge("e2","cancel","playback"),
               Edge("e3","task","commit","另一条线","green"),
               Edge("e4","commit","complete"),
               Edge("e5","speech","task","不等于取消","red","dashed",-80)),
              "停播、截断上下文、取消后台任务和补偿副作用，是四个不同动作。"),
        Scene("07-cross-modal-gates", "跨模态门禁与可回放证据包",
              "不让一种模态的空缺由另一种模态的自信表述填补。",
              (n("source","来源门\n身份 + 哈希 + 版本",60,250,"blue",300),
               n("time","时间门\n帧新鲜度 + 事件序",60,450,"violet",300),
               n("scope","权限门\n允许范围 + 审批",60,650,"orange",300),
               n("decision","统一决策\nAnswer / Unknown / Block / Refresh",620,430,"green",430,180),
               n("bundle","回放包\n输入摘要 + 中间态 + 原因",1180,430,"blue",340,180)),
              (Edge("e1","source","decision"),Edge("e2","time","decision"),
               Edge("e3","scope","decision"),Edge("e4","decision","bundle","可追溯","green")),
              "失败不是空白：保留缺证据的位置，下一次才知道该补什么。"),
    )


def _chart_svg() -> str:
    # This visual uses the authored chart geometry, but is not used as experiment input.
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 960" role="img" aria-labelledby="title desc">
<title id="title">增长多少？先读刻度、单位和基线</title>
<desc id="desc">零轴图和截断轴图都表示一月80千件、二月100千件，相对增长25%。</desc>
<style>.t{font-family:KaiTi,STKaiti,Microsoft YaHei,sans-serif;fill:#17365d}.s{font-family:Microsoft YaHei,sans-serif;fill:#46617f}</style>
<rect width="1600" height="960" fill="#fbf5e8"/><rect x="24" y="24" width="1552" height="912" rx="34" fill="#fffdf7" stroke="#17365d" stroke-width="3"/>
<text class="t" x="800" y="100" text-anchor="middle" font-size="44" font-weight="700">增长多少？不能只看柱子的高差</text>
<text class="s" x="800" y="153" text-anchor="middle" font-size="24">同一组数据，两种纵轴；读图之后再用独立数据手算。</text>
<rect x="80" y="200" width="690" height="580" rx="28" fill="#eaf4ff" stroke="#155b9a" stroke-width="3"/>
<text class="t" x="425" y="250" text-anchor="middle" font-size="31">零轴：柱形忠实从 0 开始</text>
<text class="s" x="130" y="320" font-size="24">单位：千件</text>
<line x1="170" y1="680" x2="710" y2="680" stroke="#17365d" stroke-width="4"/><text class="s" x="120" y="690" font-size="23">0</text>
<line x1="170" y1="360" x2="710" y2="360" stroke="#8ba4bd" stroke-width="2" stroke-dasharray="8 7"/><text class="s" x="110" y="370" font-size="23">100</text>
<rect x="270" y="424" width="115" height="256" rx="10" fill="#77b3e8" stroke="#155b9a" stroke-width="3"/>
<rect x="485" y="360" width="115" height="320" rx="10" fill="#76c69a" stroke="#287a4b" stroke-width="3"/>
<text class="t" x="327" y="408" text-anchor="middle" font-size="30">80</text><text class="t" x="542" y="344" text-anchor="middle" font-size="30">100</text>
<text class="s" x="327" y="720" text-anchor="middle" font-size="25">一月</text><text class="s" x="542" y="720" text-anchor="middle" font-size="25">二月</text>
<rect x="830" y="200" width="690" height="580" rx="28" fill="#f1eafa" stroke="#6846a5" stroke-width="3"/>
<text class="t" x="1175" y="250" text-anchor="middle" font-size="31">截断轴：视觉差异被放大</text>
<text class="s" x="880" y="320" font-size="24">单位：千件</text>
<line x1="920" y1="680" x2="1460" y2="680" stroke="#17365d" stroke-width="4"/><text class="s" x="865" y="690" font-size="23">70</text>
<line x1="920" y1="360" x2="1460" y2="360" stroke="#8ba4bd" stroke-width="2" stroke-dasharray="8 7"/><text class="s" x="860" y="370" font-size="23">100</text>
<rect x="1020" y="573.333" width="115" height="106.667" rx="10" fill="#77b3e8" stroke="#155b9a" stroke-width="3"/>
<rect x="1235" y="360" width="115" height="320" rx="10" fill="#76c69a" stroke="#287a4b" stroke-width="3"/>
<text class="t" x="1077" y="555" text-anchor="middle" font-size="30">80</text><text class="t" x="1292" y="344" text-anchor="middle" font-size="30">100</text>
<text class="s" x="1077" y="720" text-anchor="middle" font-size="25">一月</text><text class="s" x="1292" y="720" text-anchor="middle" font-size="25">二月</text>
<rect x="180" y="825" width="1240" height="70" rx="20" fill="#fff7c9" stroke="#9d7510" stroke-width="3"/>
<text class="t" x="800" y="869" text-anchor="middle" font-size="29" font-weight="700">相对增长 = (100 − 80) ÷ 80 = 25%　两张图相同</text>
</svg>
"""


def generate(root: Path) -> tuple[Path, ...]:
    root = Path(root)
    source_dir = root / "infographic" / "chapter17"
    image_dir = root / "book" / "images" / "chapter17"
    source_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    chart = image_dir / "01-chart-evidence.svg"
    chart.write_text(_chart_svg(), encoding="utf-8", newline="\n")
    outputs.append(chart)
    for scene in build_scenes():
        source = source_dir / f"{scene.stem}.tldr"
        image = image_dir / f"{scene.stem}.svg"
        source.write_text(json.dumps(_tldraw(scene), ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
        image.write_text(_svg(scene), encoding="utf-8", newline="\n")
        outputs.extend((source, image))
    return tuple(outputs)


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2]
    for path in generate(base):
        print(path.relative_to(base))
