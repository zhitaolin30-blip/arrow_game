import pytest

from arrow_game.core import Direction, GamePhase, GameState, Level, MoveResult, replay_solution, solve_level
from arrow_game.levels import LEVELS


def level(*rows: str, mistakes: int = 3) -> Level:
    return Level("测试关", tuple(rows), mistakes)


def started(test_level: Level, clock=lambda: 10.0) -> GameState:
    game = GameState((test_level,), clock=clock)
    game.start_game()
    return game


def test_t01_clear_arrow_is_removed() -> None:
    game = started(level("R."))
    assert game.attempt_move(0, 0) is MoveResult.REMOVED
    assert game.remaining_arrows == 0


def test_t02_blocked_arrow_stays_and_costs_a_mistake() -> None:
    game = started(level("R.L"))
    assert game.attempt_move(0, 0) is MoveResult.BLOCKED
    assert game.direction_at(0, 0) is Direction.RIGHT
    assert game.mistakes_remaining == 2


@pytest.mark.parametrize(
    ("grid", "position"),
    [
        (("U",), (0, 0)),
        (("D",), (0, 0)),
        (("L",), (0, 0)),
        (("R",), (0, 0)),
    ],
)
def test_t03_edge_arrow_facing_out_is_safe(grid: tuple[str, ...], position: tuple[int, int]) -> None:
    game = started(Level("边界", grid, 3))
    assert game.has_clear_path(*position)
    assert game.attempt_move(*position) is MoveResult.REMOVED


def test_t04_clearing_level_shows_complete_then_advances() -> None:
    game = GameState((level("R"), level("L")))
    game.start_game()
    assert game.attempt_move(0, 0) is MoveResult.REMOVED
    assert game.phase is GamePhase.LEVEL_COMPLETE
    assert game.next_level()
    assert game.current_level_index == 1
    assert game.phase is GamePhase.PLAYING


def test_t05_mistakes_exhausted_causes_failure_and_can_restart() -> None:
    game = started(level("R.L", mistakes=2))
    assert game.attempt_move(0, 0) is MoveResult.BLOCKED
    assert game.attempt_move(0, 0) is MoveResult.BLOCKED
    assert game.phase is GamePhase.FAILED
    game.restart_level()
    assert game.phase is GamePhase.PLAYING
    assert game.mistakes_remaining == 2


def test_t06_restart_restores_board_mistakes_and_timer() -> None:
    current = [10.0]
    game = started(level("R.L"), clock=lambda: current[0])
    game.attempt_move(0, 0)
    current[0] = 15.0
    game.restart_level()
    assert ["".join(row) for row in game.board] == ["R.L"]
    assert game.mistakes_remaining == 3
    assert game.elapsed == 0.0


def test_distant_arrow_blocks_entire_path() -> None:
    game = started(level("R...L"))
    assert not game.has_clear_path(0, 0)


def test_empty_and_outside_clicks_are_ignored() -> None:
    game = started(level("R."))
    assert game.attempt_move(0, 1) is MoveResult.IGNORED
    assert game.attempt_move(-1, 0) is MoveResult.IGNORED
    assert game.mistakes_remaining == 3


def test_timer_freezes_when_level_ends() -> None:
    current = [4.0]
    game = started(level("R"), clock=lambda: current[0])
    current[0] = 7.25
    game.attempt_move(0, 0)
    current[0] = 20.0
    assert game.elapsed == pytest.approx(3.25)


def test_last_level_transitions_to_all_complete() -> None:
    game = started(level("R"))
    game.attempt_move(0, 0)
    assert not game.next_level()
    assert game.phase is GamePhase.ALL_COMPLETE


def test_moves_are_ignored_outside_playing_phase() -> None:
    game = started(level("R"))
    game.go_to_menu()
    assert game.attempt_move(0, 0) is MoveResult.IGNORED


@pytest.mark.parametrize("game_level", LEVELS)
def test_every_builtin_level_is_solvable(game_level: Level) -> None:
    solution = solve_level(game_level)
    assert solution is not None
    assert len(solution) == sum(cell != "." for row in game_level.grid for cell in row)
    assert replay_solution(game_level, solution)


def test_builtin_levels_grow_from_9_to_36_cells_with_more_empty_space() -> None:
    cell_counts = [len(item.grid) * len(item.grid[0]) for item in LEVELS]
    empty_counts = [sum(cell == "." for row in item.grid for cell in row) for item in LEVELS]
    assert cell_counts == [9, 16, 25, 36]
    assert empty_counts == [5, 10, 17, 22]


def test_extension_level_starts_with_only_two_valid_choices() -> None:
    game = GameState((LEVELS[-1],))
    game.start_game()
    valid_moves = [
        (row, col)
        for row in range(game.rows)
        for col in range(game.cols)
        if game.direction_at(row, col) is not None and game.has_clear_path(row, col)
    ]
    assert game.remaining_arrows == 14
    assert len(valid_moves) == 2


def test_invalid_level_is_rejected() -> None:
    with pytest.raises(ValueError):
        level("RX")
