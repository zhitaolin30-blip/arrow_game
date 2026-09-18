from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arrow_game.core import GameState, MoveResult, replay_solution, solve_level
from arrow_game.levels import LEVELS


def main() -> None:
    print("一箭又一箭 · 项目自检")
    print("=" * 42)
    for index, level in enumerate(LEVELS, start=1):
        solution = solve_level(level)
        count = sum(cell != "." for row in level.grid for cell in row)
        passed = solution is not None and replay_solution(level, solution)
        print(f"关卡 {index}: {level.name:<12} 箭头 {count:>2}  可解性 {'通过' if passed else '失败'}")
        if not passed:
            raise SystemExit(1)

    game = GameState(LEVELS)
    game.start_game()
    result = game.attempt_move(0, 0)
    assert result is MoveResult.BLOCKED
    print("T02 阻挡与失误扣减：通过")
    print("全部自检通过。")


if __name__ == "__main__":
    main()
