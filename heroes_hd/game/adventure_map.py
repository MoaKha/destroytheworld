"""Adventure map for Heroes HD."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
import math
from config import (TERRAIN_GRASS, TERRAIN_WATER, TERRAIN_ROCK,
                    TERRAIN_MOVEMENT_COST, OBJ_TOWN, OBJ_HERO, OBJ_MINE,
                    OBJ_ARTIFACT, OBJ_RESOURCE, OBJ_DWELLING, OBJ_MONSTER,
                    OBJ_SHRINE, OBJ_WELL, OBJ_TREASURE_CHEST)


@dataclass
class MapObject:
    """An object placed on the adventure map."""
    obj_type: str
    x: int
    y: int
    data: dict = field(default_factory=dict)
    player_id: int = -1  # -1 = neutral

    @property
    def is_passable(self) -> bool:
        return self.obj_type in {OBJ_SHRINE, OBJ_WELL}


@dataclass
class Tile:
    """A single tile on the adventure map."""
    terrain: str = TERRAIN_GRASS
    passable: bool = True
    explored: bool = False  # has been seen by any allied hero
    visible: bool = False   # currently visible (fog of war)
    objects: list = field(default_factory=list)  # MapObject list

    @property
    def movement_cost(self) -> int:
        return TERRAIN_MOVEMENT_COST.get(self.terrain, 100)

    @property
    def has_town(self) -> bool:
        return any(o.obj_type == OBJ_TOWN for o in self.objects)

    @property
    def has_hero(self) -> bool:
        return any(o.obj_type == OBJ_HERO for o in self.objects)

    def get_top_object(self) -> Optional[MapObject]:
        if self.objects:
            return self.objects[-1]
        return None


class AdventureMap:
    """The world map for Heroes HD."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles: list[list[Tile]] = [
            [Tile() for _ in range(width)]
            for _ in range(height)
        ]
        self.objects: list[MapObject] = []

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def is_passable(self, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)
        if not tile or not tile.passable:
            return False
        for obj in tile.objects:
            if obj.obj_type in {OBJ_HERO, OBJ_TOWN}:
                return False  # Heroes / towns block movement
        return True

    def set_terrain(self, x: int, y: int, terrain: str):
        tile = self.get_tile(x, y)
        if tile:
            tile.terrain = terrain
            tile.passable = terrain not in {TERRAIN_WATER, TERRAIN_ROCK}

    def place_object(self, obj: MapObject):
        tile = self.get_tile(obj.x, obj.y)
        if tile:
            tile.objects.append(obj)
        self.objects.append(obj)

    def remove_object(self, obj: MapObject):
        tile = self.get_tile(obj.x, obj.y)
        if tile and obj in tile.objects:
            tile.objects.remove(obj)
        if obj in self.objects:
            self.objects.remove(obj)

    def move_object(self, obj: MapObject, new_x: int, new_y: int):
        self.remove_object(obj)
        obj.x = new_x
        obj.y = new_y
        self.place_object(obj)

    def get_objects_at(self, x: int, y: int) -> list[MapObject]:
        tile = self.get_tile(x, y)
        return list(tile.objects) if tile else []

    def get_objects_by_type(self, obj_type: str) -> list[MapObject]:
        return [o for o in self.objects if o.obj_type == obj_type]

    # ── Pathfinding (A*) ──────────────────────────────────────────────────────

    def find_path(self, start_x: int, start_y: int,
                  goal_x: int, goal_y: int,
                  max_cost: int = 99999) -> list[tuple[int, int]]:
        """A* pathfinding. Returns list of (x,y) tiles or empty list if no path."""
        import heapq

        def h(x, y):
            return abs(x - goal_x) + abs(y - goal_y)

        open_set = [(h(start_x, start_y), 0, start_x, start_y)]
        came_from: dict[tuple, tuple] = {}
        g_score: dict[tuple, int] = {(start_x, start_y): 0}

        DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]

        while open_set:
            _, cost, x, y = heapq.heappop(open_set)
            if (x, y) == (goal_x, goal_y):
                path = []
                cur = (goal_x, goal_y)
                while cur in came_from:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path

            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                tile = self.get_tile(nx, ny)
                if not tile:
                    continue
                if (nx, ny) != (goal_x, goal_y) and not tile.passable:
                    continue
                move_cost = tile.movement_cost
                if dx != 0 and dy != 0:
                    move_cost = int(move_cost * 1.4)
                new_cost = cost + move_cost
                if new_cost > max_cost:
                    continue
                if new_cost < g_score.get((nx, ny), 999999):
                    g_score[(nx, ny)] = new_cost
                    came_from[(nx, ny)] = (x, y)
                    heapq.heappush(open_set, (new_cost + h(nx, ny), new_cost, nx, ny))
        return []

    def get_reachable_tiles(self, start_x: int, start_y: int,
                            movement_points: int) -> set[tuple[int, int]]:
        """BFS to find all tiles reachable within movement points."""
        import heapq
        open_set = [(0, start_x, start_y)]
        visited: dict[tuple, int] = {(start_x, start_y): 0}
        DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

        while open_set:
            cost, x, y = heapq.heappop(open_set)
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                tile = self.get_tile(nx, ny)
                if not tile or not tile.passable:
                    continue
                new_cost = cost + tile.movement_cost
                if new_cost <= movement_points and new_cost < visited.get((nx, ny), 999999):
                    visited[(nx, ny)] = new_cost
                    heapq.heappush(open_set, (new_cost, nx, ny))
        return set(visited.keys())

    # ── Fog of War ────────────────────────────────────────────────────────────

    def reveal_around(self, x: int, y: int, radius: int):
        """Reveal and explore tiles in a radius."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    tile = self.get_tile(x + dx, y + dy)
                    if tile:
                        tile.explored = True
                        tile.visible = True

    def update_visibility(self, hero_positions: list[tuple[int, int, int]]):
        """Update visibility. hero_positions: list of (x, y, sight_radius)."""
        # Reset current visibility
        for row in self.tiles:
            for tile in row:
                tile.visible = False
        # Reveal around each hero
        for x, y, radius in hero_positions:
            self.reveal_around(x, y, radius)

    # ── Mine income ───────────────────────────────────────────────────────────

    MINE_RESOURCES = {
        "gold_mine": ("gold", 1000),
        "wood_mill": ("wood", 2),
        "ore_pit": ("ore", 2),
        "mercury_pool": ("mercury", 1),
        "sulfur_mine": ("sulfur", 1),
        "crystal_cavern": ("crystal", 1),
        "gem_pond": ("gems", 1),
    }

    def get_mine_income(self, player_id: int) -> dict[str, int]:
        """Calculate daily mine income for a player."""
        income: dict[str, int] = {}
        for obj in self.objects:
            if obj.obj_type == OBJ_MINE and obj.player_id == player_id:
                mine_type = obj.data.get("mine_type", "")
                if mine_type in self.MINE_RESOURCES:
                    resource, amount = self.MINE_RESOURCES[mine_type]
                    income[resource] = income.get(resource, 0) + amount
        return income
