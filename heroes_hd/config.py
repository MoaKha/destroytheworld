"""Global configuration constants for Heroes HD."""

# Window settings
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
WINDOW_TITLE = "Heroes of Might & Magic III - HD Edition"
TARGET_FPS = 60
FULLSCREEN = False

# Adventure map tile size (pixels)
TILE_SIZE = 64
TILE_SIZE_HD = 96  # HD tiles

# Combat hex grid
HEX_SIZE = 48
COMBAT_GRID_COLS = 17
COMBAT_GRID_ROWS = 11

# Map sizes
MAP_SMALL = 36
MAP_MEDIUM = 72
MAP_LARGE = 108
MAP_EXTRA_LARGE = 144

# Resources
RESOURCES = ["gold", "wood", "ore", "mercury", "sulfur", "crystal", "gems"]
STARTING_GOLD = 20000
STARTING_WOOD = 20
STARTING_ORE = 20

# Hero movement
HERO_MOVEMENT_BASE = 1500  # movement points per day
HERO_SPEED_MULTIPLIER = 1.0

# Turn system
MAX_PLAYERS = 8
DAYS_PER_WEEK = 7
WEEKS_PER_MONTH = 4

# AI difficulty
AI_EASY = 0
AI_NORMAL = 1
AI_HARD = 2
AI_EXPERT = 3

# Colors (RGB)
COLOR_GOLD = (255, 215, 0)
COLOR_SILVER = (192, 192, 192)
COLOR_RED = (220, 50, 47)
COLOR_GREEN = (0, 200, 0)
COLOR_BLUE = (30, 144, 255)
COLOR_DARK_BG = (20, 20, 30)
COLOR_PANEL_BG = (40, 35, 25)
COLOR_PANEL_BORDER = (100, 80, 40)
COLOR_TEXT_NORMAL = (220, 200, 150)
COLOR_TEXT_HIGHLIGHT = (255, 240, 180)
COLOR_TEXT_DISABLED = (120, 110, 80)

# Player colors
PLAYER_COLORS = [
    (220, 50, 47),   # Red
    (30, 144, 255),  # Blue
    (139, 90, 43),   # Brown (Tan)
    (50, 200, 50),   # Green
    (255, 165, 0),   # Orange
    (148, 0, 211),   # Purple
    (0, 190, 190),   # Teal
    (220, 220, 220), # White
]

# Terrain types
TERRAIN_GRASS = "grass"
TERRAIN_DIRT = "dirt"
TERRAIN_SAND = "sand"
TERRAIN_SNOW = "snow"
TERRAIN_SWAMP = "swamp"
TERRAIN_LAVA = "lava"
TERRAIN_ROUGH = "rough"
TERRAIN_SUBTERRANEAN = "subterranean"
TERRAIN_WATER = "water"
TERRAIN_ROCK = "rock"

TERRAIN_MOVEMENT_COST = {
    TERRAIN_GRASS: 100,
    TERRAIN_DIRT: 100,
    TERRAIN_SAND: 150,
    TERRAIN_SNOW: 150,
    TERRAIN_SWAMP: 175,
    TERRAIN_LAVA: 150,
    TERRAIN_ROUGH: 125,
    TERRAIN_SUBTERRANEAN: 100,
    TERRAIN_WATER: 999,  # impassable on land
    TERRAIN_ROCK: 999,   # impassable
}

TERRAIN_COLORS = {
    TERRAIN_GRASS: (34, 139, 34),
    TERRAIN_DIRT: (139, 90, 43),
    TERRAIN_SAND: (210, 180, 140),
    TERRAIN_SNOW: (220, 235, 245),
    TERRAIN_SWAMP: (85, 107, 47),
    TERRAIN_LAVA: (180, 60, 20),
    TERRAIN_ROUGH: (160, 120, 80),
    TERRAIN_SUBTERRANEAN: (80, 60, 40),
    TERRAIN_WATER: (30, 100, 180),
    TERRAIN_ROCK: (80, 80, 80),
}

# Faction names
FACTION_CASTLE = "castle"
FACTION_RAMPART = "rampart"
FACTION_TOWER = "tower"
FACTION_INFERNO = "inferno"
FACTION_NECROPOLIS = "necropolis"
FACTION_DUNGEON = "dungeon"
FACTION_STRONGHOLD = "stronghold"
FACTION_FORTRESS = "fortress"
FACTION_CONFLUX = "conflux"

ALL_FACTIONS = [
    FACTION_CASTLE, FACTION_RAMPART, FACTION_TOWER,
    FACTION_INFERNO, FACTION_NECROPOLIS, FACTION_DUNGEON,
    FACTION_STRONGHOLD, FACTION_FORTRESS, FACTION_CONFLUX,
]

FACTION_COLORS = {
    FACTION_CASTLE: (220, 200, 150),
    FACTION_RAMPART: (34, 139, 34),
    FACTION_TOWER: (100, 180, 220),
    FACTION_INFERNO: (220, 50, 20),
    FACTION_NECROPOLIS: (80, 80, 120),
    FACTION_DUNGEON: (120, 60, 160),
    FACTION_STRONGHOLD: (180, 100, 40),
    FACTION_FORTRESS: (60, 120, 60),
    FACTION_CONFLUX: (180, 150, 220),
}

# Skill levels
SKILL_NONE = 0
SKILL_BASIC = 1
SKILL_ADVANCED = 2
SKILL_EXPERT = 3

SKILL_LEVEL_NAMES = {
    SKILL_NONE: "None",
    SKILL_BASIC: "Basic",
    SKILL_ADVANCED: "Advanced",
    SKILL_EXPERT: "Expert",
}

# Hero secondary skills
SECONDARY_SKILLS = [
    "archery", "armorer", "artillery", "ballistics", "diplomacy",
    "eagle_eye", "estates", "fire_magic", "first_aid", "intelligence",
    "irresistible_magic", "leadership", "learning", "logistics",
    "luck", "mysticism", "navigation", "necromancy", "offense",
    "pathfinding", "resistance", "scholar", "scouting", "sorcery",
    "tactics", "water_magic", "air_magic", "earth_magic", "wisdom",
]

# Spell schools
SCHOOL_FIRE = "fire"
SCHOOL_WATER = "water"
SCHOOL_EARTH = "earth"
SCHOOL_AIR = "air"

# Artifact slots
SLOT_HEAD = "head"
SLOT_NECK = "neck"
SLOT_SHOULDER = "shoulder"
SLOT_HAND = "hand"
SLOT_FEET = "feet"
SLOT_MISC = "misc"
SLOT_WEAPON = "weapon"
SLOT_SHIELD = "shield"
SLOT_CLOAK = "cloak"
SLOT_RING = "ring"

# Combat states
COMBAT_STATE_IDLE = "idle"
COMBAT_STATE_MOVE = "move"
COMBAT_STATE_ATTACK = "attack"
COMBAT_STATE_SPELL = "spell"
COMBAT_STATE_WAIT = "wait"
COMBAT_STATE_DEFEND = "defend"

# Object types on adventure map
OBJ_TOWN = "town"
OBJ_HERO = "hero"
OBJ_MINE = "mine"
OBJ_ARTIFACT = "artifact"
OBJ_RESOURCE = "resource"
OBJ_DWELLING = "dwelling"
OBJ_MONSTER = "monster"
OBJ_SHRINE = "shrine"
OBJ_WELL = "well"
OBJ_STABLE = "stable"
OBJ_TAVERN = "tavern"
OBJ_WHIRLPOOL = "whirlpool"
OBJ_SUBTERRANEAN_GATE = "subterranean_gate"
OBJ_TREE_OF_KNOWLEDGE = "tree_of_knowledge"
OBJ_LEARNING_STONE = "learning_stone"
OBJ_PANDORAS_BOX = "pandoras_box"
OBJ_TREASURE_CHEST = "treasure_chest"
