"""Central game manager for Heroes HD."""
from __future__ import annotations
import random
from typing import Optional, List
from game.player import Player
from game.hero import Hero, HERO_CLASSES, HERO_NAMES_BY_FACTION
from game.town import Town
from game.resources import Resources
from game.adventure_map import AdventureMap, MapObject
from game.combat import CombatManager
from game.ai_player import AIPlayer
from data_loader import DataLoader
from config import (ALL_FACTIONS, PLAYER_COLORS, OBJ_HERO, OBJ_TOWN,
                    OBJ_MINE, OBJ_RESOURCE, OBJ_MONSTER, OBJ_ARTIFACT,
                    OBJ_TREASURE_CHEST, OBJ_SHRINE, OBJ_WELL,
                    DAYS_PER_WEEK, WEEKS_PER_MONTH)


class GameManager:
    """Manages the complete game state and turn logic."""

    def __init__(self):
        self.players: list[Player] = []
        self.game_map: Optional[AdventureMap] = None
        self.current_player_idx: int = 0
        self.current_day: int = 1
        self.current_turn: int = 1
        self.creature_db: dict = {}
        self.spell_db: dict = {}
        self.artifact_db: dict = {}
        self.ai_players: dict[int, AIPlayer] = {}
        self.human_player_id: int = 0
        self.pending_combat: Optional[CombatManager] = None
        self._rng = random.Random()

    def initialize(self, players: list[Player], game_map: AdventureMap):
        """Set up a new game."""
        self.players = players
        self.game_map = game_map
        self.creature_db = DataLoader.load_creatures()
        self.spell_db = DataLoader.load_spells_flat()
        self.artifact_db = DataLoader.load_artifacts_flat()
        self.current_player_idx = 0
        self.current_day = 1
        self.current_turn = 1

        # Set up AI players
        for player in players:
            if not player.is_human:
                self.ai_players[player.player_id] = AIPlayer(player, self.creature_db)

        # Weekly growth for all towns
        for player in players:
            player.new_week(self.creature_db)

        # Place hero objects on map
        for player in players:
            for hero in player.heroes:
                hero_obj = MapObject(
                    obj_type=OBJ_HERO, x=hero.map_x, y=hero.map_y,
                    data={"hero": hero}, player_id=player.player_id
                )
                game_map.place_object(hero_obj)
                # Reveal around starting hero
                game_map.reveal_around(hero.map_x, hero.map_y, 6)

    @property
    def current_player(self) -> Optional[Player]:
        if 0 <= self.current_player_idx < len(self.players):
            return self.players[self.current_player_idx]
        return None

    def end_player_turn(self):
        """End the current player's turn and advance to next player."""
        current = self.current_player
        if current:
            current.turn_done = True

        # Advance to next active player
        num_players = len(self.players)
        for _ in range(num_players):
            self.current_player_idx = (self.current_player_idx + 1) % num_players
            next_player = self.players[self.current_player_idx]
            if next_player.is_active and not next_player.has_lost:
                break

        # Check if we've wrapped around (new day)
        if self.current_player_idx == 0:
            self._advance_day()

        # Reset turn_done for next player
        next_p = self.current_player
        if next_p:
            next_p.turn_done = False

    def _advance_day(self):
        """Process a new day."""
        self.current_day += 1
        self.current_turn += 1

        # New day for all players
        for player in self.players:
            player.new_day(self.game_map)

        # Weekly events
        if self.current_day % DAYS_PER_WEEK == 1:
            self._process_new_week()

    def _process_new_week(self):
        """Process weekly events (creature growth, etc.)."""
        # Week of plague: 10% chance
        week_mult = 1.0
        if self._rng.random() < 0.05:
            week_mult = 0.0  # Plague week - no growth
        elif self._rng.random() < 0.1:
            week_mult = 2.0  # Double growth week

        for player in self.players:
            player.new_week(self.creature_db)

    def run_ai_turns(self):
        """Run AI turns until it's a human player's turn."""
        while self.current_player and not self.current_player.is_human:
            ai = self.ai_players.get(self.current_player.player_id)
            if ai:
                ai.take_turn(self.game_map, self.players)
            self.end_player_turn()

    def handle_encounter(self, hero: Hero, objects: list[MapObject],
                         tx: int, ty: int) -> Optional[str]:
        """Handle when a hero steps onto a tile with objects.
        Returns 'combat', 'pickup', etc. or None."""
        player = next((p for p in self.players if p.player_id == hero.player_id), None)
        if not player:
            return None

        result = None
        for obj in list(objects):
            if obj.obj_type == OBJ_MINE:
                if obj.player_id != hero.player_id:
                    obj.player_id = hero.player_id
                    result = "mine_captured"

            elif obj.obj_type == OBJ_RESOURCE:
                res = obj.data.get("resource", "gold")
                amount = obj.data.get("amount", 0)
                player.resources.add({res: amount})
                self.game_map.remove_object(obj)
                result = "resource"

            elif obj.obj_type == OBJ_TREASURE_CHEST:
                gold = obj.data.get("gold", 500)
                exp = obj.data.get("exp", 250)
                player.resources.add({"gold": gold})
                hero.gain_experience(exp)
                self.game_map.remove_object(obj)
                result = "treasure"

            elif obj.obj_type == OBJ_ARTIFACT:
                art_id = obj.data.get("artifact_id")
                if art_id:
                    art_data = self.artifact_db.get(art_id)
                    if art_data:
                        hero.backpack.append(art_data)
                self.game_map.remove_object(obj)
                result = "artifact"

            elif obj.obj_type == OBJ_SHRINE:
                spell_id = obj.data.get("spell_id")
                if spell_id and hero.has_spellbook:
                    hero.learn_spell(spell_id)
                result = "shrine"

            elif obj.obj_type == OBJ_WELL:
                hero.spell_points = hero.max_spell_points
                result = "well"

            elif obj.obj_type == OBJ_MONSTER:
                # Initiate combat
                army = {
                    0: {
                        "creature": obj.data.get("creature_id", "pikeman"),
                        "count": obj.data.get("count", 10),
                    }
                }
                self.pending_combat = self._create_combat(hero, None, army, obj.player_id)
                self.game_map.remove_object(obj)
                return "combat"

            elif obj.obj_type == OBJ_TOWN:
                town = obj.data.get("town")
                if town and town.player_id != hero.player_id and town.player_id != -1:
                    # Enemy town — combat!
                    result = "combat"
                elif town:
                    # Friendly or neutral town
                    result = "town"

        return result

    def _create_combat(self, attacker_hero: Hero, defender_hero: Optional[Hero],
                       defender_army: dict = None, defender_player_id: int = -1) -> CombatManager:
        """Create a combat encounter."""
        attacker_army = attacker_hero.army if attacker_hero else {}
        if defender_army is None:
            defender_army = defender_hero.army if defender_hero else {}

        # Create placeholder hero data for defender if no hero
        class SimpleHero:
            def __init__(self, pid):
                self.player_id = pid
                self.effective_attack = 0
                self.effective_defense = 0
                self.effective_power = 1
                self.effective_knowledge = 1
                self.spell_points = 0
                self.max_spell_points = 0
                self.spells = []
                self.has_spellbook = False
                def cast_spell(self, spell): return False

        def_hero = defender_hero or SimpleHero(defender_player_id)

        combat = CombatManager(
            attacker_hero=attacker_hero,
            defender_hero=def_hero,
            attacker_army=attacker_army,
            defender_army=defender_army,
            creature_db=self.creature_db,
        )
        return combat

    def apply_combat_result(self, combat: CombatManager):
        """Apply combat results back to the game world."""
        winner_id = combat.is_combat_over()
        if winner_id is None:
            return

        # Update hero armies with survivors
        for unit in combat.units:
            if unit.player_id == combat.attacker_hero.player_id if combat.attacker_hero else -1:
                hero = combat.attacker_hero
                if hero and unit.slot in hero.army:
                    if unit.alive:
                        hero.army[unit.slot]["count"] = unit.count
                    else:
                        del hero.army[unit.slot]

        # Check for player defeat
        for player in self.players:
            player.check_defeat()

    def check_victory(self) -> Optional[int]:
        """Returns winning player_id, or None if game continues."""
        active = [p for p in self.players if p.is_active and not p.has_lost]
        if len(active) == 1:
            return active[0].player_id
        # All opponents eliminated
        human = next((p for p in self.players if p.is_human and not p.has_lost), None)
        if human and all(p.has_lost for p in self.players if not p.is_human):
            return human.player_id
        return None


def create_game(num_human: int = 1, num_cpu: int = 1,
                factions: list[str] = None, map_size: int = 72,
                seed: int = None) -> "tuple[GameManager, AdventureMap]":
    """Factory function to create a complete new game."""
    from map_generator.generator import RandomMapGenerator

    rng = random.Random(seed)
    total = num_human + num_cpu
    if not factions:
        factions = rng.sample(ALL_FACTIONS, min(total, len(ALL_FACTIONS)))

    # Create players
    players: list[Player] = []
    for i in range(total):
        faction = factions[i % len(factions)]
        is_human = (i < num_human)
        player = Player(
            player_id=i,
            name=f"Player {i+1}" if is_human else f"CPU {i - num_human + 1}",
            is_human=is_human,
            faction=faction,
            resources=Resources(),
        )
        players.append(player)

    # Generate map
    gen = RandomMapGenerator(map_size=map_size, num_players=num_human,
                             num_cpu=num_cpu, seed=seed)
    creature_db = DataLoader.load_creatures()
    game_map = gen.generate(creature_db)

    # Assign starting positions: find player towns
    town_objs = game_map.get_objects_by_type(OBJ_TOWN)
    player_towns = [t for t in town_objs if t.player_id >= 0]
    player_towns.sort(key=lambda t: t.player_id)

    # Give each player starting hero near their town
    hero_classes_by_faction = {
        "castle": "knight", "rampart": "ranger", "tower": "alchemist",
        "inferno": "demoniac", "necropolis": "death_knight", "dungeon": "overlord",
        "stronghold": "barbarian", "fortress": "beastmaster", "conflux": "planeswalker",
    }

    for i, player in enumerate(players):
        # Find player town
        town_obj = next((t for t in town_objs if t.player_id == i), None)
        if not town_obj:
            # Assign first available neutral town
            neutral_towns = [t for t in town_objs if t.player_id == -1]
            if neutral_towns:
                town_obj = neutral_towns[0]
                town_obj.player_id = i
                town_obj.data["town"].player_id = i

        if town_obj:
            town = town_obj.data.get("town")
            if town:
                player.add_town(town)

        # Create starting hero
        faction = player.faction
        hero_class = hero_classes_by_faction.get(faction, "knight")
        hero = Hero(hero_class=hero_class, player_id=i)

        # Place hero near town
        if town_obj:
            hero.map_x = min(game_map.width - 1, town_obj.x + 1)
            hero.map_y = town_obj.y
        else:
            hero.map_x = rng.randint(5, map_size - 5)
            hero.map_y = rng.randint(5, map_size - 5)

        # Give starting army based on faction
        starting_creatures = {
            "castle": [("pikeman", 20), ("archer", 10)],
            "rampart": [("centaur", 20), ("wood_elf", 8)],
            "tower": [("gremlin", 30), ("stone_gargoyle", 10)],
            "inferno": [("imp", 30), ("gog", 10)],
            "necropolis": [("skeleton", 25), ("walking_dead", 10)],
            "dungeon": [("troglodyte", 25), ("harpy", 10)],
            "stronghold": [("goblin", 30), ("wolf_rider", 10)],
            "fortress": [("gnoll", 25), ("lizardman", 10)],
            "conflux": [("pixie", 30), ("air_elemental", 8)],
        }
        army = starting_creatures.get(faction, [("pikeman", 20)])
        for cid, count in army:
            hero.add_creature(cid, count)

        player.add_hero(hero)

    # Create and initialize game manager
    gm = GameManager()
    gm.human_player_id = 0 if num_human > 0 else -1
    gm.initialize(players, game_map)

    return gm, game_map
