"""Game state machine managing transitions between screens."""
from typing import Optional


class GameState:
    """Base class for all game states."""

    def __init__(self, game):
        self.game = game

    def on_enter(self, previous_state=None):
        """Called when this state becomes active."""

    def on_exit(self):
        """Called when leaving this state."""

    def handle_event(self, event):
        """Handle a pygame event. Return new state name to transition, or None."""

    def update(self, dt: float):
        """Update game logic."""

    def draw(self, renderer):
        """Draw the state."""


class StateMachine:
    """Manages the stack of game states."""

    def __init__(self, game):
        self.game = game
        self._states: dict[str, GameState] = {}
        self._current: Optional[GameState] = None
        self._current_name: Optional[str] = None
        self._stack: list[tuple[str, GameState]] = []

    def register(self, name: str, state: GameState):
        self._states[name] = state

    def switch(self, name: str, **kwargs):
        """Switch to a state by name."""
        if self._current:
            self._current.on_exit()
        prev = self._current_name
        self._current_name = name
        self._current = self._states[name]
        self._current.on_enter(previous_state=prev, **kwargs)

    def push(self, name: str, **kwargs):
        """Push a state onto the stack (pausing the current one)."""
        if self._current:
            self._stack.append((self._current_name, self._current))
        self.switch(name, **kwargs)

    def pop(self):
        """Return to the previous state."""
        if self._stack:
            name, state = self._stack.pop()
            if self._current:
                self._current.on_exit()
            self._current_name = name
            self._current = state
            self._current.on_enter(previous_state=self._current_name)

    def handle_event(self, event):
        if self._current:
            result = self._current.handle_event(event)
            if result and isinstance(result, str):
                self.switch(result)

    def update(self, dt: float):
        if self._current:
            result = self._current.update(dt)
            if result and isinstance(result, str):
                self.switch(result)

    def draw(self, renderer):
        if self._current:
            self._current.draw(renderer)

    @property
    def current_name(self) -> Optional[str]:
        return self._current_name
