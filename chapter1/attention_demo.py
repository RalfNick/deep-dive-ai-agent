"""A minimal, inspectable causal self-attention calculation."""

from __future__ import annotations

import numpy as np


def softmax(values: np.ndarray) -> np.ndarray:
    """Compute a numerically stable softmax along the final axis."""
    shifted = values - np.max(values, axis=-1, keepdims=True)
    exp_values = np.exp(shifted)
    return exp_values / np.sum(exp_values, axis=-1, keepdims=True)


def causal_attention(
    query: np.ndarray, key: np.ndarray, value: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return scores, mask, masked scores, weights, and attended values."""
    dimension = query.shape[-1]
    scores = query @ key.T / np.sqrt(dimension)

    future_positions = np.triu(
        np.ones((query.shape[0], key.shape[0]), dtype=bool), k=1
    )
    masked_scores = np.where(future_positions, -np.inf, scores)
    weights = softmax(masked_scores)
    output = weights @ value
    return scores, future_positions, masked_scores, weights, output


def main() -> None:
    # Three toy token representations. Identity projections keep the math visible.
    tokens = np.array(
        [
            [1.0, 0.0],
            [0.8, 0.2],
            [0.0, 1.0],
        ]
    )

    scores, mask, masked_scores, weights, output = causal_attention(
        tokens, tokens, tokens
    )

    np.set_printoptions(precision=3, suppress=True)
    print(f"d_k: {tokens.shape[-1]}")
    print("Q = K = V:\n", tokens)
    print("raw scores:\n", scores)
    print("\ncausal mask (True means hidden):\n", mask)
    print("\nmasked scores:\n", masked_scores)
    print("\ncausal attention weights:\n", weights)
    print("\nrow sums:\n", weights.sum(axis=1))
    print("\nattended values:\n", output)

    assert np.allclose(weights.sum(axis=1), 1.0)
    assert np.allclose(np.triu(weights, k=1), 0.0)


if __name__ == "__main__":
    main()
