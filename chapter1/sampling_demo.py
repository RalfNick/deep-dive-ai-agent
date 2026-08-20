"""Show temperature on a toy categorical distribution.

The Chinese labels are atomic teaching categories, not guaranteed tokenizer
tokens and not calibrated probabilities of real tool calls.
"""

from __future__ import annotations

import argparse

import numpy as np


ACTION_LABELS = np.array(["读取", "调用", "删除"])
LOGITS = np.array([2.0, 1.0, 0.1], dtype=float)
TEMPERATURES = (0.5, 1.0, 2.0)


def softmax(logits: np.ndarray, temperature: float) -> np.ndarray:
    """Convert logits to probabilities at a positive temperature."""
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    scaled = logits / temperature
    shifted = scaled - np.max(scaled)
    exp_values = np.exp(shifted)
    return exp_values / np.sum(exp_values)


def sample_counts(
    probabilities: np.ndarray, draws: int, seed: int
) -> np.ndarray:
    """Draw token indices and return their observed counts."""
    randomizer = np.random.default_rng(seed)
    samples = randomizer.choice(len(ACTION_LABELS), size=draws, p=probabilities)
    return np.bincount(samples, minlength=len(ACTION_LABELS))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.draws <= 0:
        raise ValueError("draws must be positive")

    print("note: labels are toy atomic categories, not real tokenizer tokens")
    print(f"action labels: {ACTION_LABELS.tolist()}")
    print(f"logits: {LOGITS.tolist()}")
    print(f"draws: {args.draws}, seed: {args.seed}")

    for temperature in TEMPERATURES:
        probabilities = softmax(LOGITS, temperature)
        counts = sample_counts(probabilities, args.draws, args.seed)
        frequencies = counts / args.draws
        print(f"\ntemperature={temperature:.1f}")
        for token, probability, frequency in zip(
            ACTION_LABELS, probabilities, frequencies
        ):
            print(
                f"  {token}: probability={probability:.4f}, "
                f"observed={frequency:.4f}"
            )

        assert np.isclose(np.sum(probabilities), 1.0)


if __name__ == "__main__":
    main()
