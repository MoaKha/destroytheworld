"""Camera / viewport for scrolling the adventure map."""
import pygame
from config import TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT


class Camera:
    """Tracks the viewport position over the map."""

    SCROLL_SPEED = 8  # tiles per second at border scroll
    BORDER_SIZE = 40  # pixels from edge that triggers scroll

    def __init__(self, map_width: int, map_height: int,
                 viewport_w: int = WINDOW_WIDTH, viewport_h: int = WINDOW_HEIGHT):
        self.map_width = map_width
        self.map_height = map_height
        self.viewport_w = viewport_w
        self.viewport_h = viewport_h
        # Position in pixel space
        self.x = 0.0
        self.y = 0.0
        # Smooth scrolling target
        self._target_x = 0.0
        self._target_y = 0.0

    @property
    def tile_offset_x(self) -> int:
        return int(self.x) // TILE_SIZE

    @property
    def tile_offset_y(self) -> int:
        return int(self.y) // TILE_SIZE

    @property
    def pixel_offset_x(self) -> int:
        return int(self.x) % TILE_SIZE

    @property
    def pixel_offset_y(self) -> int:
        return int(self.y) % TILE_SIZE

    @property
    def visible_tiles_x(self) -> int:
        return self.viewport_w // TILE_SIZE + 2

    @property
    def visible_tiles_y(self) -> int:
        return self.viewport_h // TILE_SIZE + 2

    def get_camera_rect(self) -> tuple[int, int, int, int]:
        """Returns (tile_x, tile_y, tiles_wide, tiles_tall) of visible area."""
        return (self.tile_offset_x, self.tile_offset_y,
                self.visible_tiles_x, self.visible_tiles_y)

    def center_on_tile(self, tile_x: int, tile_y: int):
        """Center camera on a tile coordinate."""
        target_px = tile_x * TILE_SIZE - self.viewport_w // 2 + TILE_SIZE // 2
        target_py = tile_y * TILE_SIZE - self.viewport_h // 2 + TILE_SIZE // 2
        self._target_x = max(0, min(target_px, self.max_x))
        self._target_y = max(0, min(target_py, self.max_y))
        self.x = self._target_x
        self.y = self._target_y

    def scroll_to(self, px: float, py: float):
        self._target_x = max(0, min(px, self.max_x))
        self._target_y = max(0, min(py, self.max_y))

    @property
    def max_x(self) -> float:
        return max(0.0, self.map_width * TILE_SIZE - self.viewport_w)

    @property
    def max_y(self) -> float:
        return max(0.0, self.map_height * TILE_SIZE - self.viewport_h)

    def update(self, dt: float, mouse_pos: tuple[int, int] = None, keys=None):
        """Smooth camera update; also handles edge scrolling and arrow keys."""
        speed = self.SCROLL_SPEED * TILE_SIZE * dt

        if mouse_pos:
            mx, my = mouse_pos
            if mx < self.BORDER_SIZE:
                self._target_x = max(0, self._target_x - speed)
            if mx > self.viewport_w - self.BORDER_SIZE:
                self._target_x = min(self.max_x, self._target_x + speed)
            if my < self.BORDER_SIZE:
                self._target_y = max(0, self._target_y - speed)
            if my > self.viewport_h - self.BORDER_SIZE:
                self._target_y = min(self.max_y, self._target_y + speed)

        if keys:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self._target_x = max(0, self._target_x - speed)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self._target_x = min(self.max_x, self._target_x + speed)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self._target_y = max(0, self._target_y - speed)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self._target_y = min(self.max_y, self._target_y + speed)

        # Lerp to target
        lerp_speed = min(1.0, dt * 12)
        self.x += (self._target_x - self.x) * lerp_speed
        self.y += (self._target_y - self.y) * lerp_speed

    def world_to_screen(self, wx: int, wy: int) -> tuple[int, int]:
        """Convert world tile coords to screen pixel coords."""
        sx = wx * TILE_SIZE - int(self.x)
        sy = wy * TILE_SIZE - int(self.y)
        return sx, sy

    def screen_to_world(self, sx: int, sy: int) -> tuple[int, int]:
        """Convert screen pixel to world tile coords."""
        wx = (sx + int(self.x)) // TILE_SIZE
        wy = (sy + int(self.y)) // TILE_SIZE
        return wx, wy
