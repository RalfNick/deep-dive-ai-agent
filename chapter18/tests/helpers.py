from dataclasses import replace
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def packet(**changes):
    from chapter18.contracts import BudgetLimits, TaskPacket
    return replace(TaskPacket(
        "task-root", None, "manager", "确认当前版本共享方式", "public", "v2", ("sharing",),
        frozenset({"public-current", "parallel-product", "parallel-support", "conflict-a", "conflict-b"}),
        frozenset({"knowledge", "read", "propose"}), frozenset({"src/linkcheck.py", "src/policy.py"}),
        ("sharing",), (), BudgetLimits(), 0,
    ), **changes)


def fixture_repo(tmp_path):
    root = tmp_path / "book"
    shutil.copytree(ROOT / "chapter18/fixtures", root / "chapter18/fixtures")
    return root
