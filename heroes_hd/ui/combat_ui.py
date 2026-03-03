"""Combat screen UI for Heroes HD."""
import pygame
import math
from engine.state_machine import GameState
from game.combat import CombatManager, CombatUnit
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, HEX_SIZE, COMBAT_GRID_COLS,
                    COMBAT_GRID_ROWS, COLOR_DARK_BG, COLOR_GOLD,
                    COLOR_TEXT_NORMAL, COLOR_TEXT_HIGHLIGHT, COLOR_PANEL_BG,
                    COLOR_PANEL_BORDER, PLAYER_COLORS)

# Layout
COMBAT_AREA_X = 20
COMBAT_AREA_Y = 60
COMBAT_AREA_W = WINDOW_WIDTH - 320
COMBAT_AREA_H = WINDOW_HEIGHT - 180
SIDEBAR_X = WINDOW_WIDTH - 290
LOG_H = 120
LOG_Y = WINDOW_HEIGHT - LOG_H - 20

# Hex pixel dimensions
HEX_W = int(HEX_SIZE * 2)
HEX_H = int(HEX_SIZE * math.sqrt(3))
GRID_OFFSET_X = COMBAT_AREA_X + 20
GRID_OFFSET_Y = COMBAT_AREA_Y + 20


class CombatUIState(GameState):
    """Tactical hex-grid combat screen."""

    def __init__(self, game):
        super().__init__(game)
        self.combat: CombatManager = None
        self._active_unit: CombatUnit = None
        self._hovered_hex = None
        self._selected_spell = None
        self._phase = "move"  # move / attack / spell
        self._anim_t = 0.0
        self._log_scroll = 0
        self._result = None  # "attacker_wins" / "defender_wins" / "draw"
        self._show_result = False
        self._result_timer = 0.0

    def on_enter(self, previous_state=None, **kwargs):
        self.combat = self.game.current_combat
        if self.combat:
            self._active_unit = self.combat.next_turn()
        self._phase = "move"
        self._show_result = False
        self._result = None

    def handle_event(self, event):
        if self._show_result:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                return "adventure"
            return

        if event.type == pygame.MOUSEMOTION:
            self._handle_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_click(event.pos)
            elif event.button == 3:
                self._phase = "move"
        elif event.type == pygame.KEYDOWN:
            return self._handle_key(event)

    def _handle_hover(self, pos):
        col, row = self._screen_to_hex(pos)
        if 0 <= col < COMBAT_GRID_COLS and 0 <= row < COMBAT_GRID_ROWS:
            self._hovered_hex = (col, row)
        else:
            self._hovered_hex = None

    def _handle_click(self, pos):
        if not self.combat or not self._active_unit:
            return
        col, row = self._screen_to_hex(pos)
        if col < 0 or row < 0:
            return self._handle_ui_click(pos)

        unit = self._active_unit
        combat = self.combat

        if self._phase == "move":
            # Check if clicking on enemy (attack)
            target = self._get_unit_at(col, row)
            if target and target.player_id != unit.player_id and target.alive:
                result = combat.attack(unit, target)
                for msg in result["log"]:
                    self.combat.log.append(msg)
                self._check_combat_end()
                self._advance_turn()
            elif (col, row) in combat.reachable_hexes:
                combat.move_unit(unit, col, row)

        elif self._phase == "attack":
            target = self._get_unit_at(col, row)
            if target and target.player_id != unit.player_id and target.alive:
                result = combat.attack(unit, target)
                self._check_combat_end()
                self._advance_turn()
            self._phase = "move"

    def _handle_ui_click(self, pos):
        mx, my = pos
        # Action buttons
        btn_y = WINDOW_HEIGHT - 60
        buttons = self._get_action_buttons()
        for action, rect in buttons.items():
            if rect.collidepoint(pos):
                return self._handle_action(action)

    def _handle_key(self, event):
        if not self.combat or not self._active_unit:
            return
        if event.key == pygame.K_w:
            return self._handle_action("wait")
        elif event.key == pygame.K_d:
            return self._handle_action("defend")
        elif event.key == pygame.K_a:
            self._phase = "attack"
        elif event.key == pygame.K_ESCAPE:
            self._phase = "move"

    def _handle_action(self, action: str):
        if not self.combat or not self._active_unit:
            return
        unit = self._active_unit
        if action == "wait":
            self.combat.wait(unit)
            self._advance_turn()
        elif action == "defend":
            self.combat.defend(unit)
            self._advance_turn()
        elif action == "attack":
            self._phase = "attack"

    def _advance_turn(self):
        winner = self.combat.is_combat_over()
        if winner is not None:
            self._result = winner
            self._show_result = True
            self._result_timer = 3.0
            # Apply results to game
            if self.game.game_manager:
                self.game.game_manager.apply_combat_result(self.combat)
            return

        self._active_unit = self.combat.next_turn()
        if not self._active_unit:
            self._advance_turn()
        else:
            # Auto-advance AI turns
            gm = self.game.game_manager
            if (gm and self._active_unit and
                    self._active_unit.player_id != gm.human_player_id):
                self._ai_take_turn()

    def _ai_take_turn(self):
        """Simple AI combat logic."""
        unit = self._active_unit
        combat = self.combat
        if not unit or not unit.alive:
            return

        # Find best target
        enemies = [u for u in combat.units
                   if u.alive and u.player_id != unit.player_id]
        if not enemies:
            self._advance_turn()
            return

        # Target weakest enemy
        target = min(enemies, key=lambda u: u.total_hp)

        if unit.is_ranged:
            # Shoot directly
            result = combat.attack(unit, target)
        else:
            # Move toward target then attack
            attack_hexes = [h for h in combat.grid.neighbors(target.col, target.row)
                            if h in combat.reachable_hexes or h == (unit.col, unit.row)]
            if attack_hexes:
                best_hex = min(attack_hexes,
                               key=lambda h: combat.grid.distance(h[0], h[1], target.col, target.row))
                if best_hex != (unit.col, unit.row):
                    combat.move_unit(unit, best_hex[0], best_hex[1])
                result = combat.attack(unit, target)
            else:
                # Move toward target
                if combat.reachable_hexes:
                    best = min(combat.reachable_hexes,
                               key=lambda h: combat.grid.distance(h[0], h[1], target.col, target.row))
                    combat.move_unit(unit, best[0], best[1])
                    unit.has_acted = True

        self._check_combat_end()
        self._advance_turn()

    def _check_combat_end(self):
        winner = self.combat.is_combat_over()
        if winner is not None:
            self._result = winner
            self._show_result = True

    def _get_unit_at(self, col: int, row: int) -> CombatUnit:
        if not self.combat:
            return None
        for unit in self.combat.units:
            if unit.alive and unit.col == col and unit.row == row:
                return unit
        return None

    def _screen_to_hex(self, pos) -> tuple[int, int]:
        mx, my = pos
        # Approximate inverse hex to pixel
        col = (mx - GRID_OFFSET_X) // HEX_W
        row = (my - GRID_OFFSET_Y) // HEX_H
        return int(col), int(row)

    def _hex_to_screen(self, col: int, row: int) -> tuple[int, int]:
        x = GRID_OFFSET_X + col * HEX_W + (row % 2) * HEX_SIZE
        y = GRID_OFFSET_Y + row * HEX_H
        return int(x), int(y)

    def _get_action_buttons(self) -> dict[str, pygame.Rect]:
        y = WINDOW_HEIGHT - 56
        return {
            "attack": pygame.Rect(20, y, 100, 44),
            "wait": pygame.Rect(130, y, 100, 44),
            "defend": pygame.Rect(240, y, 100, 44),
        }

    def update(self, dt: float):
        self._anim_t += dt
        if self._show_result:
            self._result_timer -= dt

    def draw(self, renderer):
        renderer.clear((20, 30, 20))
        if not self.combat:
            renderer.draw_text("No combat in progress", (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
                               COLOR_GOLD, renderer.font_large, center=True)
            return

        self._draw_background(renderer)
        self._draw_hex_grid(renderer)
        self._draw_units(renderer)
        self._draw_sidebar(renderer)
        self._draw_bottom_bar(renderer)
        self._draw_combat_log(renderer)

        if self._show_result:
            self._draw_result_overlay(renderer)

    def _draw_background(self, renderer):
        terrain_colors = {
            "grass": (40, 80, 40),
            "dirt": (100, 70, 40),
            "snow": (180, 200, 220),
            "sand": (160, 140, 80),
            "lava": (100, 40, 20),
            "swamp": (60, 80, 40),
        }
        terrain = getattr(self.combat, "terrain", "grass")
        bg_color = terrain_colors.get(terrain, (40, 80, 40))
        pygame.draw.rect(renderer.screen, bg_color,
                         (COMBAT_AREA_X, COMBAT_AREA_Y, COMBAT_AREA_W, COMBAT_AREA_H))

    def _draw_hex_grid(self, renderer):
        combat = self.combat
        unit = self._active_unit

        for row in range(COMBAT_GRID_ROWS):
            for col in range(COMBAT_GRID_COLS):
                cx, cy = self._hex_to_screen(col, row)
                points = self._hex_points(cx + HEX_SIZE, cy + HEX_SIZE // 2)

                # Determine fill color
                is_reachable = unit and (col, row) in combat.reachable_hexes
                is_hovered = self._hovered_hex == (col, row)
                is_obstacle = (col, row) in combat.grid.obstacles

                if is_obstacle:
                    fill = (80, 60, 40)
                elif is_hovered:
                    fill = (80, 100, 80)
                elif is_reachable:
                    fill = (60, 100, 60)
                else:
                    fill = (50, 70, 50) if (col + row) % 2 == 0 else (45, 65, 45)

                pygame.draw.polygon(renderer.screen, fill, points)

                # Attackable highlight
                if unit and self._hovered_hex == (col, row):
                    target = self._get_unit_at(col, row)
                    if target and target.player_id != unit.player_id:
                        pygame.draw.polygon(renderer.screen, (200, 60, 60), points, 3)
                    else:
                        pygame.draw.polygon(renderer.screen, (100, 150, 100), points, 1)
                else:
                    pygame.draw.polygon(renderer.screen, (30, 50, 30), points, 1)

    def _hex_points(self, cx: int, cy: int) -> list[tuple[int, int]]:
        pts = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            pts.append((int(cx + HEX_SIZE * math.cos(angle)),
                        int(cy + HEX_SIZE * math.sin(angle))))
        return pts

    def _draw_units(self, renderer):
        combat = self.combat
        anim_pulse = abs(math.sin(self._anim_t * 3))

        for unit in combat.units:
            if not unit.alive:
                continue
            cx, cy = self._hex_to_screen(unit.col, unit.row)
            cx += HEX_SIZE
            cy += HEX_SIZE // 2

            # Determine color
            color = tuple(unit.creature_data.get("color", [160, 160, 160]))
            player_color = PLAYER_COLORS[unit.player_id] if unit.player_id < len(PLAYER_COLORS) else color

            # Active unit pulsing outline
            is_active = (unit is self._active_unit)
            if is_active:
                pulse_r = int(HEX_SIZE * 0.8 + anim_pulse * 4)
                pygame.draw.circle(renderer.screen, (255, 255, 100), (cx, cy), pulse_r, 3)

            # Draw creature body
            body_r = int(HEX_SIZE * 0.6)
            pygame.draw.circle(renderer.screen, color, (cx, cy), body_r)
            pygame.draw.circle(renderer.screen, player_color, (cx, cy), body_r, 2)

            # Player indicator dot
            pygame.draw.circle(renderer.screen, player_color, (cx - body_r // 2, cy - body_r), 5)

            # Count
            count_str = str(unit.count)
            renderer.draw_text(count_str, (cx, cy),
                               (0, 0, 0), renderer.font_small, center=True, shadow=False)

            # HP bar
            hp = unit.creature_data.get("hp", 10)
            hp_frac = unit.current_hp / hp
            bar_w = body_r * 2
            bar_x = cx - body_r
            bar_y = cy + body_r + 2
            pygame.draw.rect(renderer.screen, (60, 0, 0), (bar_x, bar_y, bar_w, 5))
            pygame.draw.rect(renderer.screen, (0, 200, 0), (bar_x, bar_y, int(bar_w * hp_frac), 5))

            # Creature name (abbreviated)
            name = unit.creature_data.get("name", "?")[:8]
            renderer.draw_text(name, (cx, cy - body_r - 12),
                               COLOR_TEXT_NORMAL, renderer.font_tiny, center=True)

            # Status effects
            effect_y = bar_y + 8
            for eff in unit.effects:
                eff_color = {
                    "bless": (255, 220, 80), "curse": (180, 60, 60),
                    "speed_boost": (100, 220, 100), "speed_reduction": (180, 80, 80),
                    "blind": (200, 200, 200), "defense_boost": (80, 120, 220),
                }.get(eff["type"], (200, 200, 200))
                pygame.draw.circle(renderer.screen, eff_color, (cx - 8, effect_y), 4)
                effect_y += 10

    def _draw_sidebar(self, renderer):
        panel_rect = (SIDEBAR_X, 20, 280, WINDOW_HEIGHT - 40)
        renderer.draw_panel(panel_rect, "Combat Info")

        combat = self.combat
        y = 50

        # Turn info
        renderer.draw_text(f"Round {combat.turn_number + 1}",
                           (SIDEBAR_X + 8, y), COLOR_GOLD, renderer.font_medium)
        y += 28

        # Active unit info
        if self._active_unit:
            unit = self._active_unit
            pid = unit.player_id
            player_color = PLAYER_COLORS[pid] if pid < len(PLAYER_COLORS) else (200, 200, 200)

            renderer.draw_text("Active Unit:", (SIDEBAR_X + 8, y),
                               COLOR_TEXT_NORMAL, renderer.font_small)
            y += 20
            renderer.draw_text(unit.creature_data.get("name", "?"),
                               (SIDEBAR_X + 8, y), player_color, renderer.font_medium)
            y += 24
            renderer.draw_text(f"Count: {unit.count}", (SIDEBAR_X + 8, y),
                               COLOR_TEXT_NORMAL, renderer.font_small)
            y += 18
            renderer.draw_text(f"HP: {unit.current_hp}/{unit.creature_data.get('hp', 10)}",
                               (SIDEBAR_X + 8, y), (100, 220, 100), renderer.font_small)
            y += 18
            renderer.draw_text(f"Speed: {unit.speed}", (SIDEBAR_X + 8, y),
                               COLOR_TEXT_NORMAL, renderer.font_small)
            y += 18
            renderer.draw_text(f"ATK: {unit.attack}  DEF: {unit.defense}",
                               (SIDEBAR_X + 8, y), COLOR_TEXT_NORMAL, renderer.font_small)
            y += 22

            # Abilities
            abilities = unit.creature_data.get("abilities", [])
            if abilities:
                renderer.draw_text("Abilities:", (SIDEBAR_X + 8, y),
                                   COLOR_GOLD, renderer.font_small)
                y += 16
                for ab in abilities[:4]:
                    renderer.draw_text(f"• {ab.replace('_', ' ').title()}",
                                       (SIDEBAR_X + 12, y), COLOR_TEXT_NORMAL, renderer.font_tiny)
                    y += 13

        y += 20
        pygame.draw.line(renderer.screen, COLOR_PANEL_BORDER,
                         (SIDEBAR_X + 4, y), (SIDEBAR_X + 276, y))
        y += 10

        # Unit summary
        renderer.draw_text("Units Remaining:", (SIDEBAR_X + 8, y),
                           COLOR_GOLD, renderer.font_small)
        y += 20
        for pid in range(2):
            units_alive = [u for u in combat.units if u.alive and u.player_id == pid]
            total = sum(u.count for u in units_alive)
            p_color = PLAYER_COLORS[pid] if pid < len(PLAYER_COLORS) else (200, 200, 200)
            renderer.draw_text(f"P{pid+1}: {total} creatures ({len(units_alive)} stacks)",
                               (SIDEBAR_X + 8, y), p_color, renderer.font_small)
            y += 20

    def _draw_bottom_bar(self, renderer):
        bar_rect = (0, WINDOW_HEIGHT - 64, SIDEBAR_X, 64)
        renderer.draw_panel(bar_rect)

        # Action buttons
        mx, my = pygame.mouse.get_pos()
        buttons = self._get_action_buttons()
        labels = {"attack": "Attack [A]", "wait": "Wait [W]", "defend": "Defend [D]"}
        for action, rect in buttons.items():
            renderer.draw_button(rect, labels[action], hover=rect.collidepoint(mx, my))

        # Phase indicator
        phase_text = {"move": "Select: Move or Attack", "attack": "Select Target to Attack",
                      "spell": "Select Spell Target"}
        renderer.draw_text(phase_text.get(self._phase, ""),
                           (400, WINDOW_HEIGHT - 40),
                           COLOR_TEXT_HIGHLIGHT, renderer.font_small)

    def _draw_combat_log(self, renderer):
        log_rect = (SIDEBAR_X, LOG_Y, 280, LOG_H)
        renderer.draw_panel(log_rect, "Combat Log")
        log = self.combat.log[-6:] if self.combat else []
        for i, entry in enumerate(log):
            renderer.draw_text(entry[:38], (SIDEBAR_X + 6, LOG_Y + 18 + i * 16),
                               COLOR_TEXT_NORMAL, renderer.font_tiny)

    def _draw_result_overlay(self, renderer):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        renderer.screen.blit(overlay, (0, 0))

        result = self._result
        if result == -1:
            msg = "Draw!"
            color = (200, 200, 200)
        elif result == 0:
            msg = "Attacker Victorious!"
            color = PLAYER_COLORS[0]
        elif result == 1:
            msg = "Defender Victorious!"
            color = PLAYER_COLORS[1]
        else:
            msg = f"Player {result} Wins!"
            color = PLAYER_COLORS[result % len(PLAYER_COLORS)]

        renderer.draw_text(msg, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40),
                           color, renderer.font_huge, center=True)
        renderer.draw_text("Click or press any key to continue...",
                           (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40),
                           COLOR_TEXT_NORMAL, renderer.font_medium, center=True)

        # Show survivors
        if self.combat:
            survivors = [u for u in self.combat.units if u.alive]
            y = WINDOW_HEIGHT // 2 + 80
            renderer.draw_text("Survivors:", (WINDOW_WIDTH // 2, y),
                               COLOR_GOLD, renderer.font_medium, center=True)
            y += 28
            for u in survivors:
                p_color = PLAYER_COLORS[u.player_id % len(PLAYER_COLORS)]
                renderer.draw_text(f"{u.creature_data.get('name', '?')} x{u.count}",
                                   (WINDOW_WIDTH // 2, y), p_color, renderer.font_small, center=True)
                y += 20
