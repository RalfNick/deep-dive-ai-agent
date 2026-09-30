"""Deterministic answer checks for the thirteen Chapter 17 exercises."""

from __future__ import annotations

import argparse
from decimal import Decimal
import os
from pathlib import Path

from .contracts import EventRecord
from .output import _is_reparse, canonical_json
from .voice import reduce_events


def payload() -> dict:
    old, new, floor = Decimal(80), Decimal(100), Decimal(70)
    growth = (new - old) / old * 100
    exposed = ((new - floor) - (old - floor)) / (old - floor) * 100
    events = (
        EventRecord(1, 10, "s", "t", "task", "task_started", ()),
        EventRecord(2, 20, "s", "t", "task", "speech_started", ()),
        EventRecord(3, 30, "s", "t", "task", "response_cancelled", ()),
        EventRecord(4, 40, "s", "t", "task", "playback_stopped", ()),
        EventRecord(5, 50, "s", "t", "task", "conversation_truncated", ()),
    )
    state = reduce_events(events)
    items = [
        ("来源/观察/决策", "三层分开，最终回复不可代替来源和读数", {}),
        ("增长率", "20 千件；25% 相对增长；二月为一月的 125%", {
            "absolute_increase_thousand": "20", "relative_growth_percent": format(growth.normalize(), "f"),
            "new_as_percent_of_old": "125"}),
        ("截断轴", "露出高度误算 200%；业务值真实增长 25%", {
            "truncated_visual_growth_percent": format(exposed.normalize(), "f"),
            "actual_growth_percent": format(growth.normalize(), "f")}),
        ("图/CSV 冲突", "图 Jan 80、CSV Jan 81 应 unknown，保留两来源", {}),
        ("未知 SVG", "不支持的 transform/双轴等返回 unknown，不猜数值", {}),
        ("非等比坐标", "x=1.5 倍，y=2 倍；新点为 (600,450)", {
            "uniform_display_xy": [800, 450], "nonuniform_display_xy": [600, 450]}),
        ("旧帧", "提议 f1 与当前 f-new 不符，应 refresh、无执行", {}),
        ("屏幕伪指令", "画面/OCR 是低信任材料，不能扩大 allowlist 或审批", {}),
        ("缺后验", "executed=true 而 status=unknown；先查服务端幂等回执", {}),
        ("语音排序", "已停播、已截断、后台仍运行", {
            "playback": state.playback, "conversation_tail": state.conversation_tail,
            "backend_task": state.backend_task}),
        ("重复和晚到", "同内容幂等；已提交副作用保留；晚到取消不覆盖完成", {}),
        ("真实评估", "至少覆盖读图、单位、帧、越权、停播和后台六类反例", {}),
        ("系统取舍", "可信数据库优先；解释截图须看截图；中断播报不冒称任务取消", {}),
    ]
    return {"schema_version": "chapter17.exercises.v1", "answers": [
        {"number": index, "topic": topic, "criterion": criterion, "computed": computed}
        for index, (topic, criterion, computed) in enumerate(items, 1)]}


def _write(root: Path, destination: Path, data: dict) -> Path:
    root = Path(os.path.abspath(root))
    raw = destination if destination.is_absolute() else root / destination
    if ".." in raw.parts:
        raise ValueError("parent traversal denied")
    path = Path(os.path.abspath(raw))
    try:
        rel = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("answer path outside repository") from exc
    if len(rel.parts) < 3 or rel.parts[:2] != ("chapter17", ".runs") or path.suffix != ".json":
        raise ValueError("answers must be JSON under chapter17/.runs")
    for candidate in (path, *path.parents):
        if _is_reparse(candidate):
            raise ValueError("linked answer path denied")
        if candidate == root:
            break
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_json(data))
    return path


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 17 deterministic exercise answers")
    parser.add_argument("--all", action="store_true", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    base = Path(__file__).resolve().parents[1] if root is None else Path(root)
    print(_write(base, Path(args.output), payload()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
