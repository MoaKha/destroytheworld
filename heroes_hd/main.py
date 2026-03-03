#!/usr/bin/env python3
"""
Heroes of Might & Magic III - HD Edition
A fan-made high-definition recreation of the classic HoMM3 game.

Features:
- All 9 original factions: Castle, Rampart, Tower, Inferno, Necropolis,
  Dungeon, Stronghold, Fortress, Conflux
- 126 creatures (14 per faction including upgrades)
- Hex-grid tactical combat with all original abilities
- Town building system with 9 unique faction buildings
- Hero progression with primary/secondary skills
- Complete spell system (4 schools, 50+ spells)
- Random map generator with zone-based generation
- Fog of war and pathfinding
- Resource management (7 resource types)
- Basic AI opponents
- Extensible creature system via JSON data files

Controls:
- Left click: Select hero / Move / Interact
- Right click: Show info / Cancel
- Arrow keys / WASD: Scroll map
- Enter: End turn
- H: Cycle through heroes
- ESC: Cancel / Back
- F5: Return to main menu

Usage:
    python main.py                    # Start with default settings
    python main.py --players 2        # 2 human players (hotseat)
    python main.py --cpu 3            # 1 human vs 3 CPU
    python main.py --size large       # Large map
    python main.py --seed 12345       # Specific random seed
    python main.py --fullscreen       # Fullscreen mode
"""
import sys
import os
import argparse
import pygame

# Ensure we can import from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, TARGET_FPS,
                    FULLSCREEN, MAP_SMALL, MAP_MEDIUM, MAP_LARGE, MAP_EXTRA_LARGE)
from engine.renderer import Renderer
from engine.state_machine import StateMachine
from ui.main_menu import MainMenuState
from ui.adventure_ui import AdventureUIState
from ui.town_ui import TownUIState
from ui.combat_ui import CombatUIState


class HeroesHD:
    """Main game application."""

    def __init__(self, args):
        self.args = args
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        # Create window
        flags = pygame.FULLSCREEN if args.fullscreen else 0
        if args.fullscreen:
            info = pygame.display.Info()
            w, h = info.current_w, info.current_h
        else:
            w, h = WINDOW_WIDTH, WINDOW_HEIGHT

        self.screen = pygame.display.set_mode((w, h), flags)
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.game_manager = None
        self.current_town = None
        self.current_combat = None

        # Renderer
        self.renderer = Renderer(self.screen)

        # State machine
        self.sm = StateMachine(self)
        self.sm.register("main_menu", MainMenuState(self))
        self.sm.register("adventure", AdventureUIState(self))
        self.sm.register("town", TownUIState(self))
        self.sm.register("combat", CombatUIState(self))
        self.sm.switch("main_menu")

    def start_new_game(self, num_human: int = None, num_cpu: int = None,
                       map_size: int = None, seed: int = None):
        """Start a new game with given parameters."""
        from game.game_manager import create_game
        from config import ALL_FACTIONS

        num_human = num_human or self.args.players
        num_cpu = num_cpu or self.args.cpu

        size_map = {
            "small": MAP_SMALL,
            "medium": MAP_MEDIUM,
            "large": MAP_LARGE,
            "xl": MAP_EXTRA_LARGE,
        }
        map_size = map_size or size_map.get(self.args.size, MAP_MEDIUM)
        seed = seed or self.args.seed

        print(f"Generating map (size={map_size}, players={num_human}, cpu={num_cpu}, seed={seed})...")
        self.game_manager, _ = create_game(
            num_human=num_human,
            num_cpu=num_cpu,
            map_size=map_size,
            seed=seed,
        )
        print("Map generated! Starting game...")

    def start_random_map(self):
        """Start a game with a fresh random map."""
        import random
        self.start_new_game(seed=random.randint(1, 999999))

    def enter_town(self, town):
        """Set the current town for the town UI."""
        self.current_town = town

    def start_combat(self, combat_manager):
        """Set and start a combat encounter."""
        self.current_combat = combat_manager

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0  # seconds
            dt = min(dt, 0.05)  # Cap at 50ms to prevent spiral of death

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.sm.handle_event(event)

            # Update
            self.sm.update(dt)

            # Draw
            self.sm.draw(self.renderer)
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Heroes of Might & Magic III - HD Edition"
    )
    parser.add_argument("--players", type=int, default=1,
                        help="Number of human players (default: 1)")
    parser.add_argument("--cpu", type=int, default=1,
                        help="Number of CPU opponents (default: 1)")
    parser.add_argument("--size", choices=["small", "medium", "large", "xl"],
                        default="medium", help="Map size (default: medium)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for map generation")
    parser.add_argument("--fullscreen", action="store_true",
                        help="Launch in fullscreen mode")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    game = HeroesHD(args)
    game.run()
