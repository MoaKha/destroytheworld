# Heroes of Might & Magic III — HD Edition

A faithful, high-definition fan recreation of the classic turn-based strategy game.

## Features

### 9 Complete Factions
Each with 14 creature types (7 base + 7 upgraded):

| Faction | Creatures (examples) | Specialty |
|---------|---------------------|-----------|
| **Castle** | Pikeman → Halberdier … Angel → Archangel | Morale, Leadership |
| **Rampart** | Centaur → Centaur Captain … Green Dragon → Gold Dragon | Magic Resistance |
| **Tower** | Gremlin → Master Gremlin … Giant → Titan | Ranged, Magic |
| **Inferno** | Imp → Familiar … Devil → Arch Devil | No Morale, Fire |
| **Necropolis** | Skeleton → Skeleton Warrior … Bone Dragon → Ghost Dragon | Undead, Necromancy |
| **Dungeon** | Troglodyte → Infernal Troglodyte … Red Dragon → Black Dragon | Magic Immunity |
| **Stronghold** | Goblin → Hobgoblin … Behemoth → Ancient Behemoth | Brute Strength |
| **Fortress** | Gnoll → Gnoll Marauder … Hydra → Chaos Hydra | Poison, Counter |
| **Conflux** | Pixie → Sprite … Firebird → Phoenix | Elemental Magic |

### Creature System
- 126 unique creature definitions in `data/creatures.json`
- **Fully extensible**: add new creatures by editing the JSON — no code changes needed
- Abilities: Flying, Ranged, Double Strike, No Retaliation, Life Drain, Breath Attack, and 40+ more
- Accurate HoMM3 stats: ATK, DEF, HP, DMG, Speed, Initiative, Growth

### Combat System
- **Hex-grid tactical battles** (17×11 grid)
- Initiative-based turn order
- Melee and ranged attacks with accurate HoMM3 damage formula
- Retaliation mechanics
- **51 spells** across 4 schools (Air, Fire, Water, Earth)
- Spell effects: Bless, Curse, Haste, Slow, Blind, Fireball, Armageddon, Resurrection, and more
- Basic AI combat opponent

### Adventure Map
- A* pathfinding with terrain movement costs
- Fog of war / area of vision per hero
- 9 terrain types (Grass, Dirt, Sand, Snow, Swamp, Lava, Rough, Water, Rock)
- Map objects: Towns, Mines, Monsters, Artifacts, Resources, Shrines, Wells, Treasure Chests

### Random Map Generator
- Zone-based generation (like original HoMM3 RMG)
- 9 zone templates: Player Start, Rich Mines, Dense Forest, Wasteland, Tundra, Volcanic, Swampland, Neutral Town, Treasure Trove
- Automatic corridor generation between zones
- Balanced starting positions for up to 8 players

### Town System
- Building construction with prerequisite chains
- Creature recruitment (weekly growth)
- Mage Guild (5 levels, random spell assignment)
- Fort / Citadel / Castle upgrades
- Daily gold income

### Hero System
- 18 hero classes across all 9 factions
- Primary stats: Attack, Defense, Power, Knowledge
- 29 secondary skills (Logistics, Necromancy, Eagle Eye, Wisdom, etc.)
- Artifact slots: Weapon, Shield, Head, Neck, Shoulder, Cloak, Feet, 2x Ring, 3x Misc
- 49 artifacts including Relics and combo sets
- Experience and level-up system

### Resources
- 7 resource types: Gold, Wood, Ore, Mercury, Sulfur, Crystal, Gems
- Mine capture and daily income
- Town income scaling with buildings

## Installation

```bash
# Install dependencies
pip install pygame numpy

# Run the game
python main.py

# Options:
python main.py --players 1 --cpu 2    # 1 human vs 2 CPU
python main.py --size large           # Large map
python main.py --seed 12345           # Fixed seed for reproducibility
python main.py --fullscreen           # Fullscreen mode
```

## Controls

| Key | Action |
|-----|--------|
| Left Click | Select hero / Move / Interact |
| Right Click | Show info / Cancel |
| Arrow Keys / WASD | Scroll map |
| **Enter** | End turn |
| **H** | Cycle through heroes |
| **ESC** | Cancel / Back |
| **W** (combat) | Wait |
| **D** (combat) | Defend |
| **A** (combat) | Attack mode |
| **F5** | Return to main menu |

## Extending the Game

### Adding New Creatures

Edit `data/creatures.json` to add creatures to any faction:

```json
{
  "my_faction": [
    {
      "id": "my_creature",
      "name": "My Creature",
      "upgraded": null,
      "tier": 1,
      "faction": "my_faction",
      "attack": 5, "defense": 5,
      "min_damage": 2, "max_damage": 4,
      "hp": 15,
      "speed": 5,
      "initiative": 10,
      "growth": 10,
      "ai_value": 120,
      "cost": {"gold": 80},
      "abilities": ["flying", "ranged"],
      "description": "My custom creature.",
      "color": [180, 100, 200]
    }
  ]
}
```

**Available abilities:**
`flying`, `ranged`, `double_shot`, `double_strike`, `no_enemy_retaliation`, `unlimited_retaliation`, `breath_attack`, `binding_attack`, `life_drain`, `drain_mana`, `undead`, `no_morale`, `magic_resistance`, `jousting`, `immune_fire`, `immune_to_mind`, `immune_to_magic_all`, `regeneration`, `multi_hex_attack`, `poison_attack`, `petrify_attack`, `death_stare`, `return_after_attack`, `dispel_on_attack`, `fire_shield`, `lightning_strike`, `summon_demons`, `raise_dead`

### Adding New Spells

Edit `data/spells.json`:

```json
{
  "fire": [
    {
      "id": "my_spell",
      "name": "My Spell",
      "level": 3,
      "cost": 12,
      "effect": "damage",
      "power": 20,
      "description": "A powerful custom spell.",
      "target": "enemy_unit"
    }
  ]
}
```

### Adding New Artifacts

Edit `data/artifacts.json`:

```json
{
  "treasures": [
    {
      "id": "my_artifact",
      "name": "My Artifact",
      "slot": "weapon",
      "class": "treasure",
      "cost": 5000,
      "bonus": {"attack": 3, "speed": 1},
      "description": "A custom artifact."
    }
  ]
}
```

## Architecture

```
heroes_hd/
├── main.py                 # Entry point
├── config.py               # All game constants
├── data_loader.py          # JSON data loading
├── data/
│   ├── creatures.json      # All 126 creature definitions
│   ├── spells.json         # 51 spells across 4 schools
│   └── artifacts.json      # 49 artifacts
├── engine/
│   ├── renderer.py         # HD rendering system
│   ├── camera.py           # Scrolling viewport
│   └── state_machine.py    # Game state management
├── game/
│   ├── resources.py        # Resource management
│   ├── hero.py             # Hero system
│   ├── town.py             # Town/building system
│   ├── adventure_map.py    # World map with A* pathfinding
│   ├── combat.py           # Hex-grid combat system
│   ├── player.py           # Player management
│   ├── ai_player.py        # AI opponent
│   └── game_manager.py     # Central game controller
├── map_generator/
│   └── generator.py        # Random map generator
└── ui/
    ├── main_menu.py        # Main menu
    ├── adventure_ui.py     # Adventure map screen
    ├── town_ui.py          # Town management screen
    └── combat_ui.py        # Tactical combat screen
```

## Legal Notice

This is a fan-made educational recreation of Heroes of Might & Magic III.
Heroes of Might & Magic III is a trademark of Ubisoft Entertainment.
Original game: https://store.ubisoft.com/ie/heroes-of-might-and-magic-iii--complete/575ffd9ba3be1633568b4d8c.html
This project does not include any original game assets or copyrighted content.
