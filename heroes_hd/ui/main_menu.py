"""Main menu screen for Heroes HD."""
import pygame
from engine.state_machine import GameState
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_DARK_BG, COLOR_GOLD,
                    COLOR_TEXT_NORMAL, COLOR_TEXT_HIGHLIGHT, COLOR_PANEL_BG,
                    COLOR_PANEL_BORDER, ALL_FACTIONS, FACTION_COLORS,
                    MAP_SMALL, MAP_MEDIUM, MAP_LARGE, MAP_EXTRA_LARGE)


class MainMenuState(GameState):
    """The main menu of Heroes HD."""

    MENU_ITEMS = [
        ("New Game",     "new_game"),
        ("Random Map",   "random_map"),
        ("Load Game",    "load_game"),
        ("Credits",      "credits"),
        ("Quit",         "quit"),
    ]

    def __init__(self, game):
        super().__init__(game)
        self._hovered = -1
        self._phase = "main"  # main / new_game / random_map
        self._anim_t = 0.0

    def on_enter(self, previous_state=None, **kwargs):
        self._phase = "main"
        self._hovered = -1

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._phase = "main"

    def _update_hover(self, pos):
        self._hovered = -1
        for i, rect in enumerate(self._get_menu_rects()):
            if rect.collidepoint(pos):
                self._hovered = i

    def _handle_click(self, pos):
        for i, rect in enumerate(self._get_menu_rects()):
            if rect.collidepoint(pos):
                _, action = self.MENU_ITEMS[i]
                if action == "quit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif action == "new_game":
                    self.game.start_new_game()
                    return "adventure"
                elif action == "random_map":
                    self.game.start_random_map()
                    return "adventure"
                elif action == "credits":
                    self._phase = "credits"

    def _get_menu_rects(self):
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2 - 60
        rects = []
        for i in range(len(self.MENU_ITEMS)):
            r = pygame.Rect(cx - 150, cy + i * 60, 300, 48)
            rects.append(r)
        return rects

    def update(self, dt: float):
        self._anim_t += dt

    def draw(self, renderer):
        renderer.clear(COLOR_DARK_BG)

        # Animated star background
        self._draw_stars(renderer)

        # Title
        title_y = 80
        renderer.draw_text("Heroes of Might & Magic III",
                           (WINDOW_WIDTH // 2, title_y),
                           COLOR_GOLD, renderer.font_title, center=True)
        renderer.draw_text("HD Edition",
                           (WINDOW_WIDTH // 2, title_y + 50),
                           COLOR_TEXT_HIGHLIGHT, renderer.font_large, center=True)

        if self._phase == "main":
            self._draw_main_menu(renderer)
        elif self._phase == "credits":
            self._draw_credits(renderer)

    def _draw_stars(self, renderer):
        import math
        for i in range(80):
            x = (i * 239 + int(self._anim_t * 20)) % WINDOW_WIDTH
            y = (i * 173) % WINDOW_HEIGHT
            r = 1 + (i % 3)
            brightness = int(150 + 100 * math.sin(self._anim_t * 0.5 + i))
            pygame.draw.circle(renderer.screen, (brightness, brightness, brightness), (x, y), r)

    def _draw_main_menu(self, renderer):
        rects = self._get_menu_rects()
        for i, rect in enumerate(rects):
            label, _ = self.MENU_ITEMS[i]
            renderer.draw_button(rect, label, hover=(self._hovered == i))

        # Version info
        renderer.draw_text("v1.0 HD — Fan Recreation",
                           (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30),
                           (120, 110, 80), renderer.font_small, center=True)

    def _draw_credits(self, renderer):
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        lines = [
            "Heroes of Might & Magic III HD Edition",
            "",
            "Original game by New World Computing",
            "Published by 3DO / Ubisoft",
            "",
            "This is a fan-made recreation for educational purposes.",
            "All 9 original factions recreated:",
            "Castle, Rampart, Tower, Inferno, Necropolis,",
            "Dungeon, Stronghold, Fortress, Conflux",
            "",
            "Press ESC to return",
        ]
        renderer.draw_panel((cx - 400, cy - 250, 800, 500), "Credits")
        for i, line in enumerate(lines):
            renderer.draw_text(line, (cx, cy - 200 + i * 30),
                               COLOR_TEXT_NORMAL, renderer.font_small, center=True)
