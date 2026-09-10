"""Create an inspectable fixture in a new empty directory. Never resets it."""
import argparse
from pathlib import Path
from .workbench import GUIDANCE, create_workspace


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--with-guidance", action="store_true")
    args = parser.parse_args()
    create_workspace(args.destination)
    if args.with_guidance:
        (args.destination / "AGENTS.md").write_text(GUIDANCE, encoding="utf-8", newline="\n")
        (args.destination / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8", newline="\n")
    print(args.destination.resolve())
