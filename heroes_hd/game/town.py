"""Town management for Heroes HD."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from config import ALL_FACTIONS


# Building definitions per faction
BUILDINGS = {
    "castle": [
        {"id": "mage_guild_1", "name": "Mage Guild Lv.1", "cost": {"gold": 2000, "wood": 5, "ore": 5},
         "requires": [], "effect": "spells_level_1", "description": "Grants level 1 spells."},
        {"id": "mage_guild_2", "name": "Mage Guild Lv.2", "cost": {"gold": 1000, "wood": 5},
         "requires": ["mage_guild_1"], "effect": "spells_level_2"},
        {"id": "mage_guild_3", "name": "Mage Guild Lv.3", "cost": {"gold": 1000, "ore": 5},
         "requires": ["mage_guild_2"], "effect": "spells_level_3"},
        {"id": "mage_guild_4", "name": "Mage Guild Lv.4", "cost": {"gold": 1000, "crystal": 5},
         "requires": ["mage_guild_3"], "effect": "spells_level_4"},
        {"id": "mage_guild_5", "name": "Mage Guild Lv.5", "cost": {"gold": 1000, "gems": 5},
         "requires": ["mage_guild_4"], "effect": "spells_level_5"},
        {"id": "marketplace", "name": "Marketplace", "cost": {"gold": 500, "wood": 5},
         "requires": [], "effect": "trade", "description": "Allows resource trading."},
        {"id": "resource_silo", "name": "Resource Silo", "cost": {"gold": 5000, "wood": 5},
         "requires": ["marketplace"], "effect": "daily_wood_1", "description": "+1 Wood per day."},
        {"id": "tavern", "name": "Tavern", "cost": {"gold": 500, "wood": 5},
         "requires": [], "effect": "hire_heroes", "description": "Hire heroes here."},
        {"id": "blacksmith", "name": "Blacksmith", "cost": {"gold": 1000, "ore": 5},
         "requires": [], "effect": "buy_siege", "description": "Buy ballista and catapult."},
        {"id": "fort", "name": "Fort", "cost": {"gold": 5000, "wood": 20, "ore": 20},
         "requires": [], "effect": "walls_1", "description": "Basic walls."},
        {"id": "citadel", "name": "Citadel", "cost": {"gold": 10000, "wood": 20},
         "requires": ["fort"], "effect": "walls_2", "description": "Stronger walls + moat."},
        {"id": "castle", "name": "Castle", "cost": {"gold": 20000, "wood": 20, "ore": 20},
         "requires": ["citadel"], "effect": "walls_3", "description": "Full castle fortifications."},
        # Creature dwellings
        {"id": "guardhouse", "name": "Guardhouse", "cost": {"gold": 200, "wood": 5},
         "requires": [], "effect": "recruit_pikeman", "description": "Recruit Pikemen."},
        {"id": "upgraded_guardhouse", "name": "Upgraded Guardhouse", "cost": {"gold": 400},
         "requires": ["guardhouse"], "effect": "recruit_halberdier"},
        {"id": "archer_tower", "name": "Archer's Tower", "cost": {"gold": 500, "wood": 5},
         "requires": [], "effect": "recruit_archer"},
        {"id": "upgraded_archer_tower", "name": "Upg. Archer's Tower", "cost": {"gold": 1000},
         "requires": ["archer_tower"], "effect": "recruit_marksman"},
        {"id": "griffin_tower", "name": "Griffin Tower", "cost": {"gold": 1000, "wood": 5, "ore": 3},
         "requires": ["fort"], "effect": "recruit_griffin"},
        {"id": "royal_griffin_tower", "name": "Royal Griffin Tower", "cost": {"gold": 2000},
         "requires": ["griffin_tower"], "effect": "recruit_royal_griffin"},
        {"id": "barracks", "name": "Barracks", "cost": {"gold": 2000, "wood": 10, "ore": 10},
         "requires": ["fort"], "effect": "recruit_swordsman"},
        {"id": "upg_barracks", "name": "Upg. Barracks", "cost": {"gold": 3000},
         "requires": ["barracks"], "effect": "recruit_crusader"},
        {"id": "monastery", "name": "Monastery", "cost": {"gold": 3000, "wood": 10},
         "requires": ["citadel"], "effect": "recruit_monk"},
        {"id": "upg_monastery", "name": "Upg. Monastery", "cost": {"gold": 4000},
         "requires": ["monastery"], "effect": "recruit_zealot"},
        {"id": "jousting_arena", "name": "Jousting Arena", "cost": {"gold": 5000, "wood": 5, "mercury": 2},
         "requires": ["citadel"], "effect": "recruit_cavalier"},
        {"id": "upg_jousting_arena", "name": "Upg. Jousting Arena", "cost": {"gold": 6000},
         "requires": ["jousting_arena"], "effect": "recruit_champion"},
        {"id": "portal_of_glory", "name": "Portal of Glory", "cost": {"gold": 20000, "wood": 5, "gems": 5},
         "requires": ["castle"], "effect": "recruit_angel"},
        {"id": "upg_portal_of_glory", "name": "Upg. Portal of Glory", "cost": {"gold": 30000, "gems": 10},
         "requires": ["portal_of_glory"], "effect": "recruit_archangel"},
    ],
}

# Creature recruitment mapping: building effect -> (creature_id, tier)
RECRUITMENT_MAP = {
    "recruit_pikeman": ("pikeman", 1),
    "recruit_halberdier": ("halberdier", 1),
    "recruit_archer": ("archer", 2),
    "recruit_marksman": ("marksman", 2),
    "recruit_griffin": ("griffin", 3),
    "recruit_royal_griffin": ("royal_griffin", 3),
    "recruit_swordsman": ("swordsman", 4),
    "recruit_crusader": ("crusader", 4),
    "recruit_monk": ("monk", 5),
    "recruit_zealot": ("zealot", 5),
    "recruit_cavalier": ("cavalier", 6),
    "recruit_champion": ("champion", 6),
    "recruit_angel": ("angel", 7),
    "recruit_archangel": ("archangel", 7),
}

GENERIC_BUILDINGS = {
    "mage_guild_1": {"cost": {"gold": 2000, "wood": 5, "ore": 5}, "requires": []},
    "mage_guild_2": {"cost": {"gold": 1000, "wood": 5}, "requires": ["mage_guild_1"]},
    "mage_guild_3": {"cost": {"gold": 1000, "ore": 5}, "requires": ["mage_guild_2"]},
    "marketplace": {"cost": {"gold": 500, "wood": 5}, "requires": []},
    "tavern": {"cost": {"gold": 500, "wood": 5}, "requires": []},
    "blacksmith": {"cost": {"gold": 1000, "ore": 5}, "requires": []},
    "fort": {"cost": {"gold": 5000, "wood": 20, "ore": 20}, "requires": []},
    "citadel": {"cost": {"gold": 10000, "wood": 20}, "requires": ["fort"]},
    "castle_building": {"cost": {"gold": 20000, "wood": 20, "ore": 20}, "requires": ["citadel"]},
}


class Town:
    """Represents a town/city on the map."""

    def __init__(self, faction: str, player_id: int, name: str,
                 map_x: int, map_y: int):
        self.faction = faction
        self.player_id = player_id  # -1 = neutral
        self.name = name
        self.map_x = map_x
        self.map_y = map_y

        # Buildings built in this town
        self.buildings: set[str] = {"guardhouse", "archer_tower"}  # starting buildings

        # Creature pool (waiting to be recruited)
        self.creature_pool: dict[str, int] = {}  # {creature_id: available_count}

        # Garrison: creatures defending the town (7 slots)
        self.garrison: dict[int, dict] = {}

        # Hero currently in town
        self.visiting_hero: Optional[object] = None
        self.garrisoned_hero: Optional[object] = None

        # Income per day (additional to base)
        self.income_bonus = 0

        # Mage guild spells
        self.available_spells: dict[str, list[str]] = {
            "1": [], "2": [], "3": [], "4": [], "5": []
        }
        self._generate_spells()

    def _generate_spells(self):
        """Assign random spells to each guild level."""
        import random
        from data_loader import DataLoader
        all_spells = DataLoader.load_spells()
        by_level: dict[int, list] = {1: [], 2: [], 3: [], 4: [], 5: []}
        for school_spells in all_spells.values():
            for spell in school_spells:
                lv = spell.get("level", 1)
                if lv in by_level:
                    by_level[lv].append(spell["id"])
        for lv in range(1, 6):
            pool = by_level[lv]
            count = min(3, len(pool))
            self.available_spells[str(lv)] = random.sample(pool, count)

    # ── Building ──────────────────────────────────────────────────────────────

    def can_build(self, building_id: str, resources) -> tuple[bool, str]:
        """Check if a building can be constructed."""
        all_buildings = BUILDINGS.get(self.faction, [])
        bdata = next((b for b in all_buildings if b["id"] == building_id), None)
        if not bdata:
            return False, "Unknown building"
        if building_id in self.buildings:
            return False, "Already built"
        for req in bdata.get("requires", []):
            if req not in self.buildings:
                return False, f"Requires {req}"
        if not resources.can_afford(bdata["cost"]):
            return False, "Insufficient resources"
        return True, "OK"

    def build(self, building_id: str, resources) -> tuple[bool, str]:
        ok, msg = self.can_build(building_id, resources)
        if not ok:
            return False, msg
        all_buildings = BUILDINGS.get(self.faction, [])
        bdata = next(b for b in all_buildings if b["id"] == building_id)
        resources.spend(bdata["cost"])
        self.buildings.add(building_id)
        return True, f"{bdata['name']} constructed!"

    def get_available_buildings(self) -> list[dict]:
        """Return buildings that can potentially be built (not yet built)."""
        all_b = BUILDINGS.get(self.faction, [])
        return [b for b in all_b if b["id"] not in self.buildings]

    # ── Recruitment ───────────────────────────────────────────────────────────

    def get_recruitable_creatures(self) -> list[tuple[str, int]]:
        """Return list of (creature_id, count) that can be recruited."""
        result = []
        for b_id in self.buildings:
            # Find building effect
            all_b = BUILDINGS.get(self.faction, [])
            bdata = next((b for b in all_b if b["id"] == b_id), None)
            if not bdata:
                continue
            effect = bdata.get("effect", "")
            if effect in RECRUITMENT_MAP:
                cid, _ = RECRUITMENT_MAP[effect]
                count = self.creature_pool.get(cid, 0)
                result.append((cid, count))
        return result

    def recruit(self, creature_id: str, count: int, resources, creature_db: dict) -> tuple[bool, str]:
        """Recruit creatures from the pool."""
        available = self.creature_pool.get(creature_id, 0)
        if count > available:
            return False, f"Only {available} available"
        cdata = creature_db.get(creature_id)
        if not cdata:
            return False, "Unknown creature"
        cost = dict(cdata.get("cost", {"gold": 0}))
        total_cost = {res: amt * count for res, amt in cost.items()}
        if not resources.can_afford(total_cost):
            return False, "Insufficient resources"
        resources.spend(total_cost)
        self.creature_pool[creature_id] = available - count
        return True, f"Recruited {count} {cdata['name']}"

    # ── Weekly growth ─────────────────────────────────────────────────────────

    def weekly_growth(self, creature_db: dict, week_multiplier: float = 1.0):
        """Add weekly creature growth to pool."""
        for b_id in self.buildings:
            all_b = BUILDINGS.get(self.faction, [])
            bdata = next((b for b in all_b if b["id"] == b_id), None)
            if not bdata:
                continue
            effect = bdata.get("effect", "")
            if effect in RECRUITMENT_MAP:
                cid, _ = RECRUITMENT_MAP[effect]
                cdata = creature_db.get(cid)
                if cdata:
                    growth = int(cdata.get("growth", 1) * week_multiplier)
                    self.creature_pool[cid] = self.creature_pool.get(cid, 0) + growth

    # ── Daily income ──────────────────────────────────────────────────────────

    def get_daily_income(self) -> dict[str, int]:
        income = {"gold": 1000 + self.income_bonus}
        # Resource silo
        if "resource_silo" in self.buildings:
            income["wood"] = income.get("wood", 0) + 1
        # Castle upgrade
        if "castle_building" in self.buildings:
            income["gold"] += 4000
        elif "citadel" in self.buildings:
            income["gold"] += 2000
        elif "fort" in self.buildings:
            income["gold"] += 1000
        return income

    def get_defense_level(self) -> int:
        if "castle_building" in self.buildings:
            return 3
        if "citadel" in self.buildings:
            return 2
        if "fort" in self.buildings:
            return 1
        return 0

    def get_spells_for_level(self, level: int) -> list[str]:
        """Get spells available from mage guild up to given level."""
        spells = []
        for lv in range(1, level + 1):
            guild_id = f"mage_guild_{lv}"
            if guild_id in self.buildings:
                spells.extend(self.available_spells.get(str(lv), []))
        return spells

    def to_dict(self) -> dict:
        return {
            "faction": self.faction,
            "player_id": self.player_id,
            "name": self.name,
            "map_x": self.map_x,
            "map_y": self.map_y,
            "buildings": list(self.buildings),
            "creature_pool": self.creature_pool,
            "garrison": self.garrison,
        }
