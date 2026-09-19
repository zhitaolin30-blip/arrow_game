from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time
from typing import Callable, Iterable, Sequence


class Direction(str, Enum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"

    @property
    def delta(self) -> tuple[int, int]:
        return {
            Direction.UP: (-1, 0),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }[self]


class MoveResult(str, Enum):
    REMOVED = "removed"
    BLOCKED = "blocked"
    IGNORED = "ignored"


class GamePhase(str, Enum):
    MENU = "menu"
    PLAYING = "playing"
    LEVEL_COMPLETE = "level_complete"
    FAILED = "failed"
    ALL_COMPLETE = "all_complete"


@dataclass(frozen=True)
class Level:
    name: str
    grid: tuple[str, ...]
    max_mistakes: int
    three_star_seconds: float = 30.0
    two_star_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("关卡名称不能为空")
        if not self.grid or not self.grid[0]:
            raise ValueError("关卡棋盘不能为空")
        width = len(self.grid[0])
        if any(len(row) != width for row in self.grid):
            raise ValueError("关卡棋盘必须为矩形")
        allowed = {".", *(direction.value for direction in Direction)}
        if any(cell not in allowed for row in self.grid for cell in row):
            raise ValueError("棋盘只能包含 U/D/L/R/.")
        if not any(cell != "." for row in self.grid for cell in row):
            raise ValueError("关卡至少需要一个箭头")
        if self.max_mistakes <= 0:
            raise ValueError("失误上限必须大于 0")
        if self.three_star_seconds <= 0 or self.two_star_seconds <= self.three_star_seconds:
            raise ValueError("星级时间阈值必须为递增的正数")


class GameState:
    """与 Pygame 无关的游戏规则和流程状态。"""

    def __init__(
        self,
        levels: Sequence[Level],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not levels:
            raise ValueError("至少需要一个关卡")
        self.levels = tuple(levels)
        self.clock = clock
        self.current_level_index = 0
        self.phase = GamePhase.MENU
        self.board: list[list[str]] = []
        self.mistakes_remaining = 0
        self.mistakes_made = 0
        self.hints_remaining = 2
        self.stars_earned = 0
        self._started_at = 0.0
        self._frozen_elapsed = 0.0
        self._load_current_level()
        self.phase = GamePhase.MENU

    @property
    def level(self) -> Level:
        return self.levels[self.current_level_index]

    @property
    def rows(self) -> int:
        return len(self.board)

    @property
    def cols(self) -> int:
        return len(self.board[0])

    @property
    def remaining_arrows(self) -> int:
        return sum(cell != "." for row in self.board for cell in row)

    @property
    def elapsed(self) -> float:
        if self.phase is GamePhase.PLAYING:
            return max(0.0, self.clock() - self._started_at)
        return self._frozen_elapsed

    def start_game(self) -> None:
        self.current_level_index = 0
        self._load_current_level()

    def go_to_menu(self) -> None:
        self._freeze_timer()
        self.phase = GamePhase.MENU

    def restart_level(self) -> None:
        self._load_current_level()

    def next_level(self) -> bool:
        if self.phase is not GamePhase.LEVEL_COMPLETE:
            return False
        if self.current_level_index + 1 >= len(self.levels):
            self.phase = GamePhase.ALL_COMPLETE
            return False
        self.current_level_index += 1
        self._load_current_level()
        return True

    def direction_at(self, row: int, col: int) -> Direction | None:
        if not self._inside(row, col):
            return None
        value = self.board[row][col]
        return None if value == "." else Direction(value)

    def has_clear_path(self, row: int, col: int) -> bool:
        direction = self.direction_at(row, col)
        if direction is None:
            return False
        dr, dc = direction.delta
        row += dr
        col += dc
        while self._inside(row, col):
            if self.board[row][col] != ".":
                return False
            row += dr
            col += dc
        return True

    def available_moves(self) -> list[tuple[int, int]]:
        """返回当前所有可安全消除的箭头。"""
        if self.phase is not GamePhase.PLAYING:
            return []
        return [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.direction_at(row, col) is not None and self.has_clear_path(row, col)
        ]

    def request_hint(self) -> tuple[int, int] | None:
        """消耗一次机会，返回一个当前可正确点击的格子。"""
        if self.phase is not GamePhase.PLAYING or self.hints_remaining <= 0:
            return None
        moves = self.available_moves()
        if not moves:
            return None
        self.hints_remaining -= 1
        return moves[0]

    def calculate_stars(self) -> int:
        """按完成时间和失误次数计算 1–3 星。"""
        if self.mistakes_made == 0 and self.elapsed <= self.level.three_star_seconds:
            return 3
        if self.mistakes_made <= 1 and self.elapsed <= self.level.two_star_seconds:
            return 2
        return 1

    def attempt_move(self, row: int, col: int) -> MoveResult:
        if self.phase is not GamePhase.PLAYING:
            return MoveResult.IGNORED
        direction = self.direction_at(row, col)
        if direction is None:
            return MoveResult.IGNORED

        if not self.has_clear_path(row, col):
            self.mistakes_remaining -= 1
            self.mistakes_made += 1
            if self.mistakes_remaining <= 0:
                self.mistakes_remaining = 0
                self._freeze_timer()
                self.phase = GamePhase.FAILED
            return MoveResult.BLOCKED

        self.board[row][col] = "."
        if self.remaining_arrows == 0:
            self._freeze_timer()
            self.phase = GamePhase.LEVEL_COMPLETE
            self.stars_earned = self.calculate_stars()
        return MoveResult.REMOVED

    def _inside(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def _load_current_level(self) -> None:
        self.board = [list(row) for row in self.level.grid]
        self.mistakes_remaining = self.level.max_mistakes
        self.mistakes_made = 0
        self.hints_remaining = 2
        self.stars_earned = 0
        self._started_at = self.clock()
        self._frozen_elapsed = 0.0
        self.phase = GamePhase.PLAYING

    def _freeze_timer(self) -> None:
        if self.phase is GamePhase.PLAYING:
            self._frozen_elapsed = max(0.0, self.clock() - self._started_at)


def _clear_path_on_board(board: tuple[str, ...], row: int, col: int) -> bool:
    direction = Direction(board[row][col])
    dr, dc = direction.delta
    row += dr
    col += dc
    rows, cols = len(board), len(board[0])
    while 0 <= row < rows and 0 <= col < cols:
        if board[row][col] != ".":
            return False
        row += dr
        col += dc
    return True


def solve_level(level: Level) -> list[tuple[int, int]] | None:
    """用 DFS 返回一条通关点击序列；无解时返回 None。"""

    start = tuple(level.grid)
    failed: set[tuple[str, ...]] = set()

    def search(board: tuple[str, ...]) -> list[tuple[int, int]] | None:
        if all(cell == "." for row in board for cell in row):
            return []
        if board in failed:
            return None
        for row, line in enumerate(board):
            for col, cell in enumerate(line):
                if cell == "." or not _clear_path_on_board(board, row, col):
                    continue
                mutable = [list(value) for value in board]
                mutable[row][col] = "."
                result = search(tuple("".join(value) for value in mutable))
                if result is not None:
                    return [(row, col), *result]
        failed.add(board)
        return None

    return search(start)


def replay_solution(level: Level, moves: Iterable[tuple[int, int]]) -> bool:
    game = GameState((level,))
    game.start_game()
    for row, col in moves:
        if game.attempt_move(row, col) is not MoveResult.REMOVED:
            return False
    return game.phase is GamePhase.LEVEL_COMPLETE
