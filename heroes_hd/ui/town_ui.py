"""Town screen UI for Heroes HD."""
import pygame
from engine.state_machine import GameState
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_DARK_BG, COLOR_GOLD,
                    COLOR_TEXT_NORMAL, COLOR_TEXT_HIGHLIGHT, COLOR_PANEL_BG,
                    COLOR_PANEL_BORDER, FACTION_COLORS)
from data_loader import DataLoader


class TownUIState(GameState):
    """Town management screen."""

    TAB_OVERVIEW = 0
    TAB_BUILD = 1
    TAB_RECRUIT = 2
    TAB_GARRISON = 3

    def __init__(self, game):
        super().__init__(game)
        self._town = None
        self._player = None
        self._tab = self.TAB_OVERVIEW
        self._hovered_building = None
        self._hovered_creature = None
        self._message = ""
        self._msg_timer = 0.0
        self._creature_db = {}

    def on_enter(self, previous_state=None, **kwargs):
        self._town = self.game.current_town
        self._player = self.game.game_manager.current_player if self.game.game_manager else None
        self._tab = self.TAB_OVERVIEW
        self._creature_db = DataLoader.load_creatures()
        self._message = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "adventure"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_hover(event.pos)

    def _handle_click(self, pos):
        mx, my = pos
        # Tabs
        tab_rects = self._get_tab_rects()
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(pos):
                self._tab = i
                return

        # Close button
        close_rect = pygame.Rect(WINDOW_WIDTH - 120, 20, 100, 36)
        if close_rect.collidepoint(pos):
            return "adventure"

        if self._tab == self.TAB_BUILD:
            self._handle_build_click(pos)
        elif self._tab == self.TAB_RECRUIT:
            self._handle_recruit_click(pos)

    def _handle_build_click(self, pos):
        if not self._town or not self._player:
            return
        buildings = self._town.get_available_buildings()
        rects = self._get_building_rects(buildings)
        for i, (bdata, rect) in enumerate(zip(buildings, rects)):
            if rect.collidepoint(pos):
                ok, msg = self._town.build(bdata["id"], self._player.resources)
                self._show_message(msg)
                break

    def _handle_recruit_click(self, pos):
        if not self._town or not self._player:
            return
        recruitable = self._town.get_recruitable_creatures()
        rects = self._get_recruit_rects(recruitable)
        for i, ((cid, count), rect) in enumerate(zip(recruitable, rects)):
            if rect.collidepoint(pos) and count > 0:
                # Recruit all
                ok, msg = self._town.recruit(
                    cid, count, self._player.resources, self._creature_db
                )
                if ok:
                    # Add to visiting hero
                    for hero in self._player.heroes:
                        if hero.map_x == self._town.map_x and hero.map_y == self._town.map_y:
                            hero.add_creature(cid, count)
                            break
                self._show_message(msg)
                break

    def _handle_hover(self, pos):
        self._hovered_building = None
        self._hovered_creature = None
        if self._tab == self.TAB_BUILD and self._town:
            buildings = self._town.get_available_buildings()
            for bdata, rect in zip(buildings, self._get_building_rects(buildings)):
                if rect.collidepoint(pos):
                    self._hovered_building = bdata
                    break

    def _get_tab_rects(self):
        tabs = ["Overview", "Build", "Recruit", "Garrison"]
        rects = []
        for i, tab in enumerate(tabs):
            rects.append(pygame.Rect(20 + i * 160, 70, 150, 36))
        return rects

    def _get_building_rects(self, buildings):
        rects = []
        cols, rows = 3, 6
        w, h = (WINDOW_WIDTH - 80) // cols, 48
        for i, b in enumerate(buildings[:18]):
            col = i % cols
            row = i // cols
            rects.append(pygame.Rect(40 + col * w, 130 + row * (h + 8), w - 8, h))
        return rects

    def _get_recruit_rects(self, recruitable):
        rects = []
        for i in range(len(recruitable)):
            rects.append(pygame.Rect(40, 130 + i * 64, WINDOW_WIDTH - 80, 56))
        return rects

    def _show_message(self, msg: str):
        self._message = msg
        self._msg_timer = 3.0

    def update(self, dt: float):
        if self._msg_timer > 0:
            self._msg_timer -= dt

    def draw(self, renderer):
        renderer.clear(COLOR_DARK_BG)
        if not self._town:
            renderer.draw_text("No town selected", (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
                               COLOR_GOLD, renderer.font_large, center=True)
            return

        self._draw_header(renderer)
        self._draw_tabs(renderer)

        if self._tab == self.TAB_OVERVIEW:
            self._draw_overview(renderer)
        elif self._tab == self.TAB_BUILD:
            self._draw_build(renderer)
        elif self._tab == self.TAB_RECRUIT:
            self._draw_recruit(renderer)
        elif self._tab == self.TAB_GARRISON:
            self._draw_garrison(renderer)

        self._draw_message(renderer)
        self._draw_close_button(renderer)

    def _draw_header(self, renderer):
        town = self._town
        faction_color = FACTION_COLORS.get(town.faction, (200, 200, 200))
        renderer.draw_text(f"{town.name}", (WINDOW_WIDTH // 2, 20),
                           faction_color, renderer.font_title, center=True)
        renderer.draw_text(f"{town.faction.title()} Town",
                           (WINDOW_WIDTH // 2, 52),
                           COLOR_TEXT_NORMAL, renderer.font_medium, center=True)

        # Town illustration (drawn procedurally)
        self._draw_town_illustration(renderer, faction_color)

    def _draw_town_illustration(self, renderer, color):
        """Draw a simple procedural town illustration."""
        # Background sky
        sky_rect = (0, 0, WINDOW_WIDTH, 60)
        pygame.draw.rect(renderer.screen, (20, 30, 60), sky_rect)

        # Town silhouette
        cx, cy = WINDOW_WIDTH // 2, 50
        faction = self._town.faction
        if faction == "castle":
            self._draw_castle_silhouette(renderer, cx, cy, color)
        elif faction == "necropolis":
            self._draw_necropolis_silhouette(renderer, cx, cy, color)
        else:
            self._draw_generic_town_silhouette(renderer, cx, cy, color)

    def _draw_castle_silhouette(self, renderer, cx, cy, color):
        # Main keep
        pygame.draw.rect(renderer.screen, color, (cx - 30, 20, 60, 40))
        # Towers
        for tx in [cx - 50, cx + 30]:
            pygame.draw.rect(renderer.screen, color, (tx, 25, 20, 35))
            pygame.draw.polygon(renderer.screen, (180, 160, 120),
                                [(tx, 25), (tx + 10, 10), (tx + 20, 25)])
        # Gate
        pygame.draw.rect(renderer.screen, (20, 15, 10), (cx - 10, 42, 20, 18))

    def _draw_necropolis_silhouette(self, renderer, cx, cy, color):
        # Spires
        for tx in [cx - 40, cx, cx + 40]:
            h = 50 if tx == cx else 35
            pygame.draw.polygon(renderer.screen, color,
                                [(tx - 8, 60), (tx, 60 - h), (tx + 8, 60)])

    def _draw_generic_town_silhouette(self, renderer, cx, cy, color):
        pygame.draw.rect(renderer.screen, color, (cx - 40, 25, 80, 35))
        pygame.draw.polygon(renderer.screen, (180, 150, 100),
                            [(cx - 45, 25), (cx, 8), (cx + 45, 25)])

    def _draw_tabs(self, renderer):
        tabs = ["Overview", "Build", "Recruit", "Garrison"]
        rects = self._get_tab_rects()
        mx, my = pygame.mouse.get_pos()
        for i, (tab, rect) in enumerate(zip(tabs, rects)):
            active = (i == self._tab)
            renderer.draw_button(rect, tab, hover=rect.collidepoint(mx, my), active=active)

    def _draw_overview(self, renderer):
        town = self._town
        y = 130
        # Daily income
        income = town.get_daily_income()
        renderer.draw_text("Daily Income:", (40, y), COLOR_GOLD, renderer.font_medium)
        y += 30
        for res, amount in income.items():
            renderer.draw_text(f"  +{amount} {res.title()}", (40, y),
                               COLOR_TEXT_NORMAL, renderer.font_small)
            y += 22
        y += 20
        # Built buildings
        renderer.draw_text("Built Buildings:", (40, y), COLOR_GOLD, renderer.font_medium)
        y += 30
        from game.town import BUILDINGS
        all_b = {b["id"]: b for b in BUILDINGS.get(town.faction, [])}
        cols = 3
        for i, bid in enumerate(sorted(town.buildings)):
            bdata = all_b.get(bid, {"name": bid})
            col = i % cols
            row = i // cols
            renderer.draw_text(f"• {bdata.get('name', bid)}",
                               (40 + col * 350, y + row * 20),
                               COLOR_TEXT_NORMAL, renderer.font_small)
        y += (len(town.buildings) // cols + 1) * 20 + 20

        # Mage guild spells
        guild_level = sum(1 for b in town.buildings if "mage_guild" in b)
        if guild_level > 0:
            renderer.draw_text(f"Mage Guild (Level {guild_level}):", (40, y),
                               COLOR_GOLD, renderer.font_medium)
            y += 30
            spells = town.get_spells_for_level(guild_level)
            for spell_id in spells:
                renderer.draw_text(f"  {spell_id.replace('_', ' ').title()}", (40, y),
                                   (100, 160, 220), renderer.font_small)
                y += 18

    def _draw_build(self, renderer):
        town = self._town
        player = self._player
        buildings = town.get_available_buildings()
        if not buildings:
            renderer.draw_text("All buildings constructed!", (WINDOW_WIDTH // 2, 250),
                               COLOR_GOLD, renderer.font_large, center=True)
            return

        rects = self._get_building_rects(buildings)
        mx, my = pygame.mouse.get_pos()
        from game.town import BUILDINGS

        for bdata, rect in zip(buildings, rects):
            can_afford = player and player.resources.can_afford(bdata.get("cost", {}))
            hover = rect.collidepoint(mx, my)
            renderer.draw_button(rect, bdata["name"], hover=hover, disabled=not can_afford)

            # Cost display
            cost_strs = [f"{res}: {amt}" for res, amt in bdata.get("cost", {}).items()]
            cost_text = " | ".join(cost_strs)
            renderer.draw_text(cost_text, (rect.x + 4, rect.bottom - 14),
                               COLOR_GOLD if can_afford else (120, 100, 60),
                               renderer.font_tiny)

        # Tooltip
        if self._hovered_building:
            b = self._hovered_building
            tip = f"{b['name']}: {b.get('description', '')}"
            renderer.draw_text(tip, (40, WINDOW_HEIGHT - 60),
                               COLOR_TEXT_HIGHLIGHT, renderer.font_small)

    def _draw_recruit(self, renderer):
        town = self._town
        player = self._player
        recruitable = town.get_recruitable_creatures()

        if not recruitable:
            renderer.draw_text("No creatures available to recruit.", (WINDOW_WIDTH // 2, 250),
                               COLOR_TEXT_NORMAL, renderer.font_medium, center=True)
            return

        rects = self._get_recruit_rects(recruitable)
        mx, my = pygame.mouse.get_pos()

        for (cid, count), rect in zip(recruitable, rects):
            cdata = self._creature_db.get(cid, {})
            can_afford = (count > 0 and player and
                          player.resources.can_afford(
                              {r: a * count for r, a in cdata.get("cost", {}).items()}))
            hover = rect.collidepoint(mx, my)

            renderer.draw_panel(rect)
            color = tuple(cdata.get("color", [160, 160, 160]))

            # Creature circle
            pygame.draw.circle(renderer.screen, color,
                               (rect.x + 30, rect.centery), 22)

            # Name and stats
            renderer.draw_text(cdata.get("name", cid), (rect.x + 60, rect.y + 6),
                               color, renderer.font_medium)
            stats_text = (f"ATK:{cdata.get('attack',0)} "
                          f"DEF:{cdata.get('defense',0)} "
                          f"HP:{cdata.get('hp',0)} "
                          f"SPD:{cdata.get('speed',0)}")
            renderer.draw_text(stats_text, (rect.x + 60, rect.y + 28),
                               COLOR_TEXT_NORMAL, renderer.font_tiny)

            # Count and cost
            cost = cdata.get("cost", {})
            cost_str = " ".join(f"{amt}{res[:2]}" for res, amt in cost.items())
            renderer.draw_text(f"Available: {count} | Cost each: {cost_str}",
                               (rect.x + 60, rect.y + 42),
                               COLOR_GOLD if can_afford else (150, 120, 60),
                               renderer.font_tiny)

            # Recruit button
            btn_rect = pygame.Rect(rect.right - 160, rect.y + 8, 150, 40)
            renderer.draw_button(btn_rect, f"Recruit All ({count})",
                                 hover=hover, disabled=not can_afford)

    def _draw_garrison(self, renderer):
        town = self._town
        y = 130
        renderer.draw_text("Garrison Troops:", (40, y), COLOR_GOLD, renderer.font_medium)
        y += 30
        if not town.garrison:
            renderer.draw_text("No troops garrisoned.", (40, y),
                               COLOR_TEXT_NORMAL, renderer.font_small)
            return
        for slot, stack in sorted(town.garrison.items()):
            cdata = self._creature_db.get(stack["creature"], {})
            renderer.draw_text(f"Slot {slot}: {cdata.get('name', stack['creature'])} x{stack['count']}",
                               (40, y), COLOR_TEXT_NORMAL, renderer.font_small)
            y += 24

    def _draw_message(self, renderer):
        if self._message and self._msg_timer > 0:
            msg_rect = pygame.Rect(WINDOW_WIDTH // 2 - 300, WINDOW_HEIGHT - 50, 600, 36)
            pygame.draw.rect(renderer.screen, COLOR_PANEL_BG, msg_rect, border_radius=6)
            pygame.draw.rect(renderer.screen, COLOR_PANEL_BORDER, msg_rect, 2, border_radius=6)
            renderer.draw_text(self._message, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 32),
                               COLOR_TEXT_HIGHLIGHT, renderer.font_medium, center=True)

    def _draw_close_button(self, renderer):
        close_rect = pygame.Rect(WINDOW_WIDTH - 120, 20, 100, 36)
        mx, my = pygame.mouse.get_pos()
        renderer.draw_button(close_rect, "Back [ESC]", hover=close_rect.collidepoint(mx, my))
