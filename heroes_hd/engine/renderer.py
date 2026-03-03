"""HD Renderer for Heroes HD - handles all drawing operations."""
import pygame
import math
from config import (TILE_SIZE, HEX_SIZE, TERRAIN_COLORS, FACTION_COLORS,
                    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_NORMAL,
                    COLOR_TEXT_HIGHLIGHT, COLOR_GOLD, COLOR_DARK_BG)


class Renderer:
    """Central rendering system for the game."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self._init_fonts()
        self._tile_cache: dict = {}
        self._hex_cache: dict = {}

    def _init_fonts(self):
        pygame.font.init()
        self.font_tiny = pygame.font.SysFont("Arial", 11)
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_medium = pygame.font.SysFont("Arial", 18)
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_huge = pygame.font.SysFont("Arial", 52, bold=True)

    # ── Primitives ──────────────────────────────────────────────────────────

    def clear(self, color=COLOR_DARK_BG):
        self.screen.fill(color)

    def draw_rect(self, rect, color, border=0, border_radius=0):
        pygame.draw.rect(self.screen, color, rect, border, border_radius=border_radius)

    def draw_border(self, rect, color, width=2, border_radius=0):
        pygame.draw.rect(self.screen, color, rect, width, border_radius=border_radius)

    def draw_line(self, start, end, color, width=1):
        pygame.draw.line(self.screen, color, start, end, width)

    def draw_circle(self, center, radius, color, width=0):
        pygame.draw.circle(self.screen, color, center, radius, width)

    def draw_text(self, text, pos, color=COLOR_TEXT_NORMAL, font=None, center=False, shadow=True):
        font = font or self.font_medium
        if shadow:
            shadow_surf = font.render(text, True, (0, 0, 0))
            if center:
                r = shadow_surf.get_rect(center=(pos[0] + 1, pos[1] + 1))
            else:
                r = (pos[0] + 1, pos[1] + 1)
            self.screen.blit(shadow_surf, r)
        surf = font.render(text, True, color)
        if center:
            r = surf.get_rect(center=pos)
            self.screen.blit(surf, r)
        else:
            self.screen.blit(surf, pos)
        return surf.get_rect(topleft=pos if not center else r.topleft)

    def draw_text_centered(self, text, rect, color=COLOR_TEXT_NORMAL, font=None):
        font = font or self.font_medium
        cx, cy = rect[0] + rect[2] // 2, rect[1] + rect[3] // 2
        self.draw_text(text, (cx, cy), color, font, center=True)

    # ── Panel / UI ───────────────────────────────────────────────────────────

    def draw_panel(self, rect, title=None, bg=None, border_color=None):
        bg = bg or COLOR_PANEL_BG
        border_color = border_color or COLOR_PANEL_BORDER
        pygame.draw.rect(self.screen, bg, rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=6)
        if title:
            self.draw_text_centered(title, (rect[0], rect[1] - 20, rect[2], 20),
                                    COLOR_GOLD, self.font_small)

    def draw_button(self, rect, text, hover=False, active=False, disabled=False):
        if disabled:
            bg = (40, 40, 40)
            text_color = (100, 100, 100)
            border = (80, 80, 80)
        elif active:
            bg = (80, 60, 20)
            text_color = COLOR_GOLD
            border = COLOR_GOLD
        elif hover:
            bg = (70, 55, 30)
            text_color = COLOR_TEXT_HIGHLIGHT
            border = (160, 140, 80)
        else:
            bg = (50, 40, 20)
            text_color = COLOR_TEXT_NORMAL
            border = COLOR_PANEL_BORDER
        pygame.draw.rect(self.screen, bg, rect, border_radius=4)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=4)
        self.draw_text_centered(text, rect, text_color, self.font_small)

    def draw_progress_bar(self, rect, value, max_value, fg_color, bg_color=(30, 30, 30)):
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=3)
        if max_value > 0:
            fill_w = int(rect[2] * value / max_value)
            if fill_w > 0:
                fill_rect = (rect[0], rect[1], fill_w, rect[3])
                pygame.draw.rect(self.screen, fg_color, fill_rect, border_radius=3)
        pygame.draw.rect(self.screen, (80, 80, 80), rect, 1, border_radius=3)

    # ── Terrain tile ─────────────────────────────────────────────────────────

    def get_terrain_tile(self, terrain_type: str, size=TILE_SIZE) -> pygame.Surface:
        key = (terrain_type, size)
        if key in self._tile_cache:
            return self._tile_cache[key]
        surf = pygame.Surface((size, size))
        base_color = TERRAIN_COLORS.get(terrain_type, (128, 128, 128))
        surf.fill(base_color)
        # Add texture variation
        self._add_terrain_texture(surf, terrain_type, size)
        self._tile_cache[key] = surf
        return surf

    def _add_terrain_texture(self, surf: pygame.Surface, terrain: str, size: int):
        import random
        rng = random.Random(hash(terrain) % 9999)
        base = TERRAIN_COLORS.get(terrain, (128, 128, 128))
        # Draw variation dots
        for _ in range(size // 4):
            x, y = rng.randint(0, size - 1), rng.randint(0, size - 1)
            var = rng.randint(-20, 20)
            c = tuple(max(0, min(255, base[i] + var)) for i in range(3))
            surf.set_at((x, y), c)
        # Draw grid border
        pygame.draw.rect(surf, tuple(max(0, c - 30) for c in base), (0, 0, size, size), 1)

    # ── Adventure map tile ───────────────────────────────────────────────────

    def draw_map_tile(self, terrain: str, rect, fog=False, selected=False):
        tile = self.get_terrain_tile(terrain, TILE_SIZE)
        self.screen.blit(tile, rect)
        if fog:
            fog_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            fog_surf.fill((0, 0, 0, 180))
            self.screen.blit(fog_surf, rect)
        if selected:
            pygame.draw.rect(self.screen, (255, 255, 100), rect, 2)

    # ── Hex grid (combat) ────────────────────────────────────────────────────

    def hex_to_pixel(self, col, row) -> tuple[int, int]:
        """Convert hex grid coordinates to pixel center."""
        x = HEX_SIZE * 2 * col + (row % 2) * HEX_SIZE
        y = int(HEX_SIZE * 1.732 * row)
        return x, y

    def get_hex_points(self, cx, cy, size=None) -> list[tuple[int, int]]:
        size = size or HEX_SIZE
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            px = cx + size * math.cos(angle)
            py = cy + size * math.sin(angle)
            points.append((int(px), int(py)))
        return points

    def draw_hex(self, col, row, offset_x, offset_y, color=None, border_color=None,
                 selected=False, reachable=False, attackable=False):
        cx, cy = self.hex_to_pixel(col, row)
        cx += offset_x
        cy += offset_y
        points = self.get_hex_points(cx, cy)

        # Fill
        if color:
            pygame.draw.polygon(self.screen, color, points)
        else:
            fill = (50, 70, 50) if (col + row) % 2 == 0 else (45, 65, 45)
            pygame.draw.polygon(self.screen, fill, points)

        # Overlays
        if reachable:
            overlay = pygame.Surface((HEX_SIZE * 2, HEX_SIZE * 2), pygame.SRCALPHA)
            pygame.draw.polygon(overlay, (100, 200, 100, 80),
                                [(p[0] - offset_x - cx + HEX_SIZE,
                                  p[1] - offset_y - cy + HEX_SIZE) for p in points])
        if attackable:
            pygame.draw.polygon(self.screen, (200, 80, 80, 0), points, 0)
            pygame.draw.polygon(self.screen, (220, 60, 60), points, 2)

        # Border
        bc = (255, 255, 100) if selected else (border_color or (30, 50, 30))
        pygame.draw.polygon(self.screen, bc, points, 1 if not selected else 2)

    # ── Creature card ────────────────────────────────────────────────────────

    def draw_creature_icon(self, rect, creature_data: dict, count: int = 0, selected=False):
        """Draw a creature unit card."""
        color = tuple(creature_data.get("color", [160, 160, 160]))
        border = (255, 220, 50) if selected else COLOR_PANEL_BORDER
        pygame.draw.rect(self.screen, tuple(max(0, c - 30) for c in color), rect, border_radius=4)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=4)

        # Draw simplified creature shape
        cx = rect[0] + rect[2] // 2
        cy = rect[1] + rect[3] // 2 - 4
        r = min(rect[2], rect[3]) // 3
        pygame.draw.circle(self.screen, color, (cx, cy), r)
        pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), r, 1)

        # Name (abbreviated)
        name = creature_data.get("name", "?")[:8]
        self.draw_text(name, (rect[0] + 2, rect[1] + 2), COLOR_TEXT_NORMAL, self.font_tiny)

        # Count
        if count > 0:
            count_str = str(count) if count < 1000 else f"{count // 1000}k"
            self.draw_text(count_str, (rect[0] + rect[2] - 30, rect[1] + rect[3] - 16),
                           COLOR_GOLD, self.font_small)

    # ── Hero portrait ────────────────────────────────────────────────────────

    def draw_hero_portrait(self, rect, hero_data: dict, player_color: tuple):
        """Draw a hero portrait."""
        pygame.draw.rect(self.screen, player_color, rect, border_radius=4)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, rect, 2, border_radius=4)
        cx, cy = rect[0] + rect[2] // 2, rect[1] + rect[3] // 2
        # Head
        r = min(rect[2], rect[3]) // 4
        pygame.draw.circle(self.screen, (220, 180, 140), (cx, cy - r // 2), r)
        # Body
        body_w = rect[2] * 2 // 3
        body_h = rect[3] // 3
        pygame.draw.rect(self.screen, player_color,
                         (cx - body_w // 2, cy + r // 2, body_w, body_h))
        # Name
        name = hero_data.get("name", "Hero")[:10]
        self.draw_text(name, (rect[0] + 2, rect[1] + rect[3] - 16), COLOR_GOLD, self.font_tiny)

    # ── Resource display ─────────────────────────────────────────────────────

    def draw_resources(self, resources: dict, y: int):
        """Draw resource bar across the bottom."""
        icons = {
            "gold": (COLOR_GOLD, "G"),
            "wood": ((100, 160, 60), "W"),
            "ore": ((140, 140, 140), "O"),
            "mercury": ((180, 80, 200), "Hg"),
            "sulfur": ((220, 180, 40), "Su"),
            "crystal": ((100, 200, 220), "Cr"),
            "gems": ((120, 200, 120), "Ge"),
        }
        x = 10
        for res, (color, abbr) in icons.items():
            val = resources.get(res, 0)
            pygame.draw.circle(self.screen, color, (x + 10, y + 12), 8)
            self.draw_text(f"{val}", (x + 22, y + 4), COLOR_TEXT_NORMAL, self.font_small)
            x += 90

    # ── Minimap ──────────────────────────────────────────────────────────────

    def draw_minimap(self, rect, game_map, camera_rect):
        """Draw a minimap of the entire adventure map."""
        pygame.draw.rect(self.screen, (20, 20, 20), rect)
        if not game_map:
            return
        map_w = game_map.width
        map_h = game_map.height
        cell_w = rect[2] / map_w
        cell_h = rect[3] / map_h

        for y in range(map_h):
            for x in range(map_w):
                tile = game_map.tiles[y][x]
                color = TERRAIN_COLORS.get(tile.terrain, (100, 100, 100))
                if not tile.explored:
                    color = (20, 20, 20)
                px = int(rect[0] + x * cell_w)
                py = int(rect[1] + y * cell_h)
                pw = max(1, int(cell_w))
                ph = max(1, int(cell_h))
                pygame.draw.rect(self.screen, color, (px, py, pw, ph))

        # Camera viewport rect on minimap
        cam_x = int(rect[0] + camera_rect[0] * cell_w)
        cam_y = int(rect[1] + camera_rect[1] * cell_h)
        cam_w = int(camera_rect[2] * cell_w)
        cam_h = int(camera_rect[3] * cell_h)
        pygame.draw.rect(self.screen, (255, 255, 255),
                         (cam_x, cam_y, cam_w, cam_h), 1)

        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, rect, 1)
