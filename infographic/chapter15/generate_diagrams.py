"""Generate seven Chapter 15 diagrams from shared editable scene models."""
from __future__ import annotations

import json
from pathlib import Path

from infographic.chapter14.generate_diagrams import (
    Edge,
    HEIGHT,
    Node,
    Scene,
    WIDTH,
    _svg,
    _tldraw,
)


APPROVED_DIAGRAMS = (
    ("01-intervention-tree", "干预决策树：先修哪一层"),
    ("02-trajectory-data-factory", "轨迹数据工厂：从运行证据到训练样本"),
    ("03-objective-map", "三类目标地图：SFT、偏好优化与 RL"),
    ("04-sft-probability-shift", "SFT 概率变化：示范会被复制"),
    ("05-dpo-preference-pair", "DPO 偏好对：扩大同状态下的相对间隔"),
    ("06-reward-hacking", "奖励投机现场：高回报不能购买安全"),
    ("07-training-release-loop", "训练—评测—发布闭环"),
)


def _intervention_tree() -> Scene:
    nodes = (
        Node("failure", "1 观察失败\n先固定证据", 80, 350, 230, 130, "red"),
        Node("facts", "2 缺事实？\nRAG / Context", 390, 180, 250, 120, "blue"),
        Node("boundary", "3 可确定阻断？\nHarness", 390, 360, 250, 120, "orange"),
        Node("instruction", "4 指令含糊？\nPrompt / Skill", 390, 540, 250, 120, "green"),
        Node("capacity", "5 能力缺口？\nModel Route", 790, 250, 270, 130, "violet"),
        Node("repeat", "6 跨任务重复？\n可复用监督？", 790, 500, 270, 130, "yellow", "diamond"),
        Node("train", "7 Post-training\n最后的可验证选项", 1210, 370, 300, 150, "red", "check-box"),
    )
    edges = (
        Edge("e1", "failure", "facts", "反事实 1"),
        Edge("e2", "failure", "boundary", "反事实 2"),
        Edge("e3", "failure", "instruction", "反事实 3"),
        Edge("e4", "facts", "capacity", "事实已完整"),
        Edge("e5", "boundary", "capacity", "边界已正确"),
        Edge("e6", "instruction", "repeat", "指令已澄清"),
        Edge("e7", "capacity", "repeat", "能力足够"),
        Edge("e8", "repeat", "train", "证据齐全", "red"),
    )
    return Scene(
        APPROVED_DIAGRAMS[0][0], APPROVED_DIAGRAMS[0][1],
        "从最小、最可验证的干预开始；证据不足时返回 inconclusive。",
        nodes, edges,
        "后训练不是失败的默认答案，而是上游解释被排除后的工程选择。",
    )


def _data_factory() -> Scene:
    nodes = (
        Node("trace", "1 Raw Trace\n结果 + 过程 + 来源", 70, 350, 230, 140, "blue"),
        Node("normalize", "2 Normalize\n结构与状态对齐", 360, 220, 250, 120, "green"),
        Node("redact", "3 Redact\n凭据与身份脱敏", 360, 510, 250, 120, "violet"),
        Node("audit", "4 Audit\n回执 · 越界 · 隐藏答案", 700, 340, 300, 150, "orange"),
        Node("dedupe", "5 Dedupe\n精确 + 语义家族", 1080, 190, 250, 120, "yellow"),
        Node("split", "6 Split\nTrain / Val / Eval", 1080, 510, 250, 120, "blue"),
        Node("samples", "7 Samples\nSFT / Preference / Reward", 1380, 350, 180, 150, "green", "check-box"),
    )
    edges = (
        Edge("e1", "trace", "normalize"), Edge("e2", "trace", "redact"),
        Edge("e3", "normalize", "audit"), Edge("e4", "redact", "audit"),
        Edge("e5", "audit", "dedupe"), Edge("e6", "audit", "split"),
        Edge("e7", "dedupe", "samples"), Edge("e8", "split", "samples"),
    )
    return Scene(
        APPROVED_DIAGRAMS[1][0], APPROVED_DIAGRAMS[1][1],
        "先保留 provenance，再脱敏、审计、去重和隔离评测集。",
        nodes, edges,
        "成功轨迹不自动等于好训练数据；任何安全或泄漏发现都先隔离。",
    )


def _objective_map() -> Scene:
    nodes = (
        Node("question", "1 想改变什么行为？", 90, 370, 270, 120, "red", "diamond"),
        Node("sft", "2 SFT\n输入：目标动作\n更新：模仿概率", 500, 180, 270, 170, "blue"),
        Node("dpo", "3 Preference\n输入：chosen / rejected\n更新：相对间隔", 500, 400, 270, 170, "violet"),
        Node("rl", "4 RL\n输入：环境回报\n更新：策略回报", 500, 620, 270, 170, "orange"),
        Node("sft_risk", "5 风险\n复制坏示范\n状态覆盖不足", 1000, 190, 280, 150, "yellow"),
        Node("dpo_risk", "6 风险\n伪偏好 · 跨状态配对", 1000, 420, 280, 140, "yellow"),
        Node("rl_risk", "7 风险\n奖励投机 · 信用错配", 1000, 640, 280, 140, "red"),
        Node("eval", "8 冻结评测 + 安全门禁", 1320, 390, 240, 150, "green", "check-box"),
    )
    edges = (
        Edge("e1", "question", "sft"), Edge("e2", "question", "dpo"), Edge("e3", "question", "rl"),
        Edge("e4", "sft", "sft_risk"), Edge("e5", "dpo", "dpo_risk"), Edge("e6", "rl", "rl_risk"),
        Edge("e7", "sft_risk", "eval"), Edge("e8", "dpo_risk", "eval"), Edge("e9", "rl_risk", "eval"),
    )
    return Scene(
        APPROVED_DIAGRAMS[2][0], APPROVED_DIAGRAMS[2][1],
        "三类目标使用不同监督信号，但都不能替代独立验收。",
        nodes, edges,
        "目标函数决定模型被鼓励成为什么；评测与门禁决定它是否可以发布。",
    )


def _sft_shift() -> Scene:
    nodes = (
        Node("state", "1 State\nwrite_requested", 80, 350, 250, 130, "blue"),
        Node("clean", "2 干净示范\nTarget = read", 420, 190, 260, 130, "green"),
        Node("bad", "3 污染示范\nTarget = modify_tests", 420, 520, 260, 130, "red"),
        Node("ce", "4 Cross Entropy\n提高目标动作概率", 800, 350, 300, 150, "violet"),
        Node("read_up", "5 P(read) ↑\n安全信息先补齐", 1190, 200, 280, 130, "green", "check-box"),
        Node("hack_up", "6 P(modify_tests) ↑\n捷径同样被复制", 1190, 530, 280, 130, "red", "x-box"),
    )
    edges = (
        Edge("e1", "state", "clean"), Edge("e2", "state", "bad"),
        Edge("e3", "clean", "ce"), Edge("e4", "bad", "ce"),
        Edge("e5", "ce", "read_up", "好数据"), Edge("e6", "ce", "hack_up", "坏数据", "red"),
    )
    return Scene(
        APPROVED_DIAGRAMS[3][0], APPROVED_DIAGRAMS[3][1],
        "同一个损失函数不会知道示范是否符合安全意图。",
        nodes, edges,
        "SFT 忠实复制被保留的示范：数据审计不是训练前的可选清洁步骤。",
    )


def _dpo_pair() -> Scene:
    nodes = (
        Node("state", "1 同一 State\nwrite_requested", 80, 350, 250, 130, "blue"),
        Node("chosen", "2 Chosen\nread\nlog π = -0.8", 420, 180, 250, 150, "green"),
        Node("rejected", "3 Rejected\nmodify_tests\nlog π = -1.2", 420, 530, 250, 150, "red"),
        Node("reference", "4 Reference\n间隔 = 0.1", 790, 180, 260, 130, "yellow"),
        Node("candidate", "5 Candidate\n间隔 = 0.4", 790, 530, 260, 130, "violet"),
        Node("margin", "6 β = 0.5\nDPO margin = 0.15", 1160, 260, 300, 140, "orange"),
        Node("loss", "7 Loss ≈ 0.620957\n扩大相对偏好", 1160, 520, 300, 140, "green", "check-box"),
    )
    edges = (
        Edge("e1", "state", "chosen"), Edge("e2", "state", "rejected"),
        Edge("e3", "chosen", "reference"), Edge("e4", "rejected", "candidate"),
        Edge("e5", "reference", "margin"), Edge("e6", "candidate", "margin"),
        Edge("e7", "margin", "loss"),
    )
    return Scene(
        APPROVED_DIAGRAMS[4][0], APPROVED_DIAGRAMS[4][1],
        "偏好比较必须来自同一状态，参考策略用于衡量相对漂移。",
        nodes, edges,
        "DPO 不是给回答打绝对分，而是扩大 chosen 相对 rejected 的改进间隔。",
    )


def _reward_hacking() -> Scene:
    nodes = (
        Node("task", "1 任务\n修复失败测试", 70, 350, 230, 130, "blue"),
        Node("safe", "2 安全路径\n改代码 · 4 步\nReward = +6", 390, 180, 270, 160, "green"),
        Node("shortcut", "3 捷径\n改测试 · 1 步\nReward = +10", 390, 520, 270, 160, "red"),
        Node("penalty", "4 标量惩罚\n+10 − 3 = +7", 780, 520, 270, 140, "orange"),
        Node("ranking", "5 错误排序\n捷径 +7 > 安全 +6", 1150, 500, 310, 150, "red", "x-box"),
        Node("gate", "6 Safety Veto\n违规动作不可接受", 780, 180, 270, 140, "violet"),
        Node("release", "7 发布候选\nOutcome 通过 + Safety 通过", 1150, 180, 310, 150, "green", "check-box"),
    )
    edges = (
        Edge("e1", "task", "safe"), Edge("e2", "task", "shortcut"),
        Edge("e3", "safe", "gate"), Edge("e4", "shortcut", "penalty", "可抵消", "red"),
        Edge("e5", "penalty", "ranking", "+7", "red"),
        Edge("e6", "gate", "release", "不可抵消", "green"),
        Edge("e7", "ranking", "release", "拒绝", "red", "dashed"),
    )
    return Scene(
        APPROVED_DIAGRAMS[5][0], APPROVED_DIAGRAMS[5][1],
        "标量奖励会相互抵消；硬门禁表达不可交易的约束。",
        nodes, edges,
        "安全不是总分中的一项：任务奖励再高，也不能购买一次受保护文件写入。",
    )


def _training_loop() -> Scene:
    nodes = (
        Node("version", "1 Data Version\n来源 · 许可 · 切分", 80, 300, 250, 140, "blue"),
        Node("train", "2 Train Candidate\nSFT / Preference / RL", 410, 180, 280, 150, "violet"),
        Node("eval", "3 Frozen Eval\n能力 + 回归切片", 790, 170, 270, 140, "green"),
        Node("gate", "4 Safety Gate\n零违规 · 零污染", 1170, 270, 270, 140, "orange", "diamond"),
        Node("canary", "5 Canary\n小流量 + 可观测", 1130, 570, 260, 130, "yellow"),
        Node("release", "6 Release\n版本与证据绑定", 730, 650, 270, 130, "green", "check-box"),
        Node("rollback", "7 Rollback\n恢复模型与 Harness", 300, 590, 290, 140, "red"),
    )
    edges = (
        Edge("e1", "version", "train"), Edge("e2", "train", "eval"),
        Edge("e3", "eval", "gate"), Edge("e4", "gate", "canary"),
        Edge("e5", "canary", "release"), Edge("e6", "release", "rollback", "异常", "red", "dashed"),
        Edge("e7", "rollback", "version", "新数据回流", "violet", "dashed"),
    )
    return Scene(
        APPROVED_DIAGRAMS[6][0], APPROVED_DIAGRAMS[6][1],
        "候选策略只有与数据、评测、门禁和回滚证据绑定，才是可发布系统。",
        nodes, edges,
        "后训练不是一次离线作业，而是数据—训练—评测—灰度—回滚的版本化闭环。",
    )


SCENES = (
    _intervention_tree(),
    _data_factory(),
    _objective_map(),
    _sft_shift(),
    _dpo_pair(),
    _reward_hacking(),
    _training_loop(),
)


def generate_all(output_root: Path, source_root: Path) -> tuple[Path, ...]:
    """Write editable Tldraw sources and self-contained SVG renders."""

    output_root = Path(output_root)
    source_root = Path(source_root)
    output_root.mkdir(parents=True, exist_ok=True)
    source_root.mkdir(parents=True, exist_ok=True)
    renders: list[Path] = []
    for scene in SCENES:
        source = source_root / f"{scene.stem}.tldr"
        render = output_root / f"{scene.stem}.svg"
        source.write_text(
            json.dumps(_tldraw(scene), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        render.write_text(_svg(scene), encoding="utf-8", newline="\n")
        renders.append(render)
    return tuple(renders)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    source_root = Path(__file__).resolve().parent
    for render in generate_all(root / "book" / "images" / "chapter15", source_root):
        print(f"{source_root.relative_to(root) / (render.stem + '.tldr')} -> {render.relative_to(root)}")
