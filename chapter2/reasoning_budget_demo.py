"""把推理预算类比为受限搜索节点数，观察质量、成本与任务难度。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Maze:
    name: str
    rows: tuple[str, ...]


MAZES = (
    Maze("easy", ("S...G",)),
    Maze("turn", ("S#...", ".#.#G", ".....")),
    Maze("detour", ("S..#...", "##.#.#.", "...#.#G", ".#...#.", ".......")),
    Maze("blocked", ("S#G", "###", "...")),
)


def locate(rows: tuple[str, ...], symbol: str) -> tuple[int, int]:
    for r, row in enumerate(rows):
        if symbol in row:
            return r, row.index(symbol)
    raise ValueError(f"missing {symbol}")


def solve(maze: Maze, budget: int) -> tuple[bool, int, int | None]:
    start = locate(maze.rows, "S")
    goal = locate(maze.rows, "G")
    queue = deque([(start, 0)])
    visited = {start}
    expanded = 0

    while queue and expanded < budget:
        (row, col), distance = queue.popleft()
        expanded += 1
        if (row, col) == goal:
            return True, expanded, distance
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if not (0 <= nr < len(maze.rows)):
                continue
            if not (0 <= nc < len(maze.rows[nr])):
                continue
            if maze.rows[nr][nc] == "#" or (nr, nc) in visited:
                continue
            visited.add((nr, nc))
            queue.append(((nr, nc), distance + 1))
    return False, expanded, None


def main() -> None:
    budgets = (4, 8, 16, 32, 64)
    print("budget  solved/4  expanded  detail")
    print("------  --------  --------  ------")
    for budget in budgets:
        results = [(maze.name, *solve(maze, budget)) for maze in MAZES]
        solved = sum(success for _, success, _, _ in results)
        expanded = sum(count for _, _, count, _ in results)
        detail = ", ".join(
            f"{name}:{'ok/' + str(distance) if success else 'fail'}"
            for name, success, _, distance in results
        )
        print(f"{budget:>6}  {solved:>6}/4  {expanded:>8}  {detail}")

    print("\n观察 1：简单任务很早达到饱和，继续加预算只增加上限。")
    print("观察 2：困难但可解任务需要更多搜索；不可解任务不会被预算治好。")
    print("边界：这不是语言模型基准，只是推理时计算取舍的可控类比。")


if __name__ == "__main__":
    main()
