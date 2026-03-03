"""Player management for Heroes HD."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from game.resources import Resources
from game.hero import Hero
from config import PLAYER_COLORS, AI_NORMAL


@dataclass
class Player:
    """Represents a human or AI player."""
    player_id: int
    name: str
    is_human: bool = True
    ai_difficulty: int = AI_NORMAL
    faction: str = "castle"
    color: tuple = field(default_factory=lambda: (220, 50, 47))

    # Resources
    resources: Resources = field(default_factory=Resources)

    # Heroes and towns
    heroes: list = field(default_factory=list)
    towns: list = field(default_factory=list)

    # State
    is_active: bool = True
    turn_done: bool = False
    has_lost: bool = False

    # Day tracking
    days_played: int = 0

    def __post_init__(self):
        if self.player_id < len(PLAYER_COLORS):
            self.color = PLAYER_COLORS[self.player_id]

    def add_hero(self, hero: Hero):
        self.heroes.append(hero)
        hero.player_id = self.player_id

    def remove_hero(self, hero: Hero):
        if hero in self.heroes:
            self.heroes.remove(hero)

    def add_town(self, town):
        self.towns.append(town)
        town.player_id = self.player_id

    def remove_town(self, town):
        if town in self.towns:
            self.towns.remove(town)

    def new_day(self, game_map):
        """Process start of new day for this player."""
        self.days_played += 1

        # Collect town income
        for town in self.towns:
            income = town.get_daily_income()
            self.resources.add(income)

        # Collect mine income
        mine_income = game_map.get_mine_income(self.player_id)
        self.resources.add(mine_income)

        # Reset hero movement
        for hero in self.heroes:
            hero.new_day()

    def new_week(self, creature_db: dict):
        """Process start of new week (creature growth)."""
        for town in self.towns:
            town.weekly_growth(creature_db)

    def check_defeat(self) -> bool:
        """Check if this player has been defeated."""
        if not self.heroes and not self.towns:
            self.has_lost = True
            self.is_active = False
            return True
        return False

    def get_all_heroes_movement_done(self) -> bool:
        """Returns True if all heroes have used their movement."""
        return all(h.movement_points <= 0 for h in self.heroes)

    @property
    def total_army_strength(self) -> int:
        """Rough estimate of total army strength."""
        total = 0
        for hero in self.heroes:
            for stack in hero.army.values():
                total += stack["count"] * 100  # simplified
        return total
