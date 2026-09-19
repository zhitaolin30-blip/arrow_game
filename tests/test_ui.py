import pygame

from arrow_game.core import Direction, GamePhase, MoveResult
from arrow_game.ui import ARROW_GREEN, DANGER, DIRECTION_COLORS, ArrowGameApp, HEIGHT, WIDTH


def make_app() -> ArrowGameApp:
    pygame.init()
    return ArrowGameApp(screen=pygame.Surface((WIDTH, HEIGHT)))


def test_pixel_mapping_returns_cell_and_ignores_outside() -> None:
    app = make_app()
    app.game.start_game()
    board, cell = app.board_geometry()
    assert app.cell_at_pixel((board.x + cell / 2, board.y + cell / 2)) == (0, 0)
    assert app.cell_at_pixel((0, 0)) is None


def test_normal_arrows_are_green_and_collision_is_red() -> None:
    assert {DIRECTION_COLORS[direction] for direction in Direction} == {ARROW_GREEN}
    assert DANGER != ARROW_GREEN


def test_animation_allows_immediate_click_on_another_arrow() -> None:
    app = make_app()
    app.game.start_game()
    assert app.attempt_cell(0, 1, now=1.0) is MoveResult.REMOVED
    assert app.attempt_cell(2, 2, now=1.01) is MoveResult.REMOVED
    assert app.game.remaining_arrows == 6
    assert len(app.animations) == 2


def test_same_colliding_arrow_cannot_charge_twice_during_animation() -> None:
    app = make_app()
    app.game.start_game()
    assert app.attempt_cell(1, 0, now=1.0) is MoveResult.BLOCKED
    assert app.attempt_cell(1, 0, now=1.01) is MoveResult.IGNORED
    assert app.game.mistakes_remaining == 2


def test_successful_click_creates_flying_animation() -> None:
    app = make_app()
    app.game.start_game()
    assert app.attempt_cell(0, 1, now=1.0) is MoveResult.REMOVED
    assert app.animations[-1].kind == "flying"


def test_failed_click_creates_collision_animation() -> None:
    app = make_app()
    app.game.start_game()
    assert app.attempt_cell(1, 0, now=1.0) is MoveResult.BLOCKED
    assert app.animations[-1].kind == "blocked"


def test_correct_and_incorrect_moves_use_different_sounds() -> None:
    class Recorder:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def play_correct(self) -> None:
            self.calls.append("correct")

        def play_incorrect(self) -> None:
            self.calls.append("incorrect")

    app = make_app()
    recorder = Recorder()
    app.sounds = recorder
    app.game.start_game()

    assert app.attempt_cell(1, 0, now=1.0) is MoveResult.BLOCKED
    app.animations.clear()
    assert app.attempt_cell(0, 1, now=2.0) is MoveResult.REMOVED
    assert recorder.calls == ["incorrect", "correct"]


def test_hint_highlights_a_valid_cell_and_clears_after_move() -> None:
    app = make_app()
    app.game.start_game()
    hinted = app.use_hint()
    assert hinted is not None
    assert app.game.has_clear_path(*hinted)
    assert app.game.hints_remaining == 1
    app.draw(1.0)
    assert app.attempt_cell(*hinted, now=1.0) is MoveResult.REMOVED
    assert app.hinted_cell is None


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
