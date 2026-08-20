"""Fit counts and sample a tiny character-level bigram language model."""

from __future__ import annotations

import argparse
import random
from collections import Counter, defaultdict


CORPUS = """
Agent 读取任务，选择工具，观察结果，再决定下一步。
模型生成候选动作，运行时执行动作，测试提供反馈。
可靠的 Agent 不只产生答案，还要验证答案。
上下文应该保留高价值信息，而不是堆满所有历史。
工具扩大能力边界，权限限制行动边界。
""".strip()


def train(text: str) -> dict[str, Counter[str]]:
    """Count next-character transitions."""
    transitions: dict[str, Counter[str]] = defaultdict(Counter)
    sequence = "^" + text + "$"
    for current, following in zip(sequence, sequence[1:]):
        transitions[current][following] += 1
    return transitions


def choose(counter: Counter[str], randomizer: random.Random) -> str:
    """Sample one character in proportion to its observed count."""
    characters = list(counter)
    weights = [counter[character] for character in characters]
    return randomizer.choices(characters, weights=weights, k=1)[0]


def generate(
    transitions: dict[str, Counter[str]], max_new_chars: int, seed: int
) -> str:
    """Generate at most the requested number of characters."""
    randomizer = random.Random(seed)
    current = "^"
    result: list[str] = []

    for _ in range(max_new_chars):
        following = choose(transitions[current], randomizer)
        if following == "$":
            break
        result.append(following)
        current = following
    return "".join(result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new-chars", type=int, default=120)
    parser.add_argument(
        "--steps",
        dest="max_new_chars",
        type=int,
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transitions = train(CORPUS)
    sample = generate(
        transitions,
        max_new_chars=args.max_new_chars,
        seed=args.seed,
    )
    print(f"vocabulary: {len(transitions)} current-character states")
    print(f"seed: {args.seed}")
    print(f"generation_limit: {args.max_new_chars} characters")
    print(f"sample:\n{sample}")


if __name__ == "__main__":
    main()
