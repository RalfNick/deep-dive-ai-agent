"""Run with python -m chapter11.quickstart from the book repository root."""
import json
from pathlib import Path
import tempfile
from .experiments import repair


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="book-ch11-quickstart-") as folder:
        print(json.dumps(repair(Path(folder) / "repo"), ensure_ascii=False, indent=2))
