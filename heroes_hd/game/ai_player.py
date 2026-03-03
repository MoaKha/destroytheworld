"""Basic AI player for Heroes HD."""
from __future__ import annotations
import random
from typing import Optional
from game.player import Player
from game.adventure_map import AdventureMap, MapObject
from config import (OBJ_TOWN, OBJ_MINE, OBJ_RESOURCE, OBJ_ARTIFACT,
                    OBJ_MONSTER, OBJ_TREASURE_CHEST, AI_EASY, AI_NORMAL,
                    AI_HARD, AI_EXPERT)


class AIPlayer:
    """Simple AI that controls a player's heroes and towns."""

    def __init__(self, player: Player, creature_db: dict):
        self.player = player
        self.creature_db = creature_db
        self.rng = random.Random()
        self.target_cache: dict = {}  # hero_id -> target position

    def take_turn(self, game_map: AdventureMap, all_players: list[Player]):
        """Execute the AI's turn."""
        player = self.player

        # Build in towns
        for town in player.towns:
            self._build_in_town(town, player)

        # Recruit creatures
        for town in player.towns:
            self._recruit_creatures(town, player)

        # Move heroes
        for hero in player.heroes:
            if hero.movement_points > 0:
                self._move_hero(hero, game_map, all_players)

        player.turn_done = True

    def _build_in_town(self, town, player: Player):
        """Try to build the most valuable available building."""
        from game.town import BUILDINGS
        all_b = BUILDINGS.get(town.faction, [])
        available = [b for b in all_b
                     if b["id"] not in town.buildings
                     and player.resources.can_afford(b.get("cost", {}))
                     and all(r in town.buildings for r in b.get("requires", []))]
        if not available:
            return
        # Priority: creature buildings > mage guild > fort upgrades
        priority = sorted(available, key=lambda b: (
            0 if b.get("effect", "").startswith("recruit") else
            1 if "mage_guild" in b["id"] else
            2 if b["id"] in ("fort", "citadel", "castle_building") else 3
        ))
        if priority:
            town.build(priority[0]["id"], player.resources)

    def _recruit_creatures(self, town, player: Player):
        """Recruit all available creatures if affordable."""
        recruitable = town.get_recruitable_creatures()
        for cid, count in recruitable:
            if count <= 0:
                continue
            cdata = self.creature_db.get(cid, {})
            cost = cdata.get("cost", {"gold": 0})
            total = {r: a * count for r, a in cost.items()}
            if player.resources.can_afford(total):
                ok, _ = town.recruit(cid, count, player.resources, self.creature_db)
                if ok:
                    # Find a hero in town or garrisoned
                    for hero in player.heroes:
                        if hero.map_x == town.map_x and hero.map_y == town.map_y:
                            hero.add_creature(cid, count)
                            break

    def _move_hero(self, hero, game_map: AdventureMap, all_players: list[Player]):
        """Move hero toward a target."""
        difficulty = self.player.ai_difficulty
        target = self._find_target(hero, game_map, all_players)

        if not target:
            # Random wander
            self._wander(hero, game_map)
            return

        tx, ty = target
        path = game_map.find_path(hero.map_x, hero.map_y, tx, ty,
                                  max_cost=hero.movement_points)

        steps_per_turn = max(1, hero.movement_points // 100)
        if difficulty == AI_EASY:
            steps_per_turn = max(1, steps_per_turn // 2)

        for step_x, step_y in path[:steps_per_turn]:
            tile = game_map.get_tile(step_x, step_y)
            if not tile:
                break
            cost = tile.movement_cost
            if hero.movement_points < cost:
                break

            # Check for encounters
            objects = game_map.get_objects_at(step_x, step_y)
            for obj in objects:
                self._handle_encounter(hero, obj, game_map, all_players)

            hero.use_movement(cost)
            # Move hero on map
            hero_objs = [o for o in game_map.get_objects_at(hero.map_x, hero.map_y)
                         if o.data.get("hero") is hero]
            for ho in hero_objs:
                game_map.move_object(ho, step_x, step_y)
            hero.map_x = step_x
            hero.map_y = step_y

    def _find_target(self, hero, game_map: AdventureMap,
                     all_players: list[Player]) -> Optional[tuple[int, int]]:
        """Find the best target for the AI hero."""
        best = None
        best_score = -1

        # Check cached target
        cached = self.target_cache.get(id(hero))
        if cached:
            tx, ty = cached
            tile = game_map.get_tile(tx, ty)
            if tile and not tile.objects:
                del self.target_cache[id(hero)]
            else:
                return cached

        for obj in game_map.objects:
            score = self._evaluate_object(hero, obj, all_players)
            if score > best_score:
                best_score = score
                best = (obj.x, obj.y)

        if best:
            self.target_cache[id(hero)] = best
        return best

    def _evaluate_object(self, hero, obj: MapObject, all_players: list[Player]) -> float:
        """Score an object for AI targeting."""
        dist = abs(obj.x - hero.map_x) + abs(obj.y - hero.map_y)
        if dist == 0:
            return -1

        base_score = 0.0
        if obj.obj_type == OBJ_MINE and obj.player_id != self.player.player_id:
            base_score = 500.0
        elif obj.obj_type == OBJ_TOWN and obj.player_id not in (self.player.player_id, -1):
            base_score = 1000.0
        elif obj.obj_type == OBJ_RESOURCE:
            base_score = 200.0
        elif obj.obj_type == OBJ_ARTIFACT:
            base_score = 300.0
        elif obj.obj_type == OBJ_TREASURE_CHEST:
            base_score = 250.0
        elif obj.obj_type == OBJ_MONSTER:
            # Only attack if we're strong enough
            monster_strength = obj.data.get("count", 10) * 100
            hero_strength = sum(s["count"] for s in hero.army.values()) * 100
            if hero_strength > monster_strength * 1.5:
                base_score = 150.0
            else:
                return -1

        return base_score / (dist + 1)

    def _handle_encounter(self, hero, obj: MapObject, game_map: AdventureMap,
                          all_players: list[Player]):
        """Handle an encounter when a hero steps onto an object."""
        if obj.obj_type == OBJ_MINE:
            obj.player_id = self.player.player_id
        elif obj.obj_type == OBJ_RESOURCE:
            res = obj.data.get("resource", "gold")
            amount = obj.data.get("amount", 0)
            self.player.resources.add({res: amount})
            game_map.remove_object(obj)
        elif obj.obj_type == OBJ_TREASURE_CHEST:
            gold = obj.data.get("gold", 500)
            self.player.resources.add({"gold": gold})
            game_map.remove_object(obj)

    def _wander(self, hero, game_map: AdventureMap):
        """Move hero in a random direction."""
        import random
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for _ in range(5):
            dx, dy = random.choice(dirs)
            nx, ny = hero.map_x + dx, hero.map_y + dy
            if game_map.is_passable(nx, ny) and hero.movement_points >= 100:
                hero.use_movement(100)
                hero_objs = [o for o in game_map.get_objects_at(hero.map_x, hero.map_y)
                             if o.data.get("hero") is hero]
                for ho in hero_objs:
                    game_map.move_object(ho, nx, ny)
                hero.map_x = nx
                hero.map_y = ny
                break
