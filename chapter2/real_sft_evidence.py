"""训练两个微型神经语言模型，记录预训练、SFT 与保留集曲线。

这是可重复的教学实验，不是开放权重大模型或生产微调基准。模型是一个
固定上下文的字符级因果 MLP，真正执行梯度下降与 assistant-only SFT。
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


SEED = 20_260_809
CONTEXT = 12
PAD = "¤"

PRETRAIN_LINES = (
    "模型根据前文预测下一个字符。",
    "代码修改前应读取实现并运行测试。",
    "测试失败提供证据，测试通过不代表没有隐藏错误。",
    "工具扩大行动能力，权限限制行动边界。",
    "结构合法不等于语义正确，执行前还要检查策略。",
    "价格解析应该保留旧行为并覆盖人民币符号。",
    "解释问题时先给结论，再给证据和边界。",
    "危险操作需要外部授权，模型不能批准自己。",
)

RETAIN_TEXT = "\n".join(
    (
        "语言模型学习条件概率分布。",
        "验证集用于观察未参与更新的数据。",
        "可靠系统记录输入输出成本和延迟。",
        "上下文变化不会自动更新模型权重。",
    )
)

SFT_TRAIN = (
    ("任务=修复价格；动作：", "测试"),
    ("任务=修复日期；动作：", "测试"),
    ("任务=修改解析；动作：", "测试"),
    ("任务=排查回归；动作：", "测试"),
    ("任务=解释概念；动作：", "回答"),
    ("任务=总结日志；动作：", "回答"),
    ("任务=比较方案；动作：", "回答"),
    ("任务=说明边界；动作：", "回答"),
    ("任务=删除系统；动作：", "拒绝"),
    ("任务=导出密钥；动作：", "拒绝"),
    ("任务=绕过审批；动作：", "拒绝"),
    ("任务=访问越界；动作：", "拒绝"),
)

SFT_VALID = (
    ("任务=修复货币；动作：", "测试"),
    ("任务=检查缺陷；动作：", "测试"),
    ("任务=解释公式；动作：", "回答"),
    ("任务=归纳结果；动作：", "回答"),
    ("任务=泄露密码；动作：", "拒绝"),
    ("任务=跳过授权；动作：", "拒绝"),
)


@dataclass(frozen=True)
class ModelConfig:
    name: str
    embedding: int
    hidden: int


CONFIGS = (
    ModelConfig("micro-11k", embedding=8, hidden=32),
    ModelConfig("micro-40k", embedding=16, hidden=96),
)


class CausalMLP:
    def __init__(self, vocab_size: int, config: ModelConfig, rng: np.random.Generator):
        scale = 0.08
        self.params = {
            "embedding": rng.normal(0, scale, (vocab_size, config.embedding)),
            "w1": rng.normal(0, scale, (CONTEXT * config.embedding, config.hidden)),
            "b1": np.zeros(config.hidden),
            "w2": rng.normal(0, scale, (config.hidden, vocab_size)),
            "b2": np.zeros(vocab_size),
        }
        self.m = {name: np.zeros_like(value) for name, value in self.params.items()}
        self.v = {name: np.zeros_like(value) for name, value in self.params.items()}
        self.adam_step = 0

    @property
    def parameter_count(self) -> int:
        return sum(value.size for value in self.params.values())

    def loss_and_grads(
        self, inputs: np.ndarray, targets: np.ndarray, with_grads: bool
    ) -> tuple[float, dict[str, np.ndarray] | None]:
        embedding = self.params["embedding"][inputs]
        flat = embedding.reshape(inputs.shape[0], -1)
        hidden_pre = flat @ self.params["w1"] + self.params["b1"]
        hidden = np.tanh(hidden_pre)
        logits = hidden @ self.params["w2"] + self.params["b2"]
        logits -= logits.max(axis=1, keepdims=True)
        exp = np.exp(logits)
        probabilities = exp / exp.sum(axis=1, keepdims=True)
        loss = -np.log(probabilities[np.arange(len(targets)), targets] + 1e-12).mean()
        if not with_grads:
            return float(loss), None

        d_logits = probabilities
        d_logits[np.arange(len(targets)), targets] -= 1
        d_logits /= len(targets)
        grads: dict[str, np.ndarray] = {}
        grads["w2"] = hidden.T @ d_logits
        grads["b2"] = d_logits.sum(axis=0)
        d_hidden = (d_logits @ self.params["w2"].T) * (1 - hidden * hidden)
        grads["w1"] = flat.T @ d_hidden
        grads["b1"] = d_hidden.sum(axis=0)
        d_embedding = (d_hidden @ self.params["w1"].T).reshape(embedding.shape)
        grads["embedding"] = np.zeros_like(self.params["embedding"])
        np.add.at(
            grads["embedding"],
            inputs.reshape(-1),
            d_embedding.reshape(-1, d_embedding.shape[-1]),
        )
        return float(loss), grads

    def update(self, grads: dict[str, np.ndarray], learning_rate: float) -> None:
        norm = float(np.sqrt(sum(np.sum(grad * grad) for grad in grads.values())))
        scale = min(1.0, 5.0 / (norm + 1e-12))
        self.adam_step += 1
        for name, grad in grads.items():
            grad = grad * scale
            self.m[name] = 0.9 * self.m[name] + 0.1 * grad
            self.v[name] = 0.999 * self.v[name] + 0.001 * (grad * grad)
            m_hat = self.m[name] / (1 - 0.9**self.adam_step)
            v_hat = self.v[name] / (1 - 0.999**self.adam_step)
            self.params[name] -= learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8)

    def predict(self, inputs: np.ndarray) -> np.ndarray:
        embedding = self.params["embedding"][inputs].reshape(inputs.shape[0], -1)
        hidden = np.tanh(embedding @ self.params["w1"] + self.params["b1"])
        return hidden @ self.params["w2"] + self.params["b2"]


def vocabulary() -> tuple[dict[str, int], list[str]]:
    all_text = "\n".join(PRETRAIN_LINES) + RETAIN_TEXT
    all_text += "".join(prompt + response for prompt, response in SFT_TRAIN + SFT_VALID)
    characters = [PAD] + sorted(set(all_text))
    return {char: index for index, char in enumerate(characters)}, characters


def contexts_for_text(text: str, char_to_id: dict[str, int]) -> tuple[np.ndarray, np.ndarray]:
    prefix = PAD * CONTEXT
    sequence = prefix + text
    inputs: list[list[int]] = []
    targets: list[int] = []
    for position in range(CONTEXT, len(sequence)):
        inputs.append([char_to_id[char] for char in sequence[position - CONTEXT : position]])
        targets.append(char_to_id[sequence[position]])
    return np.asarray(inputs, dtype=np.int64), np.asarray(targets, dtype=np.int64)


def assistant_only_dataset(
    pairs: tuple[tuple[str, str], ...], char_to_id: dict[str, int]
) -> tuple[np.ndarray, np.ndarray]:
    inputs: list[list[int]] = []
    targets: list[int] = []
    for prompt, response in pairs:
        sequence = PAD * CONTEXT + prompt + response
        response_start = CONTEXT + len(prompt)
        for position in range(response_start, len(sequence)):
            inputs.append(
                [char_to_id[char] for char in sequence[position - CONTEXT : position]]
            )
            targets.append(char_to_id[sequence[position]])
    return np.asarray(inputs, dtype=np.int64), np.asarray(targets, dtype=np.int64)


def evaluate_loss(model: CausalMLP, data: tuple[np.ndarray, np.ndarray]) -> float:
    return model.loss_and_grads(*data, with_grads=False)[0]


def generate(
    model: CausalMLP,
    prompt: str,
    length: int,
    char_to_id: dict[str, int],
    id_to_char: list[str],
) -> str:
    text = PAD * CONTEXT + prompt
    result: list[str] = []
    for _ in range(length):
        context = np.asarray(
            [[char_to_id[char] for char in text[-CONTEXT:]]], dtype=np.int64
        )
        next_char = id_to_char[int(model.predict(context).argmax(axis=1)[0])]
        result.append(next_char)
        text += next_char
    return "".join(result)


def task_success(
    model: CausalMLP,
    pairs: tuple[tuple[str, str], ...],
    char_to_id: dict[str, int],
    id_to_char: list[str],
) -> tuple[float, list[tuple[str, str, str]]]:
    rows = []
    for prompt, expected in pairs:
        actual = generate(model, prompt, len(expected), char_to_id, id_to_char)
        rows.append((prompt, expected, actual))
    success = sum(expected == actual for _, expected, actual in rows) / len(rows)
    return success, rows


def train(
    model: CausalMLP,
    train_data: tuple[np.ndarray, np.ndarray],
    steps: int,
    batch_size: int,
    learning_rate: float,
    rng: np.random.Generator,
    callback,
) -> None:
    inputs, targets = train_data
    for step in range(1, steps + 1):
        indices = rng.integers(0, len(targets), size=min(batch_size, len(targets)))
        _, grads = model.loss_and_grads(inputs[indices], targets[indices], with_grads=True)
        assert grads is not None
        model.update(grads, learning_rate)
        if step == 1 or step % 10 == 0 or step == steps:
            callback(step)


def svg_polyline(
    points: list[tuple[int, float]],
    x: int,
    y: int,
    width: int,
    height: int,
    max_step: int,
    min_value: float,
    max_value: float,
) -> str:
    coordinates = []
    for step, value in points:
        px = x + (step / max_step) * width
        ratio = (value - min_value) / max(max_value - min_value, 1e-9)
        py = y + height - ratio * height
        coordinates.append(f"{px:.1f},{py:.1f}")
    return " ".join(coordinates)


def write_svg(curves: dict[str, dict[str, list[tuple[int, float]]]], output: Path) -> None:
    width, height = 1080, 520
    panels = ((70, 80, 430, 330, "预训练：验证损失"), (600, 80, 430, 330, "SFT：目标集与保留集损失"))
    colors = {"micro-11k": "#3157d5", "micro-40k": "#e16a3d"}
    all_pre = [value for model in curves.values() for _, value in model["pretrain"]]
    all_sft = [
        value
        for model in curves.values()
        for metric in ("target", "retain")
        for _, value in model[metric]
    ]
    ranges = ((min(all_pre) * 0.9, max(all_pre) * 1.05), (min(all_sft) * 0.9, max(all_sft) * 1.05))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1080" height="520" rx="24" fill="#f8fafc"/>',
        '<text x="54" y="42" font-family="Microsoft YaHei, sans-serif" font-size="22" font-weight="700" fill="#172033">真实梯度实验：两个微型因果语言模型</text>',
    ]
    for panel_index, (x, y, panel_width, panel_height, title) in enumerate(panels):
        min_value, max_value = ranges[panel_index]
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="{panel_width}" height="{panel_height}" rx="12" fill="#ffffff" stroke="#d8e0ea"/>',
                f'<text x="{x + 14}" y="{y + 28}" font-family="Microsoft YaHei, sans-serif" font-size="17" font-weight="700" fill="#20345d">{title}</text>',
                f'<line x1="{x + 48}" y1="{y + 50}" x2="{x + 48}" y2="{y + panel_height - 36}" stroke="#718096"/>',
                f'<line x1="{x + 48}" y1="{y + panel_height - 36}" x2="{x + panel_width - 16}" y2="{y + panel_height - 36}" stroke="#718096"/>',
                f'<text x="{x + 5}" y="{y + 60}" font-family="Consolas" font-size="12" fill="#718096">{max_value:.2f}</text>',
                f'<text x="{x + 5}" y="{y + panel_height - 32}" font-family="Consolas" font-size="12" fill="#718096">{min_value:.2f}</text>',
                f'<text x="{x + panel_width - 48}" y="{y + panel_height - 14}" font-family="Microsoft YaHei, sans-serif" font-size="12" fill="#718096">step</text>',
            ]
        )
        for model_name, model_curves in curves.items():
            metrics = ("pretrain",) if panel_index == 0 else ("target", "retain")
            for metric in metrics:
                points = model_curves[metric]
                dash = ' stroke-dasharray="8 6"' if metric == "retain" else ""
                polyline = svg_polyline(
                    points,
                    x + 48,
                    y + 50,
                    panel_width - 64,
                    panel_height - 86,
                    max(step for step, _ in points),
                    min_value,
                    max_value,
                )
                parts.append(
                    f'<polyline points="{polyline}" fill="none" stroke="{colors[model_name]}" stroke-width="3"{dash}/>'
                )
    parts.extend(
        [
            '<line x1="75" y1="454" x2="112" y2="454" stroke="#3157d5" stroke-width="3"/><text x="120" y="459" font-family="Microsoft YaHei, sans-serif" font-size="14" fill="#334155">micro-11k</text>',
            '<line x1="225" y1="454" x2="262" y2="454" stroke="#e16a3d" stroke-width="3"/><text x="270" y="459" font-family="Microsoft YaHei, sans-serif" font-size="14" fill="#334155">micro-40k</text>',
            '<line x1="430" y1="454" x2="467" y2="454" stroke="#718096" stroke-width="3"/><text x="475" y="459" font-family="Microsoft YaHei, sans-serif" font-size="14" fill="#334155">实线：目标/验证</text>',
            '<line x1="655" y1="454" x2="692" y2="454" stroke="#718096" stroke-width="3" stroke-dasharray="8 6"/><text x="700" y="459" font-family="Microsoft YaHei, sans-serif" font-size="14" fill="#334155">虚线：保留集</text>',
            '<text x="54" y="495" font-family="Microsoft YaHei, sans-serif" font-size="13" fill="#5d6b82">固定 seed；字符级因果 MLP；曲线只证明本实验中的优化与遗忘，不代表大模型规模结论。</text>',
            "</svg>",
        ]
    )
    output.write_text("\n".join(parts), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-artifacts", action="store_true", help="只打印结果，不写 CSV/JSON/SVG")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    char_to_id, id_to_char = vocabulary()
    # 保留集来自同一通用分布，但不参加 SFT；这样可以观察窄域更新是否损伤旧分布。
    general_lines = PRETRAIN_LINES + tuple(RETAIN_TEXT.splitlines())
    pretrain_text = "\n".join(general_lines * 32)
    split = int(len(pretrain_text) * 0.82)
    pretrain_train = contexts_for_text(pretrain_text[:split], char_to_id)
    pretrain_valid = contexts_for_text(pretrain_text[split:], char_to_id)
    retain_data = contexts_for_text(RETAIN_TEXT, char_to_id)
    sft_train = assistant_only_dataset(SFT_TRAIN, char_to_id)
    sft_valid = assistant_only_dataset(SFT_VALID, char_to_id)

    curves: dict[str, dict[str, list[tuple[int, float]]]] = {}
    summaries: list[dict[str, float | int | str]] = []
    prediction_rows: list[dict[str, str]] = []

    for config_index, config in enumerate(CONFIGS):
        rng = np.random.default_rng(SEED + config_index)
        model = CausalMLP(len(id_to_char), config, rng)
        curves[config.name] = {"pretrain": [], "target": [], "retain": []}

        curves[config.name]["pretrain"].append((0, evaluate_loss(model, pretrain_valid)))
        train(
            model,
            pretrain_train,
            steps=180,
            batch_size=96,
            learning_rate=0.012,
            rng=rng,
            callback=lambda step, m=model, n=config.name: curves[n]["pretrain"].append(
                (step, evaluate_loss(m, pretrain_valid))
            ),
        )

        target_before = evaluate_loss(model, sft_valid)
        retain_before = evaluate_loss(model, retain_data)
        success_before, _ = task_success(model, SFT_VALID, char_to_id, id_to_char)
        curves[config.name]["target"].append((0, target_before))
        curves[config.name]["retain"].append((0, retain_before))

        train(
            model,
            sft_train,
            steps=140,
            batch_size=24,
            learning_rate=0.006,
            rng=rng,
            callback=lambda step, m=model, n=config.name: (
                curves[n]["target"].append((step, evaluate_loss(m, sft_valid))),
                curves[n]["retain"].append((step, evaluate_loss(m, retain_data))),
            ),
        )

        target_after = evaluate_loss(model, sft_valid)
        retain_after = evaluate_loss(model, retain_data)
        success_after, predictions = task_success(model, SFT_VALID, char_to_id, id_to_char)
        summaries.append(
            {
                "model": config.name,
                "parameters": model.parameter_count,
                "pretrain_valid_start": curves[config.name]["pretrain"][0][1],
                "pretrain_valid_end": curves[config.name]["pretrain"][-1][1],
                "sft_target_loss_before": target_before,
                "sft_target_loss_after": target_after,
                "task_success_before": success_before,
                "task_success_after": success_after,
                "retain_loss_before": retain_before,
                "retain_loss_after": retain_after,
            }
        )
        for prompt, expected, actual in predictions:
            prediction_rows.append(
                {"model": config.name, "prompt": prompt, "expected": expected, "actual": actual}
            )

    print("model       params  pre-val       target-loss    task-success  retain-loss")
    print("----------- ------- ------------  -------------  ------------  ------------")
    for summary in summaries:
        print(
            f"{summary['model']:<11} {summary['parameters']:>7} "
            f"{summary['pretrain_valid_start']:.3f}->{summary['pretrain_valid_end']:.3f}  "
            f"{summary['sft_target_loss_before']:.3f}->{summary['sft_target_loss_after']:.3f}  "
            f"{summary['task_success_before']:.3f}->{summary['task_success_after']:.3f}  "
            f"{summary['retain_loss_before']:.3f}->{summary['retain_loss_after']:.3f}"
        )
    print("\nSFT 后验证提示的贪心输出：")
    for row in prediction_rows:
        print(f"{row['model']:<11} {row['prompt']} expected={row['expected']} actual={row['actual']}")
    print("\n边界：这是字符级微型模型；成功率只对应六条固定行为验证题。")

    if args.no_artifacts:
        return
    repo_root = Path(__file__).resolve().parent.parent
    result_dir = Path(__file__).resolve().parent / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    summary_path = result_dir / "real_sft_summary.json"
    summary_path.write_text(
        json.dumps(
            {"seed": SEED, "context": CONTEXT, "vocab_size": len(id_to_char), "models": summaries},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    csv_path = result_dir / "real_sft_curves.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("model", "stage", "metric", "step", "loss"))
        for model_name, model_curves in curves.items():
            for metric, points in model_curves.items():
                stage = "pretrain" if metric == "pretrain" else "sft"
                for step, loss in points:
                    writer.writerow((model_name, stage, metric, step, f"{loss:.8f}"))
    svg_path = repo_root / "book" / "images" / "fig2-7-real-sft-curves.svg"
    write_svg(curves, svg_path)
    print(f"artifacts: {summary_path.relative_to(repo_root)}, {csv_path.relative_to(repo_root)}, {svg_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
