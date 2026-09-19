from __future__ import annotations

import os
from pathlib import Path
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from arrow_game.core import Direction, GamePhase
from arrow_game.ui import Animation, ArrowGameApp, HEIGHT, WIDTH


OUTPUT = PROJECT_ROOT / "screenshots"


def save(app: ArrowGameApp, name: str, now: float = 10.0) -> None:
    app.draw(now)
    path = OUTPUT / name
    pygame.image.save(app.screen, path)
    print(f"已生成 {path.relative_to(OUTPUT.parent)}")


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    pygame.init()
    surface = pygame.Surface((WIDTH, HEIGHT))
    app = ArrowGameApp(screen=surface)

    save(app, "01_start.png")

    app.game.start_game()
    save(app, "02_game.png")

    app.use_hint()
    save(app, "07_hint.png")

    app.game.current_level_index = 3
    app.game.restart_level()
    app.hinted_cell = None
    save(app, "06_extension.png")

    app.game.current_level_index = 0
    app.game.restart_level()

    app.game.attempt_move(1, 0)
    app.animations = [Animation("blocked", 1, 0, Direction.RIGHT, 9.75, 0.5)]
    save(app, "03_collision.png")

    app.animations.clear()
    app.game.board = [["." for _ in row] for row in app.game.board]
    app.game.phase = GamePhase.LEVEL_COMPLETE
    app.game._frozen_elapsed = 8.6
    app.game.mistakes_made = 0
    app.game.stars_earned = 3
    save(app, "04_complete.png")

    app.game.phase = GamePhase.FAILED
    app.game.mistakes_remaining = 0
    app.game._frozen_elapsed = 12.4
    save(app, "05_failed.png")
    pygame.quit()


if __name__ == "__main__":
    main()
