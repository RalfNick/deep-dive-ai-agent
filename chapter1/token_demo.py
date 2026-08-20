"""Inspect how text becomes bytes and model tokens."""

from __future__ import annotations

import importlib.metadata
import platform
import sys

import tiktoken


DEFAULT_SAMPLES = [
    "深入浅出地讲解智能体",
    "深入浅出 AI Agent",
    "for item in tools:\n    run(item)",
    "Agent 🤖 uses tools 🔧",
]


def inspect_text(
    text: str, encoding_name: str = "o200k_base"
) -> dict[str, object]:
    """Return the observable byte and token representation of one string."""
    encoding = tiktoken.get_encoding(encoding_name)
    token_ids = encoding.encode(text)
    return {
        "text": text,
        "characters": len(text),
        "utf8_bytes": text.encode("utf-8"),
        "token_ids": token_ids,
        "token_bytes": [
            encoding.decode_single_token_bytes(token) for token in token_ids
        ],
        "encoding": encoding_name,
    }


def describe(text: str, encoding_name: str = "o200k_base") -> None:
    """Print character, byte, and token representations for one string."""
    result = inspect_text(text, encoding_name)
    print(f"text: {result['text']!r}")
    print(f"characters: {result['characters']}")
    print(f"utf-8 bytes: {len(result['utf8_bytes'])}")
    print(f"tokens: {len(result['token_ids'])}")
    print(f"token ids: {result['token_ids']}")
    print(f"token bytes: {result['token_bytes']}")
    print("-")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    encoding_name = "o200k_base"
    print(f"python: {platform.python_version()}")
    print(f"tiktoken: {importlib.metadata.version('tiktoken')}")
    print(f"encoding: {encoding_name}")
    print("=")
    samples = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else DEFAULT_SAMPLES
    for sample in samples:
        describe(sample, encoding_name)


if __name__ == "__main__":
    main()
