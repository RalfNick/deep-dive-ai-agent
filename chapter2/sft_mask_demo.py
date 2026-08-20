"""用一个可手算的对话展示 SFT 的移位标签与 assistant-only loss。"""

from __future__ import annotations

import math
from dataclasses import dataclass


IGNORE_INDEX = -100


@dataclass(frozen=True)
class Token:
    token_id: int
    text: str
    role: str


TOKENS = [
    Token(10, "<user>", "user"),
    Token(11, "修复", "user"),
    Token(12, "价格", "user"),
    Token(13, "<assistant>", "assistant"),
    Token(14, "先", "assistant"),
    Token(15, "运行", "assistant"),
    Token(16, "测试", "assistant"),
    Token(17, "<eos>", "assistant"),
]

# 这个教学模板把 <assistant> 起始标记视为回答的一部分，因此预测它时会计入
# assistant-only loss。真实训练框架可能选择遮罩该标记；关键是训练与部署模板一致。
ASSISTANT_START_IS_TARGET = True

# 模拟模型在每个预测位置分配给正确下一 Token 的概率。
TARGET_PROBABILITIES = [0.90, 0.62, 0.41, 0.72, 0.55, 0.80, 0.67]


def build_training_rows(assistant_only: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for position, (current, target, probability) in enumerate(
        zip(TOKENS[:-1], TOKENS[1:], TARGET_PROBABILITIES)
    ):
        label = target.token_id
        # 只有目标 Token 属于 assistant 回答时，才计入 assistant-only loss。
        if assistant_only and target.role != "assistant":
            label = IGNORE_INDEX
        rows.append(
            {
                "position": position,
                "input": current.text,
                "target": target.text,
                "role": target.role,
                "label": label,
                "p(target)": probability,
                "loss": None if label == IGNORE_INDEX else -math.log(probability),
            }
        )
    return rows


def mean_loss(rows: list[dict[str, object]]) -> float:
    losses = [float(row["loss"]) for row in rows if row["loss"] is not None]
    return sum(losses) / len(losses)


def print_rows(title: str, rows: list[dict[str, object]]) -> None:
    print(f"\n{title}")
    print("pos input         -> target        role       label  loss")
    print("--- -------------    ------------- ---------- ------ ------")
    for row in rows:
        label = "MASK" if row["label"] == IGNORE_INDEX else str(row["label"])
        loss = "  -  " if row["loss"] is None else f"{float(row['loss']):.3f}"
        print(
            f"{row['position']:>3} {row['input']:<13} -> "
            f"{row['target']:<13} {row['role']:<10} {label:>6} {loss:>6}"
        )
    print(f"有效位置数: {sum(row['loss'] is not None for row in rows)}")
    print(f"平均交叉熵: {mean_loss(rows):.3f}")


def main() -> None:
    all_token_rows = build_training_rows(assistant_only=False)
    assistant_rows = build_training_rows(assistant_only=True)
    print_rows("方案 A：所有 Token 都计算损失", all_token_rows)
    print_rows("方案 B：只对 assistant 目标计算损失", assistant_rows)
    print("\n观察：两种方案使用同一段对话，但优化目标并不相同。")
    print(f"模板选择：<assistant> 是否作为训练目标 = {ASSISTANT_START_IS_TARGET}")
    print("边界：这个玩具表只解释标签遮罩，不代表真实模型的训练质量。")


if __name__ == "__main__":
    main()
