from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import sys
import time

import pygame

from .core import Direction, GamePhase, GameState, MoveResult
from .levels import LEVELS


WIDTH, HEIGHT = 960, 720
FPS = 60

BG_TOP = (16, 25, 48)
BG_BOTTOM = (27, 48, 82)
PANEL = (31, 47, 77)
PANEL_LIGHT = (43, 64, 101)
TEXT = (239, 244, 255)
MUTED = (165, 178, 204)
ACCENT = (255, 177, 74)
ACCENT_HOVER = (255, 195, 103)
DANGER = (245, 92, 101)
SUCCESS = (79, 205, 151)
GRID_LINE = (81, 105, 145)

DIRECTION_COLORS = {
    Direction.UP: (244, 104, 117),
    Direction.DOWN: (94, 211, 154),
    Direction.LEFT: (91, 162, 255),
    Direction.RIGHT: (255, 177, 74),
}


@dataclass
class Animation:
    kind: str
    row: int
    col: int
    direction: Direction
    started_at: float
    duration: float

    def progress(self, now: float) -> float:
        return min(1.0, max(0.0, (now - self.started_at) / self.duration))


class ArrowGameApp:
    def __init__(self, *, screen: pygame.Surface | None = None) -> None:
        pygame.init()
        pygame.font.init()
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        if pygame.display.get_surface() is not None:
            pygame.display.set_caption("一箭又一箭")
        self.clock = pygame.time.Clock()
        self.game = GameState(LEVELS)
        self.running = True
        self.animation: Animation | None = None
        self.fonts = {
            "title": self._font(68, bold=True),
            "large": self._font(40, bold=True),
            "medium": self._font(27, bold=True),
            "body": self._font(21),
            "small": self._font(17),
        }
        self.start_button = pygame.Rect(350, 510, 260, 68)
        self.restart_button = pygame.Rect(610, 638, 150, 48)
        self.menu_button = pygame.Rect(775, 638, 150, 48)
        self.overlay_primary = pygame.Rect(345, 430, 270, 58)
        self.overlay_secondary = pygame.Rect(345, 504, 270, 50)

    @property
    def input_locked(self) -> bool:
        return self.animation is not None

    def run(self) -> None:
        while self.running:
            now = time.monotonic()
            for event in pygame.event.get():
                self.handle_event(event, now)
            self.update(now)
            self.draw(now)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_event(self, event: pygame.event.Event, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.animation = None
                self.game.go_to_menu()
                return
            if event.key == pygame.K_r and self.game.phase in {
                GamePhase.PLAYING,
                GamePhase.FAILED,
                GamePhase.LEVEL_COMPLETE,
            }:
                self.animation = None
                self.game.restart_level()
                return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        position = event.pos
        if self.game.phase is GamePhase.MENU:
            if self.start_button.collidepoint(position):
                self.game.start_game()
            return

        if self.input_locked:
            return

        if self.game.phase is GamePhase.PLAYING:
            if self.restart_button.collidepoint(position):
                self.game.restart_level()
            elif self.menu_button.collidepoint(position):
                self.game.go_to_menu()
            else:
                cell = self.cell_at_pixel(position)
                if cell is not None:
                    self.attempt_cell(*cell, now=now)
            return

        if self.game.phase is GamePhase.LEVEL_COMPLETE:
            if self.overlay_primary.collidepoint(position):
                self.game.next_level()
            elif self.overlay_secondary.collidepoint(position):
                self.game.restart_level()
        elif self.game.phase is GamePhase.FAILED:
            if self.overlay_primary.collidepoint(position):
                self.game.restart_level()
            elif self.overlay_secondary.collidepoint(position):
                self.game.go_to_menu()
        elif self.game.phase is GamePhase.ALL_COMPLETE:
            if self.overlay_primary.collidepoint(position):
                self.game.start_game()
            elif self.overlay_secondary.collidepoint(position):
                self.game.go_to_menu()

    def attempt_cell(self, row: int, col: int, *, now: float | None = None) -> MoveResult:
        if self.input_locked:
            return MoveResult.IGNORED
        direction = self.game.direction_at(row, col)
        if direction is None:
            return MoveResult.IGNORED
        result = self.game.attempt_move(row, col)
        if result is MoveResult.REMOVED:
            self.animation = Animation("flying", row, col, direction, now or time.monotonic(), 0.42)
        elif result is MoveResult.BLOCKED:
            self.animation = Animation("blocked", row, col, direction, now or time.monotonic(), 0.48)
        return result

    def update(self, now: float) -> None:
        if self.animation and self.animation.progress(now) >= 1.0:
            self.animation = None

    def draw(self, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        self._draw_background()
        if self.game.phase is GamePhase.MENU:
            self._draw_menu()
            return
        self._draw_game(now)
        if self.animation is None and self.game.phase in {
            GamePhase.LEVEL_COMPLETE,
            GamePhase.FAILED,
            GamePhase.ALL_COMPLETE,
        }:
            self._draw_result_overlay()

    def board_geometry(self) -> tuple[pygame.Rect, float]:
        size = min(470, 92 * max(self.game.rows, self.game.cols))
        cell = size / max(self.game.rows, self.game.cols)
        width = cell * self.game.cols
        height = cell * self.game.rows
        return pygame.Rect((WIDTH - width) / 2, 145 + (470 - height) / 2, width, height), cell

    def cell_at_pixel(self, position: tuple[int, int]) -> tuple[int, int] | None:
        rect, cell = self.board_geometry()
        if not rect.collidepoint(position):
            return None
        col = int((position[0] - rect.x) / cell)
        row = int((position[1] - rect.y) / cell)
        if 0 <= row < self.game.rows and 0 <= col < self.game.cols:
            return row, col
        return None

    def _draw_background(self) -> None:
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            color = tuple(int(a + (b - a) * ratio) for a, b in zip(BG_TOP, BG_BOTTOM))
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))
        for x, y, radius, alpha in ((110, 120, 120, 18), (850, 180, 170, 15), (720, 650, 220, 12)):
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*ACCENT, alpha), (radius, radius), radius)
            self.screen.blit(glow, (x - radius, y - radius))

    def _draw_menu(self) -> None:
        self._text("一箭又一箭", self.fonts["title"], TEXT, (WIDTH // 2, 155), center=True)
        self._text("ONE ARROW AFTER ANOTHER", self.fonts["small"], ACCENT, (WIDTH // 2, 218), center=True)

        card = pygame.Rect(205, 270, 550, 180)
        self._panel(card)
        rules = (
            "点击箭头，检查它朝向的整条路径",
            "前方无阻挡：飞出棋盘    有阻挡：扣除失误机会",
            "清空全部箭头即可通关，失误耗尽则挑战失败",
        )
        for index, line in enumerate(rules):
            color = TEXT if index == 0 else MUTED
            self._text(line, self.fonts["body"], color, (WIDTH // 2, 315 + index * 48), center=True)

        self._button(self.start_button, "开始游戏", primary=True)
        self._text("鼠标点击箭头 · R 重新开始 · Esc 返回主页", self.fonts["small"], MUTED, (WIDTH // 2, 620), center=True)
        self._draw_decorative_arrows()

    def _draw_game(self, now: float) -> None:
        self._text(self.game.level.name, self.fonts["medium"], TEXT, (WIDTH // 2, 38), center=True)
        hud_items = (
            ("剩余箭头", str(self.game.remaining_arrows), ACCENT),
            ("剩余失误", str(self.game.mistakes_remaining), SUCCESS if self.game.mistakes_remaining > 1 else DANGER),
            ("本关用时", f"{self.game.elapsed:05.1f}s", (112, 179, 255)),
        )
        for index, (label, value, color) in enumerate(hud_items):
            rect = pygame.Rect(145 + index * 230, 72, 210, 58)
            self._panel(rect, radius=14)
            self._text(label, self.fonts["small"], MUTED, (rect.x + 18, rect.centery))
            self._text(value, self.fonts["medium"], color, (rect.right - 18, rect.centery), right=True)

        board_rect, cell = self.board_geometry()
        shadow = board_rect.inflate(22, 22)
        pygame.draw.rect(self.screen, (12, 20, 38), shadow, border_radius=20)
        pygame.draw.rect(self.screen, PANEL, board_rect, border_radius=14)
        for row in range(self.game.rows):
            for col in range(self.game.cols):
                cell_rect = pygame.Rect(
                    board_rect.x + col * cell,
                    board_rect.y + row * cell,
                    cell,
                    cell,
                )
                pygame.draw.rect(self.screen, GRID_LINE, cell_rect, width=2)
                direction = self.game.direction_at(row, col)
                if direction is not None:
                    self._draw_arrow(cell_rect.center, direction, cell * 0.31, DIRECTION_COLORS[direction])

        if self.animation:
            self._draw_animation(self.animation, now, board_rect, cell)

        self._button(self.restart_button, "重新开始")
        self._button(self.menu_button, "返回主页")
        self._text("R 重开   ·   Esc 返回主页", self.fonts["small"], MUTED, (35, 663))

    def _draw_animation(self, animation: Animation, now: float, board: pygame.Rect, cell: float) -> None:
        progress = animation.progress(now)
        x = board.x + (animation.col + 0.5) * cell
        y = board.y + (animation.row + 0.5) * cell
        dr, dc = animation.direction.delta
        if animation.kind == "flying":
            eased = progress * progress
            distance = max(WIDTH, HEIGHT) * eased
            x += dc * distance
            y += dr * distance
            color = DIRECTION_COLORS[animation.direction]
            self._draw_arrow((x, y), animation.direction, cell * 0.31, color)
            for step in range(1, 5):
                alpha = max(0, 90 - step * 17)
                ghost = pygame.Surface((int(cell), int(cell)), pygame.SRCALPHA)
                center = (cell / 2 - dc * step * 12, cell / 2 - dr * step * 12)
                self._draw_arrow(center, animation.direction, cell * 0.13, (*color, alpha), surface=ghost)
                self.screen.blit(ghost, (x - cell / 2, y - cell / 2))
        else:
            offset = math.sin(progress * math.pi) * 18
            jitter = math.sin(progress * math.pi * 8) * 3
            x += dc * offset + (jitter if dr else 0)
            y += dr * offset + (jitter if dc else 0)
            self._draw_arrow((x, y), animation.direction, cell * 0.31, DANGER)

    def _draw_result_overlay(self) -> None:
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((5, 10, 23, 185))
        self.screen.blit(veil, (0, 0))
        card = pygame.Rect(270, 175, 420, 405)
        pygame.draw.rect(self.screen, (29, 44, 72), card, border_radius=24)
        pygame.draw.rect(self.screen, PANEL_LIGHT, card, width=2, border_radius=24)

        if self.game.phase is GamePhase.LEVEL_COMPLETE:
            title, subtitle, color = "关卡完成！", f"用时 {self.game.elapsed:.1f} 秒", SUCCESS
            primary, secondary = "进入下一关", "重玩本关"
        elif self.game.phase is GamePhase.FAILED:
            title, subtitle, color = "挑战失败", "失误机会已经用完", DANGER
            primary, secondary = "重新挑战", "返回主页"
        else:
            title, subtitle, color = "全部通关！", "三道谜题全部完成", ACCENT
            primary, secondary = "再玩一次", "返回主页"

        pygame.draw.circle(self.screen, color, (WIDTH // 2, 245), 42, width=5)
        if self.game.phase is GamePhase.FAILED:
            pygame.draw.line(self.screen, color, (466, 231), (494, 259), width=7)
            pygame.draw.line(self.screen, color, (494, 231), (466, 259), width=7)
        else:
            pygame.draw.lines(self.screen, color, False, ((459, 245), (474, 260), (503, 226)), width=7)
        self._text(title, self.fonts["large"], TEXT, (WIDTH // 2, 320), center=True)
        self._text(subtitle, self.fonts["body"], MUTED, (WIDTH // 2, 368), center=True)
        self._button(self.overlay_primary, primary, primary=True)
        self._button(self.overlay_secondary, secondary)

    def _draw_decorative_arrows(self) -> None:
        decorations = (
            ((115, 170), Direction.RIGHT, 34),
            ((835, 135), Direction.DOWN, 28),
            ((125, 565), Direction.UP, 25),
            ((825, 570), Direction.LEFT, 36),
        )
        for center, direction, size in decorations:
            self._draw_arrow(center, direction, size, (*DIRECTION_COLORS[direction], 120))

    def _draw_arrow(
        self,
        center: tuple[float, float],
        direction: Direction,
        size: float,
        color: tuple[int, ...],
        *,
        surface: pygame.Surface | None = None,
    ) -> None:
        target = surface or self.screen
        x, y = center
        shaft = size * 0.9
        half = size * 0.22
        head = size * 0.72
        points = [
            (-shaft, -half),
            (0, -half),
            (0, -head),
            (shaft, 0),
            (0, head),
            (0, half),
            (-shaft, half),
        ]
        angle = {
            Direction.RIGHT: 0,
            Direction.DOWN: math.pi / 2,
            Direction.LEFT: math.pi,
            Direction.UP: -math.pi / 2,
        }[direction]
        rotated = []
        for px, py in points:
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            rotated.append((x + rx, y + ry))
        pygame.draw.polygon(target, color, rotated)

    def _panel(self, rect: pygame.Rect, *, radius: int = 20) -> None:
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=radius)
        pygame.draw.rect(self.screen, PANEL_LIGHT, rect, width=1, border_radius=radius)

    def _button(self, rect: pygame.Rect, label: str, *, primary: bool = False) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        if primary:
            color = ACCENT_HOVER if hovered else ACCENT
            text_color = (30, 33, 43)
        else:
            color = (57, 79, 117) if hovered else PANEL_LIGHT
            text_color = TEXT
        pygame.draw.rect(self.screen, color, rect, border_radius=14)
        self._text(label, self.fonts["body"], text_color, rect.center, center=True)

    def _text(
        self,
        value: str,
        font: pygame.font.Font,
        color: tuple[int, ...],
        position: tuple[float, float],
        *,
        center: bool = False,
        right: bool = False,
    ) -> None:
        rendered = font.render(value, True, color)
        rect = rendered.get_rect()
        if center:
            rect.center = position
        elif right:
            rect.midright = position
        else:
            rect.midleft = position
        self.screen.blit(rendered, rect)

    @staticmethod
    def _font(size: int, *, bold: bool = False) -> pygame.font.Font:
        candidates = (
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msyh.ttc",
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "simhei.ttf",
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
        )
        for path in candidates:
            if path.exists():
                font = pygame.font.Font(str(path), size)
                font.set_bold(bold)
                return font
        return pygame.font.Font(None, size)


def main() -> None:
    try:
        ArrowGameApp().run()
    except pygame.error as exc:
        print(f"无法启动游戏窗口：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
