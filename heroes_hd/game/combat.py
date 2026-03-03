"""Hex-grid combat system for Heroes HD."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import random
import math
from config import (COMBAT_GRID_COLS, COMBAT_GRID_ROWS, HEX_SIZE,
                    COMBAT_STATE_IDLE, COMBAT_STATE_MOVE, COMBAT_STATE_ATTACK,
                    COMBAT_STATE_SPELL, COMBAT_STATE_WAIT, COMBAT_STATE_DEFEND)


@dataclass
class CombatUnit:
    """A stack of creatures in combat."""
    creature_id: str
    creature_data: dict
    count: int
    player_id: int
    slot: int  # 0-6
    col: int = 0
    row: int = 0

    # Runtime stats
    current_hp: int = 0
    has_acted: bool = False
    is_waiting: bool = False
    is_defending: bool = False
    effects: list = field(default_factory=list)  # active spell effects

    def __post_init__(self):
        self.current_hp = self.creature_data.get("hp", 10)

    @property
    def alive(self) -> bool:
        return self.count > 0

    @property
    def is_ranged(self) -> bool:
        return "ranged" in self.creature_data.get("abilities", [])

    @property
    def can_fly(self) -> bool:
        return "flying" in self.creature_data.get("abilities", [])

    @property
    def speed(self) -> int:
        base = self.creature_data.get("speed", 4)
        for eff in self.effects:
            if eff["type"] == "speed_boost":
                base += eff.get("value", 0)
            elif eff["type"] == "speed_reduction":
                base = max(1, base - eff.get("value", 0))
        return base

    @property
    def attack(self) -> int:
        return self.creature_data.get("attack", 5)

    @property
    def defense(self) -> int:
        base = self.creature_data.get("defense", 5)
        if self.is_defending:
            base += self.creature_data.get("defense", 5) // 4
        return base

    @property
    def initiative(self) -> int:
        return self.creature_data.get("initiative", 10)

    @property
    def total_hp(self) -> int:
        hp = self.creature_data.get("hp", 10)
        return (self.count - 1) * hp + self.current_hp

    def roll_damage(self, hero_attack_bonus: int = 0,
                    target_defense: int = 0,
                    hero_defense_bonus: int = 0) -> int:
        """Calculate damage dealt to a target."""
        min_dmg = self.creature_data.get("min_damage", 1)
        max_dmg = self.creature_data.get("max_damage", 3)
        base = random.randint(min_dmg, max_dmg) * self.count

        # Attack vs defense calculation (HoMM3 formula)
        net_atk = self.attack + hero_attack_bonus
        net_def = max(0, target_defense + hero_defense_bonus)

        if net_atk >= net_def:
            bonus = min(3.0, 1.0 + 0.05 * (net_atk - net_def))
        else:
            bonus = max(0.3, 1.0 - 0.025 * (net_def - net_atk))

        # Check for bless / curse effects
        for eff in self.effects:
            if eff["type"] == "bless":
                base = max_dmg * self.count
            elif eff["type"] == "curse":
                base = min_dmg * self.count

        return max(1, int(base * bonus))

    def take_damage(self, damage: int) -> int:
        """Apply damage. Returns number of creatures killed."""
        hp = self.creature_data.get("hp", 10)
        killed = 0

        remaining = damage
        while remaining > 0 and self.count > 0:
            if remaining >= self.current_hp:
                remaining -= self.current_hp
                self.count -= 1
                killed += 1
                self.current_hp = hp
            else:
                self.current_hp -= remaining
                remaining = 0

        return killed

    def heal(self, amount: int):
        """Heal up to maximum HP."""
        hp_per = self.creature_data.get("hp", 10)
        self.current_hp = min(hp_per, self.current_hp + amount)

    def tick_effects(self):
        """Remove expired effects and apply DoT."""
        remaining = []
        for eff in self.effects:
            eff["duration"] -= 1
            if eff["duration"] > 0:
                remaining.append(eff)
        self.effects = remaining

    def add_effect(self, effect_type: str, value: int = 0, duration: int = 3):
        # Don't stack same effects
        self.effects = [e for e in self.effects if e["type"] != effect_type]
        self.effects.append({"type": effect_type, "value": value, "duration": duration})


@dataclass
class HexGrid:
    """Hexagonal combat grid."""
    cols: int = COMBAT_GRID_COLS
    rows: int = COMBAT_GRID_ROWS
    obstacles: set = field(default_factory=set)  # set of (col, row)

    def neighbors(self, col: int, row: int) -> list[tuple[int, int]]:
        """Get valid neighbor hexes (6-connected)."""
        if row % 2 == 0:
            dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1)]
        else:
            dirs = [(-1,0),(1,0),(0,-1),(0,1),(1,-1),(1,1)]
        result = []
        for dc, dr in dirs:
            nc, nr = col + dc, row + dr
            if 0 <= nc < self.cols and 0 <= nr < self.rows:
                if (nc, nr) not in self.obstacles:
                    result.append((nc, nr))
        return result

    def distance(self, c1: int, r1: int, c2: int, r2: int) -> int:
        """Hex distance using cube coordinates."""
        def offset_to_cube(c, r):
            x = c - (r - (r & 1)) // 2
            z = r
            y = -x - z
            return x, y, z
        ax, ay, az = offset_to_cube(c1, r1)
        bx, by, bz = offset_to_cube(c2, r2)
        return max(abs(ax-bx), abs(ay-by), abs(az-bz))

    def find_reachable(self, start_col: int, start_row: int,
                       speed: int, units: list[CombatUnit]) -> set[tuple[int, int]]:
        """BFS to find reachable hexes within speed steps."""
        import collections
        occupied = {(u.col, u.row) for u in units if u.alive}
        occupied.discard((start_col, start_row))

        visited = {(start_col, start_row): 0}
        queue = collections.deque([(start_col, start_row, 0)])
        reachable = set()

        while queue:
            col, row, dist = queue.popleft()
            for nc, nr in self.neighbors(col, row):
                if (nc, nr) in visited:
                    continue
                new_dist = dist + 1
                if new_dist <= speed and (nc, nr) not in occupied:
                    visited[(nc, nr)] = new_dist
                    reachable.add((nc, nr))
                    queue.append((nc, nr, new_dist))

        return reachable

    def find_attack_hexes(self, attacker_col: int, attacker_row: int,
                          target: CombatUnit, units: list[CombatUnit]) -> list[tuple[int, int]]:
        """Find hexes from which the attacker can melee attack the target."""
        target_neighbors = self.neighbors(target.col, target.row)
        occupied = {(u.col, u.row) for u in units if u.alive and u is not attacker_unit}
        # Remove occupied hexes except attacker position
        reachable = self.find_reachable(attacker_col, attacker_row,
                                        999, units)
        reachable.add((attacker_col, attacker_row))
        return [h for h in target_neighbors if h in reachable or h == (attacker_col, attacker_row)]

    def path_to(self, start_col: int, start_row: int,
                goal_col: int, goal_row: int,
                units: list[CombatUnit]) -> list[tuple[int, int]]:
        """A* path on hex grid avoiding other units."""
        import heapq
        occupied = {(u.col, u.row) for u in units if u.alive}
        occupied.discard((start_col, start_row))
        occupied.discard((goal_col, goal_row))

        def h(c, r):
            return self.distance(c, r, goal_col, goal_row)

        open_set = [(h(start_col, start_row), 0, start_col, start_row)]
        came_from: dict = {}
        g_score = {(start_col, start_row): 0}

        while open_set:
            _, cost, col, row = heapq.heappop(open_set)
            if (col, row) == (goal_col, goal_row):
                path = []
                cur = (goal_col, goal_row)
                while cur in came_from:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path
            for nc, nr in self.neighbors(col, row):
                if (nc, nr) in occupied and (nc, nr) != (goal_col, goal_row):
                    continue
                new_cost = cost + 1
                if new_cost < g_score.get((nc, nr), 999999):
                    g_score[(nc, nr)] = new_cost
                    came_from[(nc, nr)] = (col, row)
                    heapq.heappush(open_set, (new_cost + h(nc, nr), new_cost, nc, nr))
        return []


# Make the fix for the method that references 'attacker_unit' (which was a bug):
def _find_attack_hexes(grid: HexGrid, attacker: CombatUnit,
                       target: CombatUnit, units: list[CombatUnit]) -> list[tuple[int, int]]:
    target_neighbors = grid.neighbors(target.col, target.row)
    occupied = {(u.col, u.row) for u in units if u.alive and u is not attacker}
    reachable = grid.find_reachable(attacker.col, attacker.row, 999, units)
    reachable.add((attacker.col, attacker.row))
    return [h for h in target_neighbors if h in reachable]


class CombatManager:
    """Manages a complete combat encounter."""

    def __init__(self, attacker_hero, defender_hero,
                 attacker_army: dict, defender_army: dict,
                 creature_db: dict, terrain: str = "grass"):
        self.attacker_hero = attacker_hero
        self.defender_hero = defender_hero
        self.creature_db = creature_db
        self.terrain = terrain
        self.grid = HexGrid()
        self.turn_number = 0
        self.log: list[str] = []
        self.state = COMBAT_STATE_IDLE
        self.selected_unit: Optional[CombatUnit] = None
        self.active_unit: Optional[CombatUnit] = None
        self.reachable_hexes: set = set()
        self.attackable_units: list[CombatUnit] = []

        # Place units
        self.units: list[CombatUnit] = []
        self._place_army(attacker_army, player_id=attacker_hero.player_id if attacker_hero else 0,
                         side="left")
        self._place_army(defender_army, player_id=defender_hero.player_id if defender_hero else 1,
                         side="right")

        # Sort by initiative for turn order
        self._build_turn_queue()

    def _place_army(self, army: dict, player_id: int, side: str):
        col = 1 if side == "left" else COMBAT_GRID_COLS - 2
        rows = [5, 3, 7, 1, 9, 2, 8]  # placement rows
        for slot_idx, (slot, stack) in enumerate(sorted(army.items())):
            if slot_idx >= 7:
                break
            cid = stack["creature"]
            count = stack["count"]
            cdata = self.creature_db.get(cid)
            if not cdata or count <= 0:
                continue
            row = rows[slot_idx % len(rows)]
            unit = CombatUnit(
                creature_id=cid,
                creature_data=cdata,
                count=count,
                player_id=player_id,
                slot=slot,
                col=col,
                row=row,
            )
            self.units.append(unit)

    def _build_turn_queue(self):
        """Build initiative-based turn order (highest initiative first)."""
        self._turn_queue = sorted(
            [u for u in self.units if u.alive],
            key=lambda u: (-u.initiative, -u.speed)
        )
        self._queue_index = 0

    def next_turn(self) -> Optional[CombatUnit]:
        """Advance to the next unit's turn."""
        # Reset acted flags at start of each full round
        alive = [u for u in self.units if u.alive]
        if not alive:
            return None

        # Find next unit that hasn't acted
        for _ in range(len(self._turn_queue)):
            if self._queue_index >= len(self._turn_queue):
                # New round
                self.turn_number += 1
                for u in self.units:
                    u.has_acted = False
                    u.is_waiting = False
                    u.tick_effects()
                self._build_turn_queue()
                self._queue_index = 0

            unit = self._turn_queue[self._queue_index]
            self._queue_index += 1

            if unit.alive and not unit.has_acted and not unit.is_waiting:
                self.active_unit = unit
                self._compute_reachable()
                return unit

        return None

    def _compute_reachable(self):
        if not self.active_unit:
            return
        u = self.active_unit
        self.reachable_hexes = self.grid.find_reachable(u.col, u.row, u.speed, self.units)

        # Find attackable enemy units
        enemy_id = 1 - u.player_id if u.player_id in (0, 1) else (0 if u.player_id != 0 else 1)
        enemies = [eu for eu in self.units if eu.alive and eu.player_id != u.player_id]
        if u.is_ranged:
            self.attackable_units = enemies
        else:
            # Melee: must be adjacent or reachable
            self.attackable_units = []
            for enemy in enemies:
                attack_hexes = _find_attack_hexes(self.grid, u, enemy, self.units)
                if attack_hexes:
                    self.attackable_units.append(enemy)

    def move_unit(self, unit: CombatUnit, target_col: int, target_row: int) -> bool:
        """Move a unit to a hex."""
        if (target_col, target_row) not in self.reachable_hexes:
            return False
        unit.col = target_col
        unit.row = target_row
        self._compute_reachable()
        return True

    def attack(self, attacker: CombatUnit, target: CombatUnit) -> dict:
        """Perform a melee or ranged attack. Returns combat result dict."""
        results = {"attacker": attacker, "target": target, "damage": 0,
                   "killed": 0, "retaliation_damage": 0, "retaliation_killed": 0,
                   "log": []}

        hero_atk = self.attacker_hero.effective_attack if (
            self.attacker_hero and attacker.player_id == self.attacker_hero.player_id
        ) else 0
        hero_def = self.defender_hero.effective_defense if (
            self.defender_hero and target.player_id == self.defender_hero.player_id
        ) else 0

        # Compute damage
        damage = attacker.roll_damage(
            hero_attack_bonus=hero_atk,
            target_defense=target.defense,
            hero_defense_bonus=hero_def,
        )

        # Double strike
        if "double_strike" in attacker.creature_data.get("abilities", []):
            damage = attacker.roll_damage(hero_atk, target.defense, hero_def) * 2

        killed = target.take_damage(damage)
        results["damage"] = damage
        results["killed"] = killed

        msg = (f"{attacker.creature_data['name']} x{attacker.count} attacks "
               f"{target.creature_data['name']} x{target.count + killed} for {damage} damage")
        if killed:
            msg += f", killing {killed}"
        results["log"].append(msg)
        self.log.append(msg)

        # Retaliation (if target survives and hasn't retaliated)
        can_retaliate = (target.alive and
                         "no_enemy_retaliation" not in attacker.creature_data.get("abilities", []) and
                         not attacker.is_ranged)
        if can_retaliate:
            ret_hero_atk = (self.defender_hero.effective_attack
                            if self.defender_hero and target.player_id == self.defender_hero.player_id
                            else 0)
            ret_hero_def = (self.attacker_hero.effective_defense
                            if self.attacker_hero and attacker.player_id == self.attacker_hero.player_id
                            else 0)
            ret_damage = target.roll_damage(ret_hero_atk, attacker.defense, ret_hero_def)
            ret_killed = attacker.take_damage(ret_damage)
            results["retaliation_damage"] = ret_damage
            results["retaliation_killed"] = ret_killed
            ret_msg = (f"{target.creature_data['name']} retaliates for {ret_damage} damage")
            if ret_killed:
                ret_msg += f", killing {ret_killed}"
            results["log"].append(ret_msg)
            self.log.append(ret_msg)

        attacker.has_acted = True
        return results

    def cast_spell(self, caster_hero, spell: dict,
                   target_unit: Optional[CombatUnit] = None,
                   target_col: int = -1, target_row: int = -1) -> dict:
        """Cast a spell in combat."""
        results = {"spell": spell, "log": []}
        effect = spell.get("effect", "")
        power = caster_hero.effective_power

        if effect == "damage" and target_unit:
            dmg = spell.get("power", 10) * power
            killed = target_unit.take_damage(dmg)
            msg = f"Spell {spell['name']} deals {dmg} damage to {target_unit.creature_data['name']}"
            if killed:
                msg += f", killing {killed}"
            results["log"].append(msg)
            self.log.append(msg)

        elif effect == "area_damage":
            victims = [u for u in self.units
                       if u.alive and u.player_id != caster_hero.player_id
                       and abs(u.col - target_col) <= 1 and abs(u.row - target_row) <= 1]
            for v in victims:
                dmg = spell.get("power", 10) * power
                killed = v.take_damage(dmg)
                msg = f"{spell['name']} hits {v.creature_data['name']} for {dmg}"
                if killed:
                    msg += f", killing {killed}"
                results["log"].append(msg)
                self.log.append(msg)

        elif effect == "all_damage":
            for u in self.units:
                if u.alive:
                    dmg = spell.get("power", 10) * power
                    u.take_damage(dmg)
            msg = f"{spell['name']} strikes all creatures!"
            results["log"].append(msg)
            self.log.append(msg)

        elif effect == "heal" and target_unit:
            heal_amount = spell.get("power", 5) * power
            target_unit.heal(heal_amount)
            results["log"].append(f"{spell['name']} heals {target_unit.creature_data['name']}")

        elif effect == "speed_boost" and target_unit:
            target_unit.add_effect("speed_boost", value=spell.get("power", 3), duration=3)
            results["log"].append(f"{spell['name']} boosts speed of {target_unit.creature_data['name']}")

        elif effect == "speed_reduction" and target_unit:
            target_unit.add_effect("speed_reduction", value=spell.get("power", 2), duration=3)
            results["log"].append(f"{spell['name']} slows {target_unit.creature_data['name']}")

        elif effect == "bless" and target_unit:
            target_unit.add_effect("bless", duration=3)
            results["log"].append(f"{spell['name']}: {target_unit.creature_data['name']} blessed")

        elif effect == "curse" and target_unit:
            target_unit.add_effect("curse", duration=3)
            results["log"].append(f"{spell['name']}: {target_unit.creature_data['name']} cursed")

        elif effect == "attack_boost" and target_unit:
            target_unit.add_effect("attack_boost", value=spell.get("power", 3), duration=3)
            results["log"].append(f"{spell['name']}: {target_unit.creature_data['name']} attack boosted")

        elif effect == "defense_boost" and target_unit:
            target_unit.add_effect("defense_boost", value=spell.get("power", 3), duration=3)
            results["log"].append(f"{spell['name']}: {target_unit.creature_data['name']} defense boosted")

        elif effect == "blind" and target_unit:
            target_unit.add_effect("blind", duration=2)
            results["log"].append(f"{spell['name']}: {target_unit.creature_data['name']} blinded!")

        elif effect == "resurrect" and target_unit:
            hp = target_unit.creature_data.get("hp", 10)
            resurrect_count = (spell.get("power", 40) * power) // hp
            target_unit.count += resurrect_count
            target_unit.current_hp = target_unit.creature_data["hp"]
            results["log"].append(f"{spell['name']} resurrects {resurrect_count} {target_unit.creature_data['name']}")

        caster_hero.cast_spell(spell)
        return results

    def wait(self, unit: CombatUnit):
        """Unit waits (acts later in the round)."""
        unit.is_waiting = True
        # Move to end of queue
        self._turn_queue.append(unit)

    def defend(self, unit: CombatUnit):
        """Unit defends (increases defense this round)."""
        unit.is_defending = True
        unit.has_acted = True

    def is_combat_over(self) -> Optional[int]:
        """Returns winning player_id, or -1 for draw, or None if ongoing."""
        alive_players = set(u.player_id for u in self.units if u.alive)
        if len(alive_players) == 0:
            return -1  # Draw
        if len(alive_players) == 1:
            return alive_players.pop()
        return None

    def get_combat_result(self) -> dict:
        """Final result summary."""
        winner = self.is_combat_over()
        alive_units = [u for u in self.units if u.alive]
        total_xp = sum(
            u.creature_data.get("ai_value", 0) * (original - u.count)
            for u in self.units
            for original in [u.count]  # simplified
        )
        return {
            "winner_player_id": winner,
            "alive_units": alive_units,
            "turn_count": self.turn_number,
            "log": self.log,
        }
