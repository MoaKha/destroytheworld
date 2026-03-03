"""Hero system for Heroes HD."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Optional
from config import (HERO_MOVEMENT_BASE, SECONDARY_SKILLS, SKILL_NONE,
                    SKILL_BASIC, SKILL_ADVANCED, SKILL_EXPERT,
                    SLOT_HEAD, SLOT_NECK, SLOT_SHOULDER, SLOT_HAND,
                    SLOT_FEET, SLOT_MISC, SLOT_WEAPON, SLOT_SHIELD,
                    SLOT_CLOAK, SLOT_RING)

# Hero class data (prototype definitions)
HERO_CLASSES = {
    "knight": {
        "faction": "castle", "primary_skills": {"attack": 2, "defense": 2, "power": 1, "knowledge": 1},
        "specialties": ["leadership", "armorer"],
        "description": "A valiant knight specializing in combat."
    },
    "cleric": {
        "faction": "castle", "primary_skills": {"attack": 1, "defense": 1, "power": 2, "knowledge": 2},
        "specialties": ["wisdom", "first_aid"],
        "description": "A holy cleric skilled in magic."
    },
    "ranger": {
        "faction": "rampart", "primary_skills": {"attack": 1, "defense": 2, "power": 1, "knowledge": 2},
        "specialties": ["archery", "pathfinding"],
        "description": "A forest ranger expert in ranged combat."
    },
    "druid": {
        "faction": "rampart", "primary_skills": {"attack": 0, "defense": 1, "power": 3, "knowledge": 2},
        "specialties": ["wisdom", "earth_magic"],
        "description": "A druid harnessing nature magic."
    },
    "alchemist": {
        "faction": "tower", "primary_skills": {"attack": 1, "defense": 1, "power": 2, "knowledge": 2},
        "specialties": ["scholar", "intelligence"],
        "description": "An alchemist of arcane knowledge."
    },
    "wizard": {
        "faction": "tower", "primary_skills": {"attack": 0, "defense": 0, "power": 3, "knowledge": 3},
        "specialties": ["wisdom", "sorcery"],
        "description": "A powerful wizard of the tower."
    },
    "demoniac": {
        "faction": "inferno", "primary_skills": {"attack": 2, "defense": 1, "power": 2, "knowledge": 1},
        "specialties": ["fire_magic", "offense"],
        "description": "A warrior bound to infernal powers."
    },
    "heretic": {
        "faction": "inferno", "primary_skills": {"attack": 1, "defense": 0, "power": 3, "knowledge": 2},
        "specialties": ["sorcery", "fire_magic"],
        "description": "A heretic wielding forbidden fire magic."
    },
    "death_knight": {
        "faction": "necropolis", "primary_skills": {"attack": 2, "defense": 2, "power": 1, "knowledge": 1},
        "specialties": ["necromancy", "leadership"],
        "description": "A death knight commanding undead armies."
    },
    "necromancer": {
        "faction": "necropolis", "primary_skills": {"attack": 0, "defense": 0, "power": 2, "knowledge": 4},
        "specialties": ["necromancy", "wisdom"],
        "description": "A necromancer raising the dead."
    },
    "overlord": {
        "faction": "dungeon", "primary_skills": {"attack": 2, "defense": 2, "power": 1, "knowledge": 1},
        "specialties": ["offense", "armorer"],
        "description": "An overlord commanding dungeon forces."
    },
    "warlock": {
        "faction": "dungeon", "primary_skills": {"attack": 0, "defense": 1, "power": 3, "knowledge": 2},
        "specialties": ["scholar", "sorcery"],
        "description": "A warlock of dark magic."
    },
    "barbarian": {
        "faction": "stronghold", "primary_skills": {"attack": 4, "defense": 0, "power": 1, "knowledge": 1},
        "specialties": ["offense", "resistance"],
        "description": "A powerful barbarian warrior."
    },
    "battle_mage": {
        "faction": "stronghold", "primary_skills": {"attack": 2, "defense": 1, "power": 1, "knowledge": 2},
        "specialties": ["intelligence", "sorcery"],
        "description": "A battle mage of the stronghold."
    },
    "beastmaster": {
        "faction": "fortress", "primary_skills": {"attack": 1, "defense": 2, "power": 1, "knowledge": 2},
        "specialties": ["pathfinding", "scouting"],
        "description": "A beastmaster commanding wild creatures."
    },
    "witch": {
        "faction": "fortress", "primary_skills": {"attack": 1, "defense": 0, "power": 3, "knowledge": 2},
        "specialties": ["wisdom", "water_magic"],
        "description": "A witch of the swamp."
    },
    "planeswalker": {
        "faction": "conflux", "primary_skills": {"attack": 1, "defense": 1, "power": 2, "knowledge": 2},
        "specialties": ["earth_magic", "air_magic"],
        "description": "A planeswalker of the elements."
    },
    "elementalist": {
        "faction": "conflux", "primary_skills": {"attack": 0, "defense": 0, "power": 3, "knowledge": 3},
        "specialties": ["wisdom", "intelligence"],
        "description": "An elementalist mastering all schools."
    },
}

HERO_NAMES_BY_FACTION = {
    "castle": ["Roland", "Catherine", "Sorsha", "Christian", "Edric", "Sylvia"],
    "rampart": ["Ivor", "Jenova", "Kyrre", "Melodia", "Rion", "Ufretin"],
    "tower": ["Aine", "Astral", "Cyra", "Josephine", "Neela", "Solmyr"],
    "inferno": ["Calh", "Fiona", "Ignissa", "Marius", "Nymus", "Pyre"],
    "necropolis": ["Charna", "Clavius", "Galthran", "Isra", "Moandor", "Straker"],
    "dungeon": ["Ajit", "Arlach", "Dace", "Damacon", "Gunnar", "Lorelei"],
    "stronghold": ["Crag Hack", "Gretchin", "Gurnisson", "Jabarkas", "Krellion"],
    "fortress": ["Alkin", "Bron", "Gerwulf", "Korbac", "Tazar", "Torosar"],
    "conflux": ["Erdamon", "Fiur", "Gelare", "Grindan", "Lacus", "Monere"],
}


@dataclass
class ArtifactSlots:
    head: Optional[dict] = None
    neck: Optional[dict] = None
    shoulder: Optional[dict] = None
    hand: Optional[dict] = None
    feet: Optional[dict] = None
    weapon: Optional[dict] = None
    shield: Optional[dict] = None
    cloak: Optional[dict] = None
    ring1: Optional[dict] = None
    ring2: Optional[dict] = None
    misc1: Optional[dict] = None
    misc2: Optional[dict] = None
    misc3: Optional[dict] = None

    def all_artifacts(self) -> list[dict]:
        return [a for a in [self.head, self.neck, self.shoulder, self.hand,
                             self.feet, self.weapon, self.shield, self.cloak,
                             self.ring1, self.ring2, self.misc1, self.misc2, self.misc3]
                if a is not None]

    def get_bonus(self, stat: str) -> int:
        total = 0
        for art in self.all_artifacts():
            bonus = art.get("bonus", {})
            total += bonus.get(stat, 0)
        return total


class Hero:
    """Represents a hero in the game."""

    def __init__(self, hero_class: str, player_id: int, name: str = None):
        self.id = id(self)
        self.hero_class = hero_class
        self.player_id = player_id
        cls_data = HERO_CLASSES.get(hero_class, HERO_CLASSES["knight"])
        self.faction = cls_data["faction"]
        primary = cls_data["primary_skills"]

        # Name
        import random
        names = HERO_NAMES_BY_FACTION.get(self.faction, ["Hero"])
        self.name = name or random.choice(names)

        # Primary stats
        self.attack = primary.get("attack", 1)
        self.defense = primary.get("defense", 1)
        self.power = primary.get("power", 1)
        self.knowledge = primary.get("knowledge", 1)

        # Level & experience
        self.level = 1
        self.experience = 0
        self.exp_to_next = 1000

        # Spell points (mana)
        self.max_spell_points = self.knowledge * 10
        self.spell_points = self.max_spell_points

        # Secondary skills: {skill_name: level 0-3}
        self.secondary_skills: dict[str, int] = {}
        for skill in cls_data.get("specialties", []):
            self.secondary_skills[skill] = SKILL_BASIC

        # Spell book
        self.spells: list[str] = []  # list of spell IDs
        self.has_spellbook = self.power > 0 or hero_class in [
            "wizard", "cleric", "druid", "necromancer", "warlock", "witch", "elementalist", "heretic"
        ]

        # Army: {slot_idx: {"creature": creature_id, "count": n}}
        self.army: dict[int, dict] = {}  # max 7 stacks

        # Position on adventure map
        self.map_x = 0
        self.map_y = 0
        self.movement_points = HERO_MOVEMENT_BASE
        self.max_movement = HERO_MOVEMENT_BASE

        # Artifacts
        self.artifacts = ArtifactSlots()
        self.backpack: list[dict] = []

        # Morale / luck
        self.morale = 0
        self.luck = 0

        # State
        self.can_move = True
        self.in_combat = False
        self.on_boat = False

    # ── Level up ─────────────────────────────────────────────────────────────

    def gain_experience(self, amount: int) -> list[str]:
        """Add experience. Returns list of level-up events."""
        events = []
        self.experience += amount
        while self.experience >= self.exp_to_next:
            self.experience -= self.exp_to_next
            events.append(self._level_up())
        return events

    def _level_up(self) -> str:
        self.level += 1
        self.exp_to_next = int(self.exp_to_next * 1.5)
        # Increase primary stat based on class
        import random
        cls_data = HERO_CLASSES.get(self.hero_class, {})
        primary = cls_data.get("primary_skills", {})
        # Weighted random primary stat
        weights = {
            "attack": primary.get("attack", 1) + 1,
            "defense": primary.get("defense", 1) + 1,
            "power": primary.get("power", 1) + 1,
            "knowledge": primary.get("knowledge", 1) + 1,
        }
        choices = [s for s, w in weights.items() for _ in range(w)]
        stat = random.choice(choices)
        setattr(self, stat, getattr(self, stat) + 1)

        # Recalculate spell points
        self.max_spell_points = (self.knowledge * 10 +
                                 self.artifacts.get_bonus("spell_points"))
        self.spell_points = min(self.spell_points + self.knowledge * 5,
                                self.max_spell_points)
        return f"Level {self.level}! +1 {stat.capitalize()}"

    # ── Army management ───────────────────────────────────────────────────────

    def add_creature(self, creature_id: str, count: int) -> bool:
        """Add creatures to army. Returns True if successful."""
        # Find existing stack
        for slot, stack in self.army.items():
            if stack["creature"] == creature_id:
                stack["count"] += count
                return True
        # Find empty slot
        for slot in range(7):
            if slot not in self.army:
                self.army[slot] = {"creature": creature_id, "count": count}
                return True
        return False  # Army full

    def remove_creature(self, slot: int, count: int = None):
        if slot in self.army:
            if count is None or self.army[slot]["count"] <= count:
                del self.army[slot]
            else:
                self.army[slot]["count"] -= count

    def total_army_value(self, creature_db: dict) -> int:
        total = 0
        for stack in self.army.values():
            cid = stack["creature"]
            if cid in creature_db:
                total += creature_db[cid].get("ai_value", 0) * stack["count"]
        return total

    # ── Stats with bonuses ────────────────────────────────────────────────────

    @property
    def effective_attack(self) -> int:
        return self.attack + self.artifacts.get_bonus("attack")

    @property
    def effective_defense(self) -> int:
        return self.defense + self.artifacts.get_bonus("defense")

    @property
    def effective_power(self) -> int:
        return self.power + self.artifacts.get_bonus("power")

    @property
    def effective_knowledge(self) -> int:
        return self.knowledge + self.artifacts.get_bonus("knowledge")

    def skill_level(self, skill: str) -> int:
        return self.secondary_skills.get(skill, SKILL_NONE)

    def has_skill(self, skill: str) -> bool:
        return self.secondary_skills.get(skill, SKILL_NONE) > SKILL_NONE

    # ── Movement ──────────────────────────────────────────────────────────────

    def reset_movement(self):
        logistics_bonus = self.skill_level("logistics") * 0.1
        artifact_bonus = self.artifacts.get_bonus("movement")
        self.max_movement = int(HERO_MOVEMENT_BASE * (1 + logistics_bonus)) + artifact_bonus
        self.movement_points = self.max_movement
        self.can_move = True

    def use_movement(self, cost: int) -> bool:
        if self.movement_points >= cost:
            self.movement_points -= cost
            return True
        return False

    # ── New day ───────────────────────────────────────────────────────────────

    def new_day(self):
        self.reset_movement()
        # Mana regeneration
        mysticism = self.skill_level("mysticism")
        regen = [0, 2, 3, 4][mysticism] if mysticism <= 3 else 4
        regen += self.artifacts.get_bonus("mana_regen") if hasattr(self.artifacts, "get_bonus") else 0
        self.spell_points = min(self.max_spell_points, self.spell_points + regen)

    # ── Spells ────────────────────────────────────────────────────────────────

    def learn_spell(self, spell_id: str) -> bool:
        if spell_id not in self.spells and self.has_spellbook:
            self.spells.append(spell_id)
            return True
        return False

    def can_cast(self, spell: dict) -> bool:
        cost = spell.get("cost", 0)
        return (spell["id"] in self.spells and
                self.spell_points >= cost and
                self.has_spellbook)

    def cast_spell(self, spell: dict) -> bool:
        if self.can_cast(spell):
            self.spell_points -= spell.get("cost", 0)
            return True
        return False

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "hero_class": self.hero_class,
            "faction": self.faction,
            "player_id": self.player_id,
            "level": self.level,
            "experience": self.experience,
            "attack": self.attack,
            "defense": self.defense,
            "power": self.power,
            "knowledge": self.knowledge,
            "spell_points": self.spell_points,
            "max_spell_points": self.max_spell_points,
            "secondary_skills": self.secondary_skills,
            "spells": self.spells,
            "army": self.army,
            "map_x": self.map_x,
            "map_y": self.map_y,
            "movement_points": self.movement_points,
        }
