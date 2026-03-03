"""Random map generator for Heroes HD.

Uses a zone-based approach similar to the original HoMM3 RMG:
1. Divide map into zones
2. Connect zones with corridors
3. Fill each zone with terrain appropriate to its type
4. Place towns, mines, creatures, and objects

The system is extensible: new zone templates can be added to ZONE_TEMPLATES.
"""
from __future__ import annotations
import random
import math
from typing import Optional
from config import (TILE_SIZE, MAP_SMALL, MAP_MEDIUM, MAP_LARGE, MAP_EXTRA_LARGE,
                    TERRAIN_GRASS, TERRAIN_DIRT, TERRAIN_SAND, TERRAIN_SNOW,
                    TERRAIN_SWAMP, TERRAIN_LAVA, TERRAIN_ROUGH, TERRAIN_WATER,
                    TERRAIN_ROCK, ALL_FACTIONS,
                    OBJ_TOWN, OBJ_MINE, OBJ_ARTIFACT, OBJ_RESOURCE,
                    OBJ_DWELLING, OBJ_MONSTER, OBJ_SHRINE, OBJ_WELL,
                    OBJ_TREASURE_CHEST, PLAYER_COLORS)
from game.adventure_map import AdventureMap, MapObject
from game.town import Town


# Zone type definitions
ZONE_TEMPLATES = {
    "player_start": {
        "terrain": [TERRAIN_GRASS, TERRAIN_DIRT],
        "objects": {"mines": 2, "dwellings": 1, "resources": 3, "artifacts": 1},
        "monster_strength": "weak",
        "town": True,
    },
    "rich_mines": {
        "terrain": [TERRAIN_ROUGH, TERRAIN_DIRT],
        "objects": {"mines": 5, "dwellings": 2, "resources": 4, "artifacts": 2},
        "monster_strength": "medium",
        "town": False,
    },
    "dense_forest": {
        "terrain": [TERRAIN_GRASS, TERRAIN_ROUGH],
        "objects": {"mines": 1, "dwellings": 3, "resources": 2, "artifacts": 3},
        "monster_strength": "medium",
        "town": False,
    },
    "wasteland": {
        "terrain": [TERRAIN_SAND, TERRAIN_ROUGH],
        "objects": {"mines": 2, "dwellings": 1, "resources": 5, "artifacts": 1},
        "monster_strength": "strong",
        "town": False,
    },
    "tundra": {
        "terrain": [TERRAIN_SNOW, TERRAIN_ROUGH],
        "objects": {"mines": 3, "dwellings": 2, "resources": 3, "artifacts": 2},
        "monster_strength": "medium",
        "town": False,
    },
    "volcanic": {
        "terrain": [TERRAIN_LAVA, TERRAIN_ROUGH],
        "objects": {"mines": 4, "dwellings": 1, "resources": 2, "artifacts": 4},
        "monster_strength": "strong",
        "town": False,
    },
    "swampland": {
        "terrain": [TERRAIN_SWAMP, TERRAIN_GRASS],
        "objects": {"mines": 2, "dwellings": 2, "resources": 3, "artifacts": 2},
        "monster_strength": "medium",
        "town": False,
    },
    "neutral_town": {
        "terrain": [TERRAIN_GRASS, TERRAIN_DIRT],
        "objects": {"mines": 3, "dwellings": 2, "resources": 3, "artifacts": 2},
        "monster_strength": "medium",
        "town": True,
    },
    "treasure_trove": {
        "terrain": [TERRAIN_ROUGH, TERRAIN_DIRT],
        "objects": {"mines": 1, "dwellings": 0, "resources": 8, "artifacts": 6},
        "monster_strength": "strong",
        "town": False,
    },
}

MINE_TYPES = ["gold_mine", "ore_pit", "wood_mill", "mercury_pool", "sulfur_mine",
              "crystal_cavern", "gem_pond"]
RESOURCE_TYPES = ["gold", "wood", "ore", "mercury", "sulfur", "crystal", "gems"]

# Monster stacks per strength
MONSTER_POOLS = {
    "weak": [
        ("pikeman", 10, 30), ("goblin", 20, 50), ("skeleton", 15, 40),
        ("gremlin", 30, 80), ("gnoll", 15, 35), ("troglodyte", 20, 60),
    ],
    "medium": [
        ("archer", 8, 20), ("wolf_rider", 10, 25), ("wight", 6, 15),
        ("beholder", 5, 12), ("harpy", 8, 20), ("lizardman", 10, 25),
        ("dwarf", 10, 20), ("gog", 12, 30), ("centaur", 15, 35),
    ],
    "strong": [
        ("griffin", 5, 12), ("vampire", 4, 10), ("minotaur", 4, 10),
        ("pit_fiend", 3, 8), ("gorgon", 3, 8), ("cyclops", 3, 7),
        ("efreet", 3, 7), ("dendroid_guard", 5, 12), ("manticore", 3, 8),
    ],
    "very_strong": [
        ("angel", 1, 3), ("black_dragon", 1, 3), ("titan", 1, 4),
        ("arch_devil", 1, 3), ("ghost_dragon", 1, 4), ("ancient_behemoth", 1, 3),
        ("bone_dragon", 2, 5), ("archangel", 1, 2), ("chaos_hydra", 1, 3),
    ],
}


class Zone:
    """A region of the map with a specific template."""

    def __init__(self, zone_id: int, template_name: str, center_x: int, center_y: int,
                 radius: int, faction: str = None, player_id: int = -1):
        self.id = zone_id
        self.template = ZONE_TEMPLATES[template_name]
        self.template_name = template_name
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.faction = faction
        self.player_id = player_id
        self.tiles: set[tuple[int, int]] = set()
        self.connections: list[int] = []  # connected zone IDs


class RandomMapGenerator:
    """Generates a complete random map."""

    def __init__(self, map_size: int = MAP_MEDIUM, num_players: int = 2,
                 num_cpu: int = 0, seed: int = None):
        self.map_size = map_size
        self.num_players = num_players
        self.num_cpu = num_cpu
        self.rng = random.Random(seed)
        self.total_players = num_players + num_cpu
        self.creature_db: dict = {}

    def generate(self, creature_db: dict = None) -> AdventureMap:
        """Generate and return a complete adventure map."""
        if creature_db:
            self.creature_db = creature_db

        game_map = AdventureMap(self.map_size, self.map_size)

        # 1. Create zones
        zones = self._create_zones()

        # 2. Assign tiles to zones using Voronoi-like partitioning
        self._assign_tiles(game_map, zones)

        # 3. Apply terrain
        self._apply_terrain(game_map, zones)

        # 4. Add water borders and features
        self._add_water_features(game_map)

        # 5. Smooth terrain
        self._smooth_terrain(game_map)

        # 6. Place towns
        self._place_towns(game_map, zones)

        # 7. Place mines
        self._place_mines(game_map, zones)

        # 8. Place monsters
        self._place_monsters(game_map, zones)

        # 9. Place resources and treasures
        self._place_resources(game_map, zones)

        # 10. Place artifacts
        self._place_artifacts(game_map, zones)

        # 11. Place shrines and other objects
        self._place_misc_objects(game_map, zones)

        # 12. Connect zones with corridors
        self._create_corridors(game_map, zones)

        return game_map

    # ── Zone creation ─────────────────────────────────────────────────────────

    def _create_zones(self) -> list[Zone]:
        zones = []
        factions = self.rng.sample(ALL_FACTIONS, min(self.total_players, len(ALL_FACTIONS)))
        size = self.map_size

        # Player start zones — distributed evenly
        angles = [2 * math.pi * i / self.total_players for i in range(self.total_players)]
        dist = size * 0.35

        for i in range(self.total_players):
            cx = int(size / 2 + dist * math.cos(angles[i]))
            cy = int(size / 2 + dist * math.sin(angles[i]))
            cx = max(5, min(size - 5, cx))
            cy = max(5, min(size - 5, cy))
            faction = factions[i % len(factions)]
            player_id = i if i < self.num_players else -1
            zone = Zone(
                zone_id=i,
                template_name="player_start",
                center_x=cx, center_y=cy,
                radius=size // (self.total_players + 2),
                faction=faction,
                player_id=player_id,
            )
            zones.append(zone)

        # Additional zones
        zone_templates_pool = [
            "rich_mines", "dense_forest", "wasteland", "tundra",
            "volcanic", "swampland", "neutral_town", "treasure_trove"
        ]
        num_extra = self.rng.randint(self.total_players, self.total_players * 3)
        for i in range(num_extra):
            cx = self.rng.randint(5, size - 5)
            cy = self.rng.randint(5, size - 5)
            template = self.rng.choice(zone_templates_pool)
            faction = self.rng.choice(ALL_FACTIONS) if template == "neutral_town" else None
            zone = Zone(
                zone_id=self.total_players + i,
                template_name=template,
                center_x=cx, center_y=cy,
                radius=size // (self.total_players + 4),
                faction=faction,
                player_id=-1,
            )
            zones.append(zone)

        # Connect zones (minimum spanning tree style)
        for i, z1 in enumerate(zones):
            distances = [(self._zone_distance(z1, z2), j)
                        for j, z2 in enumerate(zones) if j != i]
            distances.sort()
            for _, j in distances[:2]:  # connect to 2 nearest
                if j not in z1.connections:
                    z1.connections.append(j)
                    zones[j].connections.append(i)

        return zones

    def _zone_distance(self, z1: Zone, z2: Zone) -> float:
        return math.sqrt((z1.center_x - z2.center_x)**2 + (z1.center_y - z2.center_y)**2)

    # ── Tile assignment ───────────────────────────────────────────────────────

    def _assign_tiles(self, game_map: AdventureMap, zones: list[Zone]):
        for y in range(game_map.height):
            for x in range(game_map.width):
                # Find nearest zone center
                nearest = min(zones, key=lambda z: (z.center_x - x)**2 + (z.center_y - y)**2)
                nearest.tiles.add((x, y))

    # ── Terrain ───────────────────────────────────────────────────────────────

    def _apply_terrain(self, game_map: AdventureMap, zones: list[Zone]):
        for zone in zones:
            terrain_choices = zone.template["terrain"]
            for x, y in zone.tiles:
                # Add noise variation
                noise = self.rng.random()
                if noise < 0.85:
                    terrain = terrain_choices[0]
                elif noise < 0.95:
                    terrain = terrain_choices[-1] if len(terrain_choices) > 1 else terrain_choices[0]
                else:
                    terrain = TERRAIN_ROUGH
                game_map.set_terrain(x, y, terrain)

    def _add_water_features(self, game_map: AdventureMap):
        size = self.map_size
        # Add occasional water patches (lakes)
        num_lakes = self.rng.randint(1, max(1, size // 20))
        for _ in range(num_lakes):
            cx = self.rng.randint(size // 6, size * 5 // 6)
            cy = self.rng.randint(size // 6, size * 5 // 6)
            radius = self.rng.randint(2, 5)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx*dx + dy*dy <= radius*radius:
                        if self.rng.random() < 0.7:
                            game_map.set_terrain(cx + dx, cy + dy, TERRAIN_WATER)

    def _smooth_terrain(self, game_map: AdventureMap):
        """Simple cellular automata to smooth terrain."""
        for _ in range(2):
            for y in range(1, game_map.height - 1):
                for x in range(1, game_map.width - 1):
                    neighbors = []
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            t = game_map.get_tile(x + dx, y + dy)
                            if t:
                                neighbors.append(t.terrain)
                    # Keep current terrain if water (don't spread)
                    tile = game_map.get_tile(x, y)
                    if tile and tile.terrain != TERRAIN_WATER:
                        # Most common neighbor
                        from collections import Counter
                        common = Counter(n for n in neighbors if n != TERRAIN_WATER).most_common(1)
                        if common and self.rng.random() < 0.3:
                            game_map.set_terrain(x, y, common[0][0])

    # ── Town placement ────────────────────────────────────────────────────────

    def _place_towns(self, game_map: AdventureMap, zones: list[Zone]):
        town_names_by_faction = {
            "castle": ["Brightwater", "Stormhaven", "Ironkeep", "Goldshire", "Sunspire"],
            "rampart": ["Greenwood", "Elmsdale", "Thornveil", "Sylvana", "Verdania"],
            "tower": ["Arcanum", "Spellhaven", "Mysteria", "The Pinnacle", "Azurereach"],
            "inferno": ["Hellsgate", "Ashfall", "Brimstone", "Emberhall", "Damnation"],
            "necropolis": ["Shadowmere", "Bleakholm", "Duskfall", "Graveloch", "Ashcroft"],
            "dungeon": ["Deepdelve", "Shadowvault", "Undermoor", "Obsidian", "Darkhold"],
            "stronghold": ["Ironblood", "Warchief", "Skullkeep", "Brutefang", "Battering"],
            "fortress": ["Marshkeep", "Bogfort", "Fenwatch", "Murkmere", "Reedhaven"],
            "conflux": ["Elementia", "Wyrmreach", "Maelstrom", "Vortexia", "Spiritus"],
        }

        for zone in zones:
            if not zone.template.get("town"):
                continue
            faction = zone.faction or self.rng.choice(ALL_FACTIONS)
            names = town_names_by_faction.get(faction, ["Town"])
            name = self.rng.choice(names)

            # Find a good spot near zone center
            x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y, 5)
            if x is None:
                continue

            # Ensure land
            game_map.set_terrain(x, y, TERRAIN_GRASS)
            game_map.set_terrain(x + 1, y, TERRAIN_GRASS)

            town = Town(faction=faction, player_id=zone.player_id, name=name, map_x=x, map_y=y)
            obj = MapObject(obj_type=OBJ_TOWN, x=x, y=y,
                            data={"town": town, "faction": faction, "name": name},
                            player_id=zone.player_id)
            game_map.place_object(obj)

    # ── Mine placement ────────────────────────────────────────────────────────

    def _place_mines(self, game_map: AdventureMap, zones: list[Zone]):
        for zone in zones:
            num_mines = zone.template["objects"].get("mines", 2)
            for _ in range(num_mines):
                x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y,
                                            zone.radius)
                if x is None:
                    continue
                mine_type = self.rng.choice(MINE_TYPES)
                obj = MapObject(obj_type=OBJ_MINE, x=x, y=y,
                                data={"mine_type": mine_type},
                                player_id=-1)
                game_map.place_object(obj)

    # ── Monster placement ─────────────────────────────────────────────────────

    def _place_monsters(self, game_map: AdventureMap, zones: list[Zone]):
        for zone in zones:
            strength = zone.template.get("monster_strength", "medium")
            pool = MONSTER_POOLS.get(strength, MONSTER_POOLS["medium"])
            num = self.rng.randint(2, 5)
            for _ in range(num):
                x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y,
                                            zone.radius)
                if x is None:
                    continue
                cid, min_count, max_count = self.rng.choice(pool)
                count = self.rng.randint(min_count, max_count)
                obj = MapObject(obj_type=OBJ_MONSTER, x=x, y=y,
                                data={"creature_id": cid, "count": count,
                                      "aggression": "normal"},
                                player_id=-1)
                game_map.place_object(obj)

    # ── Resources ─────────────────────────────────────────────────────────────

    def _place_resources(self, game_map: AdventureMap, zones: list[Zone]):
        for zone in zones:
            num = zone.template["objects"].get("resources", 3)
            for _ in range(num):
                x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y,
                                            zone.radius)
                if x is None:
                    continue
                res = self.rng.choice(RESOURCE_TYPES)
                amount = {
                    "gold": self.rng.randint(500, 2000),
                    "wood": self.rng.randint(5, 15),
                    "ore": self.rng.randint(5, 15),
                    "mercury": self.rng.randint(1, 5),
                    "sulfur": self.rng.randint(1, 5),
                    "crystal": self.rng.randint(1, 5),
                    "gems": self.rng.randint(1, 5),
                }.get(res, 100)
                obj = MapObject(obj_type=OBJ_RESOURCE, x=x, y=y,
                                data={"resource": res, "amount": amount},
                                player_id=-1)
                game_map.place_object(obj)

    # ── Artifacts ────────────────────────────────────────────────────────────

    def _place_artifacts(self, game_map: AdventureMap, zones: list[Zone]):
        artifact_ids = [
            "centaur_axe", "blackshard", "boots_of_speed", "pendant_of_courage",
            "necklace_of_swiftness", "cape_of_velocity", "skull_helmet",
            "shield_of_the_dwarven_lords", "collar_of_conjuring",
        ]
        for zone in zones:
            num = zone.template["objects"].get("artifacts", 1)
            for _ in range(num):
                x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y,
                                            zone.radius)
                if x is None:
                    continue
                art_id = self.rng.choice(artifact_ids)
                obj = MapObject(obj_type=OBJ_ARTIFACT, x=x, y=y,
                                data={"artifact_id": art_id},
                                player_id=-1)
                game_map.place_object(obj)

    # ── Misc objects ──────────────────────────────────────────────────────────

    def _place_misc_objects(self, game_map: AdventureMap, zones: list[Zone]):
        shrine_spells = ["haste", "bless", "slow", "bloodlust", "lightning_bolt",
                         "fireball", "cure", "stone_skin", "magic_arrow"]
        for zone in zones:
            # Shrines
            for _ in range(self.rng.randint(0, 2)):
                x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y,
                                            zone.radius)
                if x:
                    spell = self.rng.choice(shrine_spells)
                    obj = MapObject(obj_type=OBJ_SHRINE, x=x, y=y,
                                    data={"spell_id": spell}, player_id=-1)
                    game_map.place_object(obj)

            # Treasure chests
            for _ in range(self.rng.randint(1, 3)):
                x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y,
                                            zone.radius)
                if x:
                    gold = self.rng.choice([500, 1000, 1500, 2000])
                    obj = MapObject(obj_type=OBJ_TREASURE_CHEST, x=x, y=y,
                                    data={"gold": gold, "exp": gold // 2},
                                    player_id=-1)
                    game_map.place_object(obj)

            # Wells
            for _ in range(self.rng.randint(0, 1)):
                x, y = self._find_open_spot(game_map, zone.center_x, zone.center_y,
                                            zone.radius)
                if x:
                    obj = MapObject(obj_type=OBJ_WELL, x=x, y=y,
                                    data={}, player_id=-1)
                    game_map.place_object(obj)

    # ── Corridors ─────────────────────────────────────────────────────────────

    def _create_corridors(self, game_map: AdventureMap, zones: list[Zone]):
        """Carve passable corridors between connected zones."""
        connected_pairs = set()
        for zone in zones:
            for conn_id in zone.connections:
                pair = tuple(sorted([zone.id, conn_id]))
                if pair in connected_pairs:
                    continue
                connected_pairs.add(pair)
                other = next((z for z in zones if z.id == conn_id), None)
                if not other:
                    continue
                self._carve_path(game_map, zone.center_x, zone.center_y,
                                 other.center_x, other.center_y)

    def _carve_path(self, game_map: AdventureMap, x1: int, y1: int, x2: int, y2: int):
        """Carve a walkable path between two points."""
        x, y = x1, y1
        # First move horizontally, then vertically (L-shaped path)
        while x != x2:
            dx = 1 if x2 > x else -1
            x += dx
            tile = game_map.get_tile(x, y)
            if tile and tile.terrain == TERRAIN_WATER:
                game_map.set_terrain(x, y, TERRAIN_ROUGH)

        while y != y2:
            dy = 1 if y2 > y else -1
            y += dy
            tile = game_map.get_tile(x, y)
            if tile and tile.terrain == TERRAIN_WATER:
                game_map.set_terrain(x, y, TERRAIN_ROUGH)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _find_open_spot(self, game_map: AdventureMap,
                        cx: int, cy: int, radius: int,
                        max_tries: int = 30) -> tuple[Optional[int], Optional[int]]:
        """Find a random passable tile near (cx, cy) within radius."""
        for _ in range(max_tries):
            angle = self.rng.uniform(0, 2 * math.pi)
            dist = self.rng.uniform(2, radius)
            x = int(cx + dist * math.cos(angle))
            y = int(cy + dist * math.sin(angle))
            x = max(0, min(game_map.width - 1, x))
            y = max(0, min(game_map.height - 1, y))
            tile = game_map.get_tile(x, y)
            if tile and tile.passable and not tile.objects:
                return x, y
        return None, None
