"""Generate a bounded, reproducible evidence report for Chapter 1."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chapter1.attention_demo import causal_attention
from chapter1.bigram_lm import CORPUS, generate, train
from chapter1.coding_agent_demo import BROKEN_SOURCE, FIXED_SOURCE, evaluate_source
from chapter1.sampling_demo import LOGITS, sample_counts, softmax
from chapter1.token_demo import inspect_text


DEFAULT_OUTPUT = Path(__file__).resolve().parent / "reports" / "experiment-results.json"
CANONICAL_GENERATED_AT = "2026-08-13T00:00:00+08:00"


def _package_version(name: str) -> str:
    """Return an installed package version without exposing environment state."""
    return importlib.metadata.version(name)


def _entropy(probabilities: np.ndarray) -> float:
    return -float(np.sum(probabilities * np.log(probabilities)))


def build_report(generated_at: str | None = None) -> dict[str, object]:
    """Build structured observations for the five deterministic experiments."""
    timestamp = generated_at or CANONICAL_GENERATED_AT

    token_result = inspect_text("深入浅出 AI Agent")

    tokens = np.array([[1.0, 0.0], [0.8, 0.2], [0.0, 1.0]])
    _, _, _, weights, attended = causal_attention(tokens, tokens, tokens)

    bigram_seed = 7
    max_new_chars = 120
    sample = generate(
        train(CORPUS),
        max_new_chars=max_new_chars,
        seed=bigram_seed,
    )

    draws = 10_000
    sampling_seed = 7
    sampling_rows: list[dict[str, object]] = []
    for temperature in (0.5, 1.0, 2.0):
        probabilities = softmax(LOGITS, temperature)
        counts = sample_counts(probabilities, draws, sampling_seed)
        sampling_rows.append(
            {
                "temperature": temperature,
                "probabilities": np.round(probabilities, 6).tolist(),
                "observed_frequencies": np.round(counts / draws, 6).tolist(),
                "entropy": round(_entropy(probabilities), 6),
            }
        )

    broken = evaluate_source(BROKEN_SOURCE)
    fixed = evaluate_source(FIXED_SOURCE)

    return {
        "chapter_version": "1.1",
        "report_kind": "deterministic_mechanism_evidence",
        "generated_at": timestamp,
        "environment": {
            "python_contract": ">=3.11,<3.14",
            "numpy": _package_version("numpy"),
            "tiktoken": _package_version("tiktoken"),
        },
        "experiments": [
            {
                "id": "tokenizer",
                "command": 'python chapter1/token_demo.py "深入浅出 AI Agent"',
                "controls": {
                    "encoding": token_result["encoding"],
                    "input": token_result["text"],
                },
                "observations": {
                    "characters": token_result["characters"],
                    "utf8_bytes": len(token_result["utf8_bytes"]),
                    "tokens": len(token_result["token_ids"]),
                    "token_ids": token_result["token_ids"],
                    "token_bytes_reconstruct_input": (
                        b"".join(token_result["token_bytes"])
                        == token_result["utf8_bytes"]
                    ),
                },
                "supports": "A concrete tokenizer maps one string to reversible byte spans and model token IDs.",
                "does_not_prove": "Token counts from this sample generalize across languages, encodings, or models.",
            },
            {
                "id": "attention",
                "command": "python chapter1/attention_demo.py",
                "controls": {"q_equals_k_equals_v": tokens.tolist(), "d_k": 2},
                "observations": {
                    "row_sums": np.round(weights.sum(axis=1), 6).tolist(),
                    "future_weight_nonzero_count": int(
                        np.count_nonzero(np.triu(weights, k=1))
                    ),
                    "weights": np.round(weights, 6).tolist(),
                    "attended_values": np.round(attended, 6).tolist(),
                },
                "supports": "A causal mask removes access to future positions in this inspectable attention calculation.",
                "does_not_prove": "Attention weights fully explain a real model prediction.",
            },
            {
                "id": "bigram",
                "command": "python chapter1/bigram_lm.py --max-new-chars 120 --seed 7",
                "controls": {
                    "seed": bigram_seed,
                    "max_new_chars": max_new_chars,
                    "estimator": "next-character frequency counts",
                },
                "observations": {
                    "sample": sample,
                    "generated_characters": len(sample),
                },
                "supports": "A one-character context can produce local fragments while losing long-range consistency.",
                "does_not_prove": "Modern Transformer language models behave like a character Bigram model.",
            },
            {
                "id": "sampling",
                "command": "python chapter1/sampling_demo.py --draws 10000 --seed 7",
                "controls": {
                    "logits": LOGITS.tolist(),
                    "draws": draws,
                    "seed": sampling_seed,
                },
                "observations": sampling_rows,
                "supports": "For fixed logits, a higher positive temperature flattens this toy distribution and increases entropy.",
                "does_not_prove": "Temperature measures creativity or guarantees correctness in a real model.",
            },
            {
                "id": "coding_agent",
                "command": "python chapter1/coding_agent_demo.py",
                "controls": {
                    "remote_model_called": False,
                    "required_cases": [
                        "plain decimal",
                        "one leading yuan symbol",
                        "internal yuan symbol rejected",
                    ],
                },
                "observations": {
                    "broken_exit_code": broken.returncode,
                    "candidate_exit_code": fixed.returncode,
                },
                "supports": "A proposed patch becomes accepted only after an executor writes it and a verifier returns exit code 0.",
                "does_not_prove": "A real LLM would propose this patch or that three tests establish production correctness.",
            },
        ],
    }


def write_report(
    path: Path = DEFAULT_OUTPUT, generated_at: str | None = None
) -> dict[str, object]:
    """Write the report as UTF-8 JSON and return the same structure."""
    report = build_report(generated_at=generated_at)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_report(args.output)
    print(f"report: {args.output.resolve()}")
    print(f"experiments: {len(report['experiments'])}")
    print(f"generated_at: {report['generated_at']}")


if __name__ == "__main__":
    main()
