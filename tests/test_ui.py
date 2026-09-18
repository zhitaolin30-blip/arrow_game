import time

import pygame

from arrow_game.core import Direction, GamePhase, MoveResult
from arrow_game.ui import Animation, ArrowGameApp, HEIGHT, WIDTH


def make_app() -> ArrowGameApp:
    pygame.init()
    return ArrowGameApp(screen=pygame.Surface((WIDTH, HEIGHT)))


def test_pixel_mapping_returns_cell_and_ignores_outside() -> None:
    app = make_app()
    app.game.start_game()
    board, cell = app.board_geometry()
    assert app.cell_at_pixel((board.x + cell / 2, board.y + cell / 2)) == (0, 0)
    assert app.cell_at_pixel((0, 0)) is None


def test_animation_locks_repeated_input() -> None:
    app = make_app()
    app.game.start_game()
    before = app.game.remaining_arrows
    app.animation = Animation("blocked", 0, 0, Direction.RIGHT, time.monotonic(), 1.0)
    assert app.attempt_cell(0, 2) is MoveResult.IGNORED
    assert app.game.remaining_arrows == before


def test_successful_click_creates_flying_animation() -> None:
    app = make_app()
    app.game.start_game()
    assert app.attempt_cell(0, 2, now=1.0) is MoveResult.REMOVED
    assert app.animation is not None
    assert app.animation.kind == "flying"


def test_failed_click_creates_collision_animation() -> None:
    app = make_app()
    app.game.start_game()
    assert app.attempt_cell(0, 0, now=1.0) is MoveResult.BLOCKED
    assert app.animation is not None
    assert app.animation.kind == "blocked"


def test_draw_all_scenes_without_error() -> None:
    app = make_app()
    app.draw(1.0)
    app.game.start_game()
    app.draw(1.0)
    app.game.phase = GamePhase.LEVEL_COMPLETE
    app.draw(1.0)
    app.game.phase = GamePhase.FAILED
    app.draw(1.0)
    app.game.phase = GamePhase.ALL_COMPLETE
    app.draw(1.0)

