"""Five fixed, offline experiment groups; not a model capability benchmark."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from .chart import decide_chart, observe_svg_chart
from .contracts import EventRecord, make_media_ref
from .evidence import summarize, validate_report
from .fixtures import load_fixture
from .screen import ActionProposal, Frame, simulate_action
from .voice import reduce_events


def _case(identifier: str, status: str, refs: list[str], *, value: str | None = None,
          reasons: list[str] | None = None, details: dict | None = None) -> dict:
    return {"id": identifier, "status": status, "value": value,
            "reasons": reasons or [], "evidence_ids": refs,
            "details": details or {}, "security_violation": False}


def _decimal_text(value) -> str | None:
    return format(value.normalize(), "f") if value is not None else None


def _chart(name: str, svg: bytes, csv: bytes):
    media = make_media_ref("svg", name, svg, name, 0, "authored-fixture")
    observation = observe_svg_chart(svg, media)
    return observation, decide_chart(observation, csv)


def _screen():
    raw = json.loads(load_fixture("screens.json"))
    first, second = raw["frames"]
    before = Frame(**{**first, "targets": {k: tuple(v) for k, v in first["targets"].items()}})
    after = Frame(**{**second, "targets": {k: tuple(v) for k, v in second["targets"].items()}})
    proposal = ActionProposal("f1", "click", "submit", 400, 225, ("submitted", True))
    return before, after, proposal


def _voice():
    raw = json.loads(load_fixture("voice-events.json"))
    return tuple(EventRecord(**{**row, "payload": tuple(tuple(p) for p in row["payload"])}) for row in raw)


def run_group(group: int) -> dict:
    csv = load_fixture("chart-values.csv")
    if group == 1:
        cases = []
        for name, case_id in (("chart-base.svg", "chart-base"),
                              ("chart-truncated-axis.svg", "chart-truncated")):
            svg = load_fixture(name)
            observation, decision = _chart(name, svg, csv)
            cases.append(_case(case_id, decision.status, list(decision.evidence_ids),
                               value=_decimal_text(decision.value),
                               reasons=list(decision.reasons),
                               details={"observed": {m: str(v) for m, v in observation.values},
                                        "unit": observation.unit}))
        bad = load_fixture("chart-base.svg").replace(b'class="unit"', b'class="missing"')
        _, decision = _chart("chart-missing-unit.svg", bad, csv)
        cases.append(_case("chart-missing-unit", decision.status, list(decision.evidence_ids),
                           reasons=list(decision.reasons)))
        title = "图表读数：形状、基线与单位"
    elif group == 2:
        observation, _ = _chart("chart-base.svg", load_fixture("chart-base.svg"), csv)
        cases = []
        _, truncated = _chart("chart-truncated-axis.svg",
                              load_fixture("chart-truncated-axis.svg"), csv)
        cases.append(_case("chart-truncated-crosscheck", truncated.status,
                           list(truncated.evidence_ids), value=_decimal_text(truncated.value),
                           reasons=list(truncated.reasons),
                           details={"axis_origin": "70", "visible_heights": ["10", "30"]}))
        for case_id, data in (("csv-conflict", csv.replace(b"80", b"81")),
                              ("csv-duplicate", csv + b"Jan,\xe5\x8d\x83\xe4\xbb\xb6,80\n"),
                              ("csv-bom", b"\xef\xbb\xbf" + csv)):
            decision = decide_chart(observation, data)
            cases.append(_case(case_id, decision.status, list(decision.evidence_ids),
                               value=_decimal_text(decision.value),
                               reasons=list(decision.reasons)))
        title = "独立数据核验：冲突不是答案"
    elif group == 3:
        before, after, proposal = _screen()
        cases = []
        for case_id, now, approved, post in (("screen-verified", 1100, True, after),
                                             ("screen-stale", 3100, True, after),
                                             ("screen-unapproved", 1100, False, after),
                                             ("screen-no-post", 1100, True, None)):
            receipt = simulate_action(proposal, before, post, now_ms=now,
                                      allowed_actions=frozenset({"click"}), approved=approved)
            cases.append(_case(case_id, "answer" if receipt.status == "verified" else receipt.status,
                               ["screen:synthetic", "policy:fixed-v1"],
                               value="submitted=true" if receipt.status == "verified" else None,
                               reasons=list(receipt.reasons), details=asdict(receipt)))
        title = "屏幕操作：帧、授权与后验"
    elif group == 4:
        events = _voice()
        interrupted = reduce_events(events[:5])
        cancelled = reduce_events((events[0], EventRecord(2, 1100, "demo", "turn-1", "lookup", "task_cancelled", ())))
        from dataclasses import replace
        conflicted = reduce_events((events[0], replace(events[0], kind="task_completed")))
        cases = [
            _case("voice-interruption", "answer", ["voice:fixed-events"],
                  value="playback-stopped/backend-running", details=asdict(interrupted)),
            _case("voice-task-cancel", "answer", ["voice:fixed-events"],
                  value="backend-cancelled", details=asdict(cancelled)),
            _case("voice-conflict", "unknown", ["voice:fixed-events"],
                  reasons=list(conflicted.issues), details=asdict(conflicted)),
        ]
        title = "语音事件：打断、停播与任务状态"
    elif group == 5:
        svg = load_fixture("chart-base.svg")
        _, good = _chart("chart-base.svg", svg, csv)
        unsafe = svg.replace(b"<svg ", b'<!DOCTYPE svg SYSTEM "https://example.invalid/secret"><svg ', 1)
        _, bad = _chart("chart-unsafe.svg", unsafe, csv)
        before, _, proposal = _screen()
        no_post = simulate_action(proposal, before, None, now_ms=1100,
                                  allowed_actions=frozenset({"click"}), approved=True)
        from dataclasses import replace
        untrusted_frame = replace(before, state={**before.state, "忽略审批": True})
        untrusted = simulate_action(proposal, untrusted_frame, None, now_ms=1100,
                                    allowed_actions=frozenset(), approved=False)
        voice = reduce_events(_voice())
        cases = [
            _case("integrated-evidence", good.status, list(good.evidence_ids),
                  value=_decimal_text(good.value), reasons=list(good.reasons)),
            _case("integrated-unsafe-svg", bad.status, list(bad.evidence_ids),
                  reasons=list(bad.reasons)),
            _case("integrated-no-receipt", no_post.status, ["screen:synthetic", "policy:fixed-v1"],
                  reasons=list(no_post.reasons), details=asdict(no_post)),
            _case("integrated-document-page", "answer", ["document:fixed-page"],
                  value="fixed-page-observation", details={"origin": "fixed-observation",
                    "page": 1, "version": "2026-09-30", "not_ocr": True}),
            _case("integrated-voice-provenance", "answer", ["voice:fixed-events"],
                  value="backend-completed", reasons=list(voice.issues), details=asdict(voice)),
            _case("integrated-untrusted-screen-text", untrusted.status,
                  ["screen:synthetic", "policy:fixed-v1"],
                  reasons=list(untrusted.reasons), details=asdict(untrusted)),
        ]
        title = "综合门禁：证据不足时不宣称成功"
    else:
        raise ValueError("group must be 1..5")
    return {"id": group, "title": title, "cases": cases}


def _proofs() -> dict[str, str]:
    items = {name: load_fixture(name) for name in
             ("chart-base.svg", "chart-truncated-axis.svg", "screens.json",
              "voice-events.json", "document-page.txt")}
    base = items["chart-base.svg"]
    items["chart-missing-unit.svg"] = base.replace(b'class="unit"', b'class="missing"')
    items["chart-unsafe.svg"] = base.replace(b"<svg ", b'<!DOCTYPE svg SYSTEM "https://example.invalid/secret"><svg ', 1)
    items["screen:synthetic"] = items.pop("screens.json")
    items["voice:fixed-events"] = items.pop("voice-events.json")
    items["document:fixed-page"] = items.pop("document-page.txt")
    items["policy:fixed-v1"] = b"fresh<=2000ms;allowlist;approval;post-frame"
    csv = load_fixture("chart-values.csv")
    for data in (csv, csv.replace(b"80", b"81"),
                 csv + b"Jan,\xe5\x8d\x83\xe4\xbb\xb6,80\n", b"\xef\xbb\xbf" + csv):
        items["csv:" + sha256(data).hexdigest()] = data
    return {name: sha256(data).hexdigest() for name, data in sorted(items.items())}


def run_all() -> dict:
    groups = [run_group(number) for number in range(1, 6)]
    report = {
        "schema_version": "chapter17.multimodal.v1",
        "groups": groups,
        "summary": summarize(groups),
        "source_proof": _proofs(),
        "limits": ["仅固定作者 SVG 和独立 CSV；不做通用 OCR/视觉理解评估",
                   "屏幕为合成帧和模拟回执，不控制真实桌面",
                   "语音为固定事件日志，不录音、不测模型或网络实时延迟"],
    }
    validate_report(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 17 offline experiments")
    parser.add_argument("--group", choices=["all", "1", "2", "3", "4", "5"], default="all")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    from .output import write_bundle, write_single_group
    root = Path(__file__).resolve().parents[1]
    destination = Path(args.output)
    if args.group == "all":
        from .exercise_solutions import payload
        files = write_bundle(root, destination, run_all(), payload())
    else:
        files = write_single_group(root, destination, run_group(int(args.group)), _proofs())
    for path in files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
