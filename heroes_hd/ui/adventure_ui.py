"""Adventure map UI screen for Heroes HD."""
import pygame
from engine.state_machine import GameState
from engine.camera import Camera
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE, COLOR_DARK_BG,
                    COLOR_GOLD, COLOR_TEXT_NORMAL, COLOR_PANEL_BG,
                    COLOR_PANEL_BORDER, COLOR_TEXT_HIGHLIGHT, OBJ_TOWN,
                    OBJ_HERO, OBJ_MINE, OBJ_RESOURCE, OBJ_ARTIFACT,
                    OBJ_MONSTER, OBJ_SHRINE, OBJ_WELL, OBJ_TREASURE_CHEST,
                    PLAYER_COLORS, TERRAIN_COLORS, FACTION_COLORS)

# Layout constants
SIDEBAR_W = 256
MAP_VIEWPORT_W = WINDOW_WIDTH - SIDEBAR_W
MAP_VIEWPORT_H = WINDOW_HEIGHT - 60  # 60px for bottom bar
BOTTOM_BAR_Y = WINDOW_HEIGHT - 60
MINIMAP_W = 256
MINIMAP_H = 200


class AdventureUIState(GameState):
    """The adventure map gameplay screen."""

    def __init__(self, game):
        super().__init__(game)
        self.camera = None
        self._selected_hero = None
        self._hovered_tile = None
        self._reachable_tiles = set()
        self._path_preview = []
        self._show_hero_panel = True
        self._anim_t = 0.0
        self._msg_queue: list[dict] = []  # {text, timer, color}
        self._context_menu = None  # {x, y, options}

    def on_enter(self, previous_state=None, **kwargs):
        gm = self.game.game_manager
        if gm and gm.game_map:
            self.camera = Camera(
                gm.game_map.width, gm.game_map.height,
                MAP_VIEWPORT_W, MAP_VIEWPORT_H
            )
            # Center on first human hero or first town
            player = gm.current_player
            if player and player.heroes:
                h = player.heroes[0]
                self.camera.center_on_tile(h.map_x, h.map_y)
            elif player and player.towns:
                t = player.towns[0]
                self.camera.center_on_tile(t.map_x, t.map_y)
            self._selected_hero = player.heroes[0] if player and player.heroes else None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_left_click(event.pos)
            elif event.button == 3:
                return self._handle_right_click(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_move(event.pos)
        elif event.type == pygame.KEYDOWN:
            return self._handle_key(event)
        elif event.type == pygame.MOUSEWHEEL:
            pass  # Could add zoom later

    def _handle_left_click(self, pos):
        mx, my = pos
        # Check UI panels first
        if mx > MAP_VIEWPORT_W:
            return self._handle_sidebar_click(pos)
        if my > BOTTOM_BAR_Y:
            return self._handle_bottombar_click(pos)

        # Map click
        if self.camera:
            tx, ty = self.camera.screen_to_world(mx, my)
            gm = self.game.game_manager
            if gm and gm.game_map:
                objects = gm.game_map.get_objects_at(tx, ty)
                player = gm.current_player

                # Town click
                town_obj = next((o for o in objects if o.obj_type == OBJ_TOWN), None)
                if town_obj and player:
                    if town_obj.player_id == player.player_id:
                        # Enter town
                        self.game.enter_town(town_obj.data.get("town"))
                        return "town"

                # Hero click
                hero_obj = next((o for o in objects if o.obj_type == OBJ_HERO), None)
                if hero_obj and player:
                    hero = hero_obj.data.get("hero")
                    if hero and hero.player_id == player.player_id:
                        self._selected_hero = hero
                        self._compute_reachable()
                        return

                # Move selected hero
                if self._selected_hero and player:
                    if (tx, ty) in self._reachable_tiles:
                        self._move_selected_hero(tx, ty)

    def _handle_right_click(self, pos):
        """Show info tooltip on right click."""
        mx, my = pos
        if self.camera and mx < MAP_VIEWPORT_W:
            tx, ty = self.camera.screen_to_world(mx, my)
            self._hovered_tile = (tx, ty)

    def _handle_mouse_move(self, pos):
        mx, my = pos
        if self.camera and mx < MAP_VIEWPORT_W and my < BOTTOM_BAR_Y:
            tx, ty = self.camera.screen_to_world(mx, my)
            self._hovered_tile = (tx, ty)
            # Path preview
            if self._selected_hero and (tx, ty) in self._reachable_tiles:
                gm = self.game.game_manager
                if gm and gm.game_map:
                    hero = self._selected_hero
                    self._path_preview = gm.game_map.find_path(
                        hero.map_x, hero.map_y, tx, ty
                    )

    def _handle_key(self, event):
        gm = self.game.game_manager
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            # End turn
            if gm:
                gm.end_player_turn()
                self._selected_hero = None
                self._reachable_tiles = set()
                self._path_preview = []
                if not gm.current_player.is_human:
                    gm.run_ai_turns()
        elif event.key == pygame.K_h:
            # Cycle through heroes
            player = gm.current_player if gm else None
            if player and player.heroes:
                if self._selected_hero in player.heroes:
                    idx = player.heroes.index(self._selected_hero)
                    self._selected_hero = player.heroes[(idx + 1) % len(player.heroes)]
                else:
                    self._selected_hero = player.heroes[0]
                self.camera.center_on_tile(self._selected_hero.map_x,
                                           self._selected_hero.map_y)
                self._compute_reachable()
        elif event.key == pygame.K_ESCAPE:
            self._selected_hero = None
            self._reachable_tiles = set()
            self._path_preview = []
        elif event.key == pygame.K_F5:
            return "main_menu"

    def _handle_sidebar_click(self, pos):
        mx, my = pos
        # End Turn button
        end_turn_rect = pygame.Rect(MAP_VIEWPORT_W + 16, WINDOW_HEIGHT - 80, SIDEBAR_W - 32, 48)
        if end_turn_rect.collidepoint(pos):
            gm = self.game.game_manager
            if gm:
                gm.end_player_turn()
                self._selected_hero = None
                self._reachable_tiles = set()

    def _handle_bottombar_click(self, pos):
        pass  # Handle hero slot clicks in the bottom bar

    def _compute_reachable(self):
        if not self._selected_hero:
            self._reachable_tiles = set()
            return
        gm = self.game.game_manager
        if gm and gm.game_map:
            hero = self._selected_hero
            self._reachable_tiles = gm.game_map.get_reachable_tiles(
                hero.map_x, hero.map_y, hero.movement_points
            )

    def _move_selected_hero(self, tx: int, ty: int):
        hero = self._selected_hero
        gm = self.game.game_manager
        if not hero or not gm:
            return
        path = gm.game_map.find_path(hero.map_x, hero.map_y, tx, ty)
        for step_x, step_y in path:
            tile = gm.game_map.get_tile(step_x, step_y)
            if not tile:
                break
            cost = tile.movement_cost
            if hero.movement_points < cost:
                break

            # Handle encounters
            objects = gm.game_map.get_objects_at(step_x, step_y)
            encounter_result = gm.handle_encounter(hero, objects, step_x, step_y)
            if encounter_result == "combat":
                return "combat"

            hero.use_movement(cost)
            # Move map object
            hero_objs = [o for o in gm.game_map.get_objects_at(hero.map_x, hero.map_y)
                         if o.data.get("hero") is hero]
            for ho in hero_objs:
                gm.game_map.move_object(ho, step_x, step_y)
            hero.map_x = step_x
            hero.map_y = step_y

            # Update fog of war
            scouting = hero.skill_level("scouting") if hasattr(hero, 'skill_level') else 0
            sight = 5 + scouting * 2
            gm.game_map.reveal_around(step_x, step_y, sight)

        self._compute_reachable()
        self._path_preview = []

    def update(self, dt: float):
        self._anim_t += dt
        # Update camera
        if self.camera:
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < MAP_VIEWPORT_W:  # Only scroll in map area
                self.camera.update(dt, mouse_pos, keys)
            else:
                self.camera.update(dt, None, keys)
        # Tick messages
        self._msg_queue = [m for m in self._msg_queue if m["timer"] > 0]
        for m in self._msg_queue:
            m["timer"] -= dt

    def draw(self, renderer):
        renderer.clear(COLOR_DARK_BG)
        gm = self.game.game_manager
        if not gm or not gm.game_map:
            renderer.draw_text("No map loaded. Press ESC.",
                               (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
                               COLOR_GOLD, renderer.font_large, center=True)
            return

        self._draw_map(renderer, gm)
        self._draw_sidebar(renderer, gm)
        self._draw_bottom_bar(renderer, gm)
        self._draw_hud(renderer, gm)
        self._draw_messages(renderer)

    def _draw_map(self, renderer, gm):
        """Draw the visible tiles and objects."""
        if not self.camera:
            return
        game_map = gm.game_map
        cam = self.camera
        tile_ox = cam.tile_offset_x
        tile_oy = cam.tile_offset_y
        pix_ox = cam.pixel_offset_x
        pix_oy = cam.pixel_offset_y

        # Draw tiles
        for ty in range(cam.visible_tiles_y):
            for tx in range(cam.visible_tiles_x):
                map_x = tile_ox + tx
                map_y = tile_oy + ty
                tile = game_map.get_tile(map_x, map_y)
                if not tile:
                    continue
                screen_x = tx * TILE_SIZE - pix_ox
                screen_y = ty * TILE_SIZE - pix_oy
                if screen_x >= MAP_VIEWPORT_W or screen_y >= MAP_VIEWPORT_H:
                    continue

                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                renderer.draw_map_tile(tile.terrain, rect,
                                       fog=not tile.explored,
                                       selected=(self._hovered_tile == (map_x, map_y)))

        # Draw reachable overlay
        for (rx, ry) in self._reachable_tiles:
            sx, sy = cam.world_to_screen(rx, ry)
            if 0 <= sx < MAP_VIEWPORT_W and 0 <= sy < MAP_VIEWPORT_H:
                overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                overlay.fill((100, 200, 100, 60))
                renderer.screen.blit(overlay, (sx, sy))

        # Draw path preview
        for i, (px, py) in enumerate(self._path_preview):
            sx, sy = cam.world_to_screen(px, py)
            if 0 <= sx < MAP_VIEWPORT_W and 0 <= sy < MAP_VIEWPORT_H:
                pygame.draw.rect(renderer.screen, (255, 220, 50),
                                 (sx + TILE_SIZE // 4, sy + TILE_SIZE // 4,
                                  TILE_SIZE // 2, TILE_SIZE // 2))

        # Draw objects
        self._draw_objects(renderer, gm, cam)

    def _draw_objects(self, renderer, gm, cam):
        for obj in gm.game_map.objects:
            sx, sy = cam.world_to_screen(obj.x, obj.y)
            if not (0 <= sx < MAP_VIEWPORT_W and 0 <= sy < MAP_VIEWPORT_H):
                continue
            tile = gm.game_map.get_tile(obj.x, obj.y)
            if not tile or not tile.explored:
                continue

            self._draw_map_object(renderer, obj, sx, sy)

    def _draw_map_object(self, renderer, obj, sx: int, sy: int):
        size = TILE_SIZE
        cx, cy = sx + size // 2, sy + size // 2

        if obj.obj_type == OBJ_TOWN:
            faction = obj.data.get("faction", "castle")
            color = FACTION_COLORS.get(faction, (200, 180, 100))
            # Draw castle icon
            pygame.draw.rect(renderer.screen, color,
                             (sx + 4, sy + 12, size - 8, size - 16))
            pygame.draw.rect(renderer.screen, (200, 180, 100),
                             (sx + 4, sy + 12, size - 8, size - 16), 2)
            # Towers
            for tx in [sx + 4, sx + size - 16]:
                pygame.draw.rect(renderer.screen, color, (tx, sy + 4, 12, 20))
            # Flag with player color
            if obj.player_id >= 0 and obj.player_id < len(PLAYER_COLORS):
                pygame.draw.circle(renderer.screen, PLAYER_COLORS[obj.player_id],
                                   (cx, sy + 2), 6)
            renderer.draw_text(obj.data.get("name", "?")[:6], (sx, sy + size - 14),
                               COLOR_GOLD, renderer.font_tiny)

        elif obj.obj_type == OBJ_HERO:
            hero = obj.data.get("hero")
            if hero:
                pid = hero.player_id
                color = PLAYER_COLORS[pid] if pid < len(PLAYER_COLORS) else (200, 200, 200)
                # Hero figure
                is_selected = (hero is self._selected_hero)
                if is_selected:
                    pygame.draw.rect(renderer.screen, (255, 255, 100),
                                     (sx, sy, size, size), 3)
                pygame.draw.circle(renderer.screen, color, (cx, cy - 4), size // 5)
                pygame.draw.rect(renderer.screen, color,
                                 (cx - size // 8, cy + size // 10, size // 4, size // 5))
                renderer.draw_text(hero.name[:6], (sx, sy + size - 14),
                                   color, renderer.font_tiny)

        elif obj.obj_type == OBJ_MINE:
            mine_colors = {
                "gold_mine": COLOR_GOLD,
                "ore_pit": (140, 140, 140),
                "wood_mill": (100, 160, 60),
                "mercury_pool": (180, 80, 200),
                "sulfur_mine": (220, 180, 40),
                "crystal_cavern": (100, 200, 220),
                "gem_pond": (120, 200, 120),
            }
            mine_type = obj.data.get("mine_type", "gold_mine")
            color = mine_colors.get(mine_type, (150, 150, 150))
            pygame.draw.polygon(renderer.screen, color,
                                [(cx, sy + 6), (sx + 8, sy + size - 6),
                                 (sx + size - 8, sy + size - 6)])
            if obj.player_id >= 0 and obj.player_id < len(PLAYER_COLORS):
                pygame.draw.circle(renderer.screen, PLAYER_COLORS[obj.player_id],
                                   (cx, sy + 2), 4)

        elif obj.obj_type == OBJ_RESOURCE:
            res = obj.data.get("resource", "gold")
            res_colors = {
                "gold": COLOR_GOLD, "wood": (100, 160, 60),
                "ore": (140, 140, 140), "mercury": (180, 80, 200),
                "sulfur": (220, 180, 40), "crystal": (100, 200, 220),
                "gems": (120, 200, 120),
            }
            color = res_colors.get(res, (200, 200, 200))
            pygame.draw.circle(renderer.screen, color, (cx, cy), size // 4)

        elif obj.obj_type == OBJ_ARTIFACT:
            pygame.draw.polygon(renderer.screen, (220, 180, 60),
                                [(cx, sy + 8), (sx + 8, sy + size - 8),
                                 (sx + size - 8, sy + size - 8)])
            pygame.draw.polygon(renderer.screen, (255, 220, 100),
                                [(cx, sy + 8), (sx + 8, sy + size - 8),
                                 (sx + size - 8, sy + size - 8)], 1)

        elif obj.obj_type == OBJ_MONSTER:
            creature_id = obj.data.get("creature_id", "")
            count = obj.data.get("count", 0)
            pygame.draw.circle(renderer.screen, (200, 80, 80), (cx, cy), size // 4)
            renderer.draw_text(str(count), (sx + 2, sy + size - 16),
                               (255, 80, 80), renderer.font_tiny)

        elif obj.obj_type == OBJ_TREASURE_CHEST:
            pygame.draw.rect(renderer.screen, (120, 90, 40),
                             (sx + 8, sy + 16, size - 16, size - 24))
            pygame.draw.rect(renderer.screen, COLOR_GOLD,
                             (sx + 8, sy + 16, size - 16, size - 24), 2)
            pygame.draw.rect(renderer.screen, COLOR_GOLD,
                             (cx - 4, sy + 12, 8, 4))

        elif obj.obj_type == OBJ_SHRINE:
            pygame.draw.circle(renderer.screen, (100, 150, 220), (cx, cy), size // 4)
            pygame.draw.circle(renderer.screen, (150, 200, 255), (cx, cy), size // 4, 2)

        elif obj.obj_type == OBJ_WELL:
            pygame.draw.circle(renderer.screen, (60, 100, 180), (cx, cy), size // 4)
            pygame.draw.circle(renderer.screen, (100, 150, 220), (cx, cy), size // 4, 2)

    def _draw_sidebar(self, renderer, gm):
        """Draw the right sidebar."""
        sx = MAP_VIEWPORT_W
        panel_rect = (sx, 0, SIDEBAR_W, WINDOW_HEIGHT)
        renderer.draw_panel(panel_rect)

        # Player info
        player = gm.current_player
        if player:
            color = player.color
            renderer.draw_text(f"Player: {player.name}", (sx + 8, 10),
                               color, renderer.font_medium)

        # Turn/date info
        day = gm.current_day
        week = (day - 1) // 7 + 1
        month = (week - 1) // 4 + 1
        renderer.draw_text(f"Month {month}, Week {week}", (sx + 8, 36),
                           COLOR_TEXT_NORMAL, renderer.font_small)
        renderer.draw_text(f"Day {((day - 1) % 7) + 1}", (sx + 8, 54),
                           COLOR_TEXT_NORMAL, renderer.font_small)

        # Resources
        if player:
            res = player.resources
            y_off = 80
            res_data = [
                ("Gold", res.gold, COLOR_GOLD),
                ("Wood", res.wood, (100, 160, 60)),
                ("Ore", res.ore, (140, 140, 140)),
                ("Hg", res.mercury, (180, 80, 200)),
                ("Su", res.sulfur, (220, 180, 40)),
                ("Cr", res.crystal, (100, 200, 220)),
                ("Ge", res.gems, (120, 200, 120)),
            ]
            for name, val, color in res_data:
                pygame.draw.circle(renderer.screen, color, (sx + 16, y_off + 8), 7)
                renderer.draw_text(f"{name}: {val}", (sx + 28, y_off),
                                   COLOR_TEXT_NORMAL, renderer.font_small)
                y_off += 24

        # Minimap
        mm_rect = (sx + 4, WINDOW_HEIGHT - MINIMAP_H - 100, MINIMAP_W - 8, MINIMAP_H)
        cam_rect = self.camera.get_camera_rect() if self.camera else (0, 0, 20, 15)
        renderer.draw_minimap(mm_rect, gm.game_map, cam_rect)

        # End turn button
        end_btn = pygame.Rect(sx + 16, WINDOW_HEIGHT - 80, SIDEBAR_W - 32, 48)
        mx, my = pygame.mouse.get_pos()
        hover = end_btn.collidepoint(mx, my)
        renderer.draw_button(end_btn, "End Turn [Enter]", hover=hover)

        # Hero info
        if self._selected_hero:
            self._draw_hero_info(renderer, self._selected_hero, sx)

    def _draw_hero_info(self, renderer, hero, sx: int):
        """Draw selected hero stats in sidebar."""
        y = 280
        pygame.draw.line(renderer.screen, COLOR_PANEL_BORDER,
                         (sx + 4, y), (sx + SIDEBAR_W - 4, y))
        y += 8
        renderer.draw_text(hero.name, (sx + 8, y), COLOR_GOLD, renderer.font_medium)
        y += 24
        renderer.draw_text(f"Level {hero.level}", (sx + 8, y), COLOR_TEXT_NORMAL, renderer.font_small)
        y += 20
        stats = [
            (f"ATK: {hero.effective_attack}", (220, 80, 80)),
            (f"DEF: {hero.effective_defense}", (80, 120, 220)),
            (f"POW: {hero.effective_power}", (180, 80, 220)),
            (f"KNW: {hero.effective_knowledge}", (80, 200, 180)),
        ]
        for stat_text, color in stats:
            renderer.draw_text(stat_text, (sx + 8, y), color, renderer.font_small)
            y += 18
        # Movement bar
        renderer.draw_text(f"Move: {hero.movement_points}/{hero.max_movement}",
                           (sx + 8, y), COLOR_TEXT_NORMAL, renderer.font_small)
        y += 16
        bar_rect = (sx + 8, y, SIDEBAR_W - 16, 8)
        renderer.draw_progress_bar(bar_rect, hero.movement_points, hero.max_movement,
                                   (100, 220, 100))
        y += 16
        # Spell points
        renderer.draw_text(f"Mana: {hero.spell_points}/{hero.max_spell_points}",
                           (sx + 8, y), (100, 160, 220), renderer.font_small)
        y += 16
        mana_rect = (sx + 8, y, SIDEBAR_W - 16, 8)
        renderer.draw_progress_bar(mana_rect, hero.spell_points, hero.max_spell_points,
                                   (60, 120, 220))
        y += 16
        # Army
        renderer.draw_text("Army:", (sx + 8, y), COLOR_TEXT_NORMAL, renderer.font_small)
        y += 18
        for slot, stack in sorted(hero.army.items())[:7]:
            cid = stack["creature"]
            count = stack["count"]
            renderer.draw_text(f"  {cid[:12]}: {count}", (sx + 8, y),
                               COLOR_TEXT_NORMAL, renderer.font_tiny)
            y += 14

    def _draw_bottom_bar(self, renderer, gm):
        """Draw bottom info bar."""
        bar_rect = (0, BOTTOM_BAR_Y, MAP_VIEWPORT_W, 60)
        renderer.draw_panel(bar_rect)

        if gm.current_player:
            player = gm.current_player
            # Show all heroes
            x_off = 10
            for i, hero in enumerate(player.heroes):
                hero_rect = (x_off, BOTTOM_BAR_Y + 5, 50, 50)
                is_sel = (hero is self._selected_hero)
                renderer.draw_hero_portrait(hero_rect, hero.to_dict(), player.color)
                if is_sel:
                    pygame.draw.rect(renderer.screen, (255, 255, 100), hero_rect, 2)
                x_off += 60

            # Day/turn info in center
            renderer.draw_text(f"Day {gm.current_day} | Turn {gm.current_turn}",
                               (MAP_VIEWPORT_W // 2, BOTTOM_BAR_Y + 20),
                               COLOR_GOLD, renderer.font_medium, center=True)

    def _draw_hud(self, renderer, gm):
        """Draw HUD info (hover tile, combat log etc)."""
        if self._hovered_tile and self.camera:
            tx, ty = self._hovered_tile
            game_map = gm.game_map
            tile = game_map.get_tile(tx, ty)
            if tile:
                info = f"({tx},{ty}) {tile.terrain}"
                objs = game_map.get_objects_at(tx, ty)
                if objs:
                    info += f" | {objs[-1].obj_type}"
                renderer.draw_text(info, (10, BOTTOM_BAR_Y - 20),
                                   COLOR_TEXT_NORMAL, renderer.font_small)

    def _draw_messages(self, renderer):
        """Draw floating combat/event messages."""
        y = 100
        for msg in self._msg_queue[-5:]:
            alpha = min(255, int(msg["timer"] * 255))
            color = msg.get("color", COLOR_TEXT_HIGHLIGHT)
            renderer.draw_text(msg["text"], (MAP_VIEWPORT_W // 2, y),
                               color, renderer.font_medium, center=True)
            y += 30

    def push_message(self, text: str, duration: float = 2.5, color=None):
        self._msg_queue.append({
            "text": text,
            "timer": duration,
            "color": color or COLOR_TEXT_HIGHLIGHT,
        })
